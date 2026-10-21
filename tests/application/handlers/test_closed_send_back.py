"""The closed handler at an approval stage: the close is recorded, then the story is sent back."""

import dataclasses
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from branch_reading import remote_document
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.questions import AskHandler
from factory.domain.errors import CannotHandle, HostingServiceError, PushFailed
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PostKey
from factory.domain.journal import (
    FACTORY,
    HUMAN,
    JournalKind,
    JournalRecord,
    NewEntry,
    append_entry,
    entry_text,
)
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import (
    CLOSE_ENTRY_TEXT,
    SEND_BACK_QUESTION,
    send_back_entry_text,
    send_back_question,
)
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
CLOSE_SUBJECT = f"work item {WORK_ITEM}: close recorded"
CLOSED_ON = date(2026, 10, 14)

RESULT = NewEntry(speaker="smoke-tester", kind="result", text="the smoke test passed.")
EARLIER_COMMENT = NewEntry(
    speaker=HUMAN, kind="comment", text="Make the title shorter.", on=date(2026, 10, 13)
)
EARLIER_CLOSE = NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=date(2026, 10, 13))
EARLIER_SEND_BACK = NewEntry(
    speaker=FACTORY, kind="send_back", text=send_back_entry_text("doing", 1)
)
CLAIM = Claim(
    instance="laptop",
    stage="approval",
    started_at=datetime(2026, 10, 12, 11, 0, tzinfo=UTC),
    lease_duration=60,
)

Publish = Callable[..., WorkItemSnapshot]


def _definition(boundaries: Boundaries, yaml: str = PIPELINE_YAML) -> PipelineDefinition:
    return boundaries.pipeline_reader.parse(yaml)


def _handle(boundaries: Boundaries, event: Event, yaml: str = PIPELINE_YAML) -> None:
    ClosedHandler(boundaries, _definition(boundaries, yaml)).handle(event)


def _event(snapshot: WorkItemSnapshot, kind: EventKind = "closed") -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state="a" * 40)


def _state(document: WorkItemDocument) -> WorkItemState:
    assert document.state is not None
    return document.state


def _kinds(document: WorkItemDocument) -> list[JournalKind]:
    return [record.kind for record in _state(document).journal]


def _records(document: WorkItemDocument, kind: JournalKind) -> list[JournalRecord]:
    return [record for record in _state(document).journal if record.kind == kind]


def _snapshot(document: WorkItemDocument, branch_commit: str | None) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=document,
    )


@pytest.fixture
def publish(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    clock: ManualClock,
) -> Publish:
    """Return a function that pushes a story waiting at the approval and closes its pull request.

    The pull request is made ready for review first, as at a hand-over; the clock moves to
    `CLOSED_ON` so that the close entry's date is told apart from every other date.
    """
    clock.advance(timedelta(days=2))

    def push(
        pull_request: int | None,
        entries: Sequence[NewEntry] = (RESULT,),
        *,
        round_number: int = 0,
        claim: Claim | None = None,
        service: FakeHostingService | None = None,
    ) -> WorkItemSnapshot:
        created = JournalRecord(number=1, speaker=HUMAN, kind="created")
        state = WorkItemState(
            stage="approval",
            round=round_number,
            pull_request=pull_request,
            handed_over="approval",
            claim=claim,
            journal=[created],
        )
        document = WorkItemDocument(state=state, body=BODY)
        for entry in entries:
            document = append_entry(document, entry)
        text = boundaries.work_item_writer.render(document)
        human.push_file(BRANCH, PATH, text)
        if pull_request is not None:
            closing = hosting if service is None else service
            closing.set_draft(pull_request, False)
            closing.close_by_human(pull_request)
        checkout.fetch()
        return _snapshot(
            boundaries.work_item_reader.parse(text), checkout.resolve(f"origin/{BRANCH}")
        )

    return push


def _assert_reopened_as_draft(hosting: FakeHostingService, pull_request: int) -> None:
    view = hosting.get_pull_request(pull_request)
    assert view.state == "open"
    assert view.draft


def test_a_failed_reopen_leaves_the_close_recorded_and_the_story_at_the_approval(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request)
    hosting.add_human_comment(pull_request, "The title is too long.")
    hosting.fail_next("reopen")

    with pytest.raises(HostingServiceError):
        _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    comment, close = state.journal[-2:]
    assert comment.speaker == HUMAN
    assert comment.kind == "comment"
    assert entry_text(document, comment.number) == "The title is too long."
    assert close.speaker == HUMAN
    assert close.kind == "close"
    assert entry_text(document, close.number) == CLOSE_ENTRY_TEXT
    assert f"{close.number}. {CLOSED_ON.isoformat()} human: {CLOSE_ENTRY_TEXT}" in document.body
    assert state.handed_over is None
    assert state.stage == "approval"
    assert hosting.get_pull_request(pull_request).state == "closed"
    [commit] = checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit)
    assert commit.subject == CLOSE_SUBJECT


