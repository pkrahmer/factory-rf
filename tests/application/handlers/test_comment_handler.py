"""The comment handler: comments are recorded, and one written after the posted question answers."""

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from branch_reading import error_posts, remote_document
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, DispatchOutcome, Handler
from factory.application.handlers.comments import CommentHandler
from factory.application.handlers.questions import AskHandler
from factory.application.stops import StopService
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.events import Event, EventKind
from factory.domain.hosting import FACTORY_MARKER, PostKey
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.tick_status import TickStatus
from factory.domain.work_item import Blocked, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
REMOTE_STATE = "a" * 40

RESULT = NewEntry(speaker="coder", kind="result", text="implemented.")
QUESTION = NewEntry(speaker="reviewer", kind="question", text="Send it back?")
LATER_QUESTION = NewEntry(speaker="reviewer", kind="question", text="Really send it back?")
CAP_QUESTION = NewEntry(speaker=FACTORY, kind="question", text="Try again?")

Publish = Callable[[WorkItemDocument], WorkItemSnapshot]


class Counting(Handler):
    """Counts the events it is handed and passes each to the real handler."""

    def __init__(self, inner: Handler) -> None:
        self.calls = 0
        self._inner = inner

    def handle(self, event: Event) -> None:
        self.calls += 1
        self._inner.handle(event)


def _document(
    pull_request: int | None,
    entries: Sequence[NewEntry],
    *,
    stage: str = "doing",
    blocked: Blocked | None = None,
    round: int = 0,
    attempts: int = 0,
    crashes: int = 0,
    handed_over: str | None = None,
) -> WorkItemDocument:
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    state = WorkItemState(stage=stage, pull_request=pull_request, journal=[created])
    document = WorkItemDocument(state=state, body=BODY)
    for entry in entries:
        document = append_entry(document, entry)
    appended = _state_of(document)
    update: dict[str, object] = {
        "blocked": blocked,
        "round": round,
        "attempts": attempts,
        "crashes": crashes,
        "handed_over": handed_over,
    }
    return document.model_copy(update={"state": appended.model_copy(update=update)})


def _snapshot(document: WorkItemDocument, branch_commit: str | None) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=document,
    )


def _state_of(document: WorkItemDocument) -> WorkItemState:
    assert document.state is not None
    return document.state


def _event(snapshot: WorkItemSnapshot, kind: EventKind = "comment") -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state=REMOTE_STATE)


def _post_question(
    hosting: FakeHostingService, pull_request: int, blocked: Blocked, number: int
) -> int:
    key = PostKey(work_item=WORK_ITEM, kind=blocked, n=str(number))
    hosting.post_comment(pull_request, "a question", key)
    [post] = [comment for comment in hosting.factory_posts(pull_request) if comment.key == key]
    return post.id


def _remote_state(boundaries: Boundaries, checkout: GitCli) -> WorkItemState:
    return _state_of(remote_document(boundaries, checkout))


def _new_commits(checkout: GitCli, snapshot: WorkItemSnapshot) -> int:
    checkout.fetch()
    return len(checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit))


def _comment_records(state: WorkItemState) -> list[JournalRecord]:
    return [record for record in state.journal if record.kind == "comment"]


def _definition() -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {
            "contract": "1.0",
            "roles": {"coder": {"write_paths": ["src/*"]}},
            "stages": {"doing": {"role": "coder", "next": ["done"]}, "done": {}},
        }
    )


@pytest.fixture
def publish(boundaries: Boundaries, *, human: HumanClone, checkout: GitCli) -> Publish:
    """Return a function that pushes a work item document to its branch and returns its snapshot."""

    def push(document: WorkItemDocument) -> WorkItemSnapshot:
        text = boundaries.work_item_writer.render(document)
        human.push_file(BRANCH, PATH, text)
        checkout.fetch()
        return _snapshot(
            boundaries.work_item_reader.parse(text), checkout.resolve(f"origin/{BRANCH}")
        )

    return push


def _fetched(boundaries: Boundaries, checkout: GitCli) -> WorkItemSnapshot:
    document = remote_document(boundaries, checkout)
    return _snapshot(document, checkout.resolve(f"origin/{BRANCH}"))


