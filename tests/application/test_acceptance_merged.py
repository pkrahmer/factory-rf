"""The merge of an acceptance: the report is booked accepted on main, then its branch goes."""

from collections.abc import Callable
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceMerged, AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import commit_subject
from factory.domain.acceptance import AcceptanceState, book_merge
from factory.domain.bills import bill
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, PushFailed
from factory.domain.events import Event, EventKind
from factory.domain.journal import FACTORY, JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import PIPELINE_YAML, remote_commit, run_git
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
SIDECAR = cost_records_path(REPORT)
DONE_REPORT = f"{TODO}/done/F0002-A0001-acceptance.md"
DONE_SIDECAR = cost_records_path(DONE_REPORT)
PROPOSED = f"{TODO}/backlog/F0002-S0003-proposed.md"
PROPOSED_TEXT = "# Proposed story\n\n## Description\n\nCut the list in two.\n"
ROLE = "acceptance-reviewer"
STORY = "F0001-S0001"
STORY_PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
SUBJECT = commit_subject(ACCEPTANCE, "merged, archived")
FAKE_MERGE = "a" * 40


def _body(recommendation: str) -> str:
    return (
        f"# Acceptance of Todo service\n\n## Recommendation\n\n{recommendation}\n\n"
        "## Proposed stories\n\n- one story\n\n## Journal\n\n1. factory: started.\n"
        f"2. acceptance-reviewer: {recommendation}\n"
    )


Publish = Callable[..., WorkItemSnapshot]
Merge = Callable[[WorkItemSnapshot], Event]


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, with the acceptance stage `acceptance`."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


