"""The cost record of one agent run: its fields, the started and completed rules and `ok`."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord

STARTED_AT = datetime(2026, 10, 12, 8, 30, tzinfo=UTC)
BASE: dict[str, object] = {
    "run": "a" * 32,
    "work_item": "F0002-S0007",
    "stage": "tests",
    "role": "tester",
    "attempt": 0,
    "started_at": STARTED_AT,
}
STARTED: dict[str, object] = {**BASE, "status": "started"}
COMPLETED: dict[str, object] = {
    **BASE,
    "status": "completed",
    "duration_seconds": 41.0,
    "end_reason": "completed",
}


def _record(fields: dict[str, object]) -> CostRecord:
    return CostRecord.model_validate(fields)


def test_a_started_record_has_no_measures() -> None:
    record = CostRecord(
        run="a" * 32,
        work_item="F0002-S0007",
        stage="tests",
        role="tester",
        attempt=0,
        status="started",
        started_at=STARTED_AT,
    )

    assert record.duration_seconds is None
    assert record.end_reason is None
    assert record.turns is None
    assert record.tokens is None
    assert record.cost_usd is None
    assert record.image is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("duration_seconds", 1.0),
        ("end_reason", "completed"),
        ("turns", 1),
        ("tokens", TokenCounts(input=1, output=1)),
        ("cost_usd", Decimal("0.1")),
    ],
)
def test_a_started_record_with_a_measure_is_refused_as_a_whole(field: str, value: object) -> None:
    with pytest.raises(ValidationError) as caught:
        _record({**STARTED, field: value})

    assert [error["loc"] for error in caught.value.errors()] == [()]


@pytest.mark.parametrize("missing", ["duration_seconds", "end_reason"])
def test_a_completed_record_needs_duration_and_end_reason(missing: str) -> None:
    fields = {key: value for key, value in COMPLETED.items() if key != missing}

    with pytest.raises(ValidationError):
        _record(fields)


def test_a_completed_record_may_leave_turns_tokens_and_cost_unknown() -> None:
    record = _record({**COMPLETED, "turns": None, "tokens": None, "cost_usd": None})

    assert record.turns is None
    assert record.tokens is None
    assert record.cost_usd is None


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        ("run", "a" * 32, True),
        ("run", "a" * 31, False),
        ("run", "a" * 33, False),
        ("run", "A" + "a" * 31, False),
        ("attempt", 0, True),
        ("attempt", -1, False),
        ("duration_seconds", 0.0, True),
        ("duration_seconds", -0.1, False),
        ("duration_seconds", float("inf"), False),
        ("duration_seconds", float("nan"), False),
        ("turns", 0, True),
        ("turns", -1, False),
        ("started_at", datetime(2026, 10, 12, 8, 30), False),
        ("work_item", "F0002-X0001", False),
        ("stage", "Tests", False),
        ("role", "Tester", False),
    ],
)
def test_record_fields_keep_their_limits(field: str, value: object, accepted: bool) -> None:
    fields = {**COMPLETED, field: value}

    if accepted:
        assert getattr(_record(fields), field) == value
    else:
        with pytest.raises(ValidationError):
            _record(fields)


def test_started_at_is_stored_in_utc() -> None:
    east = datetime(2026, 10, 12, 10, 30, tzinfo=timezone(timedelta(hours=2)))

    record = _record({**STARTED, "started_at": east})

    assert record.started_at == STARTED_AT
    assert record.started_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("status", "end_reason", "ok"),
    [
        ("completed", "completed", True),
        ("completed", "no_result", False),
        ("completed", "time_limit", False),
        ("completed", "budget", False),
        ("completed", "died", False),
        ("started", None, False),
    ],
)
def test_ok_only_for_a_run_that_completed(status: str, end_reason: str | None, ok: bool) -> None:
    fields: dict[str, object] = {**BASE, "status": status}
    if end_reason is not None:
        fields = {**fields, "duration_seconds": 1.0, "end_reason": end_reason}

    assert _record(fields).ok is ok


def test_a_record_is_frozen_and_refuses_unknown_fields() -> None:
    record = _record(COMPLETED)
    model: type[BaseModel] = CostRecord
    field = "turns"

    with pytest.raises(ValidationError):
        model(**COMPLETED, unknown=1)
    with pytest.raises(ValidationError):
        setattr(record, field, 3)


@pytest.mark.parametrize(
    ("cost", "accepted"),
    [
        (Decimal("0"), True),
        (Decimal("0.3450"), True),
        (Decimal("-0.01"), False),
        (Decimal("NaN"), False),
        (Decimal("Infinity"), False),
    ],
)
def test_a_cost_is_finite_and_not_negative(cost: Decimal, accepted: bool) -> None:
    fields = {**COMPLETED, "cost_usd": cost}

    if accepted:
        assert _record(fields).cost_usd == cost
    else:
        with pytest.raises(ValidationError):
            _record(fields)
