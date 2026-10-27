"""The opencode login hint names the agent's user, or the factory user when none is set."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from probe_support import ENVIRONMENT, opencode_died, opencode_sso_hint


@pytest.mark.parametrize(
    "named",
    [
        pytest.param("the factory user", id="no-user"),
    ],
)
def test_the_opencode_login_hint_names_the_factory_user(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    *,
    named: str,
) -> None:
    install_agents(agent_home, ["coder"])
    settings = probe_settings.model_copy(
        update={
            "agent_runtime": "opencode",
            "pinned_opencode_version": "1.19.3",
        }
    )
    agent_runtime.queue(
        ScriptedRun(
            result=AgentRunResult(end_reason="died", duration=timedelta(seconds=5), login="none")
        )
    )

    detail = agent_run_probe_item(boundaries, settings, ENVIRONMENT).detail

    assert detail == opencode_died(named) + opencode_sso_hint()
