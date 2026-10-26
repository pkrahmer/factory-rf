"""A failed probe under opencode names opencode's own command and the login it lacks."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import AgentRunResult, EndReason, Login
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from probe_support import ENVIRONMENT, opencode_died, opencode_sso_hint

DIED = opencode_died("the factory user")
API_HINT = (
    "; the agent's API key is read from /home/agent/.anthropic-api-key: "
    "check that it is valid and that its account has credit"
)
SSO_HINT = opencode_sso_hint()


@pytest.fixture
def settings(agent_home: Path, tmp_path: Path) -> InstanceSettings:
    """Return opencode settings with both login files and an agent user."""
    install_agents(agent_home, ["coder"])
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        claude_login_file=Path("/home/agent/.claude-token"),
        api_login_file=Path("/home/agent/.anthropic-api-key"),
        agent_runtime="opencode",
        pinned_opencode_version="1.19.3",
    )


@pytest.mark.parametrize(
    ("login", "detail"),
    [
        pytest.param(None, DIED, id="no-login"),
        pytest.param("api_key", DIED + API_HINT, id="api-key"),
        pytest.param("none", DIED + SSO_HINT, id="none"),
    ],
)
def test_a_died_probe_under_opencode_names_opencode_run_and_the_login_hint(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    login: Login | None,
    detail: str,
) -> None:
    agent_runtime.queue(
        ScriptedRun(
            result=AgentRunResult(end_reason="died", duration=timedelta(seconds=5), login=login)
        )
    )

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert item.detail == detail
    assert "own login" not in item.detail


@pytest.mark.parametrize(
    ("reason", "passed", "detail"),
    [
        pytest.param(
            "completed",
            True,
            "the agent runs log in with the API key from /home/agent/.anthropic-api-key",
            id="completed",
        ),
        pytest.param("died", False, DIED + API_HINT, id="died"),
    ],
)
def test_a_probe_under_opencode_with_the_api_key_names_the_api_login_file(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    reason: EndReason,
    passed: bool,
    detail: str,
) -> None:
    duration = timedelta(seconds=5)
    result = (
        AgentRunResult(
            end_reason=reason,
            duration=duration,
            decision="question",
            entry="probe",
            login="api_key",
        )
        if reason == "completed"
        else AgentRunResult(end_reason=reason, duration=duration, login="api_key")
    )
    agent_runtime.queue(ScriptedRun(result=result))

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert item.passed == passed
    assert item.detail == detail
