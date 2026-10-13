"""The error for a work item file that cannot be read."""

from factory.domain.errors import FactoryError, WorkItemFormatError


def test_a_format_error_names_its_path_and_fault() -> None:
    error = WorkItemFormatError("bad key", "a/b.md")

    assert error.fault == "bad key"
    assert error.path == "a/b.md"
    assert str(error) == "a/b.md: bad key"


def test_a_format_error_without_a_path_is_its_fault() -> None:
    error = WorkItemFormatError("bad key")

    assert error.path is None
    assert str(error) == "bad key"
    assert issubclass(WorkItemFormatError, FactoryError)
