"""The wiring gives an agent run as another user that user's home and names the user."""

import dataclasses
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_run_environment, build_tick
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
BASE = {"PATH": "/usr/bin", "HOME": "/home/factory", "LANG": "C.UTF-8"}
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
COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)


def _every_tool(name: str) -> str | None:
    return f"/usr/bin/{name}"


@pytest.mark.parametrize(
    ("agent_user", "expected"),
    [("agent", {**BASE, "HOME": "/home/agent"}), (None, BASE)],
    ids=["agent-user", "no-agent-user"],
)
def test_the_agent_run_environment_sets_home_to_the_agent_users_home(
    agent_user: str | None, expected: dict[str, str]
) -> None:
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        agent_home=Path("/home/agent/.claude"),
        agent_user=agent_user,
    )
    base = dict(BASE)

    environment = agent_run_environment(settings, base)

    assert environment == expected
    assert base == BASE


def test_a_tick_with_an_agent_user_runs_the_agent_as_that_user_in_its_home(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", "Makefile", "lint:\n\ttrue\n")
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    settings = InstanceSettings(
        repository_url=str(remote),
        instance="factory-7",
        checkout=tmp_path / "instance-checkout",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        claude_executable=str(tmp_path / "no-claude"),
        pinned_agent_version="fake",
        agent_user="agent",
    )
    tick = build_tick(dataclasses.replace(boundaries, settings=settings), settings, _every_tool)

    tick.run()

    [request] = agent_runtime.requests()
    assert request.os_user == "agent"
    assert request.environment["HOME"] == str(settings.agent_home.parent)
