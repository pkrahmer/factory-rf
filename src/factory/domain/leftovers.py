"""Which processes of its user the leftovers program still has to end, and when it refuses."""

from collections.abc import Sequence
from typing import Annotated, Final

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt, StringConstraints

from factory.domain.sessions import ProcessEntry

LEFTOVERS_PREFIX: Final = "factory-leftovers:"
LEFTOVER_ROUNDS: Final = 50
LEFTOVER_PAUSE_SECONDS: Final = 0.1

_ROOT_UID = 0


class Identity(BaseModel):
    """Who a process runs as: its user id, that user's name, and its own process id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    uid: NonNegativeInt
    user: Annotated[str, StringConstraints(min_length=1)]
    pid: PositiveInt


def leftover_pids(entries: Sequence[ProcessEntry], identity: Identity) -> list[int]:
    """The ids, in ascending order, of the living processes of the user other than its own."""
    return sorted(
        {
            entry.pid
            for entry in entries
            if entry.uid == identity.uid and entry.pid != identity.pid and not entry.ended
        }
    )


def leftovers_refusal(identity: Identity, user: str) -> str | None:
    """Why the program must not signal as `identity` when asked for `user`; None when it may."""
    # As root, `kill(-1)` would end every process of the container.
    if identity.uid == _ROOT_UID:
        return "refuses to run as root"
    # A stand-in `sudo` that does not switch users would end the factory's own processes.
    if user != identity.user:
        return f"runs as {identity.user}, not {user}"
    return None
