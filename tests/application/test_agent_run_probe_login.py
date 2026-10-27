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
from probe_login_support import HINT, LOGIN_FILE
from probe_support import ENVIRONMENT

FAILED_REASONS: list[EndReason] = ["died", "no_result", "time_limit", "budget"]
FACTORY_USER = "the factory user"


@pytest.fixture
def coder(agent_home: Path) -> None:
    """Install the agent `coder`, among others, into the test's agent home."""
    install_agents(agent_home, ["intake", "coder", "reviewer"])


def _failed_detail(reason: EndReason, named: str, login_file: Path | None) -> str:
    present = f"the probe run ended {reason}; run claude -p by hand as {named} to see why"
    return present + (HINT if login_file is not None else "")


def _probe_result(reason: EndReason) -> AgentRunResult:
    duration = timedelta(seconds=5)
    if reason == "completed":
        return AgentRunResult(
            end_reason=reason, duration=duration, decision="question", entry="probe"
        )
    return AgentRunResult(end_reason=reason, duration=duration)


_ROWS = [
    pytest.param(
        reason,
        login_file,
        False,
        _failed_detail(reason, FACTORY_USER, login_file),
        id=f"{reason}-no-user-{'login-file' if login_file else 'no-login-file'}",
    )
    for reason in FAILED_REASONS
    for login_file in (LOGIN_FILE, None)
] + [pytest.param("completed", LOGIN_FILE, True, "", id="completed-login-file")]


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(("reason", "login_file", "passed", "detail"), _ROWS)
def test_a_probe_that_does_not_complete_names_the_login_file_when_one_is_set(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    reason: EndReason,
    login_file: Path | None,
    passed: bool,
    detail: str,
) -> None:
    agent_runtime.queue(ScriptedRun(result=_probe_result(reason)))
    probed = probe_settings.model_copy(update={"claude_login_file": login_file})

    item = agent_run_probe_item(boundaries, probed, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed == passed
    assert item.detail == detail


@pytest.mark.usefixtures("coder")
def test_a_login_file_the_runtime_cannot_read_fails_the_probe_with_the_runtime_s_message(
    boundaries: Boundaries, probe_settings: InstanceSettings, tmp_path: Path
) -> None:
    folder = tmp_path / "login-folder"
    folder.mkdir()
    runtime = ClaudeCodeRuntime(
        str(tmp_path / "bin" / "claude"), tmp_path / "runtime-state", login_file=folder
    )
    claude = dataclasses.replace(boundaries, agent_runtime=runtime)
    probed = probe_settings.model_copy(update={"claude_login_file": folder})

    item = agent_run_probe_item(claude, probed, {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)})

    assert not item.passed
    assert "cannot read the agent's login file" in item.detail
    assert str(folder) in item.detail
    assert "claude setup-token" not in item.detail
