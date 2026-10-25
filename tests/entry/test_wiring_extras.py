"""The extra machine items, in the operator guide's order, and the tick that runs them."""

import dataclasses
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.tick import TickOutcome
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_tick, machine_extras
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from wiring_support import every_tool

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
STORY = """\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal
"""
PROBE = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)
COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)


@pytest.mark.parametrize(
    "names",
    [
        pytest.param(
            ["token-file", "agent-environment", "agent-run-probe"],
            id="no-agent-user",
        ),
    ],
)
def test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user(
    boundaries: Boundaries,
    tmp_path: Path,
    agent_home: Path,
    *,
    names: list[str],
) -> None:
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
    )
    environment = {"PATH": "/usr/bin", "HOME": str(tmp_path)}

    extras = machine_extras(boundaries, settings, environment)

    assert [check().name for check in extras] == names


@pytest.mark.parametrize("token_file_exists", [False, True], ids=["no-token-file", "token-file"])
def test_a_tick_stops_on_a_failed_extra_and_otherwise_probes_in_the_stages_environment(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    token_file_exists: bool,
) -> None:
    roles = boundaries.pipeline_reader.parse(PIPELINE_YAML).roles
    install_agents(agent_home, {*roles, "coder"})
    human.push_file("main", "Makefile", "lint:\n\ttrue\nsync:\n\t@:\n")
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    token_file = tmp_path / "hosting-token"
    if token_file_exists:
        token_file.write_text("example-value\n", encoding="utf-8")
        token_file.chmod(0o600)
    agent_runtime.queue(ScriptedRun(result=PROBE))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    settings = InstanceSettings(
        repository_url=str(remote),
        instance="factory-7",
        checkout=tmp_path / "instance-checkout",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        claude_executable=str(tmp_path / "no-claude"),
        pinned_agent_version="fake",
        token_file=token_file,
    )
    tick = build_tick(dataclasses.replace(boundaries, settings=settings), settings, every_tool)

    outcome = tick.run()

    if not token_file_exists:
        assert outcome == TickOutcome(stopped="preflight_failed")
        [stop] = boundaries.health.read().stops
        assert "token-file" in stop.detail
        return
    assert outcome.stopped is None
    probe, stage = agent_runtime.requests()
    assert probe.allowed_decisions == ["question"]
    assert stage.environment == probe.environment
