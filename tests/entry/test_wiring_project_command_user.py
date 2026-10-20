"""The wiring runs every project command as the agent user, with the git folder sealed."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.claude_runtime import SUDO_EXECUTABLE
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.application.project_commands import RecordingProjectCommands
from factory.application.sealed_runs import SealedProjectCommands
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import (
    build_boundaries,
    leftovers_command,
    production_environment,
    project_command_environment,
)
from wiring_support import CREDENTIAL, every_tool

BASE = {"PATH": "/p", "HOME": "/home/factory", "LANG": "C.UTF-8"}
ADDED = {"PYTHONDONTWRITEBYTECODE": "1", "UV_LINK_MODE": "copy"}


def _no_tool(name: str) -> str | None:
    del name
    return None


def _held[T](outer: object, kind: type[T]) -> T:
    """Return the one object of `kind` that `outer` holds as an attribute."""
    [held] = [value for value in vars(outer).values() if isinstance(value, kind)]
    return held


@pytest.mark.parametrize(
    ("agent_user", "expected"),
    [
        pytest.param("agent", {**BASE, "HOME": "/home/agent", **ADDED}, id="agent-user"),
        pytest.param(None, {**BASE, **ADDED}, id="no-agent-user"),
    ],
)
def test_the_project_command_environment_is_the_agent_runs_without_bytecode_and_uv_copying(
    agent_user: str | None, expected: dict[str, str]
) -> None:
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        agent_home=Path("/home/agent/.claude"),
        agent_user=agent_user,
    )

    assert project_command_environment(settings, dict(BASE)) == expected


@pytest.mark.parametrize(
    ("agent_user", "end_leftovers", "which", "sudo", "leftovers"),
    [
        pytest.param("agent", True, every_tool, "/usr/bin/sudo", True, id="agent-user"),
        pytest.param("agent", False, every_tool, "/usr/bin/sudo", False, id="no-leftovers"),
        pytest.param("agent", True, _no_tool, SUDO_EXECUTABLE, True, id="no-sudo-found"),
        pytest.param(None, True, every_tool, None, True, id="no-agent-user"),
    ],
)
def test_the_built_project_commands_run_as_the_agent_user_inside_a_seal(
    local_settings: InstanceSettings,
    *,
    agent_user: str | None,
    end_leftovers: bool,
    which: Callable[[str], str | None],
    sudo: str | None,
    leftovers: bool,
) -> None:
    settings = local_settings.model_copy(update={"agent_user": agent_user})

    boundaries = build_boundaries(
        settings,
        CREDENTIAL,
        hosting=FakeHostingService(),
        which=which,
        end_leftovers=end_leftovers,
    )

    recording = boundaries.project_commands
    assert type(recording) is RecordingProjectCommands
    if sudo is None:
        make = _held(recording, MakeProjectCommands)
        assert type(make) is MakeProjectCommands
        assert make.user is None
        return
    sealed = _held(recording, SealedProjectCommands)
    assert type(sealed) is SealedProjectCommands
    make = _held(sealed, MakeProjectCommands)
    assert type(make) is MakeProjectCommands
    assert make.user == CommandUser(
        os_user="agent",
        sudo_executable=sudo,
        environment=project_command_environment(settings, production_environment()),
        leftovers=leftovers_command() if leftovers else None,
    )
