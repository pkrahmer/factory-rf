"""The board reader gives every running acceptance a work item row after its feature's stories."""

import io
from pathlib import Path

import pytest

from acceptance_walk import PROPOSED, PROPOSED_TEXT, AcceptanceWalk, report_of
from factory.adapters.clock import ManualClock
from factory.application.acceptance import AcceptanceService
from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.board import BoardRow
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from factory.entry.watch import run_watch
from git_support import run_git
from human_clone import HumanClone
from stage_run_support import INSTANCE

ACCEPTANCE = "F0002-A0001"
BRANCH = branch_name(ACCEPTANCE)
REPORT = report_of(ACCEPTANCE)
FEATURES = "factory/features"
FIRST_BACKLOG = f"{FEATURES}/F0001-example/backlog/F0001-S0001-first.md"
LATER = f"{FEATURES}/F0003-later"


@pytest.fixture
def opened(boundaries: Boundaries, walk: AcceptanceWalk) -> None:
    """Open the acceptance of `F0002` on its own branch."""
    boundaries.git.fetch()
    AcceptanceService(boundaries, walk.definition).open("F0002")


def _rows(boundaries: Boundaries, definition: PipelineDefinition) -> list[BoardRow]:
    boundaries.git.fetch()
    return BoardReader(boundaries).read(definition).rows


def _acceptance_row(boundaries: Boundaries, definition: PipelineDefinition) -> BoardRow:
    [row] = [row for row in _rows(boundaries, definition) if row.work_item == ACCEPTANCE]
    return row


def _branch_document(boundaries: Boundaries) -> WorkItemDocument:
    boundaries.git.fetch()
    text = boundaries.git.show_file(f"origin/{BRANCH}", REPORT)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


@pytest.mark.usefixtures("opened")
def test_an_opened_acceptance_is_a_row_titled_by_its_report(
    boundaries: Boundaries, walk: AcceptanceWalk
) -> None:
    rows = _rows(boundaries, walk.definition)

    assert rows == [
        BoardRow(
            work_item=ACCEPTANCE,
            title="Acceptance of Todo service",
            folder="in-progress",
            stage="acceptance",
            blocked=None,
            claim=None,
            running_since=None,
            pull_request=None,
        )
    ]


@pytest.mark.usefixtures("opened")
def test_an_acceptance_row_shows_stage_pull_request_and_blocked_from_its_branch(
    boundaries: Boundaries, walk: AcceptanceWalk
) -> None:
    walk.record(ACCEPTANCE, 3, [], stage="approval", blocked="question")

    row = _acceptance_row(boundaries, walk.definition)

    assert (row.stage, row.pull_request, row.blocked) == ("approval", 3, "question")


@pytest.mark.usefixtures("opened")
def test_an_acceptance_row_shows_its_claim_and_running_since(
    boundaries: Boundaries, walk: AcceptanceWalk, *, human: HumanClone, clock: ManualClock
) -> None:
    claim = Claim(instance=INSTANCE, stage="acceptance", started_at=clock.now(), lease_duration=30)
    document = _branch_document(boundaries)
    assert isinstance(document.state, AcceptanceState)
    state = document.state.model_copy(update={"stage": "acceptance", "claim": claim})
    claimed = document.model_copy(update={"state": state})
    human.push_file(BRANCH, REPORT, boundaries.work_item_writer.render(claimed))

    row = _acceptance_row(boundaries, walk.definition)

    assert (row.claim, row.running_since) == (claim, claim.started_at)


@pytest.mark.usefixtures("opened")
@pytest.mark.parametrize(
    ("pushed", "started", "expected"),
    [
        ([], [FIRST_BACKLOG], ["F0001-S0001", ACCEPTANCE]),
        (
            [
                (f"{LATER}/feature.md", "# Later\n"),
                (f"{LATER}/in-progress/F0003-S0001-a.md", "# A\n"),
            ],
            [FIRST_BACKLOG],
            ["F0001-S0001", ACCEPTANCE, "F0003-S0001"],
        ),
        ([(PROPOSED, PROPOSED_TEXT)], [PROPOSED], ["F0002-S0003", ACCEPTANCE]),
    ],
    ids=["story-of-an-earlier-feature", "stories-around-it", "story-of-its-own-feature"],
)
def test_rows_come_in_work_item_order(
    boundaries: Boundaries,
    walk: AcceptanceWalk,
    *,
    human: HumanClone,
    pushed: list[tuple[str, str]],
    started: list[str],
    expected: list[str],
) -> None:
    for path, text in pushed:
        human.push_file("main", path, text)
    for path in started:
        human.start(path)

    rows = _rows(boundaries, walk.definition)

    assert [row.work_item for row in rows] == expected


def test_a_merged_acceptance_has_its_row_until_it_is_booked_into_done(
    boundaries: Boundaries, walk: AcceptanceWalk, *, remote: Path
) -> None:
    number = walk.open(ACCEPTANCE)
    walk.record(ACCEPTANCE, number, [], stage="approval", handed_over="approval")
    walk.merge(ACCEPTANCE, number)
    run_git(remote, "branch", "-D", BRANCH)

    merged = _rows(boundaries, walk.definition)
    walk.tick()
    booked = _rows(boundaries, walk.definition)

    assert [row.work_item for row in merged] == [ACCEPTANCE]
    assert booked == []


@pytest.mark.usefixtures("opened")
def test_without_an_acceptance_stage_an_acceptance_branch_adds_no_row(
    boundaries: Boundaries, walk: AcceptanceWalk, *, human: HumanClone
) -> None:
    human.start(FIRST_BACKLOG)
    without = walk.definition.model_copy(update={"acceptance_stage": None})

    rows = _rows(boundaries, without)

    assert [row.work_item for row in rows] == ["F0001-S0001"]


@pytest.mark.usefixtures("opened")
def test_run_watch_prints_the_acceptance_row_under_work_items(boundaries: Boundaries) -> None:
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()

    status = run_watch(boundaries, INSTANCE, out, err)

    assert (status, err.getvalue()) == (0, "")
    lines = out.getvalue().splitlines()
    assert lines[lines.index("work items") + 1 :] == [
        "F0002-A0001  Acceptance of Todo service  in-progress  stage=acceptance  blocked=-  "
        "claim=-  running_since=-  pull_request=-"
    ]


def test_a_report_with_a_plain_work_item_state_is_a_format_error_with_its_path(
    boundaries: Boundaries, walk: AcceptanceWalk, *, human: HumanClone
) -> None:
    plain = WorkItemDocument(
        state=WorkItemState(stage="acceptance"), body="# Acceptance of Todo service\n"
    )
    human.push_file(BRANCH, REPORT, boundaries.work_item_writer.render(plain))
    boundaries.git.fetch()

    with pytest.raises(WorkItemFormatError) as raised:
        BoardReader(boundaries).read(walk.definition)

    assert raised.value.path == REPORT
