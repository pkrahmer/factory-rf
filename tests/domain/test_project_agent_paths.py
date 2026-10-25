"""The project's agent files: their path and their place among the protected paths."""

from pathlib import Path

import pytest

from factory.domain.agent_runs import WritePathSettings
from factory.domain.paths import PROJECT_AGENTS_DIRECTORY, project_agent_file
from factory.domain.write_paths import PROTECTED_PATHS, matches_any, refusal


def test_the_project_agent_file_lies_in_the_project_agents_directory() -> None:
    assert PROJECT_AGENTS_DIRECTORY == "factory/agents"
    assert project_agent_file("coder") == "factory/agents/coder.md"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("factory/agents/coder.md", True),
        ("factory/agents/sub/notes.md", True),
        ("factory/agentsx/coder.md", False),
        ("docs/factory/agents/coder.md", False),
        ("factory/features/F0001-x/agents/coder.md", False),
    ],
)
def test_the_project_agents_folder_is_protected(path: str, expected: bool) -> None:
    assert matches_any(path, PROTECTED_PATHS) is expected


def test_a_write_to_a_project_agent_file_is_refused_as_the_humans() -> None:
    guard = WritePathSettings(
        root=Path("/work"), write_paths=["*"], protected_paths=list(PROTECTED_PATHS)
    )

    assert refusal("factory/agents/coder.md", guard) == (
        "factory/agents/coder.md is owned by the human; a change there is a question."
    )
