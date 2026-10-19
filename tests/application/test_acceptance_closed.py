"""The close of an acceptance: the close is recorded on its branch, then booked refused on main."""

from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceClosed, AcceptanceService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import RECOMMENDATION, AcceptanceState, book_refusal
from factory.domain.bills import bill
from factory.domain.board import AcceptanceStatus
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, PushFailed
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
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import CLOSE_ENTRY_TEXT
from factory.domain.sections import section_text
from factory.domain.work_item import Blocked, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit, run_git
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
DONE = f"{TODO}/done"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
SIDECAR = cost_records_path(REPORT)
DONE_REPORT = f"{DONE}/F0002-A0001-acceptance.md"
DONE_SIDECAR = cost_records_path(DONE_REPORT)
PROPOSED = f"{TODO}/backlog/F0002-S0003-proposed.md"
PROPOSED_TEXT = "# Proposed story\n\n## Description\n\nCut the list in two.\n"
ROLE = "acceptance-reviewer"
STORY = "F0001-S0001"
STORY_PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
CLOSED_ON = date(2026, 10, 14)
TITLE = "# Acceptance of Todo service\n\n"
WORKING_BODY = f"{TITLE}## Journal\n"
APPROVAL_BODY = f"{TITLE}## {RECOMMENDATION}\n\naccepted with stories\n\n## Journal\n"
STARTED = NewEntry(speaker=FACTORY, kind="started", text="started.")
RESULT = NewEntry(speaker=ROLE, kind="result", text="accepted with stories.")
EARLIER_CLOSE = NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=date(2026, 10, 12))

Publish = Callable[..., WorkItemSnapshot]


@pytest.fixture
def opened(boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone) -> str:
    """Push the due feature `F0002-todo`, open its acceptance and return the branch."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{DONE}/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{DONE}/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    return AcceptanceService(boundaries, definition).open("F0002").branch


@pytest.fixture
def pull_request(hosting: FakeHostingService, opened: str) -> int:
    """Return the number of the acceptance's open draft pull request."""
    view = hosting.create_pull_request(opened, f"{ACCEPTANCE}: acceptance", "body", draft=True)
    return view.number


@pytest.fixture
def publish(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    clock: ManualClock,
    opened: str,
    pull_request: int,
) -> Publish:
    """Return a function that pushes the report to its branch and returns its snapshot.

    The clock moves to `CLOSED_ON`, so that the close entry's date differs from the
    comments' dates.
    """
    clock.advance(timedelta(days=2))

    def push(
        records: list[CostRecord] | None = None,
        *,
        stage: str = "approval",
        blocked: Blocked | None = None,
        entries: Sequence[NewEntry] = (STARTED, RESULT),
        proposed: bool = False,
    ) -> WorkItemSnapshot:
        at_approval = stage == "approval"
        state = AcceptanceState(
            stage=stage,
            stories=ARCHIVED,
            pull_request=pull_request,
            handed_over="approval" if at_approval else None,
            blocked=blocked,
        )
        body = APPROVAL_BODY if at_approval else WORKING_BODY
        document = WorkItemDocument(state=state, body=body)
        for entry in entries:
            document = append_entry(document, entry)
        text = boundaries.work_item_writer.render(document)
        human.push_file(opened, REPORT, text)
        if records is not None:
            human.push_file(opened, SIDECAR, sidecar_text(records))
        if proposed:
            human.push_file(opened, PROPOSED, PROPOSED_TEXT)
        checkout.fetch()
        return WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=opened,
            branch_commit=checkout.resolve(f"origin/{opened}"),
            document=boundaries.work_item_reader.parse(text),
        )

    return push


def _closed(hosting: FakeHostingService, pull_request: int, snapshot: WorkItemSnapshot) -> Event:
    hosting.close_by_human(pull_request)
    assert snapshot.branch_commit is not None
    return Event(
        kind="closed",
        work_item=snapshot,
        pull_request=hosting.get_pull_request(pull_request),
        remote_state=snapshot.branch_commit,
    )


def _main(remote: Path) -> str:
    main = remote_commit(remote, "main")
    assert main is not None
    return main


