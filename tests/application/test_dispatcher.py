"""The dispatcher hands an event to its handler, counts the errors and reports at the cap."""

from pathlib import Path
from typing import get_args

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, Handler, unhandled_kinds
from factory.application.machine import FactoryLog
from factory.application.stops import StopService
from factory.domain.errors import UnhandledEvent
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PostKey, render_post
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.post_texts import error_report_text
from factory.domain.tick_status import ErrorCount, TickStatus, find_error, record_error
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state
from git_support import remote_commit
from human_clone import HumanClone
from tick_support import Failing

WORK_ITEM = "F0001-S0001"
BRANCH = "work-item/F0001-S0001"
STATE = "a" * 40
OTHER_STATE = "b" * 40
BOOM = "ValueError: boom"
TITLED = "# Demo story\n\nSome text.\n"
ALL_KINDS: list[EventKind] = list(get_args(EventKind))


class Succeeding(Handler):
    """Records every event it is handed."""

    def __init__(self) -> None:
        self.calls: list[Event] = []

    def handle(self, event: Event) -> None:
        self.calls.append(event)


class FailingOnce(Handler):
    """Raises on its first call and succeeds afterwards."""

    def __init__(self) -> None:
        self.calls: list[Event] = []

    def handle(self, event: Event) -> None:
        self.calls.append(event)
        if len(self.calls) == 1:
            raise ValueError("boom")


