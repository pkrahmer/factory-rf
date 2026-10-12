"""The root of the factory's error hierarchy."""

from factory.domain.errors import FactoryError


def test_factory_error_is_an_exception_with_its_message() -> None:
    assert issubclass(FactoryError, Exception)
    assert str(FactoryError("x")) == "x"
