"""The machine's measures on a cost record: only on a completed one, each field in its range."""

import math

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.cost_records import CostRecord, MachineMeasures

BASE: dict[str, object] = {
    "run": "a" * 32,
    "work_item": "F0002-S0007",
    "stage": "tests",
    "role": "tester",
    "attempt": 0,
    "started_at": "2026-11-04T08:30:00Z",
}
COMPLETED: dict[str, object] = {
    **BASE,
    "status": "completed",
    "duration_seconds": 41.0,
    "end_reason": "completed",
}
STARTED: dict[str, object] = {**BASE, "status": "started"}
INTEGER_FIELDS = [
    "base_image_bytes",
    "project_layer_bytes",
    "store_free_bytes",
    "dataset_free_bytes",
    "memory_peak_since_boot_bytes",
    "memory_total_bytes",
]
FLOAT_FIELDS = ["cpu_seconds", "cpu_wait_seconds", "memory_wait_seconds"]
LARGE_BYTES = 16_000_000_000_000
LARGE_SECONDS = 1_000_000.25


def _all_nine() -> MachineMeasures:
    return MachineMeasures(
        base_image_bytes=1_580_000_000,
        project_layer_bytes=420_000_000,
        store_free_bytes=30_000_000_000,
        dataset_free_bytes=12_000_000_000,
        memory_peak_since_boot_bytes=8_100_000_000,
        memory_total_bytes=15_600_000_000,
        cpu_seconds=123.5,
        cpu_wait_seconds=0.75,
        memory_wait_seconds=0.0,
    )


def test_a_completed_record_carries_the_machine_with_its_nine_fields() -> None:
    machine = _all_nine()

    record = CostRecord.model_validate({**COMPLETED, "machine": machine})
    again = CostRecord.model_validate_json(record.model_dump_json())

    assert record.machine == machine
    assert again.machine == machine
    assert set(MachineMeasures.model_fields) == {*INTEGER_FIELDS, *FLOAT_FIELDS}
    assert MachineMeasures() == MachineMeasures(**dict.fromkeys(MachineMeasures.model_fields))
    assert CostRecord.model_validate(COMPLETED).machine is None


def test_a_started_record_with_the_machine_is_refused() -> None:
    with pytest.raises(ValidationError, match="machine"):
        CostRecord.model_validate({**STARTED, "machine": _all_nine()})


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        *[
            row
            for field in INTEGER_FIELDS
            for row in (
                pytest.param(field, 0, True, id=f"{field}-zero"),
                pytest.param(field, LARGE_BYTES, True, id=f"{field}-large"),
                pytest.param(field, -1, False, id=f"{field}-minus-one"),
            )
        ],
        *[
            row
            for field in FLOAT_FIELDS
            for row in (
                pytest.param(field, 0.0, True, id=f"{field}-zero"),
                pytest.param(field, LARGE_SECONDS, True, id=f"{field}-large"),
                pytest.param(field, -0.5, False, id=f"{field}-minus-half"),
                pytest.param(field, math.nan, False, id=f"{field}-nan"),
            )
        ],
    ],
)
def test_a_machine_measure_is_accepted_only_in_its_range(
    field: str, value: object, accepted: bool
) -> None:
    model: type[BaseModel] = MachineMeasures
    if accepted:
        measures = model(**{field: value})
        assert getattr(measures, field) == value
    else:
        with pytest.raises(ValidationError, match=field):
            model(**{field: value})
