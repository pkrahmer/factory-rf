"""Every fault of a validation error, in the rank order the readers share."""

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from factory.adapters.validation_faults import all_faults, first_fault


class _Sample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int
    name: str


def _validation_error(data: dict[str, object]) -> ValidationError:
    with pytest.raises(ValidationError) as caught:
        _Sample.model_validate(data)
    return caught.value


def test_all_faults_ranks_unknown_then_missing_then_invalid() -> None:
    error = _validation_error({"count": "many", "extra": 1})
    message = next(detail["msg"] for detail in error.errors() if detail["loc"] == ("count",))

    faults = all_faults(error, "sample")

    assert faults == ["unknown key: extra", "missing key: name", f"invalid count: {message}"]
    assert first_fault(error, "sample") == faults[0]


def test_all_faults_keeps_pydantic_order_within_one_rank() -> None:
    error = _validation_error({"count": 1, "name": "n", "second": 2, "first": 1})

    assert all_faults(error, "sample") == ["unknown key: second", "unknown key: first"]