@pytest.fixture
def opened(boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone) -> str:
    """Push the due feature `F0002-todo`, open its acceptance and return the branch."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
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
    opened: str,
    pull_request: int,
) -> Publish:
    """Return a function that pushes the report at the approval to its branch, not merged."""

    def push(
        records: list[CostRecord] | None = None,
        *,
        recommendation: str = "accepted with stories",
        proposed: bool = False,
    ) -> WorkItemSnapshot:
        journal = [
            JournalRecord(number=1, speaker=FACTORY, kind="started"),
            JournalRecord(number=2, speaker=ROLE, kind="result"),
        ]
        state = AcceptanceState(
            stage="approval",
            stories=ARCHIVED,
            pull_request=pull_request,
            handed_over="approval",
            journal=journal,
        )
        document = WorkItemDocument(state=state, body=_body(recommendation))
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


@pytest.fixture
def merge(
    *,
    remote: Path,
    human: HumanClone,
    hosting: FakeHostingService,
    checkout: GitCli,
    pull_request: int,
) -> Merge:
    """Return a function that merges the branch as the human and returns the merged event."""

    def run(snapshot: WorkItemSnapshot) -> Event:
        human.merge(BRANCH, "merge")
        main = remote_commit(remote, "main")
        assert main is not None
        hosting.merge_by_human(pull_request, main)
        checkout.fetch()
        return Event(
            kind="merged",
            work_item=snapshot,
            pull_request=hosting.get_pull_request(pull_request),
            remote_state=main,
        )

    return run


def _main_text(checkout: GitCli, path: str) -> str | None:
    checkout.fetch()
    return checkout.show_file("origin/main", path)


def _booked(boundaries: Boundaries, checkout: GitCli) -> AcceptanceState:
    text = _main_text(checkout, DONE_REPORT)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert isinstance(state, AcceptanceState)
    return state


@pytest.mark.parametrize("records", [completed_records(ACCEPTANCE, 2), None], ids=["costs", "none"])
def test_a_merged_acceptance_is_booked_accepted_in_done_with_its_cost_records(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
    records: list[CostRecord] | None,
    clock: ManualClock,
) -> None:
    snapshot = publish(records)
    event = merge(snapshot)
    merged = _main_text(checkout, REPORT)
    assert merged is not None

    AcceptanceMerged(boundaries, definition).handle(event)

    expected = book_merge(
        boundaries.work_item_reader.parse(merged), bill(records or []), at=clock.now()
    )
    assert _main_text(checkout, DONE_REPORT) == boundaries.work_item_writer.render(expected)
    assert _main_text(checkout, DONE_SIDECAR) == (
        None if records is None else sidecar_text(records)
    )
    assert checkout.list_files("origin/main", f"{TODO}/in-progress") == []


def test_after_the_booking_the_branch_is_gone_and_a_second_handling_changes_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish())
    handler = AcceptanceMerged(boundaries, definition)
    handler.handle(event)
    booked = remote_commit(remote, "main")

    handler.handle(event)

    assert remote_commit(remote, "main") == booked
    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"refs/heads/{BRANCH}") is None
    assert checkout.resolve(f"origin/{BRANCH}") is None


def test_the_booking_commit_changes_only_the_report_and_keeps_the_proposed_stories(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish(completed_records(ACCEPTANCE, 1), proposed=True))

    AcceptanceMerged(boundaries, definition).handle(event)

    checkout.fetch()
    [commit] = checkout.log("origin/main", since=event.remote_state)
    assert commit.subject == SUBJECT
    changed = run_git(remote, "diff-tree", "--no-commit-id", "--name-only", "-r", "main")
    assert set(changed.splitlines()) == {REPORT, SIDECAR, DONE_REPORT, DONE_SIDECAR}
    assert checkout.show_file("origin/main", PROPOSED) == PROPOSED_TEXT


def test_a_merge_books_accepted_whatever_the_recommendation_says(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish(recommendation="not accepted"))

    AcceptanceMerged(boundaries, definition).handle(event)

    state = _booked(boundaries, checkout)
    assert (state.stage, state.outcome) == ("done", "accepted")


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
        ("closed", True, False, None, "not a merged event"),
        ("merged", True, False, None, "not an acceptance"),
        ("merged", False, False, None, "no acceptance stage"),
        ("merged", False, True, None, "pull request is not merged"),
        ("merged", False, True, "open", "pull request is not merged"),
        ("merged", False, True, "merged", "no report on the main branch"),
    ],
    ids=[
        "another-kind",
        "a-story",
        "no-acceptance-stage",
        "no-pull-request",
        "open-pull-request",
        "no-report-on-main",
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
    if pull_request_state == "merged":
        hosting.merge_by_human(pull_request, FAKE_MERGE)
    view = None if pull_request_state is None else hosting.get_pull_request(pull_request)
    main = remote_commit(remote, "main")
    assert main is not None
    event = Event(
        kind=kind,
        work_item=_story_snapshot() if story else snapshot,
        pull_request=view,
        remote_state=main,
    )
    used = definition if stage else definition.model_copy(update={"acceptance_stage": None})

    with pytest.raises(CannotHandle) as raised:
        AcceptanceMerged(boundaries, used).handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    assert remote_commit(remote, "main") == main
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_after_a_kill_after_the_push_a_second_handling_books_once_and_deletes_the_branch(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    kill_points: KillPoints,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish())
    kill_points.arm(KillPoint.AFTER_PUSH)
    with pytest.raises(InjectedKill):
        AcceptanceMerged(boundaries, definition).handle(event)

    AcceptanceMerged(boundaries, definition).handle(event)

    kinds = [record.kind for record in _booked(boundaries, checkout).journal]
    assert kinds.count("done") == 1
    assert len(checkout.log("origin/main", since=event.remote_state)) == 1
    assert remote_commit(remote, BRANCH) is None


def test_the_handler_is_built_without_an_acceptance_stage(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    AcceptanceMerged(boundaries, definition.model_copy(update={"acceptance_stage": None}))


def test_a_main_moved_since_the_fetch_rejects_the_booking_and_keeps_the_branch(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    human: HumanClone,
    publish: Publish,
    merge: Merge,
) -> None:
    snapshot = publish()
    event = merge(snapshot)
    human.push_file("main", "notes.md", "The human pushed this.\n")

    with pytest.raises(PushFailed) as raised:
        AcceptanceMerged(boundaries, definition).handle(event)

    assert raised.value.outcome == "rejected"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_refused_branch_deletion_fails_after_the_booking_is_pushed(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    snapshot = publish()
    event = merge(snapshot)
    run_git(remote, "config", "receive.denyDeletes", "true")

    with pytest.raises(PushFailed) as raised:
        AcceptanceMerged(boundaries, definition).handle(event)

    assert raised.value.outcome == "rejected"
    assert _booked(boundaries, checkout).stage == "done"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
