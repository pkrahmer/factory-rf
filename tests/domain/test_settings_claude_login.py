"""The setting that names the file holding the agent's login token."""

from pathlib import Path

import pytest

from factory.domain.settings import CLAUDE_LOGIN_FILE_VARIABLE, read_settings

BASE = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("/home/agent/.claude-token", Path("/home/agent/.claude-token"), id="path"),
        pytest.param(None, None, id="unset"),
        pytest.param("", None, id="empty"),
        pytest.param("   ", None, id="spaces"),
    ],
)
def test_the_login_file_setting_is_a_path_or_none_when_blank(
    value: str | None, expected: Path | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ["FACTORY_CLAUDE_LOGIN_FILE"] = value

    settings = read_settings(environ)

    assert CLAUDE_LOGIN_FILE_VARIABLE == "FACTORY_CLAUDE_LOGIN_FILE"
    assert settings.claude_login_file == expected
