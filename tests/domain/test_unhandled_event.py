"""The error of an event kind that has no handler."""

from factory.domain.errors import FactoryError, UnhandledEvent


def test_an_unhandled_event_is_a_factory_error_that_names_its_kind() -> None:
    error = UnhandledEvent("merged")

    assert isinstance(error, FactoryError)
    assert error.kind == "merged"
    assert str(error) == "no handler for event kind merged"