def _document(boundaries: Boundaries, checkout: GitCli, ref: str, path: str) -> WorkItemDocument:
    checkout.fetch()
    text = checkout.show_file(ref, path)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _on_branch(boundaries: Boundaries, checkout: GitCli) -> WorkItemDocument:
    return _document(boundaries, checkout, f"origin/{BRANCH}", REPORT)


def _booked(boundaries: Boundaries, checkout: GitCli) -> WorkItemDocument:
    return _document(boundaries, checkout, "origin/main", DONE_REPORT)


def _state(document: WorkItemDocument) -> AcceptanceState:
    assert isinstance(document.state, AcceptanceState)
    return document.state


def _records(document: WorkItemDocument, kind: JournalKind) -> list[JournalRecord]:
    return [record for record in _state(document).journal if record.kind == kind]


def _reports_in_done(checkout: GitCli) -> list[str]:
    checkout.fetch()
    return [name for name in checkout.list_files("origin/main", DONE) if "-A" in name]


def _record_only(handler: AcceptanceClosed, event: Event, kill_points: KillPoints) -> None:
    # The second push is the main branch's: the kill leaves the recorded branch to be read.
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    with pytest.raises(InjectedKill):
        handler.handle(event)


def test_the_humans_comments_and_the_close_are_recorded_on_the_branch(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish()
    first_id = hosting.add_human_comment(pull_request, "Cut the scope, *really*.")
    second_id = hosting.add_human_comment(pull_request, "Not like this.")
    comments = hosting.list_comments(pull_request)
    event = _closed(hosting, pull_request, snapshot)

    _record_only(AcceptanceClosed(boundaries, definition), event, kill_points)

    document = _on_branch(boundaries, checkout)
    first, second, close = _state(document).journal[-3:]
    for record, comment in zip((first, second), comments, strict=True):
        assert (record.speaker, record.kind) == (HUMAN, "comment")
        assert entry_text(document, record.number) == comment.body
        day = comment.created_at.date().isoformat()
        assert f"{record.number}. {day} human: {comment.body}" in document.body
    assert _state(document).comments_read == [first_id, second_id]
    assert (close.speaker, close.kind) == (HUMAN, "close")
    assert entry_text(document, close.number) == CLOSE_ENTRY_TEXT
    assert f"{close.number}. {CLOSED_ON.isoformat()} human: {CLOSE_ENTRY_TEXT}" in document.body


def test_a_comment_the_factory_posted_is_neither_recorded_nor_marked_read(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish()
    key = PostKey(work_item=ACCEPTANCE, kind="question", n="1")
    hosting.post_comment(pull_request, "A post of the factory.", key)
    [post] = hosting.list_comments(pull_request)
    event = _closed(hosting, pull_request, snapshot)

    _record_only(AcceptanceClosed(boundaries, definition), event, kill_points)

    document = _on_branch(boundaries, checkout)
    assert _records(document, "comment") == []
    assert post.id not in _state(document).comments_read
    assert "A post of the factory." not in document.body


def test_a_blank_comment_gets_no_entry_and_is_marked_read(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish()
    blank_id = hosting.add_human_comment(pull_request, "  \n\t")
    event = _closed(hosting, pull_request, snapshot)

    _record_only(AcceptanceClosed(boundaries, definition), event, kill_points)

    document = _on_branch(boundaries, checkout)
    assert _records(document, "comment") == []
    assert _state(document).comments_read == [blank_id]
    assert len(_records(document, "close")) == 1


@pytest.mark.parametrize("records", [completed_records(ACCEPTANCE, 2), None], ids=["costs", "none"])
def test_a_closed_acceptance_is_booked_refused_in_done_and_nothing_else_reaches_main(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    records: list[CostRecord] | None,
    clock: ManualClock,
) -> None:
    snapshot = publish(records, proposed=True)
    comment_id = hosting.add_human_comment(pull_request, "The list cannot be sorted.")
    [comment] = hosting.list_comments(pull_request)
    event = _closed(hosting, pull_request, snapshot)
    before = _main(remote)

    AcceptanceClosed(boundaries, definition).handle(event)

    said = NewEntry(speaker=HUMAN, kind="comment", text=comment.body, on=comment.created_at.date())
    commented = append_entry(snapshot.document, said, at=clock.now())
    read = _state(commented).model_copy(update={"comments_read": [comment_id]})
    closed = NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=CLOSED_ON)
    recorded = append_entry(commented.model_copy(update={"state": read}), closed, at=clock.now())
    expected = book_refusal(
        recorded, role=ROLE, on=CLOSED_ON, bill=bill(records or []), at=clock.now()
    )
    checkout.fetch()
    assert checkout.show_file("origin/main", DONE_REPORT) == (
        boundaries.work_item_writer.render(expected)
    )
    assert checkout.show_file("origin/main", DONE_SIDECAR) == (
        None if records is None else sidecar_text(records)
    )
    changed = run_git(remote, "diff", "--name-only", before, "main").splitlines()
    assert set(changed) == ({DONE_REPORT} if records is None else {DONE_REPORT, DONE_SIDECAR})
    assert checkout.show_file("origin/main", PROPOSED) is None


def test_after_the_booking_the_branch_is_gone_and_a_second_handling_changes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    event = _closed(hosting, pull_request, publish())
    handler = AcceptanceClosed(boundaries, definition)
    handler.handle(event)
    booked = _main(remote)
    checkout.fetch()

    handler.handle(event)

    assert _main(remote) == booked
    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"refs/heads/{BRANCH}") is None
    checkout.fetch()
    assert checkout.resolve(f"origin/{BRANCH}") is None


@pytest.mark.parametrize(
    ("point", "close_on_branch"),
    [(KillPoint.BEFORE_PUSH, True), (KillPoint.AFTER_PUSH, False)],
    ids=["before-the-push-of-main", "after-the-push-of-main"],
)
def test_after_a_kill_at_the_push_of_main_a_second_handling_books_once(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
    point: KillPoint,
    close_on_branch: bool,
) -> None:
    snapshot = publish()
    hosting.add_human_comment(pull_request, "Not like this.")
    event = _closed(hosting, pull_request, snapshot)
    before = _main(remote)
    kill_points.arm(point, after=1)
    with pytest.raises(InjectedKill):
        AcceptanceClosed(boundaries, definition).handle(event)
    if close_on_branch:
        recorded = _on_branch(boundaries, checkout)
        assert len(_records(recorded, "comment")) == 1
        assert len(_records(recorded, "close")) == 1

    AcceptanceClosed(boundaries, definition).handle(event)

    assert len(_records(_booked(boundaries, checkout), "close")) == 1
    assert _reports_in_done(checkout) == [DONE_REPORT]
    assert len(checkout.log("origin/main", since=before)) == 1
    assert remote_commit(remote, BRANCH) is None


def test_a_gone_branch_without_a_report_in_done_raises_and_changes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    event = _closed(hosting, pull_request, publish())
    run_git(remote, "branch", "-D", BRANCH)
    checkout.fetch()
    before = _main(remote)

    with pytest.raises(CannotHandle) as raised:
        AcceptanceClosed(boundaries, definition).handle(event)

    assert (raised.value.kind, raised.value.reason) == (
        "closed",
        "no report on the branch or the main branch",
    )
    assert _main(remote) == before
    assert remote_commit(remote, BRANCH) is None


@pytest.mark.parametrize(
    ("stage", "blocked"),
    [("acceptance", None), ("acceptance", "question"), ("approval", None)],
    ids=["reviewer-working", "reviewer-asking", "after-the-hand-over"],
)
def test_an_acceptance_closed_at_any_stage_is_booked_refused_without_a_reason(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    stage: str,
    blocked: Blocked | None,
) -> None:
    entries = (STARTED, RESULT) if stage == "approval" else (STARTED,)
    event = _closed(hosting, pull_request, publish(stage=stage, blocked=blocked, entries=entries))

    AcceptanceClosed(boundaries, definition).handle(event)

    document = _booked(boundaries, checkout)
    state = _state(document)
    assert (state.stage, state.outcome, state.blocked) == ("done", "refused", None)
    recommendation = section_text(document.body, RECOMMENDATION)
    assert recommendation is not None
    first_paragraph = recommendation.split("\n\n")[0].strip()
    assert first_paragraph == f"Refused by the human on {CLOSED_ON.isoformat()}: no reason given"
    assert remote_commit(remote, BRANCH) is None


def _story_snapshot() -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=STORY,
        path=STORY_PATH,
        folder="in-progress",
        branch=f"work-item/{STORY}",
        branch_commit=None,
        document=WorkItemDocument(
            state=WorkItemState(stage="approval", pull_request=1), body="# First story\n"
        ),
    )