class RecordingLog(FactoryLog):
    """Keeps the lines written to it."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)


def _snapshot(
    pull_request: int | None,
    *,
    branch_commit: str | None = STATE,
    body: str = TITLED,
) -> WorkItemSnapshot:
    state = initial_state("intake").model_copy(update={"pull_request": pull_request})
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=f"factory/features/F0001-demo/in-progress/{WORK_ITEM}-x.md",
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=WorkItemDocument(state=state, body=body),
    )


def _event(
    kind: EventKind = "run", *, snapshot: WorkItemSnapshot, remote_state: str = STATE
) -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state=remote_state)


def _idle_event() -> Event:
    return Event(kind="idle", work_item=None, remote_state=STATE)


def _open_pull_request(hosting: FakeHostingService) -> int:
    return hosting.create_pull_request(BRANCH, "opened by the test", "", draft=True).number


def _report_key(remote_state: str) -> PostKey:
    return PostKey(work_item=WORK_ITEM, kind="error", n=remote_state[:12])


def _entry(dispatcher: Dispatcher, event: Event) -> ErrorCount:
    entry = find_error(dispatcher.status, event.key, event.remote_state)
    assert entry is not None
    return entry


def test_handler_for_returns_the_registered_handler_and_raises_for_a_missing_one(
    boundaries: Boundaries,
) -> None:
    handler = Succeeding()
    handlers: dict[EventKind, Handler] = {"run": handler}
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))

    assert dispatcher.handler_for("run") is handler
    with pytest.raises(UnhandledEvent) as raised:
        dispatcher.handler_for("merged")
    assert raised.value.kind == "merged"


def test_unhandled_kinds_lists_every_kind_without_a_handler_in_order() -> None:
    every: dict[EventKind, Handler] = dict.fromkeys(ALL_KINDS, Succeeding())

    assert unhandled_kinds({}) == ALL_KINDS
    assert len(ALL_KINDS) == 13
    assert unhandled_kinds(every) == []


def test_a_succeeding_handler_is_called_once_and_clears_the_earlier_errors(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    event = _event(snapshot=_snapshot(_open_pull_request(hosting)))
    handler = FailingOnce()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries))
    assert dispatcher.dispatch(event) == "error"

    outcome = dispatcher.dispatch(event)

    assert outcome == "handled"
    assert handler.calls == [event, event]
    assert [entry for entry in dispatcher.status.errors if entry.event_key == event.key] == []


def test_a_failing_handler_is_counted_once_and_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))

    outcome = dispatcher.dispatch(event)

    assert outcome == "error"
    assert dispatcher.status.errors == [
        ErrorCount(event_key=event.key, remote_state=STATE, count=1, last_error=BOOM)
    ]
    assert hosting.factory_posts(number) == []


def test_a_second_failure_counts_two_and_still_posts_nothing(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))
    dispatcher.dispatch(event)

    outcome = dispatcher.dispatch(event)

    assert outcome == "error"
    assert _entry(dispatcher, event).count == 2
    assert hosting.factory_posts(number) == []


def test_the_third_failure_posts_one_keyed_report_on_the_pull_request(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    posts = hosting.factory_posts(number)
    assert len(posts) == 1
    assert posts[0].key == _report_key(STATE)
    text = error_report_text(event.key, BOOM, STATE, 3)
    assert posts[0].body == render_post(text, _report_key(STATE))


def test_a_reported_event_on_the_same_state_is_capped_without_calling_the_handler(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    handler = Failing()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries))
    for _ in range(3):
        dispatcher.dispatch(event)

    outcome = dispatcher.dispatch(event)

    assert outcome == "capped"
    assert len(handler.calls) == 3
    assert len(hosting.factory_posts(number)) == 1
    assert _entry(dispatcher, event).reported


def test_a_new_remote_state_is_counted_from_one_and_reported_under_another_key(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    snapshot = _snapshot(number)
    first = _event(snapshot=snapshot, remote_state=STATE)
    pushed = _event(snapshot=snapshot, remote_state=OTHER_STATE)
    handler = Failing()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries))
    for _ in range(4):
        dispatcher.dispatch(first)

    after_push = dispatcher.dispatch(pushed)

    assert after_push == "error"
    assert len(handler.calls) == 4
    assert _entry(dispatcher, pushed).count == 1
    assert [dispatcher.dispatch(pushed) for _ in range(2)] == ["error", "reported"]
    assert [post.key for post in hosting.factory_posts(number)] == [
        _report_key(STATE),
        _report_key(OTHER_STATE),
    ]


def test_an_event_without_a_handler_is_counted_and_reported_like_any_error(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event("merged", snapshot=_snapshot(number))
    dispatcher = Dispatcher({}, TickStatus(), StopService(boundaries))

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    unhandled = "UnhandledEvent: no handler for event kind merged"
    assert _entry(dispatcher, event).last_error == unhandled
    posts = hosting.factory_posts(number)
    assert len(posts) == 1
    assert posts[0].key == _report_key(STATE)
    assert posts[0].body == render_post(
        error_report_text(event.key, unhandled, STATE, 3), _report_key(STATE)
    )


def test_two_events_of_one_work_item_on_one_state_share_the_one_report(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    snapshot = _snapshot(number)
    comment = _event("comment", snapshot=snapshot)
    merged = _event("merged", snapshot=snapshot)
    handlers: dict[EventKind, Handler] = {"comment": Failing(), "merged": Failing()}
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))

    comment_outcomes = [dispatcher.dispatch(comment) for _ in range(3)]
    merged_outcomes = [dispatcher.dispatch(merged) for _ in range(3)]

    assert comment_outcomes == ["error", "error", "reported"]
    assert merged_outcomes == ["error", "error", "reported"]
    posts = hosting.factory_posts(number)
    assert len(posts) == 1
    assert posts[0].body == render_post(
        error_report_text(comment.key, BOOM, STATE, 3), _report_key(STATE)
    )
    assert dispatcher.dispatch(comment) == "capped"
    assert dispatcher.dispatch(merged) == "capped"
    assert len(hosting.factory_posts(number)) == 1


@pytest.mark.parametrize(
    ("body", "title"),
    [(TITLED, f"{WORK_ITEM}: Demo story"), ("No title line here.\n", WORK_ITEM)],
)
def test_the_report_of_a_work_item_without_a_pull_request_opens_a_draft_for_it(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    remote: Path,
    *,
    body: str,
    title: str,
) -> None:
    human.push_file(BRANCH, "note.txt", "x")
    checkout.fetch()
    tip = remote_commit(remote, BRANCH)
    assert tip is not None
    event = _event(snapshot=_snapshot(None, branch_commit=tip, body=body))
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == 1
    opened = pull_requests[0]
    assert opened.draft
    assert opened.branch == BRANCH
    assert opened.title == title
    assert [post.key for post in hosting.factory_posts(opened.number)] == [_report_key(STATE)]


def test_a_report_for_a_branch_not_on_the_remote_becomes_one_log_line(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    event = _event(snapshot=_snapshot(None, branch_commit=None))
    log = RecordingLog()
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries), log)

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    assert log.lines == [f"error cap reached on {event.key}: {BOOM}"]
    assert dispatcher.dispatch(event) == "capped"
    assert len(log.lines) == 1
    assert hosting.pull_requests() == []


def test_a_report_that_cannot_be_posted_is_made_again_without_counting(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    handler = Failing()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries))
    for _ in range(2):
        dispatcher.dispatch(event)
    hosting.fail_next("post_comment")

    failed = dispatcher.dispatch(event)

    assert failed == "error"
    entry = _entry(dispatcher, event)
    assert not entry.reported
    assert entry.count == 3
    assert entry.last_error == BOOM
    assert hosting.factory_posts(number) == []

    again = dispatcher.dispatch(event)

    assert again == "reported"
    assert len(handler.calls) == 3
    assert [post.key for post in hosting.factory_posts(number)] == [_report_key(STATE)]


def test_a_report_killed_after_its_post_is_not_posted_again_after_the_restart(
    boundaries: Boundaries, hosting: FakeHostingService, kill_points: KillPoints
) -> None:
    number = _open_pull_request(hosting)
    event = _event(snapshot=_snapshot(number))
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))
    for _ in range(2):
        dispatcher.dispatch(event)
    kill_points.arm(KillPoint.AFTER_POST)

    with pytest.raises(InjectedKill):
        dispatcher.dispatch(event)
    assert len(hosting.factory_posts(number)) == 1

    restarted = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries))
    outcomes = [restarted.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    assert len(hosting.factory_posts(number)) == 1


def test_a_kill_in_the_handler_passes_through_and_leaves_the_status(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    event = _event(snapshot=_snapshot(_open_pull_request(hosting)))
    status = record_error(TickStatus(), event.key, STATE, BOOM)
    handler = Failing(InjectedKill(KillPoint.AGENT_RUN))
    dispatcher = Dispatcher({"run": handler}, status, StopService(boundaries))

    with pytest.raises(InjectedKill):
        dispatcher.dispatch(event)

    assert dispatcher.status == status


def test_an_event_without_a_work_item_is_reported_as_one_log_line(
    boundaries: Boundaries,
) -> None:
    event = _idle_event()
    log = RecordingLog()
    dispatcher = Dispatcher({"idle": Failing()}, TickStatus(), StopService(boundaries), log)

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    assert log.lines == [f"error cap reached on {event.key}: {BOOM}"]
    assert dispatcher.dispatch(event) == "capped"
    assert len(log.lines) == 1


def test_an_event_without_a_work_item_is_reported_without_a_log(
    boundaries: Boundaries,
) -> None:
    event = _idle_event()
    dispatcher = Dispatcher({"idle": Failing()}, TickStatus(), StopService(boundaries))

    outcomes = [dispatcher.dispatch(event) for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    assert _entry(dispatcher, event).reported


def _dispatch_without_git(dispatcher: Dispatcher, event: Event, checkout: Path) -> str:
    git_directory = checkout / ".git"
    away = checkout.with_name("git-away")
    git_directory.rename(away)
    try:
        return dispatcher.dispatch(event)
    finally:
        away.rename(git_directory)


def test_a_report_that_fails_with_a_git_error_leaves_the_entry_unreported(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    remote: Path,
) -> None:
    human.push_file(BRANCH, "note.txt", "x")
    checkout.fetch()
    tip = remote_commit(remote, BRANCH)
    assert tip is not None
    event = _event(snapshot=_snapshot(None, branch_commit=tip))
    log = RecordingLog()
    dispatcher = Dispatcher({"run": Failing()}, TickStatus(), StopService(boundaries), log)
    for _ in range(2):
        dispatcher.dispatch(event)

    failed = _dispatch_without_git(dispatcher, event, boundaries.checkout)

    assert failed == "error"
    entry = _entry(dispatcher, event)
    assert not entry.reported
    assert entry.count == 3
    assert entry.last_error == BOOM
    assert hosting.pull_requests() == []
    assert log.lines == []


def test_a_report_that_failed_with_a_git_error_is_made_again_once_git_is_back(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    human: HumanClone,
    checkout: GitCli,
    remote: Path,
) -> None:
    human.push_file(BRANCH, "note.txt", "x")
    checkout.fetch()
    tip = remote_commit(remote, BRANCH)
    assert tip is not None
    event = _event(snapshot=_snapshot(None, branch_commit=tip))
    handler = Failing()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries))
    for _ in range(2):
        dispatcher.dispatch(event)
    assert _dispatch_without_git(dispatcher, event, boundaries.checkout) == "error"

    again = dispatcher.dispatch(event)

    assert again == "reported"
    assert len(handler.calls) == 3
    pull_requests = hosting.pull_requests()
    assert len(pull_requests) == 1
    opened = pull_requests[0]
    assert opened.draft
    assert opened.branch == BRANCH
    assert [post.key for post in hosting.factory_posts(opened.number)] == [_report_key(STATE)]
    assert dispatcher.dispatch(event) == "capped"
    assert len(hosting.factory_posts(opened.number)) == 1


def test_a_git_error_in_the_report_of_a_branch_not_on_the_remote_writes_no_log_line(
    boundaries: Boundaries, hosting: FakeHostingService
) -> None:
    event = _event(snapshot=_snapshot(None, branch_commit=None))
    handler = Failing()
    log = RecordingLog()
    dispatcher = Dispatcher({"run": handler}, TickStatus(), StopService(boundaries), log)
    for _ in range(2):
        dispatcher.dispatch(event)

    failed = _dispatch_without_git(dispatcher, event, boundaries.checkout)

    assert failed == "error"
    entry = _entry(dispatcher, event)
    assert not entry.reported
    assert entry.count == 3
    assert entry.last_error == BOOM
    assert log.lines == []

    again = dispatcher.dispatch(event)

    assert again == "reported"
    assert len(handler.calls) == 3
    assert log.lines == [f"error cap reached on {event.key}: {BOOM}"]
    assert hosting.pull_requests() == []
