"""A cost record names the instance that ran its agent run, optional when read."""

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
    ("fields", "expected"),
    [
        (STARTED, None),
        ({**STARTED, "instance": "shakedown-podman"}, "shakedown-podman"),
        ({**COMPLETED, "instance": "shakedown-podman"}, "shakedown-podman"),
        ({**STARTED, "instance": "Shakedown"}, ValidationError),
    ],
    ids=["without", "started-with", "completed-with", "not-a-name"],
)
def test_a_cost_record_carries_an_optional_instance_name(
    fields: dict[str, object], expected: str | type[ValidationError] | None
) -> None:
    model: type[BaseModel] = CostRecord

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            model(**fields)
        return
    record = model(**fields)

    assert isinstance(record, CostRecord)
    assert record.instance == expected
