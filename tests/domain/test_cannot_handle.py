"""The error a handler raises when it cannot do its work."""

from factory.domain.errors import CannotHandle, FactoryError


def test_cannot_handle_is_a_factory_error_that_names_kind_and_reason() -> None:
    error = CannotHandle("comment", "x")

    assert isinstance(error, FactoryError)
    assert error.kind == "comment"
    assert error.reason == "x"
    assert str(error) == "cannot handle comment: x"