@pytest.mark.parametrize(
    ("kind", "story", "stage", "pull_request_state", "reason"),
    [
        ("merged", True, False, None, "not a closed event"),
        ("closed", True, False, None, "not an acceptance"),
        ("closed", False, False, None, "no acceptance stage"),
        ("closed", False, True, None, "pull request is not closed"),
        ("closed", False, True, "open", "pull request is not closed"),
    ],
    ids=[
        "another-kind",
        "a-story",
        "no-acceptance-stage",
        "no-pull-request",
        "open-pull-request",
    ],
)
def test_an_event_the_handler_cannot_book_raises_its_reason_and_changes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    kind: EventKind,
    story: bool,
    stage: bool,
    pull_request_state: str | None,
    reason: str,
) -> None:
    snapshot = publish()
    view = None if pull_request_state is None else hosting.get_pull_request(pull_request)
    main = _main(remote)
    event = Event(
        kind=kind,
        work_item=_story_snapshot() if story else snapshot,
        pull_request=view,
        remote_state=main,
    )
    used = definition if stage else definition.model_copy(update={"acceptance_stage": None})

    with pytest.raises(CannotHandle) as raised:
        AcceptanceClosed(boundaries, used).handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    assert _main(remote) == main
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_the_handler_is_built_without_an_acceptance_stage(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    AcceptanceClosed(boundaries, definition.model_copy(update={"acceptance_stage": None}))


def _status(reader: AcceptanceReader) -> AcceptanceStatus:
    return {entry.feature: entry.status for entry in reader.read()}["F0002"]


def test_a_refused_feature_is_due_again_only_after_another_story_is_archived(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    AcceptanceClosed(boundaries, definition).handle(_closed(hosting, pull_request, publish()))
    reader = AcceptanceReader(boundaries, definition)
    boundaries.git.fetch()
    assert _status(reader) == "refused"
    assert "F0002" not in reader.due_features()

    human.push_file("main", f"{DONE}/F0002-S0003-c.md", "# C\n")
    boundaries.git.fetch()

    assert _status(reader) == "due"
    assert "F0002" in reader.due_features()
    assert AcceptanceService(boundaries, definition).open("F0002").id == "F0002-A0002"


def test_a_main_moved_since_the_fetch_rejects_the_booking_after_the_close_is_recorded(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    event = _closed(hosting, pull_request, publish())
    human.push_file("main", "notes.md", "The human pushed this.\n")

    with pytest.raises(PushFailed) as raised:
        AcceptanceClosed(boundaries, definition).handle(event)

    assert raised.value.outcome == "rejected"
    assert len(_records(_on_branch(boundaries, checkout), "close")) == 1
    assert remote_commit(remote, BRANCH) is not None


def test_a_refused_branch_deletion_fails_after_the_refusal_is_pushed(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    event = _closed(hosting, pull_request, publish())
    run_git(remote, "config", "receive.denyDeletes", "true")

    with pytest.raises(PushFailed) as raised:
        AcceptanceClosed(boundaries, definition).handle(event)

    assert raised.value.outcome == "rejected"
    assert _state(_booked(boundaries, checkout)).outcome == "refused"
    assert remote_commit(remote, BRANCH) is not None


def test_an_earlier_close_of_the_human_gets_no_second_close_record(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(entries=(STARTED, RESULT, EARLIER_CLOSE, RESULT))
    event = _closed(hosting, pull_request, snapshot)

    AcceptanceClosed(boundaries, definition).handle(event)

    booked = _booked(boundaries, checkout)
    assert len(_records(booked, "close")) == 1
    assert _state(booked).outcome == "refused"
