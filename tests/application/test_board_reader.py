"""The board reader counts the story files on origin/main and reads the work items in progress."""

from definition_support import pipeline_definition
from factory.adapters.clock import ManualClock
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.application.board import BoardReader, BoardView
from factory.application.boundaries import Boundaries
from factory.domain.board import FeatureRow
from factory.domain.identifiers import branch_name
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from human_clone import HumanClone
from stage_run_support import INSTANCE

FEATURES = "factory/features"
FEATURE = f"{FEATURES}/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
SECOND_BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0002-second.md"


def _read(boundaries: Boundaries) -> BoardView:
    boundaries.git.fetch()
    return BoardReader(boundaries).read(pipeline_definition(boundaries))


def test_only_story_files_count_on_main(boundaries: Boundaries, human: HumanClone) -> None:
    human.push_file("main", f"{FEATURE}/in-progress/.gitkeep", "")
    human.push_file("main", f"{FEATURE}/done/.gitkeep", "")
    human.push_file("main", f"{FEATURE}/backlog/notes.md", "# Notes\n")
    human.push_file("main", f"{FEATURE}/backlog/feature.md", "# Misplaced\n")
    human.push_file("main", f"{FEATURES}/F0002-empty/feature.md", "# Empty feature\n")
    human.push_file("main", f"{FEATURES}/F0002-empty/backlog/.gitkeep", "")

    view = _read(boundaries)

    assert view.features == [
        FeatureRow(
            feature="F0001",
            title="Example feature",
            backlog=1,
            in_progress=0,
            done=0,
            acceptance="incomplete",
        )
    ]


def test_a_feature_title_comes_from_its_feature_file_else_its_directory(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.push_file("main", f"{FEATURE}/feature.md", "Intro\n# Todo service\n# Later title\n")
    human.push_file("main", f"{FEATURES}/F0002-missing/backlog/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{FEATURES}/F0003-untitled/feature.md", "No title here\n")
    human.push_file("main", f"{FEATURES}/F0003-untitled/backlog/F0003-S0001-b.md", "# B\n")

    view = _read(boundaries)

    assert [(row.feature, row.title) for row in view.features] == [
        ("F0001", "Todo service"),
        ("F0002", "F0002-missing"),
        ("F0003", "F0003-untitled"),
    ]


def test_each_story_in_progress_is_a_row_with_its_state_from_its_branch(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    human.start(BACKLOG_PATH)
    claim = Claim(instance=INSTANCE, stage="tests", started_at=clock.now(), lease_duration=30)
    state = WorkItemState(stage="tests", pull_request=7, claim=claim)
    text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body="# First\n"))
    human.push_file(branch_name("F0001-S0001"), PATH, text)
    human.push_file("main", SECOND_BACKLOG_PATH, "# Second story\n")
    human.start(SECOND_BACKLOG_PATH)
    human.push_file("main", f"{FEATURE}/backlog/F0001-S0003-third.md", "# Third story\n")

    view = _read(boundaries)

    assert [
        (row.work_item, row.title, row.folder, row.stage, row.claim, row.pull_request)
        for row in view.rows
    ] == [
        ("F0001-S0001", "First", "in-progress", "tests", claim, 7),
        ("F0001-S0002", "Second story", "in-progress", "intake", None, None),
    ]
    assert [row.running_since for row in view.rows] == [clock.now(), None]
