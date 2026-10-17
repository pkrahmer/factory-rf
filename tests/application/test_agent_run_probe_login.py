"""The probe of the agent run names the login file when the run does not complete."""

import dataclasses
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.domain.agent_runs import AgentRunResult, EndReason
from factory.domain.settings import InstanceSettings
from git_support import install_agents

ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": "/home/agent", "LANG": "C.UTF-8"}
LOGIN_FILE = Path("/home/agent/.claude-token")
HINT = (
    "; the agent's login token is read from /home/agent/.claude-token: "
    "make it with claude setup-token if it is missing, empty or expired"
)
FAILED_REASONS: list[EndReason] = ["died", "no_result", "time_limit", "budget"]
USERS = [("agent", "agent"), (None, "the factory user")]


@pytest.fixture
def settings(agent_home: Path, tmp_path: Path) -> InstanceSettings:
    """Return settings whose state lies in `tmp_path`, with the test's agent home."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        agent_user="agent",
    )


@pytest.fixture
def coder(agent_home: Path) -> None:
    """Install the agent `coder`, among others, into the test's agent home."""
    install_agents(agent_home, ["intake", "coder", "reviewer"])


def _failed_detail(reason: EndReason, named: str, login_file: Path | None) -> str:
    present = f"the probe run ended {reason}; run claude -p by hand as {named} to see why"
    return present + (HINT if login_file is not None else "")


_ROWS = [
    pytest.param(
        reason,
        agent_user,
        login_file,
        False,
        _failed_detail(reason, named, login_file),
        id=f"{reason}-{agent_user or 'no-user'}-{'login-file' if login_file else 'no-login-file'}",
    )
    for reason in FAILED_REASONS
    for agent_user, named in USERS
    for login_file in (LOGIN_FILE, None)
] + [pytest.param("completed", "agent", LOGIN_FILE, True, "", id="completed-login-file")]


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(("reason", "agent_user", "login_file", "passed", "detail"), _ROWS)
def test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set(
    boundaries: Boundaries,
    settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    reason: EndReason,
    agent_user: str | None,
    login_file: Path | None,
    passed: bool,
    detail: str,
) -> None:
    result = AgentRunResult(end_reason=reason, duration=timedelta(seconds=5))
    if reason == "completed":
        result = result.model_copy(update={"decision": "question", "entry": "probe"})
    agent_runtime.queue(ScriptedRun(result=result))
    probed = settings.model_copy(update={"agent_user": agent_user, "claude_login_file": login_file})

    item = agent_run_probe_item(boundaries, probed, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed == passed
    assert item.detail == detail


@pytest.mark.usefixtures("coder")
def test_a_login_file_the_runtime_cannot_read_fails_the_probe_with_the_runtime_s_message(
    boundaries: Boundaries, settings: InstanceSettings, tmp_path: Path
) -> None:
    folder = tmp_path / "login-folder"
    folder.mkdir()
    runtime = ClaudeCodeRuntime(
        str(tmp_path / "bin" / "claude"), tmp_path / "runtime-state", login_file=folder
    )
    claude = dataclasses.replace(boundaries, agent_runtime=runtime)
    probed = settings.model_copy(update={"agent_user": None, "claude_login_file": folder})

    item = agent_run_probe_item(claude, probed, {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)})

    assert not item.passed
    assert "cannot read the agent's login file" in item.detail
    assert str(folder) in item.detail
    assert "claude setup-token" not in item.detail
