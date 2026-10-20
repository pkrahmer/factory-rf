"""The wiring's item `agent-environment` passes without `factory-guard` on the agent's `PATH`."""

from pathlib import Path

import pytest

from confine_support import write_script
from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from wiring_support import machine_item


@pytest.mark.parametrize("home_exists", [True, False], ids=["home", "missing-home"])
def test_the_wiring_s_agent_environment_needs_no_factory_guard(
    boundaries: Boundaries, tmp_path: Path, *, agent_home: Path, home_exists: bool
) -> None:
    agent_path = tmp_path / "agent-bin"
    agent_path.mkdir()
    write_script(agent_path / "factory-confine", "")
    home = tmp_path / "home"
    if home_exists:
        home.mkdir()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
    )
    environment = {"PATH": str(agent_path), "HOME": str(home)}

    item = machine_item(boundaries, settings, environment, "agent-environment")

    if home_exists:
        assert item == PreflightItem(name="agent-environment", passed=True)
    else:
        detail = f"the agent run's HOME {home} is no directory"
        assert item == PreflightItem(name="agent-environment", passed=False, detail=detail)
