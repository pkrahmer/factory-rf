"""The record of one run of a project command and the values it refuses."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.command_records import CommandRecord

VALID: dict[str, object] = {
    "command": "check",
    "commit": None,
    "started_at": datetime(2026, 10, 17, 9, 0, tzinfo=UTC),
    "duration_seconds": 0,
    "status": "time_limit",
    "exit_status": None,
}


@pytest.mark.parametrize(
    ("changes", "accepted"),
    [
        ({}, True),
        ({"commit": "a" * 40, "status": "passed", "exit_status": 0}, True),
        ({"commit": "a" * 39}, False),
        ({"commit": "a" * 41}, False),
        ({"commit": "A" * 40}, False),
        ({"commit": "g" * 40}, False),
        ({"command": "Check"}, False),
        ({"duration_seconds": -1}, False),
        ({"duration_seconds": float("inf")}, False),
        ({"status": "red"}, False),
        ({"started_at": datetime(2026, 10, 17, 9, 0)}, False),  # noqa: DTZ001
    ],
)
def test_a_command_record_accepts_valid_values_and_refuses_the_others(
    changes: dict[str, object], *, accepted: bool
) -> None:
    model: type[BaseModel] = CommandRecord
    values = {**VALID, **changes}

    if accepted:
        record = model(**values)
        assert record.model_dump(exclude={"targets", "started_at"}) == {
            key: value for key, value in values.items() if key != "started_at"
        }
    else:
        with pytest.raises(ValidationError):
            model(**values)
