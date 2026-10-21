"""Work items are read from main's in-progress folder and their branches on the remote."""

from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.boundaries import Boundaries
from factory.application.work_items import RemoteWorkItems
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.paths import LIFECYCLE_FOLDERS
from factory.domain.work_item import StoryFile, initial_state
from git_support import CHECKOUT, remote_commit, write_files
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BRANCH_TEXT = "---\nstage: tests\nattempts: 1\n---\n# First story\n"
STALE_TEXT = "---\nstage: review\nattempts: 2\n---\n# First story\n"
UNREADABLE = "---\n[\n---\n# T\n"
SPECIFICATION_WITH_STATE = (
    "---\nstage: review\nattempts: 2\nround: 1\nblocked: question\n---\n"
    "# First story\n\n## Description\n\nStarted by the human.\n"
)
SPECIFICATION_BODY = "# First story\n\n## Description\n\nStarted by the human.\n"


def _items(checkout: GitCli) -> RemoteWorkItems:
    checkout.fetch()
    return RemoteWorkItems(checkout, FrontmatterWorkItemReader())


def _ids(stories: list[StoryFile]) -> list[str]:
    return [story.id for story in stories]


def _commit_local_branch(checkout: GitCli, work_tree: Path, text: str) -> None:
    checkout.fetch()
    checkout.checkout(BRANCH, start_point="origin/main")
    write_files(work_tree, {PATH: text})
    checkout.commit("local state")


def _push_in_progress(human: HumanClone, paths: list[str]) -> None:
    for path in paths:
        human.push_file("main", path, "# A story\n")


def test_in_progress_stories_are_listed_with_their_parts(
    checkout: GitCli, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)

    stories = _items(checkout).list_stories("in-progress")

    assert stories == [
        StoryFile(
            id=WORK_ITEM,
            path=PATH,
            feature_directory="F0001-example",
            file_name="F0001-S0001-first.md",
            folder="in-progress",
        )
    ]


def test_stories_only_in_the_checkout_are_not_listed(tmp_path: Path, checkout: GitCli) -> None:
    work_tree = tmp_path / CHECKOUT
    write_files(work_tree, {f"{FEATURE}/in-progress/F0001-S0002-local.md": "# Local\n"})
    items = _items(checkout)

    assert items.list_stories("in-progress") == []

    checkout.commit("a story never pushed")

    assert items.list_stories("in-progress") == []


def test_stories_are_listed_in_plain_id_order(checkout: GitCli, human: HumanClone) -> None:
    _push_in_progress(
        human,
        [
            "factory/features/F0002-second/in-progress/F0002-S0001-a.md",
            f"{FEATURE}/in-progress/F0001-S0010-b.md",
            f"{FEATURE}/in-progress/F0001-S0002-c.md",
        ],
    )

    stories = _items(checkout).list_stories("in-progress")

    assert _ids(stories) == ["F0001-S0002", "F0001-S0010", "F0002-S0001"]


@pytest.mark.parametrize(
    "path",
    [
        f"{FEATURE}/in-progress/.gitkeep",
        f"{FEATURE}/feature.md",
        f"{FEATURE}/in-progress/deeper/F0001-S0003-deep.md",
        f"{FEATURE}/in-progress/notes.md",
        "factory/features/F0001-demo/in-progress/F0002-S0001-x.md",
        f"{FEATURE}/in-progress/F0001-A0001-report.md",
    ],
)
def test_files_that_are_not_story_files_are_not_listed(
    checkout: GitCli, human: HumanClone, path: str
) -> None:
    human.push_file("main", path, "# Not a story\n")
    human.push_file("main", f"{FEATURE}/in-progress/F0001-S0002-real.md", "# Real\n")

    stories = _items(checkout).list_stories("in-progress")

    assert [story.path for story in stories] == [f"{FEATURE}/in-progress/F0001-S0002-real.md"]


def test_backlog_and_done_list_only_their_own_stories(checkout: GitCli, human: HumanClone) -> None:
    _push_in_progress(
        human, [f"{FEATURE}/done/F0001-S0002-done.md", f"{FEATURE}/in-progress/F0001-S0003-on.md"]
    )
    items = _items(checkout)

    backlog = items.list_stories("backlog")
    done = items.list_stories("done")

    assert [(story.id, story.folder) for story in backlog] == [(WORK_ITEM, "backlog")]
    assert [(story.id, story.folder) for story in done] == [("F0001-S0002", "done")]


def test_a_story_with_a_remote_branch_is_read_from_its_head(
    remote: Path, checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, PATH, BRANCH_TEXT)

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.id == WORK_ITEM
    assert snapshot.path == PATH
    assert snapshot.folder == "in-progress"
    assert snapshot.branch == "work-item/F0001-S0001"
    assert snapshot.branch_commit == remote_commit(remote, BRANCH)
    assert snapshot.document == FrontmatterWorkItemReader().parse(BRANCH_TEXT)
    assert snapshot.document.state is not None
    assert snapshot.document.state.stage == "tests"
    assert snapshot.document.body == "# First story\n"


