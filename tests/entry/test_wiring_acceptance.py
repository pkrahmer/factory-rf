"""The production wiring with the acceptance's handlers: every kind registered, the splits gated."""

from datetime import timedelta
from pathlib import Path
from typing import get_args

import pytest

from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceDueHandler, AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import unhandled_kinds
from factory.application.tick import Tick
from factory.domain.acceptance import AcceptanceState
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import CannotHandle
from factory.domain.events import Event, EventKind
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from factory.entry.wiring import NOT_YET_HANDLED, build_handlers, handler_factory
from git_support import PIPELINE_YAML, install_agents, remote_commit
from human_clone import HumanClone

INSTANCE = "factory-1"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
STATE = "a" * 40
EXAMPLE = "factory/features/F0001-example"
BACKLOG_PATH = f"{EXAMPLE}/backlog/F0001-S0001-first.md"
STORY_ID = "F0001-S0001"
STORY_BRANCH = f"work-item/{STORY_ID}"
STORY_PATH = f"{EXAMPLE}/in-progress/F0001-S0001-first.md"
STORY_DONE = f"{EXAMPLE}/done/F0001-S0001-first.md"
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
TODO = "factory/features/F0002-todo"
ACCEPTANCE = "F0002-A0001"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
DONE_REPORT = f"{TODO}/done/F0002-A0001-acceptance.md"
WITHOUT_STAGE = PIPELINE_YAML.replace("acceptance_stage: acceptance\n", "")
COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)


def test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance(
    boundaries: Boundaries,
) -> None:
    handlers = build_handlers(boundaries, pipeline_definition(boundaries), INSTANCE, ENVIRONMENT)

    assert NOT_YET_HANDLED == ()
    assert set(handlers) == set(get_args(EventKind))
    assert unhandled_kinds(handlers) == []
    assert isinstance(handlers["acceptance_due"], AcceptanceDueHandler)


def test_a_merged_story_reaches_the_story_handler_and_is_archived(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
) -> None:
    title = f"{STORY_ID}: first"
    number = hosting.create_pull_request(STORY_BRANCH, title, "body", draft=True).number
    human.start(BACKLOG_PATH)
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    state = WorkItemState(stage="doing", pull_request=number, journal=[created])
    text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=STORY))
    human.push_file(STORY_BRANCH, STORY_PATH, text)
    human.merge(STORY_BRANCH, "merge")
    checkout.fetch()
    snapshot = WorkItemSnapshot(
        id=STORY_ID,
        path=STORY_PATH,
        folder="in-progress",
        branch=STORY_BRANCH,
        branch_commit=checkout.resolve(f"origin/{STORY_BRANCH}"),
        document=boundaries.work_item_reader.parse(text),
    )
    main = remote_commit(remote, "main")
    assert main is not None
    handlers = build_handlers(boundaries, pipeline_definition(boundaries), INSTANCE, ENVIRONMENT)

    handlers["merged"].handle(Event(kind="merged", work_item=snapshot, remote_state=main))

    checkout.fetch()
    assert checkout.show_file("origin/main", STORY_DONE) is not None
    assert checkout.show_file("origin/main", STORY_PATH) is None


def test_a_run_of_an_acceptance_closed_while_due_is_booked_refused_by_the_gate(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    agent_runtime: FakeAgentRuntime,
) -> None:
    definition = pipeline_definition(boundaries)
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    branch = AcceptanceService(boundaries, definition).open("F0002").branch
    title = f"{ACCEPTANCE}: acceptance"
    number = hosting.create_pull_request(branch, title, "body", draft=True).number
    state = AcceptanceState(
        stage="acceptance", stories=["F0002-S0001", "F0002-S0002"], pull_request=number
    )
    started = NewEntry(speaker=FACTORY, kind="started", text="started.")
    document = append_entry(
        WorkItemDocument(state=state, body="# Acceptance of Todo service\n\n## Journal\n"),
        started,
    )
    text = boundaries.work_item_writer.render(document)
    human.push_file(branch, REPORT, text)
    hosting.close_by_human(number)
    checkout.fetch()
    branch_commit = checkout.resolve(f"origin/{branch}")
    assert branch_commit is not None
    snapshot = WorkItemSnapshot(
        id=ACCEPTANCE,
        path=REPORT,
        folder="in-progress",
        branch=branch,
        branch_commit=branch_commit,
        document=boundaries.work_item_reader.parse(text),
    )
    handlers = build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)

    handlers["run"].handle(Event(kind="run", work_item=snapshot, remote_state=branch_commit))

    checkout.fetch()
    booked = checkout.show_file("origin/main", DONE_REPORT)
    assert booked is not None
    booked_state = boundaries.work_item_reader.parse(booked).state
    assert isinstance(booked_state, AcceptanceState)
    assert (booked_state.stage, booked_state.outcome) == ("done", "refused")
    assert checkout.show_file("origin/main", REPORT) is None
    assert agent_runtime.requests() == []


def test_without_an_acceptance_stage_the_handlers_build_refuse_and_a_story_still_ticks(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    definition = boundaries.pipeline_reader.parse(WITHOUT_STAGE)
    assert definition.acceptance_stage is None
    handlers = build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)
    due = Event(kind="acceptance_due", work_item=None, feature="F0001", remote_state=STATE)

    with pytest.raises(CannotHandle) as refused:
        handlers["acceptance_due"].handle(due)

    assert refused.value.reason == "no acceptance stage"
    install_agents(agent_home, pipeline_definition(boundaries).roles)
    human.push_file("main", "factory/pipeline.yml", WITHOUT_STAGE)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    tick = Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, ENVIRONMENT))

    outcome = tick.run()

    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert outcome.dispatch == "handled"
