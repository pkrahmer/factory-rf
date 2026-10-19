"""The settings that choose the agent runtime of an instance and its opencode build."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import (
    AGENT_RUNTIME_VARIABLE,
    OPENCODE_EXECUTABLE_VARIABLE,
    OPENCODE_VERSION_VARIABLE,
    read_settings,
)

BASE = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, "claude", id="unset"),
        pytest.param("", "claude", id="empty"),
        pytest.param(" ", "claude", id="blank"),
        pytest.param("claude", "claude", id="claude"),
        pytest.param("opencode", "opencode", id="opencode"),
        pytest.param(" opencode ", "opencode", id="opencode-spaces"),
        pytest.param("Opencode", None, id="capital"),
        pytest.param("claude-code", None, id="claude-code"),
        pytest.param("both", None, id="both"),
    ],
)
def test_the_agent_runtime_is_claude_by_default_or_the_one_named(
    value: str | None, expected: str | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[AGENT_RUNTIME_VARIABLE] = value

    if expected is None:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert raised.value.variable == "FACTORY_AGENT_RUNTIME"
        assert "is neither claude nor opencode" in raised.value.fault
        return
    assert read_settings(environ).agent_runtime == expected


@pytest.mark.parametrize(
    ("executable", "version", "expected_executable", "expected_version"),
    [
        pytest.param(None, None, "opencode", None, id="unset"),
        pytest.param(" ", " ", "opencode", None, id="blank"),
        pytest.param("/opt/bin/opencode", "1.19.3", "/opt/bin/opencode", "1.19.3", id="set"),
    ],
)
def test_the_opencode_executable_and_pin_default_to_opencode_and_none(
    executable: str | None,
    version: str | None,
    expected_executable: str,
    expected_version: str | None,
) -> None:
    environ = dict(BASE)
    if executable is not None:
        environ[OPENCODE_EXECUTABLE_VARIABLE] = executable
    if version is not None:
        environ[OPENCODE_VERSION_VARIABLE] = version

    settings = read_settings(environ)

    assert (OPENCODE_EXECUTABLE_VARIABLE, OPENCODE_VERSION_VARIABLE) == (
        "FACTORY_OPENCODE",
        "FACTORY_OPENCODE_VERSION",
    )
    assert settings.opencode_executable == expected_executable
    assert settings.pinned_opencode_version == expected_version
