"""The opencode runtime reads its measures, refusals and end reason from the JSON events."""

import json
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step
from adapters.opencode_stand_in import (
    MODELS,
    opencode_request,
    result_text,
    stdout,
    step_finish,
    step_start,
    text,
    tool_use,
    write_opencode,
)
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.agent_runs import AgentRunResult, PermissionDenial, TokenCounts
from factory.domain.cost_records import CostRecord
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

SIDECAR = "F0001-S0001-first.costs.jsonl"
ANSWER = text(result_text())
FIRST_TOKENS = {"input": 10, "output": 5, "reasoning": 2, "cache": {"read": 100, "write": 20}}
SECOND_TOKENS = {"input": 20, "output": 6, "reasoning": 0, "cache": {"read": 0, "write": 5}}
WAIT_SECONDS = 30


def _run(tmp_path: Path, lines: list[str], *, exit_status: int = 0) -> AgentRunResult:
    executable = write_opencode(
        tmp_path / "bin", [Step(stdout=stdout(*lines), exit_status=exit_status)]
    )
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    runtime = OpencodeRuntime(str(executable), state, models=MODELS)
    return runtime.run(opencode_request(tmp_path / "work"))


@pytest.mark.parametrize(
    ("lines", "cost", "tokens", "turns"),
    [
        pytest.param(
            [
                step_start(1000),
                step_finish(2000, cost=0.012, tokens=FIRST_TOKENS),
                step_start(3000),
                ANSWER,
                step_finish(4000, cost=0.03, tokens=SECOND_TOKENS),
            ],
            Decimal("0.042"),
            TokenCounts(input=30, output=13, cache_read=100, cache_creation=25),
            2,
            id="two-steps",
        ),
        pytest.param(
            [step_start(1000), ANSWER, step_finish(2000, tokens={"input": 10, "output": 5})],
            Decimal("0.012"),
            TokenCounts(input=10, output=5, cache_read=0, cache_creation=0),
            1,
            id="no-reasoning-no-cache",
        ),
    ],
)
def test_cost_tokens_and_turns_are_summed_over_the_finished_steps(
    tmp_path: Path, lines: list[str], cost: Decimal, tokens: TokenCounts, turns: int
) -> None:
    result = _run(tmp_path, lines)

    assert (result.cost_usd, result.tokens, result.turns) == (cost, tokens, turns)


@pytest.mark.parametrize(
    ("lines", "model_seconds", "turns"),
    [
        pytest.param(
            [
                step_start(1000),
                tool_use(1500, start=1200, end=1700),
                step_finish(2000),
                step_start(3000),
                ANSWER,
                step_finish(3400),
            ],
            0.9,
            2,
            id="tool-time-left-out",
        ),
        pytest.param(
            [step_start(1000), tool_use(1500, start=1000, end=1800), ANSWER, step_finish(1500)],
            0,
            1,
            id="tools-exceed-the-step",
        ),
        pytest.param(
            [step_finish(500), step_start(1000), ANSWER, step_finish(1400)],
            0.4,
            2,
            id="finish-without-start",
        ),
        pytest.param(
            [step_start(1000), tool_use(1500, start=5000, end=5300), ANSWER, step_finish(2000)],
            0.7,
            1,
            id="tool-between-by-line-order",
        ),
        pytest.param(
            [step_start(1000), ANSWER, step_finish(2000), tool_use(2500, start=1200, end=1700)],
            1,
            1,
            id="tool-after-the-finish-line",
        ),
    ],
)
def test_the_model_time_is_each_step_less_its_tool_calls_summed(
    tmp_path: Path, lines: list[str], model_seconds: float, turns: int
) -> None:
    result = _run(tmp_path, lines)

    assert result.model_duration == timedelta(seconds=model_seconds)
    assert result.turns == turns


