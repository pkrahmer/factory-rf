"""Patient runs: a run the provider's spend limit stopped waits and resumes, up to a ceiling."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.provider_limits import CONTINUE_PROMPT, PatientRuns
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult, EndReason
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from log_support import log_lines

SESSION = "ses_a"
SECONDS = timedelta(seconds=5)
MARK = "provider limit: "


@pytest.fixture
def waiter(clock: ManualClock) -> ManualWaiter:
    """Return a manual waiter on the test's clock."""
    return ManualWaiter(clock)


@pytest.fixture
def patient(
    boundaries: Boundaries, local_settings: InstanceSettings, waiter: ManualWaiter
) -> Boundaries:
    """Return the boundaries with the waiter and settings of the default limit."""
    return replace(boundaries, waiter=waiter, settings=local_settings)


def _request(boundaries: Boundaries) -> AgentRunRequest:
    agent = AgentDefinition(
        name="coder",
        model="sonnet",
        tools=["Read"],
        budget_usd=Decimal("1"),
        instructions="Write the code.",
    )
    return AgentRunRequest(
        agent=agent,
        prompt="Do the stage.",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=60),
        working_directory=boundaries.checkout,
        environment={"HOME": "/home/factory"},
    )


def _limited(
    *,
    cost: str | None = None,
    duration: timedelta = SECONDS,
    session: str | None = SESSION,
    wait: timedelta | None = None,
) -> AgentRunResult:
    return AgentRunResult(
        end_reason="provider_limit",
        duration=duration,
        cost_usd=None if cost is None else Decimal(cost),
        session=session,
        limit_wait=wait,
    )


def _completed(cost: str = "0.30") -> AgentRunResult:
    return AgentRunResult(
        end_reason="completed",
        decision="doing",
        entry="Second call.",
        duration=SECONDS,
        cost_usd=Decimal(cost),
        session=SESSION,
    )


def _queue(runtime: FakeAgentRuntime, *results: AgentRunResult) -> None:
    for result in results:
        runtime.queue(ScriptedRun(result=result))


def _limit(boundaries: Boundaries, cooldown: timedelta, ceiling: timedelta) -> Boundaries:
    assert boundaries.settings is not None
    limit = ProviderLimit(cooldown=cooldown, ceiling=ceiling)
    settings = boundaries.settings.model_copy(update={"provider_limit": limit})
    return replace(boundaries, settings=settings)


def _limit_lines(tmp_path: Path) -> list[str]:
    return [line.split(" ", 1)[1] for line in log_lines(tmp_path) if MARK in line]


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(_completed(), id="completed"),
        pytest.param(AgentRunResult(end_reason="died", duration=SECONDS), id="died"),
    ],
)
def test_a_run_not_stopped_by_a_limit_comes_back_as_it_is(
    patient: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    result: AgentRunResult,
) -> None:
    _queue(agent_runtime, result)

    returned = PatientRuns(patient).run(_request(patient))

    assert returned == result
    assert len(agent_runtime.requests()) == 1
    assert waiter.waits == []


def test_a_limited_run_waits_the_cooldown_and_resumes_its_session_with_what_is_left(
    patient: Boundaries, agent_runtime: FakeAgentRuntime, waiter: ManualWaiter
) -> None:
    _queue(agent_runtime, _limited(cost="0.20"), _completed("0.30"))
    request = _request(patient)

    result = PatientRuns(patient).run(request)

    assert waiter.waits == [timedelta(seconds=600)]
    first, second = agent_runtime.requests()
    assert first == request
    assert second == request.model_copy(
        update={
            "prompt": CONTINUE_PROMPT,
            "resume_session": SESSION,
            "agent": request.agent.model_copy(update={"budget_usd": Decimal("0.80")}),
            "time_limit": timedelta(seconds=55),
        }
    )
    assert result.end_reason == "completed"
    assert result.cost_usd == Decimal("0.50")
    assert result.duration == timedelta(seconds=10)
    assert (result.decision, result.entry) == ("doing", "Second call.")


@pytest.mark.parametrize(
    ("named", "waited"),
    [
        pytest.param(timedelta(seconds=420), timedelta(seconds=420), id="named-wait"),
        pytest.param(timedelta(hours=3), timedelta(hours=2), id="cut-to-the-ceiling"),
    ],
)
def test_a_named_wait_is_waited_instead_of_the_cooldown_within_the_ceiling(
    patient: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    *,
    named: timedelta,
    waited: timedelta,
) -> None:
    _queue(agent_runtime, _limited(wait=named), _completed())

    result = PatientRuns(patient).run(_request(patient))

    assert waiter.waits == [waited]
    assert result.end_reason == "completed"


def test_a_limit_that_lasts_ends_the_run_at_the_ceiling(
    patient: Boundaries, agent_runtime: FakeAgentRuntime, waiter: ManualWaiter, tmp_path: Path
) -> None:
    limited = _limit(patient, timedelta(minutes=10), timedelta(minutes=30))
    _queue(agent_runtime, *[_limited()] * 5)

    result = PatientRuns(limited).run(_request(limited))

    assert len(agent_runtime.requests()) == 4
    assert waiter.waits == [timedelta(seconds=600)] * 3
    assert result.end_reason == "provider_limit"
    assert _limit_lines(tmp_path) == [
        *["provider limit: coder waits 600 s before it resumes ses_a"] * 3,
        "provider limit: coder waited 1800 s, the ceiling of 1800 s; the run ends provider_limit",
    ]


