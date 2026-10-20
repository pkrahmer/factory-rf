"""The preflight's wrapper items search the agent run's `PATH`, not the factory process's."""

from pathlib import Path

import pytest

from confine_support import write_script
from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from wiring_support import machine_item


@pytest.mark.parametrize(
    ("name", "command", "on_agent_path"),
    [
        pytest.param("confinement", "factory-confine", True, id="confinement-agent-path"),
        pytest.param("confinement", "factory-confine", False, id="confinement-own-path"),
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
    agent_path = tmp_path / "agent-bin"
    own_path = tmp_path / "own-bin"
    agent_path.mkdir()
    own_path.mkdir()
    write_script((agent_path if on_agent_path else own_path) / command, "")
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

    item = machine_item(boundaries, settings, environment, name)

    if on_agent_path:
        assert item == PreflightItem(name=name, passed=True)
    else:
        detail = f"{command} is not on the agent run's PATH {agent_path}"
        assert item == PreflightItem(name=name, passed=False, detail=detail)