@pytest.mark.parametrize(
    ("tool_line", "denials"),
    [
        pytest.param(
            tool_use(error="permission denied by rule git push*"),
            [PermissionDenial(tool="bash", detail='{"command": "git push"}')],
            id="permission",
        ),
        pytest.param(
            tool_use(
                tool_input={"description": "clean", "command": "rm -rf *"},
                error="Denied: rm -rf *",
            ),
            [
                PermissionDenial(
                    tool="bash", detail='{"command": "rm -rf *", "description": "clean"}'
                )
            ],
            id="denied",
        ),
        pytest.param(tool_use(tool="read", error="file not found"), [], id="other-error"),
        pytest.param(tool_use(status="completed", error=None), [], id="completed"),
    ],
)
def test_a_tool_call_refused_by_permission_is_a_denial_with_its_sorted_input(
    tmp_path: Path, tool_line: str, denials: list[PermissionDenial]
) -> None:
    result = _run(tmp_path, [step_start(), tool_line, ANSWER, step_finish()])

    assert result.permission_denials == denials


@pytest.mark.parametrize(
    ("tool", "tool_input", "path"),
    [
        ("write", {"filePath": "/work/src/a.py", "content": "x"}, "/work/src/a.py"),
        (
            "edit",
            {"filePath": "/work/src/a.py", "oldString": "a", "newString": "b"},
            "/work/src/a.py",
        ),
        ("bash", {"command": "git push"}, None),
        ("write", "/work/src/a.py", None),
        ("write", {"filePath": 3, "content": "x"}, None),
        ("write", {"file_path": "/work/src/a.py", "content": "x"}, None),
    ],
    ids=["write", "edit", "bash", "input-no-object", "file-path-no-string", "file-path-snake"],
)
def test_a_denial_names_the_file_path_of_its_call(
    tmp_path: Path, tool: str, tool_input: object, path: str | None
) -> None:
    refused = tool_use(tool=tool, tool_input=tool_input, error="permission denied")

    result = _run(tmp_path, [step_start(), refused, ANSWER, step_finish()])

    detail = json.dumps(tool_input, sort_keys=True)
    assert result.permission_denials == [PermissionDenial(tool=tool, detail=detail, path=path)]


def test_two_refused_calls_on_one_file_record_it_once_in_the_cost_record(
    tmp_path: Path, boundaries: Boundaries
) -> None:
    refused = tool_use(
        tool="write", tool_input={"filePath": "/work/src/a.py", "content": "x"}, error="denied"
    )
    result = _run(tmp_path, [step_start(), refused, refused, ANSWER, step_finish()])
    started = CostRecord(
        run="a" * 32,
        work_item="F0001-S0001",
        stage="doing",
        role="coder",
        attempt=0,
        status="started",
        started_at=datetime(2026, 10, 19, 9, 0, tzinfo=UTC),
    )
    run = CostRun(path=SIDECAR, run=started.run, records=[started])

    completed = CostRecorder(boundaries).complete(run, result)

    assert completed.records[-1].denied_paths == ["/work/src/a.py"]


def _negative_input() -> dict[str, object]:
    return {**FIRST_TOKENS, "input": -1}


@pytest.mark.parametrize(
    "skipped",
    [
        pytest.param("not json", id="no-json"),
        pytest.param(json.dumps({"timestamp": 1, "part": {"type": "text"}}), id="no-type"),
        pytest.param(json.dumps({"type": "step_middle", "timestamp": 1}), id="unknown-type"),
        pytest.param(step_finish(2500, cost=-0.5), id="negative-cost"),
        pytest.param(step_finish(2500, cost=None), id="no-cost"),
        pytest.param(step_finish(-1), id="negative-timestamp"),
        pytest.param(step_finish(2500, tokens=_negative_input()), id="negative-input"),
        pytest.param(step_finish(2500, tokens=None), id="no-tokens"),
        pytest.param(
            step_finish(2500, tokens={"input": 10, "reasoning": 2}), id="tokens-without-output"
        ),
    ],
)
def test_a_line_that_does_not_validate_is_skipped(tmp_path: Path, skipped: str) -> None:
    result = _run(tmp_path, [step_start(1000), ANSWER, step_finish(2000), skipped])

    assert (result.end_reason, result.cost_usd, result.turns) == ("completed", Decimal("0.012"), 1)
    assert result.tokens == TokenCounts(input=10, output=7, cache_read=100, cache_creation=20)
    assert result.model_duration == timedelta(seconds=1)


