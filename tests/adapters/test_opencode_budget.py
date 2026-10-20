"""The opencode runtime stops a call past its budget while it streams and resumes it once."""

import time
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    BOUND_SECONDS,
    RESUME_ENTRY,
    RESUME_REPLY,
    SESSION,
    WAIT_SECONDS,
    budget_steps,
    opencode_request,
    over_budget,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
)
from factory.adapters.agent_launch import FINISH_MESSAGE
from factory.adapters.opencode_runtime import CONFIG_VARIABLE
from factory.domain.agent_runs import TokenCounts
from factory.domain.kill_points import KillPoint, KillPoints
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

# What one `step_finish` of the stand-in's builders counts, as the runtime sums it.
STEP_TOKENS = TokenCounts(input=10, output=7, cache_read=100, cache_creation=20)


@pytest.mark.parametrize(
    ("first", "end_reason", "calls"),
    [
        pytest.param(
            Step(stdout=stdout(*budget_steps(0.4, 0.4, 0.2), text(result_text(), 9000))),
            "completed",
            1,
            id="at-the-budget",
        ),
        pytest.param(over_budget(), "completed", 2, id="past-the-budget"),
    ],
)
def test_a_call_is_stopped_once_its_summed_cost_passes_the_budget(
    tmp_path: Path, first: Step, end_reason: str, calls: int
) -> None:
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == end_reason
    assert len(read_calls(tmp_path / "bin")) == calls


def test_the_resume_continues_the_session_with_the_finish_message_and_sums_both_calls(
    tmp_path: Path,
) -> None:
    runtime = stand_in_runtime(tmp_path, [over_budget(), RESUME_REPLY])

    result = runtime.run(opencode_request(tmp_path / "work"))

    _, resume = read_calls(tmp_path / "bin")
    assert resume.arguments[-3:] == ["--session", SESSION, FINISH_MESSAGE]
    assert result.end_reason == "completed"
    assert result.decision == "question"
    assert result.entry == RESUME_ENTRY
    assert result.cost_usd == Decimal("1.11")
    assert result.turns == 4  # noqa: PLR2004 - three steps of the first call, one of the resume
    assert result.tokens == TokenCounts(
        input=4 * STEP_TOKENS.input,
        output=4 * STEP_TOKENS.output,
        cache_read=4 * STEP_TOKENS.cache_read,
        cache_creation=4 * STEP_TOKENS.cache_creation,
    )


def test_the_resume_runs_with_the_first_call_s_run_files_which_are_removed_after_it(
    tmp_path: Path,
) -> None:
    runtime = stand_in_runtime(tmp_path, [over_budget(), RESUME_REPLY])

    runtime.run(opencode_request(tmp_path / "work"))

    first, resume = read_calls(tmp_path / "bin")
    config = resume.environment[CONFIG_VARIABLE]
    assert config == first.environment[CONFIG_VARIABLE]
    assert resume.files[config] == first.files[config]
    assert list((tmp_path / "state").iterdir()) == []


def test_a_resume_past_its_own_budget_ends_the_run_by_budget_without_a_third_call(
    tmp_path: Path,
) -> None:
    resume = Step(
        stdout_before_wait=stdout(
            step_start(10_000),
            step_finish(10_500, cost=0.30),
            step_start(11_000),
            step_finish(11_500, cost=0.25),
        ),
        wait_seconds=WAIT_SECONDS,
    )
    runtime = stand_in_runtime(tmp_path, [over_budget(), resume, RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == "budget"
    assert result.cost_usd == Decimal("1.56")
    assert len(read_calls(tmp_path / "bin")) == 2  # noqa: PLR2004 - the call and its resume


def test_a_budget_stop_without_a_known_session_is_not_resumed(tmp_path: Path) -> None:
    runtime = stand_in_runtime(tmp_path, [over_budget(with_session=False), RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == "budget"
    assert result.cost_usd == Decimal("1.01")
    assert len(read_calls(tmp_path / "bin")) == 1


def test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit(
    tmp_path: Path,
) -> None:
    resume = Step(
        stdout_before_wait=stdout(step_start(10_000), step_finish(10_500, cost=0.1)),
        wait_seconds=WAIT_SECONDS,
    )
    runtime = stand_in_runtime(tmp_path, [over_budget(), resume])
    request = opencode_request(tmp_path / "work", time_limit=ROOMY_LIMIT)

    started = time.monotonic()
    result = runtime.run(request)

    assert time.monotonic() - started < ROOMY_BOUND_SECONDS
    assert result.end_reason == "time_limit"
    assert len(read_calls(tmp_path / "bin")) == 2  # noqa: PLR2004 - the call and its resume


def test_the_kill_point_is_reached_once_for_a_resumed_run(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    runtime = stand_in_runtime(tmp_path, [over_budget(), RESUME_REPLY], kill_points=kill_points)

    runtime.run(opencode_request(tmp_path / "work"))

    assert len(read_calls(tmp_path / "bin")) == 2  # noqa: PLR2004 - the call and its resume
    assert kill_points.reached(KillPoint.AGENT_RUN) == 1
