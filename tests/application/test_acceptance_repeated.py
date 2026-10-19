"""A feature accepted again after another story was archived: a new acceptance of its own."""

from collections.abc import Callable
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceMerged, AcceptanceService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState, story_file_ids
from factory.domain.bills import bill
from factory.domain.board import AcceptanceStatus
from factory.domain.cost_records import CostRecord
from factory.domain.events import Event
from factory.domain.journal import FACTORY, JournalRecord, entry_text
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot
from git_support import remote_commit
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
FIRST = "F0002-A0001"
SECOND = "F0002-A0002"
SECOND_BRANCH = f"work-item/{SECOND}"
SECOND_REPORT = f"{TODO}/in-progress/F0002-A0002-acceptance.md"
BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: started.\n"
FIRST_RECORDS = completed_records(FIRST, 2)
SECOND_RECORDS = completed_records(SECOND, 1)


def _done_report(work_item: str) -> str:
    return f"{TODO}/done/{work_item}-acceptance.md"


Merge = Callable[[str, list[CostRecord]], Event]


@pytest.fixture
def reader(boundaries: Boundaries, definition: PipelineDefinition) -> AcceptanceReader:
    """Return the reader of every feature's acceptance status."""
    return AcceptanceReader(boundaries, definition)


@pytest.fixture
def merge_opened(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    human: HumanClone,
    hosting: FakeHostingService,
    checkout: GitCli,
) -> Merge:
    """Return a function that opens the due acceptance, brings it to approval and merges it.

    It returns the merged event, not yet handled.
    """

    def run(work_item: str, records: list[CostRecord]) -> Event:
        checkout.fetch()
        opened = AcceptanceService(boundaries, definition).open("F0002")
        assert opened.id == work_item
        view = hosting.create_pull_request(opened.branch, work_item, "body", draft=True)
        stories = AcceptanceReader(boundaries, definition).feature_files("F0002")
        state = AcceptanceState(
            stage="approval",
            stories=story_file_ids(stories.done),
            pull_request=view.number,
            handed_over="approval",
            journal=[JournalRecord(number=1, speaker=FACTORY, kind="started")],
        )
        text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BODY))
        human.push_file(opened.branch, opened.path, text)
        human.push_file(opened.branch, cost_records_path(opened.path), sidecar_text(records))
        checkout.fetch()
        snapshot = WorkItemSnapshot(
            id=work_item,
            path=opened.path,
            folder="in-progress",
            branch=opened.branch,
            branch_commit=checkout.resolve(f"origin/{opened.branch}"),
            document=boundaries.work_item_reader.parse(text),
        )
        human.merge(opened.branch, "merge")
        main = remote_commit(remote, "main")
        assert main is not None
        hosting.merge_by_human(view.number, main)
        checkout.fetch()
        return Event(
            kind="merged",
            work_item=snapshot,
            pull_request=hosting.get_pull_request(view.number),
            remote_state=main,
        )

    return run


@pytest.fixture
def first_accepted(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    checkout: GitCli,
    merge_opened: Merge,
) -> None:
    """Accept `F0002-A0001` for two stories, then archive a third story on main."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    AcceptanceMerged(boundaries, definition).handle(merge_opened(FIRST, FIRST_RECORDS))
    human.push_file("main", f"{TODO}/done/F0002-S0003-c.md", "# C\n")
    checkout.fetch()


def _status(reader: AcceptanceReader) -> AcceptanceStatus:
    return {entry.feature: entry.status for entry in reader.read()}["F0002"]


def _done_entry(boundaries: Boundaries, checkout: GitCli, work_item: str) -> str:
    text = checkout.show_file("origin/main", _done_report(work_item))
    assert text is not None
    document = boundaries.work_item_reader.parse(text)
    assert document.state is not None
    last = document.state.journal[-1]
    assert (last.speaker, last.kind) == (FACTORY, "done")
    return entry_text(document, last.number)


@pytest.mark.usefixtures("first_accepted")
def test_a_story_archived_after_the_acceptance_makes_the_feature_due_and_opens_the_next(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    reader: AcceptanceReader,
) -> None:
    assert _status(reader) == "due"

    opened = AcceptanceService(boundaries, definition).open("F0002")

    assert (opened.id, opened.branch, opened.path) == (SECOND, SECOND_BRANCH, SECOND_REPORT)
    assert remote_commit(remote, SECOND_BRANCH) is not None
    checkout.fetch()
    assert checkout.show_file(f"origin/{SECOND_BRANCH}", SECOND_REPORT) is not None


@pytest.mark.usefixtures("first_accepted")
def test_opening_the_repeated_acceptance_leaves_the_earlier_report_and_its_costs_unchanged(
    boundaries: Boundaries, definition: PipelineDefinition, *, checkout: GitCli
) -> None:
    paths = [_done_report(FIRST), cost_records_path(_done_report(FIRST))]
    before = [checkout.show_file("origin/main", path) for path in paths]
    assert None not in before

    AcceptanceService(boundaries, definition).open("F0002")

    checkout.fetch()
    assert [checkout.show_file("origin/main", path) for path in paths] == before


@pytest.mark.usefixtures("first_accepted")
def test_a_recorded_repeated_acceptance_leaves_the_feature_accepted_and_not_due(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    reader: AcceptanceReader,
    merge_opened: Merge,
) -> None:
    event = merge_opened(SECOND, SECOND_RECORDS)
    assert _status(reader) == "merged_unrecorded"
    assert reader.due_features() == []

    AcceptanceMerged(boundaries, definition).handle(event)

    boundaries.git.fetch()
    assert _status(reader) == "accepted"
    assert reader.due_features() == []


@pytest.mark.usefixtures("first_accepted")
def test_each_acceptance_bills_only_its_own_cost_records(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    checkout: GitCli,
    merge_opened: Merge,
) -> None:
    AcceptanceMerged(boundaries, definition).handle(merge_opened(SECOND, SECOND_RECORDS))

    checkout.fetch()
    first = _done_entry(boundaries, checkout, FIRST)
    second = _done_entry(boundaries, checkout, SECOND)
    assert first == done_entry_text(bill(FIRST_RECORDS))
    assert second == done_entry_text(bill(SECOND_RECORDS))
    assert first != second
