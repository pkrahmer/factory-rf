"""The preflight item `agent-run-probe`: one agent run made exactly as a stage makes it."""

import dataclasses
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.preflight import (
    PROBE_PROMPT,
    MachineChecks,
    Preflight,
    agent_run_probe_item,
)
from factory.application.stops import StopService
from factory.domain.agent_runs import (
    AgentRunRequest,
    AgentRunResult,
    EndReason,
)
from factory.domain.errors import AgentRuntimeError
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from human_clone import HumanClone
from probe_support import COMPLETED, ENVIRONMENT

SUDO_REFUSAL = "sudo: a password is required"
IMAGE = "build-7"
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.01,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "question", "entry": "probe"},
    }
)


class RefusingRuntime(AgentRuntime):
    """An agent runtime that cannot start any run, as when `sudo` is refused."""

    def __init__(self, detail: str) -> None:
        self._detail = detail
        self.requests: list[AgentRunRequest] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        self.requests.append(request)
        raise AgentRuntimeError(self._detail)

    def version(self) -> str:
        return "fake"


@pytest.fixture
def coder(agent_home: Path) -> None:
    """Install the agent `coder`, among others, into the test's agent home."""
    install_agents(agent_home, ["intake", "coder", "reviewer"])


def _ended(reason: EndReason) -> ScriptedRun:
    return ScriptedRun(result=AgentRunResult(end_reason=reason, duration=timedelta(seconds=5)))


@pytest.mark.usefixtures("coder")
def test_a_completed_probe_passes(
    boundaries: Boundaries, probe_settings: InstanceSettings, agent_runtime: FakeAgentRuntime
) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(boundaries, probe_settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert item.passed


@pytest.mark.usefixtures("coder")
def test_the_probe_runs_the_coder_on_a_small_budget_with_the_question_alone(
    boundaries: Boundaries, probe_settings: InstanceSettings, agent_runtime: FakeAgentRuntime
) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    agent_run_probe_item(boundaries, probe_settings, ENVIRONMENT)

    [request] = agent_runtime.requests()
    assert request.prompt == PROBE_PROMPT
    assert request.allowed_decisions == ["question"]
    assert request.time_limit == timedelta(minutes=2)
    assert request.working_directory == boundaries.checkout
    assert request.environment == ENVIRONMENT
    installed = boundaries.agent_definitions.read("coder")
    assert request.agent.name == "coder"
    assert (request.agent.model, request.agent.tools) == (installed.model, installed.tools)
    assert request.agent.budget_usd == Decimal("0.10")


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize("reason", ["died", "no_result", "time_limit", "budget"])
def test_a_probe_that_does_not_complete_fails_with_its_detail(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    *,
    reason: EndReason,
) -> None:
    agent_runtime.queue(_ended(reason))

    item = agent_run_probe_item(boundaries, probe_settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert item.detail == (
        f"the probe run ended {reason}; run claude -p by hand as the factory user to see why"
    )


@pytest.mark.usefixtures("coder")
def test_a_runtime_that_cannot_run_the_probe_fails_with_its_message(
    boundaries: Boundaries, probe_settings: InstanceSettings
) -> None:
    refusing = dataclasses.replace(boundaries, agent_runtime=RefusingRuntime(SUDO_REFUSAL))

    item = agent_run_probe_item(refusing, probe_settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert SUDO_REFUSAL in item.detail


def test_a_missing_coder_fails_the_probe_naming_the_agent(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
) -> None:
    install_agents(agent_home, ["intake", "reviewer"])
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(boundaries, probe_settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert "coder" in item.detail


@pytest.mark.usefixtures("coder")
def test_the_probe_calls_claude_with_the_flags_of_a_stage(
    boundaries: Boundaries, probe_settings: InstanceSettings, tmp_path: Path
) -> None:
    bin_directory = tmp_path / "bin"
    executable = write_stand_in(bin_directory, [Step(stdout=REPLY), Step(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "runtime-state")
    claude = dataclasses.replace(boundaries, agent_runtime=runtime)
    environment = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}

    item = agent_run_probe_item(claude, probe_settings, environment)
    stage = AgentRunRequest(
        agent=boundaries.agent_definitions.read("coder"),
        prompt="Do the stage.",
        allowed_decisions=["review", "question"],
        time_limit=timedelta(minutes=30),
        working_directory=boundaries.checkout,
        environment=environment,
    )
    runtime.run(stage)

    assert item.passed
    probe_call, stage_call = read_calls(bin_directory)
    probe_flags = [word for word in probe_call.arguments if word.startswith("--")]
    stage_flags = [word for word in stage_call.arguments if word.startswith("--")]
    assert probe_flags == stage_flags


def test_the_probe_runs_once_for_each_image_build(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    human: HumanClone,
    tmp_path: Path,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    human.push_file("main", "Makefile", "lint:\n\ttrue\n")
    boundaries.git.fetch()
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    environment = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": str(tmp_path)}
    extra = [
        lambda: agent_run_probe_item(boundaries, probe_settings, environment),
    ]
    checks = MachineChecks(boundaries, probe_settings, lambda name: f"/usr/bin/{name}", extra)
    stamps = JsonPreflightStampFile(tmp_path / "state" / "preflight-stamp.json")
    preflight = Preflight(boundaries, checks, stamps, StopService(boundaries), IMAGE)

    assert preflight.run() is None
    assert preflight.run() is None

    assert len(agent_runtime.requests()) == 1
