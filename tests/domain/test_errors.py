"""The root of the factory's error hierarchy."""

from factory.domain.errors import (
    AgentRuntimeError,
    BoundaryError,
    FactoryError,
    FetchFailed,
    GitError,
    HostingServiceError,
    NothingToCommit,
    ProjectCommandError,
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


def test_nothing_to_commit_is_a_git_error() -> None:
    assert issubclass(NothingToCommit, GitError)


def test_project_command_error_names_command_and_detail() -> None:
    error = ProjectCommandError("check", "boom")

    assert error.command == "check"
    assert error.detail == "boom"
    assert str(error) == "project command check failed: boom"
    assert issubclass(ProjectCommandError, BoundaryError)


def test_agent_runtime_error_names_its_detail() -> None:
    error = AgentRuntimeError("boom")

    assert error.detail == "boom"
    assert str(error) == "agent runtime failed: boom"
    assert issubclass(AgentRuntimeError, BoundaryError)
