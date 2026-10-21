"""The production wiring with the human's handlers: every kind registered, the run gated."""

from datetime import timedelta
from pathlib import Path
from typing import get_args

from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.acceptance import (
    AcceptanceClosed,
    AcceptanceHandOver,
    AcceptanceMerged,
    SplitByWorkItemKind,
)
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler, unhandled_kinds
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.comments import CommentHandler
from factory.application.handlers.hand_over import HandOverHandler
from factory.application.handlers.lookups import DuplicateHandler, PullRequestLookupHandler
from factory.application.handlers.merged import MergedHandler
from factory.application.handlers.questions import AskHandler
from factory.application.handlers.reject import RejectHandler
from factory.application.handlers.run import RunHandler
from factory.application.handlers.run_gate import RunGate
from factory.application.tick import IdleHandler, Tick
from factory.domain.agent_runs import AgentRunResult
from factory.domain.events import EventKind
from factory.entry.wiring import NOT_YET_HANDLED, build_handlers
from git_support import install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
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


def _handlers(boundaries: Boundaries) -> dict[EventKind, Handler]:
    return build_handlers(boundaries, pipeline_definition(boundaries), INSTANCE, ENVIRONMENT)


def test_build_handlers_registers_the_kinds_of_the_human_on_the_pull_request(
    boundaries: Boundaries,
) -> None:
    handlers = _handlers(boundaries)

    assert set(handlers) >= {
        "crash",
        "idle",
        "run",
        "comment",
        "ask",
        "merged",
        "closed",
        "reject",
        "hand_over",
        "duplicate",
        "pull_request_lookup",
    }


def test_each_kind_has_its_handler_and_the_gate_shares_the_closed_and_merged_handlers(
    boundaries: Boundaries,
) -> None:
    handlers = _handlers(boundaries)
    expected: dict[EventKind, type[Handler]] = {
        "idle": IdleHandler,
        "run": RunGate,
        "comment": CommentHandler,
        "ask": AskHandler,
        "reject": RejectHandler,
        "duplicate": DuplicateHandler,
        "pull_request_lookup": PullRequestLookupHandler,
    }
    splits: dict[EventKind, tuple[type[Handler], type[Handler]]] = {
        "merged": (MergedHandler, AcceptanceMerged),
        "closed": (ClosedHandler, AcceptanceClosed),
        "hand_over": (HandOverHandler, AcceptanceHandOver),
    }

    for kind, handler_class in expected.items():
        assert isinstance(handlers[kind], handler_class), kind
    for kind, (story_class, acceptance_class) in splits.items():
        split = handlers[kind]
        assert isinstance(split, SplitByWorkItemKind), kind
        assert isinstance(split.story, story_class), kind
        assert isinstance(split.acceptance, acceptance_class), kind
    gate = handlers["run"]
    assert isinstance(gate, RunGate)
    assert isinstance(gate.run, RunHandler)
    assert gate.closed is handlers["closed"]
    assert gate.merged is handlers["merged"]


def test_the_run_entry_runs_the_stage_of_a_started_story_without_a_pull_request(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, pipeline_definition(boundaries).roles)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    tick = Tick(
        boundaries,
        INSTANCE,
        lambda definition: build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT),
    )

    outcome = tick.run()

    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert outcome.dispatch == "handled"
    assert len(agent_runtime.requests()) == 1


def test_the_kinds_not_yet_handled_are_exactly_the_kinds_without_a_handler(
    boundaries: Boundaries,
) -> None:
    handlers = _handlers(boundaries)

    assert unhandled_kinds(handlers) == list(NOT_YET_HANDLED)
    assert not set(NOT_YET_HANDLED) & set(handlers)
    assert set(get_args(EventKind)) - set(NOT_YET_HANDLED) == set(handlers)