def test_the_event_handled_again_after_a_failed_reopen_sends_back_with_one_close(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request)
    hosting.fail_next("reopen")
    with pytest.raises(HostingServiceError):
        _handle(boundaries, _event(snapshot))

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    assert _state(document).stage == "doing"
    assert len(_records(document, "close")) == 1
    assert len(_records(document, "send_back")) == 1
    _assert_reopened_as_draft(hosting, pull_request)


def test_a_close_with_a_reason_within_the_cap_sends_the_story_back_without_a_question(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request, round_number=2, claim=CLAIM)
    hosting.add_human_comment(pull_request, "The title is too long.")

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    assert state.stage == "doing"
    assert state.round == 3
    assert state.blocked is None
    assert state.claim is None
    close, send_back = state.journal[-2:]
    assert close.kind == "close"
    assert send_back.kind == "send_back"
    assert send_back.speaker == FACTORY
    assert entry_text(document, send_back.number) == send_back_entry_text("doing", 3)
    assert _records(document, "question") == []
    _assert_reopened_as_draft(hosting, pull_request)


@pytest.mark.parametrize("copied_at_the_close", [True, False])
def test_a_comment_copied_at_the_close_or_earlier_counts_as_the_reason(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    copied_at_the_close: bool,
) -> None:
    if copied_at_the_close:
        snapshot = publish(pull_request, (RESULT,))
        hosting.add_human_comment(pull_request, "The title is too long.")
    else:
        snapshot = publish(pull_request, (RESULT, EARLIER_COMMENT))

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    assert state.stage == "doing"
    assert state.blocked is None
    assert _records(document, "question") == []


def test_a_close_without_a_comment_after_the_latest_result_records_the_question(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request, (EARLIER_COMMENT, RESULT))

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    send_back, question = state.journal[-2:]
    assert send_back.kind == "send_back"
    assert question.kind == "question"
    assert question.speaker == FACTORY
    assert entry_text(document, question.number) == send_back_question(1, 3, False)
    assert state.blocked == "send_back"
    assert state.stage == "doing"
    _assert_reopened_as_draft(hosting, pull_request)


def test_a_close_past_the_round_cap_records_the_cap_question_even_with_a_reason(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request, round_number=3)
    hosting.add_human_comment(pull_request, "The title is too long.")

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    [question] = _records(document, "question")
    assert entry_text(document, question.number) == (
        "This story has now been sent back 4 times, more than 3. " + SEND_BACK_QUESTION
    )
    assert state.round == 4
    assert state.blocked == "send_back"


def test_the_send_back_posts_nothing_and_the_ask_handler_posts_its_question_once(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request)

    _handle(boundaries, _event(snapshot))

    assert hosting.factory_posts(pull_request) == []
    document = remote_document(boundaries, checkout)
    [question] = _records(document, "question")
    sent_back = _snapshot(document, checkout.resolve(f"origin/{BRANCH}"))
    ask = AskHandler(boundaries, _definition(boundaries))
    ask.handle(_event(sent_back, "ask"))
    ask.handle(_event(sent_back, "ask"))
    [post] = hosting.factory_posts(pull_request)
    assert post.key == PostKey(work_item=WORK_ITEM, kind="send_back", n=str(question.number))


def test_a_kill_before_the_close_is_pushed_changes_nothing(
    boundaries: Boundaries,
    *,
    remote: Path,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request)
    hosting.add_human_comment(pull_request, "The title is too long.")
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _handle(boundaries, _event(snapshot))

    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert hosting.get_pull_request(pull_request).state == "closed"


