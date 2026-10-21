"""The ask handler: a question is recorded in the work item first, then posted once."""

from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import pytest

from branch_reading import remote_document
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.questions import AskHandler
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.events import Event
from factory.domain.hosting import PostKey, render_post
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry, entry_text
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import attempts_cap_question
from factory.domain.work_item import Blocked, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
SUBJECT = f"work item {WORK_ITEM}: attempts cap question recorded"

RESULT = NewEntry(speaker="coder", kind="result", text="implemented.")
QUESTION = NewEntry(speaker="reviewer", kind="question", text="Send it back?")
LATER_QUESTION = NewEntry(speaker="reviewer", kind="question", text="Really send it back?")
FIRST_STALL = NewEntry(speaker=FACTORY, kind="stall", text="the checks were red")
LAST_STALL = NewEntry(speaker=FACTORY, kind="stall", text="the agent gave no result")
COMMENT = NewEntry(speaker=HUMAN, kind="comment", text="Still thinking.", on=date(2026, 10, 13))

Publish = Callable[[WorkItemDocument], WorkItemSnapshot]


def _definition() -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {
            "contract": "1.0",
            "roles": {"coder": {"write_paths": ["src/*"]}},
            "stages": {"doing": {"role": "coder", "next": ["done"]}, "done": {}},
        }
    )


def _document(
    pull_request: int | None,
    entries: Sequence[NewEntry],
    *,
    blocked: Blocked | None = None,
    attempts: int = 0,
) -> WorkItemDocument:
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    state = WorkItemState(stage="doing", pull_request=pull_request, journal=[created])
    document = WorkItemDocument(state=state, body=BODY)
    for entry in entries:
        document = append_entry(document, entry)
    appended = document.state
    assert appended is not None
    return document.model_copy(
        update={"state": appended.model_copy(update={"blocked": blocked, "attempts": attempts})}
    )


def _snapshot(document: WorkItemDocument, branch_commit: str | None) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=document,
    )


def _event(snapshot: WorkItemSnapshot) -> Event:
    return Event(kind="ask", work_item=snapshot, remote_state="a" * 40)


def _handler(boundaries: Boundaries) -> AskHandler:
    return AskHandler(boundaries, _definition())


def _questions(document: WorkItemDocument) -> list[JournalRecord]:
    assert document.state is not None
    return [record for record in document.state.journal if record.kind == "question"]


def _key(kind: Blocked, number: int) -> PostKey:
    return PostKey(work_item=WORK_ITEM, kind=kind, n=str(number))


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


def test_an_agents_question_is_posted_with_its_speaker_and_keyed_to_its_entry(
    boundaries: Boundaries, *, hosting: FakeHostingService, publish: Publish, pull_request: int
) -> None:
    document = _document(pull_request, [RESULT, QUESTION], blocked="question")
    snapshot = publish(document)

    _handler(boundaries).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    key = _key("question", 3)
    assert post.key == key
    assert post.body == render_post(f"reviewer: {entry_text(document, 3)}", key)


@pytest.mark.parametrize("blocked", ["round_cap", "crash_cap", "send_back", "attempts_cap"])
def test_a_recorded_question_is_posted_under_its_blocked_kind_without_a_commit(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
    blocked: Blocked,
) -> None:
    question = NewEntry(speaker=FACTORY, kind="question", text="What should happen?")
    snapshot = publish(_document(pull_request, [LAST_STALL, question], blocked=blocked, attempts=2))

    _handler(boundaries).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    assert post.key == _key(blocked, 3)
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_of_several_questions_the_latest_is_posted(
    boundaries: Boundaries, *, hosting: FakeHostingService, publish: Publish, pull_request: int
) -> None:
    document = _document(
        pull_request, [QUESTION, COMMENT, RESULT, LATER_QUESTION], blocked="question"
    )
    snapshot = publish(document)

    _handler(boundaries).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    key = _key("question", 5)
    assert post.key == key
    assert post.body == render_post(f"reviewer: {entry_text(document, 5)}", key)


def test_a_question_already_posted_is_not_posted_again(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [QUESTION], blocked="question"))
    handler = _handler(boundaries)
    handler.handle(_event(snapshot))

    handler.handle(_event(snapshot))

    assert len(hosting.factory_posts(pull_request)) == 1
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


@pytest.mark.parametrize(
    "blocked", ["question", "attempts_cap", "round_cap", "crash_cap", "send_back"]
)
def test_a_blocked_work_item_without_a_question_record_cannot_be_handled(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    blocked: Blocked,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], blocked=blocked, attempts=2))

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "ask"
    assert hosting.factory_posts(pull_request) == []


def test_at_the_attempts_cap_the_question_is_recorded_in_one_pushed_commit(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    clock: ManualClock,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, FIRST_STALL, LAST_STALL], attempts=2))

    _handler(boundaries).handle(_event(snapshot))

    recorded = remote_document(boundaries, checkout)
    [commit] = checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit)
    assert commit.subject == SUBJECT
    assert recorded.state is not None
    assert recorded.state.blocked == "attempts_cap"
    assert recorded.state.journal[-1] == JournalRecord(
        number=5,
        speaker=FACTORY,
        kind="question",
        at=clock.now(),
        stage="doing",
        blocked="attempts_cap",
    )
    assert entry_text(recorded, 5) == attempts_cap_question("doing", 2, LAST_STALL.text)