@pytest.mark.parametrize(
    ("lines", "cost", "input_tokens", "model_seconds"),
    [
        pytest.param(
            [step_start(1000), ANSWER, step_finish(2000, cost=0)],
            Decimal("0"),
            10,
            1,
            id="zero-cost",
        ),
        pytest.param(
            [step_start(1000), ANSWER, step_finish(2000, tokens={**FIRST_TOKENS, "input": 0})],
            Decimal("0.012"),
            0,
            1,
            id="zero-input",
        ),
        pytest.param(
            [step_start(0), ANSWER, step_finish(0)], Decimal("0.012"), 10, 0, id="zero-timestamp"
        ),
        pytest.param(
            [
                step_start(0),
                ANSWER,
                step_finish(0, cost=0, tokens={**FIRST_TOKENS, "input": 0}),
            ],
            Decimal("0"),
            0,
            0,
            id="all-zero",
        ),
    ],
)
def test_a_step_with_zero_values_is_a_valid_step(
    tmp_path: Path, lines: list[str], cost: Decimal, input_tokens: int, model_seconds: float
) -> None:
    result = _run(tmp_path, lines)

    assert result.turns == 1
    assert result.cost_usd == cost
    assert result.tokens is not None
    assert result.tokens.input == input_tokens
    assert result.model_duration == timedelta(seconds=model_seconds)


@pytest.mark.parametrize(
    ("lines", "exit_status", "end_reason", "answer", "measured"),
    [
        pytest.param(
            [step_start(), ANSWER, step_finish()],
            0,
            "completed",
            ("doing", "Built it."),
            True,
            id="completed",
        ),
        pytest.param(
            [step_start(), text(result_text("review")), step_finish()],
            0,
            "no_result",
            (None, None),
            True,
            id="decision-not-allowed",
        ),
        pytest.param(
            [step_start(), ANSWER, step_finish()], 1, "died", (None, None), True, id="exit-1"
        ),
        pytest.param([step_start(), ANSWER], 0, "died", (None, None), False, id="no-step-finish"),
    ],
)
def test_the_end_reason_follows_the_exit_the_steps_and_the_block(
    tmp_path: Path,
    lines: list[str],
    exit_status: int,
    end_reason: str,
    answer: tuple[str | None, str | None],
    *,
    measured: bool,
) -> None:
    result = _run(tmp_path, lines, exit_status=exit_status)

    assert (result.end_reason, result.decision, result.entry) == (end_reason, *answer)
    measures = (result.cost_usd, result.tokens, result.turns, result.model_duration)
    if measured:
        assert measures == (
            Decimal("0.012"),
            TokenCounts(input=10, output=7, cache_read=100, cache_creation=20),
            1,
            timedelta(seconds=1),
        )
    else:
        assert measures == (None, None, None, None)


def test_a_call_past_its_time_limit_ends_by_time_limit_without_measures(tmp_path: Path) -> None:
    played = Step(
        stdout_before_wait=stdout(step_start(), ANSWER, step_finish()), wait_seconds=WAIT_SECONDS
    )
    executable = write_opencode(tmp_path / "bin", [played])
    state = tmp_path / "state"
    state.mkdir()
    runtime = OpencodeRuntime(str(executable), state, models=MODELS)
    request = opencode_request(tmp_path / "work", time_limit=ROOMY_LIMIT)
    started = time.monotonic()

    result = runtime.run(request)

    assert time.monotonic() - started < ROOMY_BOUND_SECONDS
    assert (result.end_reason, result.decision, result.entry) == ("time_limit", None, None)
    assert (result.cost_usd, result.tokens, result.turns, result.model_duration) == (
        None,
        None,
        None,
        None,
    )
