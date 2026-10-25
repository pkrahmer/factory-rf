"""The probe run does not wait out a provider limit."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from agent_run_support import COMPLETED
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from stage_run_support import ENVIRONMENT


def test_the_probe_does_not_wait_out_a_provider_limit(
    boundaries: Boundaries,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ["coder"])
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
    )
    limited = AgentRunResult(
        end_reason="provider_limit", duration=timedelta(seconds=5), session="ses_a"
    )
    agent_runtime.queue(ScriptedRun(result=limited))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    waiter = ManualWaiter(clock)
    patient = replace(boundaries, waiter=waiter, settings=settings)

    item = agent_run_probe_item(patient, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert item.detail is not None
    assert item.detail.startswith("the probe run ended provider_limit; ")
    assert len(agent_runtime.requests()) == 1
    assert waiter.waits == []
