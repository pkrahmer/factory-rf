"""The kernel's process table read one line at a time, and what of a session is left to kill."""

from collections.abc import Collection, Iterable
from typing import Final

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt

ENDED_STATES: Final[frozenset[str]] = frozenset({"Z", "X"})

_STATE_FIELD = 0
_SESSION_FIELD = 3


class ProcessEntry(BaseModel):
    """One process of the kernel's table: its id, its session and whether it has ended."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pid: PositiveInt
    session: NonNegativeInt
    ended: bool


def parse_stat(pid: int, stat: str) -> ProcessEntry:
    """The entry of the text of `/proc/<pid>/stat`, whose name in parentheses may hold anything."""
    # The name may hold spaces and parentheses itself, so only the last `)` ends it.
    _, closing, rest = stat.rpartition(")")
    if not closing:
        raise ValueError(f"no closing parenthesis in the status line of {pid}")
    fields = rest.split()
    if len(fields) <= _SESSION_FIELD:
        raise ValueError(f"too few fields in the status line of {pid}")
    return ProcessEntry(
        pid=pid,
        session=int(fields[_SESSION_FIELD]),
        ended=fields[_STATE_FIELD] in ENDED_STATES,
    )


def left_to_kill(
    entries: Iterable[ProcessEntry], *, session: int, refused: Collection[int]
) -> list[int]:
    """The ids, in ascending order, of the session's processes still left to kill.

    A process is left when it has not ended and its id is not in `refused`.
    """
    return sorted(
        {
            entry.pid
            for entry in entries
            if entry.session == session and not entry.ended and entry.pid not in refused
        }
    )
