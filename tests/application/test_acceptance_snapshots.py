"""The acceptance reader gives a snapshot of every acceptance report in `in-progress/`."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceService
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState
from factory.domain.errors import WorkItemFormatError
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import run_git
from human_clone import HumanClone

FEATURES = "factory/features"
EXAMPLE = f"{FEATURES}/F0001-example"
TODO = f"{FEATURES}/F0002-todo"
LATER = f"{FEATURES}/F0003-later"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
DONE_REPORT = f"{TODO}/done/F0002-A0001-acceptance.md"


@pytest.fixture
def todo(human: HumanClone) -> None:
    """Push the complete feature `F0002-todo`: its feature file and two archived stories."""
    _push_todo(human)


def _push_todo(human: HumanClone) -> None:
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")


@pytest.fixture
def opened(boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone) -> None:
    """Push `F0002-todo` and open its acceptance on its own branch."""
    _push_todo(human)
    boundaries.git.fetch()
    AcceptanceService(boundaries, definition).open("F0002")


def _render(boundaries: Boundaries, state: WorkItemState) -> str:
    document = WorkItemDocument(state=state, body="# Acceptance of Todo service\n")
    return boundaries.work_item_writer.render(document)


def _snapshots(boundaries: Boundaries, definition: PipelineDefinition) -> list[WorkItemSnapshot]:
    boundaries.git.fetch()
    return AcceptanceReader(boundaries, definition).snapshots()


def _parsed(boundaries: Boundaries, ref: str, path: str) -> WorkItemDocument:
    text = boundaries.git.show_file(ref, path)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _approval(pull_request: int = 1) -> AcceptanceState:
    return AcceptanceState(
        stage="approval", stories=ARCHIVED, pull_request=pull_request, handed_over="approval"
    )


@pytest.mark.usefixtures("opened")
def test_a_report_on_its_branch_alone_gives_its_snapshot(
    boundaries: Boundaries, definition: PipelineDefinition, checkout: GitCli
) -> None:
    snapshots = _snapshots(boundaries, definition)

    assert snapshots == [
        WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=BRANCH,
            branch_commit=checkout.resolve(f"origin/{BRANCH}"),
            document=_parsed(boundaries, f"origin/{BRANCH}", REPORT),
        )
    ]


@pytest.mark.parametrize(
    ("branch", "path", "report"),
    [
        ("work-item/F0001-S0001", f"{EXAMPLE}/in-progress/F0001-S0001-first.md", False),
        ("work-item/F0001-A0001", f"{EXAMPLE}/in-progress/notes.md", False),
        ("main", f"{EXAMPLE}/in-progress/F0002-A0001-acceptance.md", True),
        (
            "work-item/F0004-A0001",
            f"{FEATURES}/F0004-missing/in-progress/F0004-A0001-acceptance.md",
            True,
        ),
    ],
    ids=[
        "story-branch",
        "acceptance-branch-without-report",
        "report-in-another-features-directory-on-main",
        "branch-report-under-a-feature-directory-main-lacks",
    ],
)
def test_a_story_branch_and_an_acceptance_branch_without_a_report_are_skipped(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    branch: str,
    path: str,
    report: bool,
) -> None:
    text = _render(boundaries, _approval()) if report else "# Not a report\n"
    human.push_file(branch, path, text)

    assert _snapshots(boundaries, definition) == []


@pytest.mark.usefixtures("opened")
def test_a_merged_report_not_yet_recorded_has_mains_path_and_the_branchs_document(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    checkout: GitCli,
) -> None:
    human.merge(BRANCH, "merge")
    human.push_file(BRANCH, REPORT, _render(boundaries, _approval()))

    snapshots = _snapshots(boundaries, definition)

    assert snapshots == [
        WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=BRANCH,
            branch_commit=checkout.resolve(f"origin/{BRANCH}"),
            document=_parsed(boundaries, f"origin/{BRANCH}", REPORT),
        )
    ]
    assert snapshots[0].document != _parsed(boundaries, "origin/main", REPORT)


@pytest.mark.usefixtures("opened")
def test_a_merged_report_whose_branch_is_deleted_is_read_from_main(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    remote: Path,
) -> None:
    human.merge(BRANCH, "merge")
    run_git(remote, "branch", "-D", BRANCH)

    snapshots = _snapshots(boundaries, definition)

    assert snapshots == [
        WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=BRANCH,
            branch_commit=None,
            document=_parsed(boundaries, "origin/main", REPORT),
        )
    ]


@pytest.mark.usefixtures("todo")
@pytest.mark.parametrize("leftover", [False, True], ids=["recorded", "leftover-branch"])
def test_a_recorded_report_gives_a_snapshot_only_from_a_leftover_branch(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    human: HumanClone,
    checkout: GitCli,
    leftover: bool,
) -> None:
    accepted = AcceptanceState(stage="done", outcome="accepted", stories=ARCHIVED)
    human.push_file("main", DONE_REPORT, _render(boundaries, accepted))
    if leftover:
        human.push_file(BRANCH, REPORT, _render(boundaries, _approval()))

    snapshots = _snapshots(boundaries, definition)

    if not leftover:
        assert snapshots == []
        return
    assert snapshots == [
        WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=BRANCH,
            branch_commit=checkout.resolve(f"origin/{BRANCH}"),
            document=_parsed(boundaries, f"origin/{BRANCH}", REPORT),
        )
    ]


@pytest.mark.usefixtures("opened")
def test_snapshots_of_two_features_come_in_work_item_order(
    boundaries: Boundaries, definition: PipelineDefinition, *, human: HumanClone
) -> None:
    later = AcceptanceState(stage="approval", stories=["F0003-S0001"])
    human.push_file("main", f"{LATER}/feature.md", "# Later\n")
    human.push_file("main", f"{LATER}/done/F0003-S0001-a.md", "# A\n")
    human.push_file(
        "main", f"{LATER}/in-progress/F0003-A0001-acceptance.md", _render(boundaries, later)
    )

    snapshots = _snapshots(boundaries, definition)

    assert [(snapshot.id, snapshot.branch_commit is None) for snapshot in snapshots] == [
        ("F0002-A0001", False),
        ("F0003-A0001", True),
    ]


@pytest.mark.usefixtures("todo")
def test_a_report_with_a_plain_work_item_state_is_a_format_error_with_its_path(
    boundaries: Boundaries, definition: PipelineDefinition, *, human: HumanClone
) -> None:
    human.push_file(BRANCH, REPORT, _render(boundaries, WorkItemState(stage="acceptance")))

    with pytest.raises(WorkItemFormatError) as raised:
        _snapshots(boundaries, definition)

    assert raised.value.path == REPORT


@pytest.mark.usefixtures("opened")
def test_no_acceptance_stage_gives_no_snapshots(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    without = definition.model_copy(update={"acceptance_stage": None})

    assert _snapshots(boundaries, without) == []
