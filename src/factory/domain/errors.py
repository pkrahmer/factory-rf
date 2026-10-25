"""The root of the errors the factory raises on purpose."""

from factory.domain.git import PushOutcome


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


class RepositoryUnsealed(GitError):
    """The checkout's git folder is not the factory's alone."""

    def __init__(self, detail: str) -> None:
        """Say what about the git folder is not the factory's alone."""
        super().__init__("seal", None, detail)


class PushFailed(FactoryError):
    """A push did not reach the remote: the branch and how the push ended."""

    branch: str
    outcome: PushOutcome

    def __init__(self, branch: str, outcome: PushOutcome) -> None:
        """Name the branch and the push's outcome."""
        super().__init__(f"push of {branch} failed: {outcome}")
        self.branch = branch
        self.outcome = outcome


class ProjectCommandError(BoundaryError):
    """A project command could not be started; a red or timed-out command is a result."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None:
        """Name the command and why it could not be started."""
        super().__init__(f"project command {command} failed: {detail}")
        self.command = command
        self.detail = detail


class SnapshotError(BoundaryError):
    """A snapshot command failed, could not start or reached its time limit."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None:
        """Name the command and what went wrong."""
        super().__init__(f"snapshot command {command} failed: {detail}")
        self.command = command
        self.detail = detail


class ContainerError(BoundaryError):
    """A container command failed, could not start or reached its time limit."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None:
        """Name the command and what went wrong."""
        super().__init__(f"container command {command} failed: {detail}")
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


class PipelineDefinitionInvalid(FactoryError):
    """The pipeline definition cannot be read: every fault, joined in one text."""

    fault: str

    def __init__(self, fault: str) -> None:
        """Name the fault; it is the whole message."""
        super().__init__(fault)
        self.fault = fault


class AgentDefinitionError(FactoryError):
    """The agent files cannot be read: the agent's name, `""` for all of them, and the fault."""

    name: str
    fault: str

    def __init__(self, name: str, fault: str) -> None:
        """Name the agent and the fault."""
        super().__init__(f"agent {name}: {fault}" if name else fault)
        self.name = name
        self.fault = fault


class AgentDefinitionMissing(AgentDefinitionError):
    """No agent of that name is installed."""


class AgentDefinitionInvalid(AgentDefinitionError):
    """The agent file exists but does not define an agent: the key at fault, `""` for the file."""

    key: str

    def __init__(self, name: str, fault: str, key: str) -> None:
        """Name the agent, the fault and the key it concerns."""
        super().__init__(name, fault)
        self.key = key


class UnhandledEvent(FactoryError):
    """An event's kind has no handler."""

    kind: str

    def __init__(self, kind: str) -> None:
        """Name the kind without a handler."""
        super().__init__(f"no handler for event kind {kind}")
        self.kind = kind


class CannotHandle(FactoryError):
    """A handler cannot do its work: the event's kind and the reason."""

    kind: str
    reason: str

    def __init__(self, kind: str, reason: str) -> None:
        """Name the event kind and why it cannot be handled."""
        super().__init__(f"cannot handle {kind}: {reason}")
        self.kind = kind
        self.reason = reason


class SettingsInvalid(FactoryError):
    """The instance's settings cannot be read: the variable at fault and the fault."""

    variable: str
    fault: str

    def __init__(self, variable: str, fault: str) -> None:
        """Name the variable and the fault."""
        super().__init__(f"{variable}: {fault}")
        self.variable = variable
        self.fault = fault
