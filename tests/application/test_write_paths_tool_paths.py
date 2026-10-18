"""The guard settings carry the definition's tool paths as they were at the stage-start commit."""

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.write_paths import WritePathService
from git_support import PIPELINE_YAML
from human_clone import HumanClone
from write_path_support import push_definition, stage_start

PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
TOOL_PATHS_YAML = PIPELINE_YAML + 'tool_paths: [".venv/*", "~/.cache/*"]\n'


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        pytest.param(TOOL_PATHS_YAML, None, [".venv/*", "~/.cache/*"], id="at-the-commit"),
        pytest.param(None, None, [], id="without-the-key"),
        pytest.param(None, TOOL_PATHS_YAML, [], id="pushed-after-the-commit"),
    ],
)
def test_at_returns_the_tool_paths_of_the_definition_at_the_stage_start_commit(
    boundaries: Boundaries,
    checkout: GitCli,
    human: HumanClone,
    *,
    before: str | None,
    after: str | None,
    expected: list[str],
) -> None:
    if before is not None:
        push_definition(human, checkout, before)
    start = stage_start(checkout, "tests")
    if after is not None:
        push_definition(human, checkout, after)

    settings = WritePathService(boundaries).at(start, PATH)

    assert settings.tool_paths == expected
    assert settings.write_paths == ["tests/*"]