@pytest.mark.parametrize(
    "second_wait",
    [
        pytest.param(timedelta(minutes=25), id="named-again"),
        pytest.param(None, id="cooldown"),
    ],
)
def test_a_named_wait_is_cut_to_what_is_left_of_the_ceiling(
    patient: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    second_wait: timedelta | None,
) -> None:
    limited = _limit(patient, timedelta(minutes=10), timedelta(minutes=30))
    _queue(
        agent_runtime,
        _limited(wait=timedelta(minutes=25)),
        _limited(wait=second_wait),
        _limited(wait=timedelta(minutes=25)),
        _completed(),
    )

    result = PatientRuns(limited).run(_request(limited))

    assert waiter.waits == [timedelta(seconds=1500), timedelta(seconds=300)]
    assert len(agent_runtime.requests()) == 3
    assert result.end_reason == "provider_limit"


def test_a_limited_run_without_a_session_starts_a_new_run_with_what_is_left(
    patient: Boundaries, agent_runtime: FakeAgentRuntime, tmp_path: Path
) -> None:
    _queue(agent_runtime, _limited(cost="0.20", session=None), _completed())
    request = _request(patient)

    PatientRuns(patient).run(request)

    _, second = agent_runtime.requests()
    assert second.prompt == request.prompt
    assert second.resume_session is None
    assert second.agent.budget_usd == Decimal("0.80")
    assert second.time_limit == timedelta(seconds=55)
    [line] = _limit_lines(tmp_path)
    assert line.endswith("before it resumes a new run")


@pytest.mark.parametrize(
    ("cost", "duration", "ended"),
    [
        pytest.param("1.00", SECONDS, "budget", id="budget-used"),
        pytest.param("1.20", SECONDS, "budget", id="budget-overrun"),
        pytest.param("0.99", SECONDS, None, id="budget-left"),
        pytest.param(None, timedelta(seconds=60), "time_limit", id="time-used"),
        pytest.param(None, timedelta(seconds=59), None, id="time-left"),
        pytest.param("1.00", timedelta(seconds=60), "budget", id="both-used"),
    ],
)
def test_a_limited_run_with_nothing_left_ends_without_a_wait(
    patient: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    *,
    cost: str | None,
    duration: timedelta,
    ended: EndReason | None,
) -> None:
    first = _limited(cost=cost, duration=duration, wait=timedelta(minutes=5))
    _queue(agent_runtime, first, _completed("0.00"))

    result = PatientRuns(patient).run(_request(patient))

    if ended is None:
        assert waiter.waits == [timedelta(minutes=5)]
        assert result.end_reason == "completed"
        return
    assert result == first.model_copy(update={"end_reason": ended, "limit_wait": None})
    assert len(agent_runtime.requests()) == 1
    assert waiter.waits == []


@pytest.mark.parametrize(
    ("named", "waited"),
    [
        pytest.param(None, timedelta(seconds=600), id="default-cooldown"),
        pytest.param(timedelta(hours=3), timedelta(seconds=7200), id="default-ceiling"),
    ],
)
def test_with_the_default_settings_the_default_limit_applies(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    *,
    named: timedelta | None,
    waited: timedelta,
) -> None:
    unset = replace(
        boundaries,
        waiter=waiter,
        settings=InstanceSettings(repository_url="/srv/project.git", instance="factory-1"),
    )
    _queue(agent_runtime, _limited(wait=named), _completed())

    PatientRuns(unset).run(_request(unset))

    assert waiter.waits == [waited]


@pytest.mark.parametrize(
    ("ceiling", "results", "waited", "line"),
    [
        pytest.param(
            timedelta(hours=2),
            [_limited(wait=timedelta(seconds=90.9)), _completed()],
            [timedelta(seconds=90.9)],
            "provider limit: coder waits 90 s before it resumes ses_a",
            id="wait",
        ),
        pytest.param(
            timedelta(seconds=1800.7),
            [_limited()] * 5,
            [timedelta(seconds=600)] * 3 + [timedelta(seconds=0.7)],
            "provider limit: coder waited 1800 s, the ceiling of 1800 s;"
            " the run ends provider_limit",
            id="ceiling",
        ),
    ],
)
def test_the_log_lines_give_whole_seconds_and_the_waits_are_kept_whole(
    patient: Boundaries,
    agent_runtime: FakeAgentRuntime,
    waiter: ManualWaiter,
    tmp_path: Path,
    *,
    ceiling: timedelta,
    results: list[AgentRunResult],
    waited: list[timedelta],
    line: str,
) -> None:
    limited = _limit(patient, timedelta(minutes=10), ceiling)
    _queue(agent_runtime, *results)

    PatientRuns(limited).run(_request(limited))

    assert waiter.waits == waited
    assert _limit_lines(tmp_path)[-1] == line
