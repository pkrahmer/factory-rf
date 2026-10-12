"""The root of the factory's error hierarchy."""

from factory.domain.errors import (
    BoundaryError,
    FactoryError,
    FetchFailed,
    GitError,
    HostingServiceError,
)


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


def test_git_error_carries_command_status_and_tail_in_its_message() -> None:
    error = GitError("git fetch --prune origin", 128, "fatal: x")
    without_status = GitError("git fetch --prune origin", None, "time limit reached")

    assert error.command == "git fetch --prune origin"
    assert error.exit_status == 128
    assert error.output_tail == "fatal: x"
    assert str(error) == "git fetch --prune origin failed (exit 128): fatal: x"
    assert without_status.exit_status is None
    assert str(without_status) == (
        "git fetch --prune origin failed (no exit status): time limit reached"
    )
    assert issubclass(FetchFailed, GitError)
    assert issubclass(GitError, BoundaryError)
