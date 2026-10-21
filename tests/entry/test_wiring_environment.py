"""The production agent environment: built from an allow list, whatever the process holds."""

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick
from factory.domain.agent_runs import AgentRunResult
from factory.entry.wiring import handler_factory, production_environment
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from stage_run_support import INSTANCE

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
SECRET_NAMES = ("GH_TOKEN", "GITHUB_TOKEN", "FACTORY_TOKEN_FILE", "GIT_ASKPASS")
LOCALE = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TERM": "xterm", "TZ": "UTC"}
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


@pytest.fixture
def secrets_in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the token's names in the process's environment for the test."""
    for name in SECRET_NAMES:
        monkeypatch.setenv(name, "example-value")


@pytest.mark.usefixtures("secrets_in_process")
def test_the_production_environment_leaves_out_the_token_and_keeps_path_and_home() -> None:
    environment = production_environment()

    assert not set(SECRET_NAMES) & set(environment)
    assert environment["PATH"].split(os.pathsep)[0] == str(Path(sys.executable).parent)
    assert environment["HOME"] == str(Path.home())


@pytest.mark.parametrize("present", [True, False], ids=["locale-set", "locale-unset"])
def test_the_production_environment_keeps_the_locale_the_process_has(
    monkeypatch: pytest.MonkeyPatch, *, present: bool
) -> None:
    for name, value in LOCALE.items():
        if present:
            monkeypatch.setenv(name, value)
        else:
            monkeypatch.delenv(name, raising=False)

    environment = production_environment()

    assert {name: environment.get(name) for name in LOCALE} == (
        LOCALE if present else dict.fromkeys(LOCALE)
    )


@pytest.mark.usefixtures("secrets_in_process")
def test_a_tick_in_the_production_environment_hands_the_agent_no_token(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    handlers = handler_factory(boundaries, INSTANCE, production_environment())
    tick = Tick(boundaries, INSTANCE, handlers)

    tick.run()

    [request] = agent_runtime.requests()
    assert not set(SECRET_NAMES) & set(request.environment)
