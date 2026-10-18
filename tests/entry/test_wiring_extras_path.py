"""The preflight's wrapper items search the agent run's `PATH`, not the factory process's."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from wiring_support import every_tool


def _bin_with(folder: Path, command: str | None) -> Path:
    folder.mkdir()
    if command is not None:
        executable = folder / command
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
    return folder


def _item(
    boundaries: Boundaries, settings: InstanceSettings, environment: dict[str, str], name: str
) -> PreflightItem:
    # The items run in order up to the one asked for, so the agent run probe never starts.
    for check in machine_extras(boundaries, settings, every_tool, environment):
        item = check()
        if item.name == name:
            return item
    raise AssertionError(name)


@pytest.mark.parametrize(
    ("name", "command", "on_agent_path"),
    [
        pytest.param("confinement", "factory-confine", True, id="confinement-agent-path"),
        pytest.param("confinement", "factory-confine", False, id="confinement-own-path"),
        pytest.param("agent-environment", "factory-guard", True, id="environment-agent-path"),
        pytest.param("agent-environment", "factory-guard", False, id="environment-own-path"),
    ],
)
def test_the_wrapper_items_search_the_agent_run_s_path_not_the_process_s(
    boundaries: Boundaries,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_home: Path,
    name: str,
    command: str,
    on_agent_path: bool,
) -> None:
    agent_path = _bin_with(tmp_path / "agent-bin", command if on_agent_path else None)
    own_path = _bin_with(tmp_path / "own-bin", None if on_agent_path else command)
    monkeypatch.setenv("PATH", str(own_path))
    home = tmp_path / "home"
    home.mkdir()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
    )
    environment = {"PATH": str(agent_path), "HOME": str(home)}

    item = _item(boundaries, settings, environment, name)

    if on_agent_path:
        assert item == PreflightItem(name=name, passed=True)
    else:
        detail = f"{command} is not on the agent run's PATH {agent_path}"
        assert item == PreflightItem(name=name, passed=False, detail=detail)
