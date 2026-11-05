"""A tool's summary in a cost record: its name's form, its counts and its seconds."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from factory.watching.domain.cost_records import CostRecord, ToolUse

STARTED_AT = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
BASH = ToolUse(tool="Bash", calls=1, failed=0, seconds=1.5)


@pytest.mark.parametrize(
    ("calls", "failed", "accepted"),
    [
        pytest.param(3, 3, True, id="failed-equal-to-calls"),
        pytest.param(3, 4, False, id="failed-above-calls"),
        pytest.param(0, 0, True, id="no-call"),
        pytest.param(-1, 0, False, id="negative-calls"),
        pytest.param(1, -1, False, id="negative-failed"),
    ],
)
def test_failed_calls_never_exceed_the_calls(*, calls: int, failed: int, accepted: bool) -> None:
    if accepted:
        assert ToolUse(tool="Bash", calls=calls, failed=failed, seconds=None).failed == failed
    else:
        with pytest.raises(ValidationError):
            ToolUse(tool="Bash", calls=calls, failed=failed, seconds=None)


@pytest.mark.parametrize(
    ("seconds", "accepted"),
    [
        pytest.param(0.0, True, id="zero"),
        pytest.param(2.5, True, id="positive"),
        pytest.param(None, True, id="no-times"),
        pytest.param(-1.0, False, id="negative"),
        pytest.param(float("nan"), False, id="nan"),
        pytest.param(float("inf"), False, id="infinity"),
    ],
)
def test_seconds_are_a_non_negative_finite_number_or_none(
    *, seconds: float | None, accepted: bool
) -> None:
    if accepted:
        assert ToolUse(tool="Bash", calls=1, failed=0, seconds=seconds).seconds == seconds
    else:
        with pytest.raises(ValidationError):
            ToolUse(tool="Bash", calls=1, failed=0, seconds=seconds)


@pytest.mark.parametrize(
    ("tool", "accepted"),
    [
        pytest.param("a" * 64, True, id="64-characters"),
        pytest.param("a" * 65, False, id="65-characters"),
        pytest.param("mcp__files:read-v1.2", True, id="underscore-colon-dash-dot"),
        pytest.param("Bash", True, id="letters"),
        pytest.param("run tests", False, id="space"),
        pytest.param("files/read", False, id="slash"),
    ],
)
def test_a_tool_name_outside_the_form_is_refused_by_the_model(*, tool: str, accepted: bool) -> None:
    if accepted:
        assert ToolUse(tool=tool, calls=1, failed=0, seconds=None).tool == tool
    else:
        with pytest.raises(ValidationError):
            ToolUse(tool=tool, calls=1, failed=0, seconds=None)


@pytest.mark.parametrize(
    ("status", "tools", "accepted"),
    [
        pytest.param("started", None, True, id="started-without-tools"),
        pytest.param("started", [], False, id="started-with-no-tool"),
        pytest.param("started", [BASH], False, id="started-with-tools"),
        pytest.param("completed", [BASH], True, id="completed-with-tools"),
        pytest.param("completed", [], True, id="completed-with-no-tool"),
        pytest.param("completed", None, True, id="completed-unread"),
    ],
)
def test_a_started_record_carries_no_tools(
    *, status: str, tools: list[ToolUse] | None, accepted: bool
) -> None:
    measures: dict[str, object] = {}
    if status == "completed":
        measures = {"duration_seconds": 5.0, "end_reason": "completed"}

    def record() -> CostRecord:
        return CostRecord.model_validate(
            {
                "run": "a" * 32,
                "work_item": "F0001-S0001",
                "stage": "tests",
                "role": "tester",
                "attempt": 0,
                "status": status,
                "started_at": STARTED_AT,
                "tools": tools,
                **measures,
            }
        )

    if accepted:
        assert record().tools == tools
    else:
        with pytest.raises(ValidationError, match="tools"):
            record()
