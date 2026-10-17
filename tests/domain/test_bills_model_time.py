"""The model's time in bills: summed where known, a column of the cost table, not in the line."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.domain.bills import bill, bills_by_stage, cost_line, cost_table
from factory.domain.cost_records import CostRecord


def _record(run: str, stage: str, seconds: float, model_seconds: float | None) -> CostRecord:
    return CostRecord(
        run=run * 32,
        work_item="F0001-S0001",
        stage=stage,
        role="coder",
        attempt=0,
        status="completed",
        started_at=datetime(2026, 10, 17, 9, 0, tzinfo=UTC),
        duration_seconds=seconds,
        model_seconds=model_seconds,
        end_reason="completed",
    )


@pytest.fixture
def stage_records() -> list[CostRecord]:
    return [
        _record("a", "tests", 120.0, 90.0),
        _record("b", "doing", 60.0, 60.0),
        _record("c", "doing", 30.0, 30.0),
    ]


@pytest.mark.parametrize(
    ("model_seconds", "expected"),
    [
        ([30.0, None, 45.0], timedelta(seconds=75)),
        ([None, None], timedelta(0)),
        ([], timedelta(0)),
    ],
    ids=["some-known", "all-unknown", "no-records"],
)
def test_the_bill_sums_the_known_model_time(
    model_seconds: list[float | None], expected: timedelta
) -> None:
    records = [
        _record("abc"[index], "doing", 60.0, seconds) for index, seconds in enumerate(model_seconds)
    ]

    assert bill(records).model_duration == expected


def test_bills_by_stage_sums_the_model_time_per_stage(stage_records: list[CostRecord]) -> None:
    result = bills_by_stage(stage_records)

    assert [(each.stage, each.bill.model_duration) for each in result] == [
        ("tests", timedelta(seconds=90)),
        ("doing", timedelta(seconds=90)),
    ]


def test_the_cost_table_has_a_model_minutes_column(stage_records: list[CostRecord]) -> None:
    assert cost_table(bills_by_stage(stage_records)) == "\n".join(
        [
            "| stage | runs | min | model min | turns | in | cached | out | USD |",
            "| :-- | --: | --: | --: | --: | --: | --: | --: | --: |",
            "| tests | 1 | 2.0 | 1.5 | 0 | 0 | 0 | 0 | 0.00 + 1 unknown |",
            "| doing | 2 | 1.5 | 1.5 | 0 | 0 | 0 | 0 | 0.00 + 2 unknown |",
            "| **total** | 3 | 3.5 | 3.0 | 0 | 0 | 0 | 0 | 0.00 + 3 unknown |",
        ]
    )


@pytest.mark.parametrize(
    ("model_seconds", "expected"),
    [(15.0, "0.3"), (14.4, "0.2")],
    ids=["a quarter minute", "just under"],
)
def test_model_minutes_are_rounded_half_up(model_seconds: float, expected: str) -> None:
    table = cost_table(bills_by_stage([_record("a", "doing", 60.0, model_seconds)]))
    row = table.splitlines()[2]

    assert row.split(" | ")[3] == expected


def test_the_cost_line_does_not_show_the_model_time() -> None:
    with_model = bill([_record("a", "doing", 60.0, 45.0)])
    without_model = bill([_record("a", "doing", 60.0, None)])

    assert with_model.model_duration == timedelta(seconds=45)
    assert cost_line(with_model) == cost_line(without_model)
