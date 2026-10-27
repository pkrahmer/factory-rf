"""The preflight writes the detail of each passed machine item to the factory log."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks, Preflight
from factory.application.stops import StopService
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from human_clone import HumanClone
from log_support import log_lines
from preflight_support import IMAGE, MAKEFILE, ROLES, TOOLS, RecordingWhich

DETAIL = "the agent runs log in with the API key from /home/agent/.anthropic-api-key"
LINE = f"preflight: agent-run-probe: {DETAIL}"


@pytest.mark.parametrize("runs", [pytest.param(1, id="first-run"), pytest.param(2, id="stamped")])
def test_a_passed_machine_item_s_detail_is_logged_once_per_image(
    tmp_path: Path,
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    human: HumanClone,
    agent_home: Path,
    runs: int,
) -> None:
    install_agents(agent_home, ROLES)
    human.push_file("main", "Makefile", MAKEFILE)
    checkout.fetch()
    settings = InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_home": agent_home,
            "pinned_agent_version": "fake",
        }
    )
    extra = [
        lambda: PreflightItem(name="agent-run-probe", passed=True, detail=DETAIL),
        lambda: PreflightItem(name="quiet-item", passed=True),
    ]
    checks = MachineChecks(boundaries, settings, RecordingWhich(TOOLS), extra)
    stamps = JsonPreflightStampFile(tmp_path / "state" / "preflight-stamp.json")

    for _ in range(runs):
        assert Preflight(boundaries, checks, stamps, StopService(boundaries), IMAGE).run() is None

    lines = log_lines(tmp_path)
    assert len([line for line in lines if line.endswith(LINE)]) == 1
    assert not any("preflight: quiet-item" in line for line in lines)
