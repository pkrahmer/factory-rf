"""The acceptance reader derives each feature's acceptance status from the remote alone."""

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import AcceptanceState, FeatureAcceptance, FeatureFiles
from factory.domain.board import FeatureRow
from factory.domain.errors import WorkItemFormatError
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
from git_support import write_files
from human_clone import HumanClone

FEATURES = "factory/features"
EXAMPLE = f"{FEATURES}/F0001-example"
TODO = f"{FEATURES}/F0002-todo"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
IN_FLIGHT_REPORT = f"{EXAMPLE}/in-progress/F0001-A0001-acceptance.md"


@pytest.fixture
def without_acceptance(definition: PipelineDefinition) -> PipelineDefinition:
    """Return the pipeline definition without an acceptance stage."""
    return definition.model_copy(update={"acceptance_stage": None})


def _reader(boundaries: Boundaries, definition: PipelineDefinition) -> AcceptanceReader:
    boundaries.git.fetch()
    return AcceptanceReader(boundaries, definition)


def _push_complete(human: HumanClone, directory: str) -> None:
    feature = directory.split("-", maxsplit=1)[0]
    human.push_file("main", f"{FEATURES}/{directory}/feature.md", f"# {directory}\n")
    human.push_file("main", f"{FEATURES}/{directory}/done/{feature}-S0001-a.md", "# A\n")
    human.push_file("main", f"{FEATURES}/{directory}/done/{feature}-S0002-b.md", "# B\n")


def _report(state: AcceptanceState) -> str:
    document = WorkItemDocument(state=state, body="# Acceptance\n")
    return FrontmatterWorkItemWriter().render(document)


def _entry(entries: list[FeatureAcceptance], feature: str) -> FeatureAcceptance:
    [entry] = [entry for entry in entries if entry.feature == feature]
    return entry


@pytest.mark.parametrize("committed", [False, True])
def test_the_work_tree_and_local_branches_are_not_read(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition, committed: bool
) -> None:
    _push_complete(human, "F0002-todo")
    reader = _reader(boundaries, definition)
    write_files(boundaries.checkout, {f"{TODO}/backlog/F0002-S0003-c.md": "# C\n"})
    if committed:
        boundaries.git.commit("a story on the local main only")

    files = reader.feature_files("F0002")

    assert files.backlog == []
    assert _entry(reader.read(), "F0002").status == "due"