def test_an_approval_with_one_next_stage_cannot_be_sent_back_and_nothing_is_recorded(
    boundaries: Boundaries,
    *,
    remote: Path,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    yaml = PIPELINE_YAML.replace(
        "approval: {approval: true, next: [done, doing]}",
        "approval: {approval: true, next: [done]}",
    )
    snapshot = publish(pull_request)
    hosting.add_human_comment(pull_request, "The title is too long.")

    with pytest.raises(CannotHandle) as raised:
        _handle(boundaries, _event(snapshot), yaml)

    assert raised.value.kind == "closed"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert hosting.get_pull_request(pull_request).state == "closed"


def test_a_story_without_a_pull_request_cannot_be_sent_back_and_nothing_is_recorded(
    boundaries: Boundaries, *, remote: Path, publish: Publish
) -> None:
    snapshot = publish(None)

    with pytest.raises(CannotHandle) as raised:
        _handle(boundaries, _event(snapshot))

    assert raised.value.kind == "closed"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


class _PushingOnDraft(FakeHostingService):
    """Once armed, pushes the human's commit to the work item's branch when a draft is set."""

    def __init__(self, human: HumanClone) -> None:
        super().__init__()
        self._human = human
        self.armed = False

    def set_draft(self, number: int, draft: bool) -> None:
        super().set_draft(number, draft)
        if self.armed:
            self.armed = False
            self._human.push_file(BRANCH, "notes.md", "The human pushed this.\n")


def test_a_rejected_push_of_the_decision_keeps_the_close_and_a_retry_sends_back_once(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    publish: Publish,
) -> None:
    hosting = _PushingOnDraft(human)
    pushing = dataclasses.replace(boundaries, hosting=hosting)
    pull_request = hosting.create_pull_request(BRANCH, f"{WORK_ITEM}: first", "body", draft=True)
    snapshot = publish(pull_request.number, service=hosting)
    hosting.armed = True

    with pytest.raises(PushFailed) as raised:
        _handle(pushing, _event(snapshot))

    assert raised.value.outcome == "rejected"
    document = remote_document(boundaries, checkout)
    assert len(_records(document, "close")) == 1
    assert _state(document).stage == "approval"
    assert checkout.show_file(f"origin/{BRANCH}", "notes.md") == "The human pushed this.\n"

    _handle(pushing, _event(snapshot))

    document = remote_document(boundaries, checkout)
    assert len(_records(document, "close")) == 1
    assert len(_records(document, "send_back")) == 1
    assert _state(document).stage == "doing"


def test_a_comment_written_before_the_retry_is_copied_and_counts_as_the_reason(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(pull_request)
    hosting.fail_next("reopen")
    with pytest.raises(HostingServiceError):
        _handle(boundaries, _event(snapshot))
    hosting.add_human_comment(pull_request, "The title is too long.")

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    state = _state(document)
    [close] = _records(document, "close")
    [comment] = _records(document, "comment")
    assert comment.number > close.number
    assert entry_text(document, comment.number) == "The title is too long."
    assert state.blocked is None
    assert _records(document, "question") == []


@pytest.mark.parametrize("labels_fail", [False, True])
def test_after_the_decision_the_labels_name_the_target_stage(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    labels_fail: bool,
) -> None:
    snapshot = publish(pull_request)
    hosting.add_human_comment(pull_request, "The title is too long.")
    if labels_fail:
        hosting.fail_next("set_labels")
        with pytest.raises(HostingServiceError):
            _handle(boundaries, _event(snapshot))
    else:
        _handle(boundaries, _event(snapshot))
        assert hosting.labels(pull_request) == ["stage:doing"]

    document = remote_document(boundaries, checkout)
    assert _state(document).stage == "doing"
    assert len(_records(document, "send_back")) == 1


@pytest.mark.parametrize(
    ("entries", "closes"),
    [
        ((EARLIER_COMMENT, EARLIER_CLOSE, EARLIER_SEND_BACK, RESULT), 2),
        ((EARLIER_COMMENT, EARLIER_CLOSE), 1),
    ],
    ids=["close-before-the-latest-result", "close-and-no-result"],
)
def test_only_a_close_recorded_since_the_latest_result_spares_a_new_close_entry(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    entries: tuple[NewEntry, ...],
    closes: int,
) -> None:
    snapshot = publish(pull_request, entries)

    _handle(boundaries, _event(snapshot))

    document = remote_document(boundaries, checkout)
    assert len(_records(document, "close")) == closes
    assert _kinds(document)[-1] in {"send_back", "question"}


def test_a_send_back_with_a_question_stamps_its_entries_with_the_stage_closed_at_and_no_run(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
    clock: ManualClock,
) -> None:
    snapshot = publish(pull_request, (EARLIER_COMMENT, RESULT))
    closed_at = _state(snapshot.document).stage

    _handle(boundaries, _event(snapshot))

    stamps = [
        (record.speaker, record.kind, record.at, record.stage, record.run)
        for record in _state(remote_document(boundaries, checkout)).journal[-3:]
    ]
    assert stamps == [
        (HUMAN, "close", clock.now(), closed_at, None),
        (FACTORY, "send_back", clock.now(), closed_at, None),
        (FACTORY, "question", clock.now(), closed_at, None),
    ]
