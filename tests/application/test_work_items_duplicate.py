"""A second in-progress file of one id is read from main, never from the first file's branch."""

import pytest

from factory.adapters.git_cli import GitCli
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.boundaries import Boundaries
from factory.application.work_items import RemoteWorkItems
from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import branch_name
from factory.domain.work_item import initial_state
from git_support import PIPELINE_YAML
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
FIRST_PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
SECOND_PATH = f"{FEATURE}/in-progress/F0001-S0001-second.md"
BRANCH_TEXT = "---\nstage: tests\nattempts: 1\n---\n# First story\n"
SECOND_TEXT = "---\nstage: review\n---\n# Second story\n\n## Description\n\nSame id.\n"


def _items(checkout: GitCli) -> RemoteWorkItems:
    checkout.fetch()
    return RemoteWorkItems(checkout, FrontmatterWorkItemReader())


def test_a_second_file_of_one_id_is_read_from_main_as_a_started_story(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, FIRST_PATH, BRANCH_TEXT)
    human.push_file("main", SECOND_PATH, SECOND_TEXT)
    items = _items(checkout)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)

    snapshots = items.read(definition)

    assert [snapshot.path for snapshot in snapshots] == [FIRST_PATH, SECOND_PATH]
    assert snapshots[0].document == FrontmatterWorkItemReader().parse(BRANCH_TEXT)
    second = snapshots[1].document
    assert second.state == initial_state(definition.first_stage())
    assert second.body == FrontmatterWorkItemReader().parse_specification(SECOND_TEXT).body


def test_the_only_file_of_an_id_missing_on_its_branch_is_still_a_format_error(
    checkout: GitCli, human: HumanClone, boundaries: Boundaries
) -> None:
    human.push_file(BRANCH, "notes.txt", "Branched before the start.\n")
    human.start(BACKLOG_PATH)
    items = _items(checkout)

    with pytest.raises(WorkItemFormatError) as raised:
        items.read(boundaries.pipeline_reader.parse(PIPELINE_YAML))

    assert raised.value.path == FIRST_PATH
