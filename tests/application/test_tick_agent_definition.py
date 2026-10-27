"""A tick whose definition names a refused agent file ends at the stop and does nothing else."""

from pathlib import Path

import pytest

from agent_definition_support import BACKLOG_PATH, COMPLETED, STORY
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick, TickOutcome
from factory.domain.stops import RepositoryStop
from factory.entry.wiring import handler_factory
from git_support import COLOURED_AGENT_FILE, PIPELINE_YAML, install_agents, write_agent
from human_clone import HumanClone
from stage_run_support import INSTANCE
from wiring_support import ENVIRONMENT

ROLE = "coder"


@pytest.fixture
def tick(boundaries: Boundaries, *, agent_home: Path, human: HumanClone) -> Tick:
    """A started story on the remote and one role's agent file holding an unapplied key."""
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    write_agent(agent_home, ROLE, COLOURED_AGENT_FILE)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    return Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, ENVIRONMENT))


def test_the_tick_ends_at_the_agent_stop(
    tick: Tick, boundaries: Boundaries, clock: ManualClock
) -> None:
    outcome = tick.run()

    assert outcome == TickOutcome(stopped="agent_definition_invalid")
    assert boundaries.health.read().stops == [
        RepositoryStop(
            scope="repository",
            reason="agent_definition_invalid",
            detail=f"{ROLE}: key not applied by the agent runtime: colour",
            at=clock.now(),
        )
    ]


def test_the_stopped_tick_requests_no_run_and_dispatches_nothing(
    tick: Tick, agent_runtime: FakeAgentRuntime, hosting: FakeHostingService
) -> None:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    outcome = tick.run()

    assert outcome.event is None
    assert outcome.dispatch is None
    assert agent_runtime.requests() == []
    assert hosting.pull_requests() == []


def test_after_the_file_is_corrected_the_next_tick_runs_the_stage(
    tick: Tick,
    boundaries: Boundaries,
    *,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    tick.run()
    install_agents(agent_home, [ROLE])
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    outcome = tick.run()

    assert outcome.stopped is None
    assert outcome.event is not None
    assert outcome.event.kind == "run"
    assert outcome.dispatch == "handled"
    reasons = [stop.reason for stop in boundaries.health.read().stops]
    assert "agent_definition_invalid" not in reasons
