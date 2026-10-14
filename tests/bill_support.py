"""Helpers for bill tests: completed cost records and the text of their sidecar."""

from datetime import UTC, datetime
from decimal import Decimal

from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord

STAGES = ("tests", "doing", "review")


def completed_records(work_item: str, count: int) -> list[CostRecord]:
    """`count` completed records of `work_item`, each its own run, stage and figures."""
    return [
        CostRecord(
            run="abcdef"[number] * 32,
            work_item=work_item,
            stage=STAGES[number % len(STAGES)],
            role="coder",
            attempt=0,
            status="completed",
            started_at=datetime(2026, 10, 12, 9, number, tzinfo=UTC),
            duration_seconds=60.0 * (number + 1),
            end_reason="completed",
            turns=number + 1,
            tokens=TokenCounts(input=10 * (number + 1), output=100),
            cost_usd=Decimal("0.5") * (number + 1),
        )
        for number in range(count)
    ]


def sidecar_text(records: list[CostRecord]) -> str:
    """The sidecar file's text of `records`."""
    return JsonLinesCostRecordWriter().render(records)
