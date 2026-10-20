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
from probe_support import ENVIRONMENT

HINT = (
    "the probe run ended died; run opencode run by hand as {user} to see why; "
    "the agent runs get no API key: log in once as {user} with the opencode build's own "
    "login, or put a key in the file FACTORY_API_LOGIN_FILE names"
)


@pytest.mark.parametrize(
    ("agent_user", "named"),
    [
        pytest.param(None, "the factory user", id="no-user"),
        pytest.param("agent", "agent", id="agent"),
    ],
)
def test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    *,
    agent_user: str | None,
    named: str,
) -> None:
    install_agents(agent_home, ["coder"])
    settings = probe_settings.model_copy(
        update={
            "agent_user": agent_user,
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

    assert detail == HINT.format(user=named)
