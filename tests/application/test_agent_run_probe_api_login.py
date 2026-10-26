"""The probe of the agent run names the login its run was handed."""

from pathlib import Path

import pytest

from application.test_agent_run_probe_login import HINT, LOGIN_FILE
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import EndReason, Login
from factory.domain.settings import AgentRuntimeName, InstanceSettings
from git_support import install_agents
from probe_support import ENVIRONMENT, opencode_died, opencode_sso_hint, probe_result

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
    agent_runtime.queue(ScriptedRun(result=probe_result(reason, login)))

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed == passed
    assert item.detail == detail


def _on_runtime(settings: InstanceSettings, runtime: AgentRuntimeName) -> InstanceSettings:
    if runtime == "claude":
        return settings
    return settings.model_copy(
        update={"agent_runtime": runtime, "pinned_opencode_version": "1.19.3"}
    )


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(
    ("runtime", "login", "detail"),
    [
        pytest.param(
            "opencode",
            "none",
            opencode_died("the factory user") + opencode_sso_hint(),
            id="opencode-none",
        ),
        pytest.param("claude", "api_key", DIED + API_HINT, id="claude-api-key"),
        pytest.param("claude", "subscription", DIED + HINT, id="claude-subscription"),
    ],
)
def test_a_died_probe_hints_only_at_a_login_its_runtime_can_use(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    runtime: AgentRuntimeName,
    login: Login,
    detail: str,
) -> None:
    agent_runtime.queue(ScriptedRun(result=probe_result("died", login)))

    item = agent_run_probe_item(boundaries, _on_runtime(settings, runtime), ENVIRONMENT)

    assert not item.passed
    assert item.detail == detail
    assert "own login" not in item.detail


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(
    ("runtime", "detail"),
    [
        pytest.param("opencode", "the agent runs get no login from a file", id="opencode"),
        pytest.param(
            "claude",
            "the agent runs get no login from a file; the runtime uses the login kept in its home",
            id="claude",
        ),
    ],
)
def test_a_completed_probe_without_a_login_file_names_the_agents_home_only_under_claude(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    runtime: AgentRuntimeName,
    detail: str,
) -> None:
    agent_runtime.queue(ScriptedRun(result=probe_result("completed", "none")))

    item = agent_run_probe_item(boundaries, _on_runtime(settings, runtime), ENVIRONMENT)

    assert item.passed
    assert item.detail == detail
