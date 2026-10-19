"""The agent runtime's version the image pins, read from the environment."""

import pytest

from factory.domain.settings import read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"FACTORY_CLAUDE_VERSION": "2.1.289"}, "2.1.289"),
        ({}, None),
        ({"FACTORY_CLAUDE_VERSION": ""}, None),
        ({"FACTORY_CLAUDE_VERSION": "   "}, None),
    ],
    ids=["set", "missing", "empty", "blank"],
)
def test_the_pinned_version_comes_from_its_variable_or_is_none(
    variables: dict[str, str], expected: str | None
) -> None:
    assert read_settings({**BASE, **variables}).pinned_agent_version == expected