def test_a_complete_feature_on_main_is_due_and_a_stray_directory_has_no_entry(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    _push_complete(human, "F0002-todo")
    human.push_file("main", f"{TODO}/in-progress/.gitkeep", "")
    human.push_file("main", f"{FEATURES}/notes/readme.md", "# Notes\n")

    entries = _reader(boundaries, definition).read()

    assert [entry.feature for entry in entries] == ["F0001", "F0002"]
    assert _entry(entries, "F0002") == FeatureAcceptance(
        feature="F0002",
        directory="F0002-todo",
        status="due",
        archived=ARCHIVED,
        next_acceptance="F0002-A0001",
    )


def test_a_recorded_covering_report_is_accepted_and_the_next_id_follows_it(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    _push_complete(human, "F0002-todo")
    state = AcceptanceState(stage="done", outcome="accepted", stories=ARCHIVED)
    human.push_file("main", f"{TODO}/done/F0002-A0001-acceptance.md", _report(state))

    entry = _entry(_reader(boundaries, definition).read(), "F0002")

    assert (entry.status, entry.archived, entry.next_acceptance) == (
        "accepted",
        ARCHIVED,
        "F0002-A0002",
    )


def test_a_report_on_its_remote_branch_is_in_flight(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    state = AcceptanceState(stage="acceptance", stories=["F0001-S0001"])
    human.push_file("work-item/F0001-A0001", IN_FLIGHT_REPORT, _report(state))

    entry = _entry(_reader(boundaries, definition).read(), "F0001")

    assert (entry.status, entry.next_acceptance) == ("in_flight", "F0001-A0002")


@pytest.mark.parametrize(
    ("branch", "path"),
    [
        ("work-item/F0001-A0001", f"{EXAMPLE}/in-progress/notes.md"),
        ("work-item/F0001-S0001", f"{EXAMPLE}/in-progress/F0001-S0001-first.md"),
    ],
)
def test_a_branch_without_a_report_is_not_in_flight(
    boundaries: Boundaries,
    human: HumanClone,
    definition: PipelineDefinition,
    branch: str,
    path: str,
) -> None:
    human.push_file(branch, path, "# Not a report\n")

    entry = _entry(_reader(boundaries, definition).read(), "F0001")

    assert (entry.status, entry.next_acceptance) == ("incomplete", "F0001-A0001")


@pytest.mark.parametrize(
    "text",
    [
        "---\nstage: [done\n---\n# Acceptance\n",
        "---\nstage: done\nround: 0\nattempts: 0\n---\n# Acceptance\n",
    ],
)
def test_an_unreadable_report_on_main_is_a_format_error_with_its_path(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition, text: str
) -> None:
    _push_complete(human, "F0002-todo")
    path = f"{TODO}/done/F0002-A0001-acceptance.md"
    human.push_file("main", path, text)
    reader = _reader(boundaries, definition)

    with pytest.raises(WorkItemFormatError) as caught:
        reader.read()

    assert caught.value.path == path


def test_a_feature_without_a_directory_has_no_files(
    boundaries: Boundaries, definition: PipelineDefinition
) -> None:
    files = _reader(boundaries, definition).feature_files("F0005")

    assert files == FeatureFiles(feature="F0005", backlog=[], in_progress=[], done=[])


def test_due_features_ascend_and_leave_out_incomplete_ones(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    _push_complete(human, "F0003-later")
    _push_complete(human, "F0002-todo")

    assert _reader(boundaries, definition).due_features() == ["F0002", "F0003"]


@pytest.mark.parametrize("complete", [False, True])
def test_nothing_is_due_without_a_complete_feature_or_an_acceptance_stage(
    boundaries: Boundaries,
    human: HumanClone,
    definition: PipelineDefinition,
    without_acceptance: PipelineDefinition,
    complete: bool,
) -> None:
    if complete:
        _push_complete(human, "F0002-todo")

    reader = _reader(boundaries, without_acceptance if complete else definition)

    assert reader.due_features() == []


@pytest.mark.parametrize(
    ("with_stage", "expected"), [(True, ["due", "incomplete", None]), (False, [None, None, None])]
)
def test_fill_board_sets_each_known_feature_status_in_order(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    definition: PipelineDefinition,
    without_acceptance: PipelineDefinition,
    with_stage: bool,
    expected: list[str | None],
) -> None:
    _push_complete(human, "F0002-todo")
    rows = [
        FeatureRow(feature=feature, title=feature, backlog=0, in_progress=0, done=0)
        for feature in ["F0002", "F0001", "F0009"]
    ]
    reader = _reader(boundaries, definition if with_stage else without_acceptance)

    filled = reader.fill_board(rows)

    assert [row.feature for row in filled] == ["F0002", "F0001", "F0009"]
    assert [row.acceptance for row in filled] == expected
    assert filled[2] == rows[2]


def test_the_first_of_two_directories_of_one_feature_counts(
    boundaries: Boundaries, human: HumanClone, definition: PipelineDefinition
) -> None:
    human.push_file("main", f"{FEATURES}/F0002-a/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{FEATURES}/F0002-b/backlog/F0002-S0002-b.md", "# B\n")
    reader = _reader(boundaries, definition)

    files = reader.feature_files("F0002")
    entries = [entry for entry in reader.read() if entry.feature == "F0002"]

    assert files == FeatureFiles(feature="F0002", done=["F0002-S0001-a.md"])
    assert [(entry.directory, entry.status) for entry in entries] == [("F0002-a", "due")]
