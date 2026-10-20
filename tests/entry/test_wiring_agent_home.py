"""The wiring builds the agent's home from the settings and hands it to runs and commands."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters import claude_runtime, opencode_runtime
from factory.adapters.agent_home import SudoAgentHome
from factory.adapters.claude_runtime import SUDO_EXECUTABLE
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.project_commands import RecordingProjectCommands
from factory.application.sealed_runs import SealedProjectCommands
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import (
    UV_CACHE_FOLDER,
    agent_home_of,
    build_boundaries,
    fresh_home_command,
)
from wiring_support import CREDENTIAL

FOUND_SUDO = "/opt/found/sudo"
SETTINGS = InstanceSettings(
    repository_url="/srv/project.git",
    instance="factory-1",
    agent_user="agent",
    agent_home=Path("/home/agent/.claude"),
    claude_login_file=Path("/home/agent/.claude-token"),
    api_login_file=Path("/home/agent/.anthropic-api-key"),
    opencode_folders=[".config/sso"],
)
STATE_FILES = [".claude/.credentials.json", ".local/share/opencode/auth.json"]


def _found(name: str) -> str | None:
    return f"/opt/found/{name}"


def _no_tool(name: str) -> str | None:
    del name
    return None


def _held[T](outer: object, kind: type[T]) -> T:
    """Return the one object of `kind` that `outer` holds as an attribute."""
    [held] = [value for value in vars(outer).values() if isinstance(value, kind)]
    return held


def test_each_runtime_names_the_login_it_keeps_in_the_home() -> None:
    assert claude_runtime.LOGIN_STATE_FILE == ".claude/.credentials.json"
    assert opencode_runtime.LOGIN_STATE_FILE == ".local/share/opencode/auth.json"


def test_the_fresh_home_program_runs_with_this_interpreter_isolated_and_uv_s_cache_is_named() -> (
    None
):
    assert fresh_home_command() == [sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]
    assert UV_CACHE_FOLDER == ".cache/uv"


@pytest.mark.parametrize(
    ("update", "kept"),
    [
        pytest.param(
            {},
            [".claude-token", ".anthropic-api-key", *STATE_FILES, ".cache/uv", ".config/sso"],
            id="claude",
        ),
        pytest.param(
            {"api_login_file": Path("/run/key")},
            [".claude-token", *STATE_FILES, ".cache/uv", ".config/sso"],
            id="api-login-outside-the-home",
        ),
        pytest.param(
            {"agent_runtime": "opencode"},
            [".claude-token", ".anthropic-api-key", *STATE_FILES, ".cache/uv", ".config/sso"],
            id="opencode",
        ),
        pytest.param({"agent_user": None}, None, id="no-agent-user"),
    ],
)
def test_the_agent_home_of_the_settings_keeps_the_logins_the_uv_cache_and_the_folders(
    update: dict[str, object], kept: list[str] | None
) -> None:
    settings = SETTINGS.model_copy(update=update)

    home = agent_home_of(settings, "/usr/bin/sudo")

    if kept is None:
        assert home is None
        return
    assert type(home) is SudoAgentHome
    assert home.home == Path("/home/agent")
    assert home.os_user == "agent"
    assert home.program == fresh_home_command()
    assert home.kept == kept


@pytest.mark.parametrize(
    ("agent_user", "which", "sudo"),
    [
        pytest.param("agent", _found, FOUND_SUDO, id="sudo-found"),
        pytest.param("agent", _no_tool, SUDO_EXECUTABLE, id="no-sudo-found"),
        pytest.param(None, _found, None, id="no-agent-user"),
    ],
)
def test_the_built_boundaries_hold_one_agent_home_shared_with_the_project_commands(
    local_settings: InstanceSettings,
    *,
    agent_user: str | None,
    which: Callable[[str], str | None],
    sudo: str | None,
) -> None:
    settings = local_settings.model_copy(update={"agent_user": agent_user})

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService(), which=which)

    if sudo is None:
        assert boundaries.agent_home is None
        return
    built = boundaries.agent_home
    assert type(built) is SudoAgentHome
    expected = agent_home_of(settings, sudo)
    assert expected is not None
    assert (built.home, built.kept, built.os_user, built.program) == (
        expected.home,
        expected.kept,
        expected.os_user,
        expected.program,
    )
    # The executable is no property of the interface; the object holds it as given.
    assert sudo in vars(built).values()
    recording = boundaries.project_commands
    assert type(recording) is RecordingProjectCommands
    sealed = _held(recording, SealedProjectCommands)
    assert _held(sealed, SudoAgentHome) is built
