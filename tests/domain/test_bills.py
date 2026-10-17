"""Bills: sums of the cost records, unknown values skipped, and their line and table texts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from factory.domain.agent_runs import EndReason, TokenCounts
from factory.domain.bills import Bill, StageBill, bill, bills_by_stage, cost_line, cost_table
from factory.domain.cost_records import CostRecord

ZERO_TOKENS = TokenCounts(input=0, output=0)


def _record(
    run: str,
    stage: str,
    seconds: float,
    reason: EndReason,
    *,
    turns: int | None,
    tokens: TokenCounts | None,
    cost: Decimal | None,
) -> CostRecord:
    return CostRecord(
        run=run * 32,
        work_item="F0001-S0001",
        stage=stage,
        role="coder",
        attempt=0,
        status="completed",
        started_at=datetime(2026, 10, 12, 9, 0, tzinfo=UTC),
        duration_seconds=seconds,
        end_reason=reason,
        turns=turns,
        tokens=tokens,
        cost_usd=cost,
    )


def _demo() -> list[CostRecord]:
    return [
        _record(
            "a",
            "tests",
            60.0,
            "completed",
            turns=7,
            tokens=TokenCounts(input=12, output=300, cache_read=1000, cache_creation=50),
            cost=Decimal("0.345"),
        ),
        _record("b", "doing", 120.0, "died", turns=None, tokens=None, cost=None),
        _record(
            "c",
            "doing",
            30.0,
            "completed",
            turns=5,
            tokens=TokenCounts(input=10, output=100, cache_read=500),
            cost=Decimal("1.2"),
        ),
    ]


def _bill(**changes: object) -> Bill:
    fields: dict[str, object] = {
        "runs": 1,
        "runs_cost_unknown": 0,
        "duration": timedelta(0),
        "turns": 0,
        "tokens": ZERO_TOKENS,
        "cost_usd": Decimal("0"),
    }
    fields.update(changes)
    return Bill.model_validate(fields)


def test_the_bill_of_the_demo_records_sums_every_known_value() -> None:
    result = bill(_demo())

    assert result.runs == 3
    assert result.runs_cost_unknown == 1
    assert result.duration == timedelta(seconds=210)
    assert result.turns == 12
    assert result.tokens == TokenCounts(input=22, output=400, cache_read=1500, cache_creation=50)
    assert result.cost_usd == Decimal("1.545")


def test_the_bill_of_no_records_is_all_zero() -> None:
    result = bill([])

    assert result.runs == 0
    assert result.runs_cost_unknown == 0
    assert result.duration == timedelta(0)
    assert result.turns == 0
    assert result.tokens == ZERO_TOKENS
    assert result.cost_usd == Decimal("0")


@pytest.mark.parametrize("reason", ["died", "time_limit", "budget"])
def test_a_failed_run_counts_in_runs_and_duration(reason: EndReason) -> None:
    records = [
        _record("a", "doing", 30.0, "completed", turns=2, tokens=ZERO_TOKENS, cost=Decimal("0.5")),
        _record("b", "doing", 45.0, reason, turns=1, tokens=ZERO_TOKENS, cost=Decimal("0.25")),
    ]

    result = bill(records)

    assert result.runs == 2
    assert result.duration == timedelta(seconds=75)


def test_an_unknown_cost_turns_or_tokens_is_skipped_never_zero() -> None:
    tokens = TokenCounts(input=3, output=4, cache_read=5, cache_creation=6)
    records = [
        _record("a", "doing", 10.0, "completed", turns=3, tokens=tokens, cost=Decimal("1.5")),
        _record("b", "doing", 20.0, "completed", turns=None, tokens=None, cost=None),
    ]

    result = bill(records)

    assert result.runs == 2
    assert result.runs_cost_unknown == 1
    assert result.cost_usd == Decimal("1.5")
    assert result.turns == 3
    assert result.tokens == tokens


def test_bills_by_stage_groups_in_first_order_and_a_returning_stage_joins_its_first_group() -> None:
    first = _record("a", "doing", 10.0, "completed", turns=1, tokens=ZERO_TOKENS, cost=Decimal("1"))
    review = _record(
        "b", "review", 20.0, "completed", turns=2, tokens=ZERO_TOKENS, cost=Decimal("2")
    )
    again = _record("c", "doing", 30.0, "completed", turns=3, tokens=ZERO_TOKENS, cost=Decimal("3"))

    result = bills_by_stage([first, review, again])

    assert result == [
        StageBill(stage="doing", bill=bill([first, again])),
        StageBill(stage="review", bill=bill([review])),
    ]
    assert result[0].bill.runs == 2


def test_the_cost_line_of_the_demo_bill() -> None:
    result = bill(_demo())

    assert cost_line(result) == (
        "3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown"
    )
    assert cost_line(result.model_copy(update={"runs_cost_unknown": 0})) == (
        "3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55"
    )


def test_minutes_and_dollars_round_half_up() -> None:
    result = _bill(duration=timedelta(seconds=3), cost_usd=Decimal("0.125"))

    assert cost_line(result) == (
        "1 runs, 0.1 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.13"
    )


def test_the_cost_table_of_the_demo_stage_bills() -> None:
    assert cost_table(bills_by_stage(_demo())) == "\n".join(
        [
            "| stage | runs | min | model min | turns | in | cached | out | USD |",
            "| :-- | --: | --: | --: | --: | --: | --: | --: | --: |",
            "| tests | 1 | 1.0 | 0.0 | 7 | 62 | 1000 | 300 | 0.35 |",
            "| doing | 2 | 2.5 | 0.0 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |",
            "| **total** | 3 | 3.5 | 0.0 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |",
        ]
    )


@pytest.mark.parametrize("field", ["runs", "runs_cost_unknown", "turns"])
def test_a_bill_count_of_zero_is_accepted(field: str) -> None:
    assert getattr(_bill(**{field: 0}), field) == 0


@pytest.mark.parametrize("field", ["runs", "runs_cost_unknown", "turns"])
def test_a_negative_bill_count_is_refused(field: str) -> None:
    with pytest.raises(ValidationError):
        _bill(**{field: -1})
