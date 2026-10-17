"""The model's time in a cost record: unknown in a started record, a finite non-negative number."""

from datetime import UTC, datetime
from typing import Literal

import pytest
from pydantic import ValidationError

from factory.domain.cost_records import CostRecord


def _record(status: Literal["started", "completed"], model_seconds: float | None) -> CostRecord:
    completed = status == "completed"
    return CostRecord(
        run="a" * 32,
        work_item="F0001-S0001",
        stage="doing",
        role="coder",
        attempt=0,
        status=status,
        started_at=datetime(2026, 10, 17, 9, 0, tzinfo=UTC),
        duration_seconds=60.0 if completed else None,
        model_seconds=model_seconds,
        end_reason="completed" if completed else None,
    )


@pytest.mark.parametrize(
    ("status", "model_seconds", "accepted"),
    [
        ("started", 1.0, False),
        ("completed", None, True),
        ("completed", 0, True),
        ("completed", 41.5, True),
        ("completed", -1, False),
        ("completed", float("nan"), False),
    ],
    ids=["started", "completed-unknown", "completed-zero", "completed", "negative", "nan"],
)
def test_model_seconds_only_in_a_completed_record_and_never_negative_or_nan(
    status: Literal["started", "completed"], model_seconds: float | None, accepted: bool
) -> None:
    if accepted:
        assert _record(status, model_seconds).model_seconds == model_seconds
    else:
        with pytest.raises(ValidationError):
            _record(status, model_seconds)
