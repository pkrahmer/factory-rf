"""The setting that names the file holding the agent's API login."""

from pathlib import Path

import pytest

from factory.domain.settings import API_LOGIN_FILE_VARIABLE, read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "/home/agent/.anthropic-api-key", Path("/home/agent/.anthropic-api-key"), id="path"
        ),
        pytest.param(None, None, id="unset"),
        pytest.param("", None, id="empty"),
        pytest.param("   ", None, id="spaces"),
    ],
)
def test_the_api_login_file_setting_is_a_path_or_none_when_blank(
    value: str | None, expected: Path | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[API_LOGIN_FILE_VARIABLE] = value

    settings = read_settings(environ)

    assert API_LOGIN_FILE_VARIABLE == "FACTORY_API_LOGIN_FILE"
    assert settings.api_login_file == expected