def test_the_recorded_attempts_cap_question_is_posted_by_the_factory(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], attempts=2))

    _handler(boundaries).handle(_event(snapshot))

    recorded = remote_document(boundaries, checkout)
    [post] = hosting.factory_posts(pull_request)
    key = _key("attempts_cap", 4)
    assert post.key == key
    assert post.body == render_post(f"factory: {entry_text(recorded, 4)}", key)


@pytest.mark.parametrize("attempts", [1, 3])
def test_below_the_attempts_cap_nothing_is_asked_and_above_it_the_question_is(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    attempts: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], attempts=attempts))
    handler = _handler(boundaries)

    if attempts == 1:
        with pytest.raises(CannotHandle) as raised:
            handler.handle(_event(snapshot))
        assert raised.value.kind == "ask"
        assert remote_commit(remote, BRANCH) == snapshot.branch_commit
        assert hosting.factory_posts(pull_request) == []
    else:
        handler.handle(_event(snapshot))
        recorded = remote_document(boundaries, checkout)
        assert recorded.state is not None
        assert recorded.state.blocked == "attempts_cap"
        assert entry_text(recorded, 4) == attempts_cap_question("doing", 3, LAST_STALL.text)
        [post] = hosting.factory_posts(pull_request)
        assert post.key == _key("attempts_cap", 4)


def test_at_the_attempts_cap_without_a_stall_record_nothing_is_recorded(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT], attempts=2))

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "ask"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert hosting.factory_posts(pull_request) == []


def test_the_attempts_cap_question_is_recorded_before_a_failing_post(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    clock: ManualClock,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], attempts=2))
    hosting.fail_next("post_comment")

    with pytest.raises(HostingServiceError):
        _handler(boundaries).handle(_event(snapshot))

    recorded = remote_document(boundaries, checkout)
    assert recorded.state is not None
    assert recorded.state.blocked == "attempts_cap"
    assert recorded.state.journal[-1] == JournalRecord(
        number=4,
        speaker=FACTORY,
        kind="question",
        at=clock.now(),
        stage="doing",
        blocked="attempts_cap",
    )
    assert hosting.factory_posts(pull_request) == []


def test_after_a_failing_post_the_recorded_question_is_posted_once_and_not_recorded_again(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], attempts=2))
    hosting.fail_next("post_comment")
    with pytest.raises(HostingServiceError):
        _handler(boundaries).handle(_event(snapshot))
    recorded_at = remote_commit(remote, BRANCH)
    reread = _snapshot(remote_document(boundaries, checkout), recorded_at)

    _handler(boundaries).handle(_event(reread))

    [post] = hosting.factory_posts(pull_request)
    assert post.key == _key("attempts_cap", 4)
    assert remote_commit(remote, BRANCH) == recorded_at
    assert len(_questions(remote_document(boundaries, checkout))) == 1


def test_a_kill_after_the_post_leaves_one_post_and_a_repeat_posts_nothing_more(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [QUESTION], blocked="question"))
    kill_points.arm(KillPoint.AFTER_POST)
    with pytest.raises(InjectedKill):
        _handler(boundaries).handle(_event(snapshot))
    assert len(hosting.factory_posts(pull_request)) == 1

    _handler(boundaries).handle(_event(snapshot))

    assert len(hosting.factory_posts(pull_request)) == 1


def test_a_kill_before_the_push_leaves_the_branch_and_a_repeat_records_and_posts_once(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, [RESULT, LAST_STALL], attempts=2))
    kill_points.arm(KillPoint.BEFORE_PUSH)
    with pytest.raises(InjectedKill):
        _handler(boundaries).handle(_event(snapshot))
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert hosting.factory_posts(pull_request) == []

    _handler(boundaries).handle(_event(snapshot))

    assert len(checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit)) == 1
    assert len(_questions(remote_document(boundaries, checkout))) == 1
    [post] = hosting.factory_posts(pull_request)
    assert post.key == _key("attempts_cap", 4)


def test_a_work_item_without_a_pull_request_cannot_be_asked(
    boundaries: Boundaries, *, hosting: FakeHostingService, remote: Path
) -> None:
    snapshot = _snapshot(_document(None, [QUESTION], blocked="question"), None)

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "ask"
    assert raised.value.reason == f"work item {WORK_ITEM} has no pull request"
    assert remote_commit(remote, BRANCH) is None
    assert hosting.pull_requests() == []


def test_comments_after_a_question_leave_the_post_keyed_to_the_question(
    boundaries: Boundaries, *, hosting: FakeHostingService, publish: Publish, pull_request: int
) -> None:
    later = NewEntry(speaker=HUMAN, kind="comment", text="Hello?", on=date(2026, 10, 14))
    document = _document(pull_request, [QUESTION, COMMENT, later], blocked="question")
    snapshot = publish(document)

    _handler(boundaries).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    key = _key("question", 2)
    assert post.key == key
    assert post.body == render_post(f"reviewer: {entry_text(document, 2)}", key)
