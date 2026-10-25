"""A stage whose run meets the provider's spend limit: it waits and goes on, or stalls at last."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.paths import cost_records_path
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from human_clone import HumanClone
from stage_run_support import PATH, branch_head, open_story, pushed_state, run_stage

SECONDS = timedelta(seconds=5)
LIMITED = AgentRunResult(
    end_reason="provider_limit", duration=SECONDS, cost_usd=Decimal("0.20"), session="ses_a"
)
COMPLETED = AgentRunResult(
    end_reason="completed",
    decision="doing",
    entry="tests written.",
    duration=SECONDS,
    cost_usd=Decimal("0.30"),
    session="ses_a",
)
NOTE = (
    "Stalled (attempt 1 of 2): the provider's spend limit lasted past the waiting ceiling. "
    "Retrying on the next tick."
)


def test_a_stage_that_waits_out_a_limit_moves_on_as_a_completed_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    opened = open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=LIMITED))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    waiter = ManualWaiter(clock)

    report = run_stage(replace(boundaries, waiter=waiter))

    assert report.stall is None
    assert report.next_stage == "doing"
    assert pushed_state(boundaries, remote).attempts == opened.attempts
    text = boundaries.git.show_file(branch_head(remote), cost_records_path(PATH))
    assert text is not None
    [record] = boundaries.cost_reader.parse(text)
    assert record.status == "completed"
    assert record.cost_usd == Decimal("0.50")
    assert waiter.waits == [timedelta(seconds=600)]


def test_a_stage_whose_limit_outlasts_the_ceiling_stalls_with_its_note(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
    hosting: FakeHostingService,
    local_settings: InstanceSettings,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=LIMITED))
    agent_runtime.queue(ScriptedRun(result=LIMITED))
    minute = timedelta(minutes=1)
    settings = local_settings.model_copy(
        update={
            "provider_limit": ProviderLimit(cooldown=minute, ceiling=minute),
            "agent_home": agent_home,
        }
    )

    report = run_stage(replace(boundaries, waiter=ManualWaiter(clock), settings=settings))

    assert report.stall is not None
    assert report.stall.reason == "provider_limit"
    assert (report.stall.attempts, report.stall.attempts_cap) == (1, 2)
    assert len(agent_runtime.requests()) == 2
    state = pushed_state(boundaries, remote)
    assert state.attempts == 1
    assert any(NOTE in post.body for post in hosting.factory_posts(report.pull_request))
