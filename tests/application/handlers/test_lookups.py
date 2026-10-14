"""The duplicate and pull request lookup handlers cannot do their work and say so loudly."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, DispatchOutcome, Handler
from factory.application.handlers.lookups import DuplicateHandler, PullRequestLookupHandler
from factory.application.handlers.questions import AskHandler
from factory.application.stops import StopService
from factory.domain.errors import CannotHandle
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PostKey, PullRequestComment
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.tick_status import TickStatus
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
REMOTE_STATE = "a" * 40
ERROR_KEY = PostKey(work_item=WORK_ITEM, kind="error", n=REMOTE_STATE[:12])


class Counting(Handler):
    """Counts the events it is handed and passes each to the real handler."""

    def __init__(self, inner: Handler) -> None:
        self.calls = 0
        self._inner = inner

    def handle(self, event: Event) -> None:
        self.calls += 1
        self._inner.handle(event)


def _definition() -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {
            "contract": "1.0",
            "roles": {"coder": {"write_paths": ["src/*"]}},
            "stages": {"doing": {"role": "coder", "next": ["done"]}, "done": {}},
        }
    )


def _event(kind: EventKind, snapshot: WorkItemSnapshot, detail: str = "") -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state=REMOTE_STATE, detail=detail)


def _error_posts(hosting: FakeHostingService, number: int) -> list[PullRequestComment]:
    return [post for post in hosting.factory_posts(number) if post.key == ERROR_KEY]


def _raised(handler: Handler, event: Event) -> CannotHandle:
    with pytest.raises(CannotHandle) as raised:
        handler.handle(event)
    return raised.value


@pytest.mark.parametrize(
    ("detail", "reason"),
    [
        ("a.md, b.md", f"two work items share the id {WORK_ITEM}: a.md, b.md"),
        ("", f"two work items share the id {WORK_ITEM}"),
    ],
)
def test_the_duplicate_handler_raises_naming_the_work_item_and_the_detail(
    snapshot_of: Callable[[WorkItemState | None], WorkItemSnapshot],
    state_with: Callable[[int | None], WorkItemState],
    *,
    detail: str,
    reason: str,
) -> None:
    event = _event("duplicate", snapshot_of(state_with(None)), detail)

    error = _raised(DuplicateHandler(), event)

    assert error.kind == "duplicate"
    assert error.reason == reason


@pytest.mark.parametrize(
    ("detail", "reason"),
    [
        ("rate limited", f"the pull request lookup for {BRANCH} failed: rate limited"),
        ("", f"the pull request lookup for {BRANCH} failed"),
    ],
)
def test_the_pull_request_lookup_handler_raises_naming_the_branch_and_the_detail(
    snapshot_of: Callable[[WorkItemState | None], WorkItemSnapshot],
    state_with: Callable[[int | None], WorkItemState],
    *,
    detail: str,
    reason: str,
) -> None:
    event = _event("pull_request_lookup", snapshot_of(state_with(None)), detail)

    error = _raised(PullRequestLookupHandler(), event)

    assert error.kind == "pull_request_lookup"
    assert error.reason == reason


@pytest.mark.parametrize(
    ("kind", "handler"),
    [("duplicate", DuplicateHandler()), ("pull_request_lookup", PullRequestLookupHandler())],
)
def test_a_lookup_handler_changes_nothing_on_the_hosting_service_or_the_remote(
    hosting: FakeHostingService,
    remote: Path,
    *,
    pull_request: int,
    work_item: WorkItemSnapshot,
    kind: EventKind,
    handler: Handler,
) -> None:
    main = remote_commit(remote, "main")
    comments = hosting.list_comments(pull_request)

    _raised(handler, _event(kind, work_item, "detail"))

    assert hosting.list_comments(pull_request) == comments
    assert remote_commit(remote, "main") == main
    assert remote_commit(remote, BRANCH) == work_item.branch_commit


def _dispatch_four_times(
    dispatcher: Dispatcher, event: Event, hosting: FakeHostingService, number: int
) -> list[DispatchOutcome]:
    outcomes: list[DispatchOutcome] = [dispatcher.dispatch(event), dispatcher.dispatch(event)]
    assert _error_posts(hosting, number) == []
    assert hosting.factory_posts(number) == []
    outcomes.append(dispatcher.dispatch(event))
    assert len(hosting.factory_posts(number)) == 1
    assert len(_error_posts(hosting, number)) == 1
    outcomes.append(dispatcher.dispatch(event))
    assert len(hosting.factory_posts(number)) == 1
    return outcomes


def test_a_duplicate_event_is_tried_three_times_and_reported_once(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    *,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    handler = Counting(DuplicateHandler())
    dispatcher = Dispatcher({"duplicate": handler}, TickStatus(), StopService(boundaries))
    event = _event("duplicate", work_item, "a.md, b.md")

    outcomes = _dispatch_four_times(dispatcher, event, hosting, pull_request)

    assert outcomes == ["error", "error", "reported", "capped"]
    assert handler.calls == 3


def test_a_pull_request_lookup_event_is_tried_three_times_and_reported_once(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    *,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    handler = Counting(PullRequestLookupHandler())
    handlers: dict[EventKind, Handler] = {"pull_request_lookup": handler}
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    event = _event("pull_request_lookup", work_item, "rate limited")

    outcomes = _dispatch_four_times(dispatcher, event, hosting, pull_request)

    assert outcomes == ["error", "error", "reported", "capped"]
    assert handler.calls == 3


def test_an_ask_event_without_a_pull_request_is_reported_once_on_a_new_draft(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    *,
    human: HumanClone,
    checkout: GitCli,
    state_with: Callable[[int | None], WorkItemState],
) -> None:
    document = WorkItemDocument(state=state_with(None), body=BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    checkout.fetch()
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=checkout.resolve(f"origin/{BRANCH}"),
        document=document,
    )
    handler = Counting(AskHandler(boundaries, _definition()))
    dispatcher = Dispatcher({"ask": handler}, TickStatus(), StopService(boundaries))
    event = _event("ask", snapshot)

    outcomes: list[DispatchOutcome] = [dispatcher.dispatch(event), dispatcher.dispatch(event)]
    assert hosting.pull_requests() == []
    outcomes.append(dispatcher.dispatch(event))
    [opened] = hosting.pull_requests()
    assert opened.draft
    assert opened.branch == BRANCH
    assert len(hosting.factory_posts(opened.number)) == 1
    assert len(_error_posts(hosting, opened.number)) == 1
    outcomes.append(dispatcher.dispatch(event))

    assert outcomes == ["error", "error", "reported", "capped"]
    assert handler.calls == 3
    assert len(hosting.pull_requests()) == 1
    assert len(hosting.factory_posts(opened.number)) == 1


def test_a_restart_tries_a_reported_duplicate_event_three_times_again_without_a_second_post(
    boundaries: Boundaries,
    hosting: FakeHostingService,
    *,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    event = _event("duplicate", work_item, "a.md, b.md")
    first = Dispatcher({"duplicate": DuplicateHandler()}, TickStatus(), StopService(boundaries))
    for _ in range(3):
        first.dispatch(event)
    assert len(_error_posts(hosting, pull_request)) == 1
    handler = Counting(DuplicateHandler())
    restarted = Dispatcher({"duplicate": handler}, TickStatus(), StopService(boundaries))

    outcomes = [restarted.dispatch(event) for _ in range(4)]

    assert outcomes == ["error", "error", "reported", "capped"]
    assert handler.calls == 3
    assert len(hosting.factory_posts(pull_request)) == 1
    assert len(_error_posts(hosting, pull_request)) == 1
