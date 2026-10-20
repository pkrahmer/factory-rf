"""The opencode runtime stops a call at once on a provider limit in its errors, not its text."""

import json
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    BOUND_SECONDS,
    REPLY,
    RESUME_REPLY,
    SESSION,
    WAIT_SECONDS,
    WAITING,
    error,
    opencode_request,
    over_budget,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
    tool_use,
)
from factory.domain.provider_limits import ProviderLimit

LIMIT_MESSAGE = "spend limit reached, try again in 7 minutes"
LIMIT_ERROR = error(LIMIT_MESSAGE, status_code=428, timestamp=3000)
LIMIT_LINE = "HTTP 428 Precondition Required"


def _without_status(line: str) -> str:
    event = json.loads(line)
    del event["error"]["data"]["statusCode"]
    return json.dumps(event)


def test_a_limit_error_after_a_step_ends_the_run_at_once_with_its_wait_and_session(
    tmp_path: Path,
) -> None:
    first = Step(
        stdout_before_wait=stdout(step_start(), step_finish(cost=0.2), LIMIT_ERROR),
        wait_seconds=WAIT_SECONDS,
    )
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == "provider_limit"
    assert result.cost_usd == Decimal("0.2")
    assert result.limit_wait == timedelta(seconds=420)
    assert result.session == SESSION
    assert len(read_calls(tmp_path / "bin")) == 1


def test_a_limit_error_before_any_step_ends_the_run_without_measures(tmp_path: Path) -> None:
    first = Step(stdout_before_wait=stdout(LIMIT_ERROR), wait_seconds=WAIT_SECONDS)
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == "provider_limit"
    assert result.cost_usd is None
    assert result.turns is None
    assert result.tokens is None
    assert result.session == SESSION


@pytest.mark.parametrize(
    ("status_code", "provider_limit"),
    [
        pytest.param(500, None, id="500-default-limit"),
        pytest.param(428, ProviderLimit(status=429), id="428-limit-429"),
    ],
)
def test_an_error_that_is_no_limit_does_not_stop_the_call(
    tmp_path: Path, status_code: int, provider_limit: ProviderLimit | None
) -> None:
    first = Step(
        stdout=stdout(step_start(), step_finish(), error(status_code=status_code)),
        exit_status=1,
    )
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY], provider_limit=provider_limit)

    result = runtime.run(opencode_request(tmp_path / "work"))

    assert result.end_reason == "died"
    assert len(read_calls(tmp_path / "bin")) == 1


@pytest.mark.parametrize(
    ("provider_limit", "wait_seconds", "end_reason"),
    [
        pytest.param(
            ProviderLimit(message="spend limit"), WAIT_SECONDS, "provider_limit", id="pattern"
        ),
        pytest.param(None, 0, "died", id="default-limit"),
    ],
)
def test_an_error_without_a_status_is_a_limit_when_its_message_holds_the_pattern(
    tmp_path: Path, provider_limit: ProviderLimit | None, wait_seconds: int, end_reason: str
) -> None:
    first = Step(
        stdout_before_wait=stdout(
            step_start(), step_finish(), _without_status(error("the spend limit is reached"))
        ),
        wait_seconds=wait_seconds,
        exit_status=1,
    )
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY], provider_limit=provider_limit)

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == end_reason


@pytest.mark.parametrize(
    ("line", "first", "end_reason"),
    [
        pytest.param(
            LIMIT_LINE,
            WAITING,
            "provider_limit",
            id="limit-line",
        ),
        pytest.param("HTTP 500 Internal Server Error", REPLY, "completed", id="500"),
        pytest.param("error 1428", REPLY, "completed", id="1428"),
    ],
)
def test_a_limit_line_on_standard_error_ends_the_run_at_once_without_a_wait(
    tmp_path: Path, line: str, first: Step, end_reason: str
) -> None:
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY], stderr_first=line)

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == end_reason
    assert result.limit_wait is None
    # The limit stop may come before the stand-in records its call; a completed run had one.
    assert len(read_calls(tmp_path / "bin")) <= 1


@pytest.mark.parametrize(
    "line",
    [
        pytest.param(text(f"The gateway said {LIMIT_LINE}.", 1200), id="text"),
        pytest.param(
            tool_use(tool_input={"command": "curl --fail -w 428 gateway"}, error="exit 428"),
            id="tool-use",
        ),
    ],
)
def test_a_limit_in_the_agent_s_text_or_a_tool_s_output_stops_nothing(
    tmp_path: Path, line: str
) -> None:
    reply = Step(
        stdout=stdout(step_start(), line, text(result_text("question", "Read it.")), step_finish())
    )
    runtime = stand_in_runtime(tmp_path, [reply, RESUME_REPLY])

    result = runtime.run(opencode_request(tmp_path / "work"))

    assert result.end_reason == "completed"
    assert result.decision == "question"
    assert result.entry == "Read it."
    assert len(read_calls(tmp_path / "bin")) == 1


def test_a_limit_in_the_resume_ends_the_run_by_the_limit_with_both_calls_costs(
    tmp_path: Path,
) -> None:
    resume = Step(
        stdout_before_wait=stdout(step_start(10_000), step_finish(10_500, cost=0.1), LIMIT_ERROR),
        wait_seconds=WAIT_SECONDS,
    )
    runtime = stand_in_runtime(tmp_path, [over_budget(), resume, RESUME_REPLY])

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == "provider_limit"
    assert result.cost_usd == Decimal("1.11")
    assert result.session == SESSION
    assert len(read_calls(tmp_path / "bin")) == 2  # noqa: PLR2004 - the call and its resume
