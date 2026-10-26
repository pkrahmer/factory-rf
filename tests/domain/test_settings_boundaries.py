"""The settings the instance's boundaries need: agent home, agent executable and token file."""

from pathlib import Path

import pytest

from factory.domain.settings import read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"FACTORY_CLAUDE_HOME": "/srv/agents"}, Path("/srv/agents")),
        ({"FACTORY_CLAUDE_HOME": "/srv/agents", "HOME": "/home/ann"}, Path("/srv/agents")),
    ],
)
def test_agent_home_comes_from_its_variable_then_home_then_the_default(
    variables: dict[str, str], expected: Path
) -> None:
    assert read_settings({**BASE, **variables}).agent_home == expected


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"FACTORY_CLAUDE": "/opt/claude/bin/claude"}, "/opt/claude/bin/claude"),
        ({}, "claude"),
        ({"FACTORY_CLAUDE": ""}, "claude"),
        ({"FACTORY_CLAUDE": "   "}, "claude"),
    ],
)
def test_claude_executable_comes_from_its_variable_or_is_claude(
    variables: dict[str, str], expected: str
) -> None:
    assert read_settings({**BASE, **variables}).claude_executable == expected


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"FACTORY_TOKEN_FILE": "/run/secrets/hosting"}, Path("/run/secrets/hosting")),
        ({}, None),
        ({"FACTORY_TOKEN_FILE": ""}, None),
        ({"FACTORY_TOKEN_FILE": "   "}, None),
    ],
)
def test_token_file_comes_from_its_variable_or_is_none(
    variables: dict[str, str], expected: Path | None
) -> None:
    assert read_settings({**BASE, **variables}).token_file == expected
