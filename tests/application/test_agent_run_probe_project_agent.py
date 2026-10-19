"""The preflight's probe runs the project's own coder and fails on a faulty one."""

import dataclasses
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import PROBE_BUDGET_USD, agent_run_probe_item
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from git_support import AGENT_FILE, COLOURED_AGENT_FILE, install_agents
from human_clone import HumanClone

ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": "/home/agent", "LANG": "C.UTF-8"}
COMPLETED = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)
PROJECT_CODER = AGENT_FILE.replace("Do the work.", "The project's coder.")


@pytest.fixture
def settings(agent_home: Path, tmp_path: Path) -> InstanceSettings:
    """Return settings whose agents run as the user `agent`, the state in `tmp_path`."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        agent_user="agent",
    )


@pytest.mark.parametrize(
    ("text", "passed", "instructions", "detail"),
    [
        pytest.param(PROJECT_CODER, True, "The project's coder.", None, id="project-coder"),
        pytest.param(
            COLOURED_AGENT_FILE,
            False,
            None,
            "agent coder: factory/agents/coder.md at origin/main: "
            "key not applied by the agent runtime: colour",
            id="faulty-project-coder",
        ),
    ],
)
def test_the_probe_runs_the_project_coder(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    agent_home: Path,
    human: HumanClone,
    agent_runtime: FakeAgentRuntime,
    text: str,
    passed: bool,
    instructions: str | None,
    detail: str | None,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    human.push_file("main", "factory/agents/coder.md", text)
    boundaries.git.fetch()
    project = dataclasses.replace(
        boundaries,
        agent_definitions=ProjectAgentDefinitions(boundaries.git, boundaries.agent_definitions),
    )
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(project, settings, ENVIRONMENT)

    assert item.passed is passed
    requests = agent_runtime.requests()
    if instructions is None:
        assert requests == []
        assert item.detail == detail
    else:
        [request] = requests
        assert request.agent.name == "coder"
        assert request.agent.instructions == instructions
        assert request.agent.budget_usd == PROBE_BUDGET_USD
