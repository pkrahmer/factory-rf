"""The error for a cost record file that cannot be read."""

from factory.domain.errors import CostRecordFormatError, FactoryError


def test_a_cost_record_format_error_names_its_line_and_fault() -> None:
    error = CostRecordFormatError(3, "not valid JSON")

    assert error.line == 3
    assert error.fault == "not valid JSON"
    assert str(error) == "line 3: not valid JSON"
    assert isinstance(error, FactoryError)
