"""The run handler: one `run` event becomes one stage run."""

from datetime import timedelta
from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.run import RunHandler
from factory.application.watcher import Watcher
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import HostingServiceError
from factory.domain.events import Event
from git_support import install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
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


def _run_event(
    boundaries: Boundaries, human: HumanClone, checkout: GitCli, agent_home: Path
) -> Event:
    """Start a complete story and return the event the watcher sees for it."""
    definition = pipeline_definition(boundaries)
    install_agents(agent_home, definition.roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    checkout.fetch()
    event = Watcher(boundaries, INSTANCE).evaluate(definition)
    assert event.kind == "run"
    return event


def _handler(boundaries: Boundaries) -> RunHandler:
    return RunHandler(boundaries, INSTANCE, pipeline_definition(boundaries), ENVIRONMENT)


def test_a_run_event_runs_the_stage_with_exactly_the_given_environment(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    event = _run_event(boundaries, human, checkout, agent_home)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    _handler(boundaries).handle(event)

    [request] = agent_runtime.requests()
    assert request.environment == ENVIRONMENT
    checkout.fetch()
    assert checkout.resolve(f"origin/work-item/{WORK_ITEM}") is not None


@pytest.mark.parametrize("kind", ["comment", "idle"])
def test_an_event_of_another_kind_is_refused_without_an_agent_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    kind: str,
) -> None:
    run = _run_event(boundaries, human, checkout, agent_home)
    if kind == "comment":
        event = Event(kind="comment", work_item=run.work_item, remote_state=run.remote_state)
    else:
        event = Event(kind="idle", work_item=None, remote_state=run.remote_state)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    with pytest.raises(ValueError):
        _handler(boundaries).handle(event)

    assert agent_runtime.requests() == []


def test_a_failure_of_the_stage_propagates(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    event = _run_event(boundaries, human, checkout, agent_home)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    hosting.fail_next("create_pull_request")

    with pytest.raises(HostingServiceError):
        _handler(boundaries).handle(event)
