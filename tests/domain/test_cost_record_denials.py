"""A completed cost record counts the refused tool calls and the files they named."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.cost_records import CostRecord

STARTED: dict[str, object] = {
    "run": "a" * 32,
    "work_item": "F0002-S0007",
    "stage": "tests",
    "role": "tester",
    "attempt": 0,
    "status": "started",
    "started_at": datetime(2026, 10, 12, 8, 30, tzinfo=UTC),
}
COMPLETED: dict[str, object] = {
    **STARTED,
    "status": "completed",
    "duration_seconds": 41.0,
    "end_reason": "completed",
}


@pytest.mark.parametrize(
    ("fields", "accepted"),
    [
        ({**COMPLETED, "denials": 0}, True),
        ({**COMPLETED, "denials": 2, "denied_paths": ["src/a.py"]}, True),
        ({**COMPLETED, "denials": -1}, False),
        ({**STARTED, "denials": 0}, False),
        ({**STARTED, "denied_paths": []}, False),
    ],
    ids=["completed-zero", "completed-two-paths", "negative", "started-denials", "started-paths"],
)
def test_only_a_completed_record_carries_a_non_negative_denial_count_and_paths(
    fields: dict[str, object], accepted: bool
) -> None:
    model: type[BaseModel] = CostRecord

    if not accepted:
        with pytest.raises(ValidationError):
            model(**fields)
        return
    record = model(**fields)

    assert isinstance(record, CostRecord)
    assert record.denials == fields["denials"]
    assert record.denied_paths == fields.get("denied_paths")
