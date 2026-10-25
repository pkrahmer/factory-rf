"""The probe of the agent run names the login its run was handed."""

from datetime import timedelta
from pathlib import Path

import pytest

from application.test_agent_run_probe_login import HINT, LOGIN_FILE
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import AgentRunResult, EndReason, Login
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from probe_support import ENVIRONMENT

API_LOGIN_FILE = Path("/home/agent/.anthropic-api-key")
API_HINT = (
    "; the agent's API key is read from /home/agent/.anthropic-api-key: "
    "check that it is valid and that its account has credit"
)
DIED = "the probe run ended died; run claude -p by hand as the factory user to see why"


@pytest.fixture
def settings(agent_home: Path, tmp_path: Path) -> InstanceSettings:
    """Return settings with both login files, whose state lies in `tmp_path`."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        claude_login_file=LOGIN_FILE,
        api_login_file=API_LOGIN_FILE,
    )


@pytest.fixture
def coder(agent_home: Path) -> None:
    """Install the agent `coder`, among others, into the test's agent home."""
    install_agents(agent_home, ["intake", "coder", "reviewer"])


def _probe_result(reason: EndReason, login: Login | None) -> AgentRunResult:
    duration = timedelta(seconds=5)
    if reason == "completed":
        return AgentRunResult(
            end_reason=reason, duration=duration, decision="question", entry="probe", login=login
        )
    return AgentRunResult(end_reason=reason, duration=duration, login=login)


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(
    ("reason", "login", "passed", "detail"),
    [
        pytest.param(
            "completed",
            "api_key",
            True,
            "the agent runs log in with the API key from /home/agent/.anthropic-api-key",
            id="completed-api-key",
        ),
        pytest.param(
            "completed",
            "subscription",
            True,
            "the agent runs log in with the subscription token from /home/agent/.claude-token",
            id="completed-subscription",
        ),
        pytest.param(
            "completed",
            "none",
            True,
            "the agent runs get no login from a file; the runtime uses the login kept in its home",
            id="completed-none",
        ),
        pytest.param("completed", None, True, "", id="completed-no-login"),
        pytest.param("died", "api_key", False, DIED + API_HINT, id="died-api-key"),
        pytest.param("died", "subscription", False, DIED + HINT, id="died-subscription"),
    ],
)
def test_the_probe_detail_names_the_login_its_run_was_handed(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    reason: EndReason,
    login: Login | None,
    passed: bool,
    detail: str,
) -> None:
    agent_runtime.queue(ScriptedRun(result=_probe_result(reason, login)))

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed == passed
    assert item.detail == detail