def test_an_answer_after_the_posted_question_is_recorded_and_ends_the_wait_in_one_commit(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    _post_question(hosting, pull_request, "question", 3)
    answer = hosting.add_human_comment(pull_request, "Yes, send it back.")

    CommentHandler(boundaries).handle(_event(snapshot))

    assert _new_commits(checkout, snapshot) == 1
    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [answer]
    assert len(_comment_records(state)) == 1
    assert state.blocked is None


def test_an_answer_at_the_attempts_cap_also_resets_the_attempts(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    document = _document(pull_request, [RESULT, CAP_QUESTION], blocked="attempts_cap", attempts=2)
    snapshot = publish(document)
    _post_question(hosting, pull_request, "attempts_cap", 3)
    answer = hosting.add_human_comment(pull_request, "Try once more.")

    CommentHandler(boundaries).handle(_event(snapshot))

    assert _new_commits(checkout, snapshot) == 1
    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [answer]
    assert state.blocked is None
    assert state.attempts == 0


def test_without_a_new_human_comment_the_work_item_stays_blocked_and_nothing_is_pushed(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    _post_question(hosting, pull_request, "question", 3)

    CommentHandler(boundaries).handle(_event(snapshot))

    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert _remote_state(boundaries, checkout).blocked == "question"


def test_comments_that_carry_the_factory_marker_do_not_answer_and_push_nothing(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    _post_question(hosting, pull_request, "question", 3)
    hosting.add_human_comment(pull_request, f"Yes, send it back.\n\n{FACTORY_MARKER}")

    CommentHandler(boundaries).handle(_event(snapshot))

    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert _remote_state(boundaries, checkout).blocked == "question"


def test_a_comment_at_an_approval_is_recorded_and_changes_nothing_else(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    document = _document(
        pull_request,
        [RESULT],
        stage="approval",
        round=1,
        attempts=1,
        crashes=1,
        handed_over="smoke-test",
    )
    snapshot = publish(document)
    comment = hosting.add_human_comment(pull_request, "Looks good so far.")

    CommentHandler(boundaries).handle(_event(snapshot))

    before = _state_of(document)
    after = _remote_state(boundaries, checkout)
    assert after.comments_read == [comment]
    assert len(_comment_records(after)) == 1
    assert after.stage == before.stage
    assert after.blocked is None
    assert after.round == before.round
    assert after.attempts == before.attempts
    assert after.crashes == before.crashes
    assert after.handed_over == before.handed_over


def test_a_comment_on_a_work_item_that_waits_for_nothing_changes_no_other_field(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    document = _document(pull_request, [RESULT], round=1, attempts=1, crashes=1)
    snapshot = publish(document)
    comment = hosting.add_human_comment(pull_request, "Mind the edge case.")

    CommentHandler(boundaries).handle(_event(snapshot))

    after = _remote_state(boundaries, checkout)
    assert after.comments_read == [comment]
    assert len(_comment_records(after)) == 1
    unchanged = after.model_copy(
        update={"comments_read": [], "journal": _state_of(document).journal}
    )
    assert unchanged == _state_of(document)


def test_a_failing_comment_listing_raises_and_pushes_nothing(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    _post_question(hosting, pull_request, "question", 3)
    hosting.add_human_comment(pull_request, "Yes, send it back.")
    hosting.fail_next("list_comments")

    with pytest.raises(HostingServiceError):
        CommentHandler(boundaries).handle(_event(snapshot))

    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_work_item_without_a_pull_request_cannot_be_handled_and_records_nothing(
    boundaries: Boundaries, *, remote: Path
) -> None:
    snapshot = _snapshot(_document(None, [RESULT, QUESTION], blocked="question"), None)

    with pytest.raises(CannotHandle) as raised:
        CommentHandler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "comment"
    assert remote_commit(remote, BRANCH) is None


def test_a_comment_older_than_the_post_is_recorded_and_only_a_later_one_answers(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    early = hosting.add_human_comment(pull_request, "Written while the stages worked.")
    _post_question(hosting, pull_request, "question", 3)

    CommentHandler(boundaries).handle(_event(snapshot))

    assert _new_commits(checkout, snapshot) == 1
    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [early]
    assert len(_comment_records(state)) == 1
    assert state.blocked == "question"

    answer = hosting.add_human_comment(pull_request, "Yes, send it back.")
    CommentHandler(boundaries).handle(_event(_fetched(boundaries, checkout)))

    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [early, answer]
    assert state.blocked is None


@pytest.mark.parametrize(
    ("entries", "posted_number"),
    [
        ([RESULT, QUESTION], None),
        ([RESULT], None),
        ([QUESTION, RESULT, LATER_QUESTION], 2),
    ],
    ids=["question-not-posted", "no-question-record", "earlier-question-posted"],
)
def test_a_comment_on_a_wait_whose_question_is_not_posted_does_not_answer(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    entries: list[NewEntry],
    posted_number: int | None,
) -> None:
    snapshot = publish(_document(pull_request, entries, blocked="question"))
    if posted_number is not None:
        _post_question(hosting, pull_request, "question", posted_number)
    comment = hosting.add_human_comment(pull_request, "Yes, send it back.")

    CommentHandler(boundaries).handle(_event(snapshot))

    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [comment]
    assert len(_comment_records(state)) == 1
    assert state.blocked == "question"


def test_a_comment_before_and_one_after_the_post_are_both_recorded_and_end_the_wait(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    early = hosting.add_human_comment(pull_request, "Written while the stages worked.")
    _post_question(hosting, pull_request, "question", 3)
    answer = hosting.add_human_comment(pull_request, "Yes, send it back.")

    CommentHandler(boundaries).handle(_event(snapshot))

    assert _new_commits(checkout, snapshot) == 1
    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [early, answer]
    assert len(_comment_records(state)) == 2
    assert state.blocked is None


def test_a_blank_comment_after_the_post_is_read_without_an_entry_and_does_not_answer(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, QUESTION], blocked="question"))
    _post_question(hosting, pull_request, "question", 3)
    blank = hosting.add_human_comment(pull_request, "  \n\t ")

    CommentHandler(boundaries).handle(_event(snapshot))

    state = _remote_state(boundaries, checkout)
    assert state.comments_read == [blank]
    assert _comment_records(state) == []
    assert state.blocked == "question"


def test_a_comment_event_that_always_fails_is_tried_three_times_and_reported_once(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    hosting.fail_next("list_comments", times=10)
    comment = Counting(CommentHandler(boundaries))
    ask = Counting(AskHandler(boundaries, _definition()))
    handlers: dict[EventKind, Handler] = {"comment": comment, "ask": ask}
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    event = _event(work_item)

    outcomes: list[DispatchOutcome] = [dispatcher.dispatch(event), dispatcher.dispatch(event)]
    assert error_posts(hosting, pull_request) == []
    outcomes.append(dispatcher.dispatch(event))
    [report] = error_posts(hosting, pull_request)
    outcomes.append(dispatcher.dispatch(event))

    assert outcomes == ["error", "error", "reported", "capped"]
    assert comment.calls == 3
    assert ask.calls == 0
    assert report.key == PostKey(work_item=WORK_ITEM, kind="error", n=REMOTE_STATE[:12])
    assert len(error_posts(hosting, pull_request)) == 1


def test_an_ask_event_that_always_fails_is_tried_three_times_and_reported_once(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT], attempts=2))
    comment = Counting(CommentHandler(boundaries))
    ask = Counting(AskHandler(boundaries, _definition()))
    handlers: dict[EventKind, Handler] = {"comment": comment, "ask": ask}
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    event = _event(snapshot, "ask")

    outcomes: list[DispatchOutcome] = [dispatcher.dispatch(event), dispatcher.dispatch(event)]
    assert error_posts(hosting, pull_request) == []
    outcomes.append(dispatcher.dispatch(event))
    [report] = error_posts(hosting, pull_request)
    outcomes.append(dispatcher.dispatch(event))

    assert outcomes == ["error", "error", "reported", "capped"]
    assert ask.calls == 3
    assert comment.calls == 0
    assert report.key == PostKey(work_item=WORK_ITEM, kind="error", n=REMOTE_STATE[:12])
    assert len(error_posts(hosting, pull_request)) == 1


def test_after_a_restart_the_failing_comment_event_is_tried_again_and_not_reported_twice(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    pull_request: int,
    work_item: WorkItemSnapshot,
) -> None:
    hosting.fail_next("list_comments", times=10)
    comment = Counting(CommentHandler(boundaries))
    ask = Counting(AskHandler(boundaries, _definition()))
    handlers: dict[EventKind, Handler] = {"comment": comment, "ask": ask}
    event = _event(work_item)
    before = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    for _ in range(3):
        before.dispatch(event)
    assert comment.calls == 3

    restarted = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    for _ in range(3):
        restarted.dispatch(event)

    assert comment.calls == 6
    assert len(error_posts(hosting, pull_request)) == 1
