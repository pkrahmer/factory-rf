"""The preflight's probe runs the project's own coder and fails on a faulty one."""

import dataclasses
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import PROBE_BUDGET_USD, agent_run_probe_item
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.settings import InstanceSettings
from git_support import COLOURED_AGENT_FILE, PROJECT_CODER, install_agents
from human_clone import HumanClone
from probe_support import COMPLETED, ENVIRONMENT


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
    probe_settings: InstanceSettings,
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
    boundaries.git.checkout("main", start_point="origin/main")
    project = dataclasses.replace(
        boundaries,
        agent_definitions=ProjectAgentDefinitions(boundaries.git, boundaries.agent_definitions),
    )
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(project, probe_settings, ENVIRONMENT)

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
