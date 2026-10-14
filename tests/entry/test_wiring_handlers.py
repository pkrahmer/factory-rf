"""The production wiring of the dispatcher: the handlers, the unhandled kinds, the environment."""

import os
import shutil
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, unhandled_kinds
from factory.application.handlers.run_gate import RunGate
from factory.application.stops import StopService
from factory.application.tick import IdleHandler, Tick
from factory.domain.agent_runs import AgentRunResult
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.tick_status import TickStatus, find_error
from factory.entry.wiring import (
    NOT_YET_HANDLED,
    agent_environment,
    build_handlers,
    handler_factory,
    production_environment,
)
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
STATE = "a" * 40
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


def _definition(boundaries: Boundaries) -> PipelineDefinition:
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)


def test_build_handlers_registers_the_idle_handler_and_the_gated_run_handler(
    boundaries: Boundaries,
) -> None:
    handlers = build_handlers(boundaries, _definition(boundaries), INSTANCE, ENVIRONMENT)

    assert {"idle", "run"} <= set(handlers)
    assert isinstance(handlers["idle"], IdleHandler)
    assert isinstance(handlers["run"], RunGate)


def test_the_kinds_without_a_handler_are_exactly_those_not_yet_handled(
    boundaries: Boundaries,
) -> None:
    handlers = build_handlers(boundaries, _definition(boundaries), INSTANCE, ENVIRONMENT)

    assert unhandled_kinds(handlers) == list(NOT_YET_HANDLED)


@pytest.mark.parametrize("guard_present", [True, False], ids=["guard-present", "guard-absent"])
def test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home(
    tmp_path: Path, *, guard_present: bool
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    home = tmp_path / "home"
    if guard_present:
        guard = scripts / "factory-guard"
        guard.write_text("", encoding="utf-8")
        guard.chmod(0o755)

    environment = agent_environment(scripts, home)

    assert set(environment) == {"PATH", "HOME"}
    assert environment["HOME"] == str(home)
    assert environment["PATH"] == f"{scripts}:/usr/local/bin:/usr/bin:/bin"
    assert environment["PATH"].split(os.pathsep)[0] == str(scripts)
    found = shutil.which("factory-guard", path=environment["PATH"])
    assert found == (str(scripts / "factory-guard") if guard_present else None)


def test_the_production_environment_uses_the_interpreter_directory_and_the_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "operator"))

    environment = production_environment()

    assert environment["PATH"].split(os.pathsep)[0] == str(Path(sys.executable).parent)
    assert environment["HOME"] == str(Path.home())
    assert environment["HOME"] == str(tmp_path / "operator")


def test_a_tick_over_the_handler_factory_runs_one_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, _definition(boundaries).roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    tick = Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, ENVIRONMENT))

    outcome = tick.run()

    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert outcome.dispatch == "handled"
    [request] = agent_runtime.requests()
    assert request.environment == ENVIRONMENT


def test_an_event_not_yet_handled_is_a_counted_error(boundaries: Boundaries) -> None:
    handlers = build_handlers(boundaries, _definition(boundaries), INSTANCE, ENVIRONMENT)
    dispatcher = Dispatcher(handlers, TickStatus(), StopService(boundaries))
    event = Event(kind="acceptance_due", work_item=None, feature="F0001", remote_state=STATE)

    outcome = dispatcher.dispatch(event)

    assert outcome == "error"
    entry = find_error(dispatcher.status, event.key, STATE)
    assert entry is not None
    assert entry.last_error == "UnhandledEvent: no handler for event kind acceptance_due"
