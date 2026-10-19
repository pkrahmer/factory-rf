"""A completed cost record keeps the login its run was handed; a started one has none."""

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
        pytest.param({**COMPLETED, "login": "api_key"}, "api_key", id="completed-api-key"),
        pytest.param(COMPLETED, None, id="completed-none"),
        pytest.param({**STARTED, "login": "api_key"}, ValidationError, id="started-login"),
    ],
)
def test_only_a_completed_record_keeps_a_login(
    fields: dict[str, object], expected: str | type[ValidationError] | None
) -> None:
    model: type[BaseModel] = CostRecord

    if expected is ValidationError:
        with pytest.raises(ValidationError, match="a started record has no login"):
            model(**fields)
        return
    record = model(**fields)

    assert isinstance(record, CostRecord)
    assert record.login == expected
    assert list(CostRecord.model_fields)[-1] == "login"
