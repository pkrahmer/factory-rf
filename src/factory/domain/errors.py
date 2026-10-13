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


class ProjectCommandError(BoundaryError):
    """A project command could not be started; a red or timed-out command is a result."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None:
        """Name the command and why it could not be started."""
        super().__init__(f"project command {command} failed: {detail}")
        self.command = command
        self.detail = detail


class AgentRuntimeError(BoundaryError):
    """The agent runtime could not run an agent; a dead or timed-out run is a result."""

    detail: str

    def __init__(self, detail: str) -> None:
        """Say why the agent runtime failed."""
        super().__init__(f"agent runtime failed: {detail}")
        self.detail = detail


class WorkItemFormatError(FactoryError):
    """A work item file cannot be read: its fault and, where known, its path."""

    fault: str
    path: str | None

    def __init__(self, fault: str, path: str | None = None) -> None:
        """Name the fault and the file it was found in."""
        super().__init__(fault if path is None else f"{path}: {fault}")
        self.fault = fault
        self.path = path


class CostRecordFormatError(FactoryError):
    """A cost record file cannot be read or written: the line and its fault."""

    line: int
    fault: str

    def __init__(self, line: int, fault: str) -> None:
        """Name the line, counted from 1, and its fault."""
        super().__init__(f"line {line}: {fault}")
        self.line = line
        self.fault = fault
