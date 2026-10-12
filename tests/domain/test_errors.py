"""The root of the factory's error hierarchy."""

from factory.domain.errors import BoundaryError, FactoryError, HostingServiceError


def test_factory_error_is_an_exception_with_its_message() -> None:
    assert issubclass(FactoryError, Exception)
    assert str(FactoryError("x")) == "x"


def test_hosting_service_error_carries_operation_detail_and_message() -> None:
    error = HostingServiceError("post_comment", "403 forbidden")

    assert error.operation == "post_comment"
    assert error.detail == "403 forbidden"
    assert str(error) == "hosting service post_comment failed: 403 forbidden"
    assert isinstance(error, BoundaryError)
    assert issubclass(HostingServiceError, BoundaryError)
    assert issubclass(HostingServiceError, FactoryError)
    assert issubclass(BoundaryError, FactoryError)
