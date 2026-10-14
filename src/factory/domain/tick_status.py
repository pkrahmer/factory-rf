"""The tick status: the errors of each event on each remote state, kept between ticks."""

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.domain.git import CommitId

ERROR_CAP = 3


class ErrorCount(BaseModel):
    """How often one event failed on one remote state, and whether that was reported."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_key: str
    remote_state: CommitId
    count: PositiveInt
    reported: bool = False
    last_error: str = ""


class TickStatus(BaseModel):
    """The error counts of the events; a local cache that may reset with the process."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    errors: list[ErrorCount] = []


def find_error(status: TickStatus, event_key: str, remote_state: CommitId) -> ErrorCount | None:
    """The entry of the event key on the remote state, if there is one."""
    for entry in status.errors:
        if entry.event_key == event_key and entry.remote_state == remote_state:
            return entry
    return None


def record_error(
    status: TickStatus, event_key: str, remote_state: CommitId, last_error: str
) -> TickStatus:
    """Count one more error of the event key on the remote state.

    A new remote state starts the key's count again at 1.
    """
    known = find_error(status, event_key, remote_state)
    if known is None:
        entry = ErrorCount(
            event_key=event_key, remote_state=remote_state, count=1, last_error=last_error
        )
    else:
        entry = known.model_copy(update={"count": known.count + 1, "last_error": last_error})
    return TickStatus(errors=[*clear_errors(status, event_key).errors, entry])


def mark_reported(status: TickStatus, event_key: str, remote_state: CommitId) -> TickStatus:
    """Mark the entry of the event key on the remote state as reported."""
    return TickStatus(
        errors=[
            entry.model_copy(update={"reported": True})
            if entry.event_key == event_key and entry.remote_state == remote_state
            else entry
            for entry in status.errors
        ]
    )


def clear_errors(status: TickStatus, event_key: str) -> TickStatus:
    """Remove every entry of the event key."""
    return TickStatus(errors=[entry for entry in status.errors if entry.event_key != event_key])


def at_cap(entry: ErrorCount) -> bool:
    """Whether the entry has reached the error cap."""
    return entry.count >= ERROR_CAP
