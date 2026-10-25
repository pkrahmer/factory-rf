"""The agent-run probe passes a run that leaves a git repository in the work tree."""

from pathlib import Path

from agent_run_support import COMPLETED
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from stage_run_support import ENVIRONMENT


def test_a_probe_run_that_leaves_a_nested_repository_passes(
    boundaries: Boundaries,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
    )
    agent_runtime.queue(
        ScriptedRun(writes={"sub/.git/HEAD": "ref: refs/heads/main\n"}, result=COMPLETED)
    )

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed
    assert item.detail == ""