def test_a_pushed_branch_wins_over_a_stale_local_branch(
    tmp_path: Path, remote: Path, checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    _commit_local_branch(checkout, tmp_path / CHECKOUT, STALE_TEXT)
    human.push_file(BRANCH, PATH, BRANCH_TEXT)

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert [snapshot.branch_commit for snapshot in snapshots] == [remote_commit(remote, BRANCH)]
    assert snapshots[0].document == FrontmatterWorkItemReader().parse(BRANCH_TEXT)


def test_a_branch_only_in_the_checkout_is_not_read(
    tmp_path: Path, checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    _commit_local_branch(checkout, tmp_path / CHECKOUT, STALE_TEXT)

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert len(snapshots) == 1
    assert snapshots[0].branch_commit is None
    assert snapshots[0].document.state == initial_state("intake")


def _start_with_state_in_file(human: HumanClone) -> None:
    human.push_file("main", BACKLOG_PATH, SPECIFICATION_WITH_STATE)
    human.start(BACKLOG_PATH)


def test_a_started_story_without_a_branch_is_at_the_first_stage(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    _start_with_state_in_file(human)
    definition = pipeline_definition(boundaries)

    snapshots = _items(checkout).read(definition)

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.branch_commit is None
    assert snapshot.document.state == initial_state(definition.first_stage())
    state = snapshot.document.state
    assert state is not None
    assert state.stage == "intake"
    assert state.attempts == 0
    assert state.round == 0
    assert state.crashes == 0
    assert state.blocked is None


def test_a_started_story_without_a_branch_keeps_its_body_and_ignores_its_keys(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    _start_with_state_in_file(human)

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    document = snapshots[0].document
    assert document.body == SPECIFICATION_BODY
    assert sorted(document.ignored_keys) == ["attempts", "blocked", "round", "stage"]


def test_a_branch_merged_into_main_is_still_read_from_the_branch(
    remote: Path, checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, PATH, BRANCH_TEXT)
    human.merge(BRANCH, "merge")

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert [snapshot.path for snapshot in snapshots] == [PATH]
    assert snapshots[0].branch_commit == remote_commit(remote, BRANCH)
    assert snapshots[0].document.state is not None
    assert snapshots[0].document.state.stage == "tests"
    assert snapshots[0].document.state.attempts == 1


def test_a_story_missing_on_its_branch_is_a_format_error(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.push_file(BRANCH, "notes.txt", "Branched before the start.\n")
    human.start(BACKLOG_PATH)
    items = _items(checkout)

    with pytest.raises(WorkItemFormatError) as raised:
        items.read(pipeline_definition(boundaries))

    assert raised.value.path == PATH


def test_unreadable_front_matter_on_the_branch_is_a_format_error(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, PATH, UNREADABLE)
    items = _items(checkout)

    with pytest.raises(WorkItemFormatError) as raised:
        items.read(pipeline_definition(boundaries))

    assert raised.value.path == PATH


def test_unreadable_front_matter_on_main_without_a_branch_is_a_format_error(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.push_file("main", BACKLOG_PATH, UNREADABLE)
    human.start(BACKLOG_PATH)
    items = _items(checkout)

    with pytest.raises(WorkItemFormatError) as raised:
        items.read(pipeline_definition(boundaries))

    assert raised.value.path == PATH


def test_only_in_progress_stories_are_read(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    _push_in_progress(
        human, [f"{FEATURE}/done/F0001-S0002-done.md", f"{FEATURE}/in-progress/F0001-S0003-on.md"]
    )

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert [(snapshot.id, snapshot.folder) for snapshot in snapshots] == [
        ("F0001-S0003", "in-progress")
    ]


def test_snapshots_come_in_plain_id_order_and_one_per_story_file(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    _push_in_progress(
        human,
        [
            "factory/features/F0002-second/in-progress/F0002-S0001-a.md",
            "factory/features/F0001-beta/in-progress/F0001-S0002-b.md",
            f"{FEATURE}/in-progress/F0001-S0010-c.md",
            "factory/features/F0001-alpha/in-progress/F0001-S0002-a.md",
        ],
    )

    snapshots = _items(checkout).read(pipeline_definition(boundaries))

    assert [(snapshot.id, snapshot.path) for snapshot in snapshots] == [
        ("F0001-S0002", "factory/features/F0001-alpha/in-progress/F0001-S0002-a.md"),
        ("F0001-S0002", "factory/features/F0001-beta/in-progress/F0001-S0002-b.md"),
        ("F0001-S0010", f"{FEATURE}/in-progress/F0001-S0010-c.md"),
        ("F0002-S0001", "factory/features/F0002-second/in-progress/F0002-S0001-a.md"),
    ]


@pytest.mark.parametrize("folder", ["ongoing", "drafts"])
def test_ongoing_and_drafts_files_are_neither_listed_nor_read(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries, folder: str
) -> None:
    human.push_file("main", f"{FEATURE}/{folder}/F0001-S0003-x.md", "# Old layout\n")
    items = _items(checkout)

    listed = [
        story.path for lifecycle in LIFECYCLE_FOLDERS for story in items.list_stories(lifecycle)
    ]

    assert listed == [BACKLOG_PATH]
    assert items.read(pipeline_definition(boundaries)) == []
