"""The root of the errors the factory raises on purpose."""


class FactoryError(Exception):
    """Every error the factory raises on purpose."""


class BoundaryError(FactoryError):
    """An outside party failed."""


class HostingServiceError(BoundaryError):
    """A call to the hosting service failed."""

    operation: str
    detail: str

    def __init__(self, operation: str, detail: str) -> None:
        """Name the failed operation and what the hosting service reported."""
        super().__init__(f"hosting service {operation} failed: {detail}")
        self.operation = operation
        self.detail = detail


class GitError(BoundaryError):
    """A git command failed, could not start or reached its time limit."""

    command: str
    exit_status: int | None
    output_tail: str

    def __init__(self, command: str, exit_status: int | None, output_tail: str) -> None:
        """Name the command, how it ended and the last lines it wrote."""
        status = "no exit status" if exit_status is None else f"exit {exit_status}"
        super().__init__(f"{command} failed ({status}): {output_tail}")
        self.command = command
        self.exit_status = exit_status
        self.output_tail = output_tail


class FetchFailed(GitError):
    """Fetching from the remote failed."""


class NothingToCommit(GitError):
    """A commit was asked for, but no change was staged."""
