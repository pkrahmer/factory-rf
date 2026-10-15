"""An acceptance the human merges before its approval is booked accepted, saying so."""

from collections.abc import Callable
from pathlib import Path
from typing import Literal

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceMerged, AcceptanceService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.bills import bill, cost_line
from factory.domain.events import Event
from factory.domain.journal import FACTORY, JournalRecord, entry_text
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot
from git_support import PIPELINE_YAML, remote_commit
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ACCEPTANCE = "F0002-A0001"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
DONE_REPORT = f"{TODO}/done/F0002-A0001-acceptance.md"
PROPOSED = f"{TODO}/backlog/F0002-S0003-proposed.md"
BEFORE_APPROVAL = "done (pull request merged before approval); cost: "
BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: started.\n"
RECORDS = completed_records(ACCEPTANCE, 2)

MergeMethod = Literal["merge", "squash", "rebase"]
Publish = Callable[..., WorkItemSnapshot]
Merge = Callable[..., Event]


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition: `acceptance`, then `approval`, then `done`."""
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
    """Return a function that pushes the report at a stage, with its cost records, unmerged."""

    def push(
        stage: str, *, blocked: Literal["question"] | None = None, proposed: bool = False
    ) -> WorkItemSnapshot:
        state = AcceptanceState(
            stage=stage,
            stories=ARCHIVED,
            pull_request=pull_request,
            blocked=blocked,
            journal=[JournalRecord(number=1, speaker=FACTORY, kind="started")],
        )
        text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BODY))
        human.push_file(opened, REPORT, text)
        human.push_file(opened, cost_records_path(REPORT), sidecar_text(RECORDS))
        if proposed:
            human.push_file(opened, PROPOSED, "# Proposed story\n")
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
    opened: str,
    pull_request: int,
) -> Merge:
    """Return a function that merges the branch as the human and returns the merged event."""

    def run(snapshot: WorkItemSnapshot, method: MergeMethod = "merge") -> Event:
        human.merge(opened, method)
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


def _booked(boundaries: Boundaries, checkout: GitCli) -> tuple[AcceptanceState, str]:
    """The report booked in `done/` on main: its state and the text of its last entry."""
    checkout.fetch()
    text = checkout.show_file("origin/main", DONE_REPORT)
    assert text is not None
    document = boundaries.work_item_reader.parse(text)
    state = document.state
    assert isinstance(state, AcceptanceState)
    last = state.journal[-1]
    assert (last.speaker, last.kind) == (FACTORY, "done")
    return state, entry_text(document, last.number)


def test_an_acceptance_merged_at_its_review_stage_is_booked_accepted_before_approval(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish("acceptance"))

    AcceptanceMerged(boundaries, definition).handle(event)

    state, text = _booked(boundaries, checkout)
    assert (state.stage, state.outcome) == ("done", "accepted")
    assert text == BEFORE_APPROVAL + cost_line(bill(RECORDS))
    assert checkout.show_file("origin/main", REPORT) is None


def test_an_acceptance_merged_while_it_waits_with_a_question_is_booked_and_unblocked(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish("acceptance", blocked="question"))

    AcceptanceMerged(boundaries, definition).handle(event)

    state, text = _booked(boundaries, checkout)
    assert (state.stage, state.outcome, state.blocked) == ("done", "accepted", None)
    assert text == BEFORE_APPROVAL + cost_line(bill(RECORDS))


def test_an_acceptance_merged_at_its_approval_before_the_hand_over_is_booked_as_usual(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish("approval"))

    AcceptanceMerged(boundaries, definition).handle(event)

    state, text = _booked(boundaries, checkout)
    assert (state.stage, state.outcome) == ("done", "accepted")
    assert text == done_entry_text(bill(RECORDS))
    assert "before approval" not in text


@pytest.mark.parametrize("method", ["merge", "squash", "rebase"])
def test_every_merge_method_books_an_acceptance_merged_before_approval_alike(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
    method: MergeMethod,
) -> None:
    event = merge(publish("acceptance"), method)

    AcceptanceMerged(boundaries, definition).handle(event)

    state, text = _booked(boundaries, checkout)
    assert (state.stage, state.outcome) == ("done", "accepted")
    assert text == BEFORE_APPROVAL + cost_line(bill(RECORDS))
    assert checkout.list_files("origin/main", f"{TODO}/in-progress") == []


def test_the_proposed_stories_of_a_merge_before_approval_leave_the_feature_incomplete(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    publish: Publish,
    merge: Merge,
) -> None:
    event = merge(publish("acceptance", proposed=True))

    AcceptanceMerged(boundaries, definition).handle(event)

    checkout.fetch()
    reader = AcceptanceReader(boundaries, definition)
    statuses = {entry.feature: entry.status for entry in reader.read()}
    assert statuses["F0002"] == "incomplete"
    assert reader.due_features() == []
