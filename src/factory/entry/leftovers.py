"""The program that ends every other process of the user it runs as, after an agent's run."""

import signal
import sys
import time
from collections.abc import Callable, Sequence
from typing import TextIO

from factory.adapters import process
from factory.domain.leftovers import (
    LEFTOVER_PAUSE_SECONDS,
    LEFTOVER_ROUNDS,
    LEFTOVERS_PREFIX,
    Identity,
    leftover_pids,
    leftovers_refusal,
)
from factory.domain.sessions import ProcessEntry

USAGE = "usage: python -m factory.entry.leftovers --user <name>"

_USER_OPTION = "--user"
_DONE = 0
_FAILED = 1


class _Stop(Exception):
    """A fault that ends the program; its message is the line to write."""


# Each outside call is a keyword of its own, so a test injects every one of them.
def main(  # noqa: PLR0913
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    identity: Callable[[], Identity] | None = None,
    kill: Callable[[int], None] | None = None,
    processes: Callable[[], list[ProcessEntry]] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> int:
    """End every other process of the user this program runs as; 0 once none is left."""
    arguments = sys.argv[1:] if argv is None else list(argv)
    errors = sys.stderr if stderr is None else stderr
    try:
        user = _parse(arguments)
        own = (process.own_identity if identity is None else identity)()
        refusal = leftovers_refusal(own, user)
        if refusal is not None:
            raise _Stop(refusal)
        _end_the_others(
            own,
            process.signal_every_other if kill is None else kill,
            process.read_process_table if processes is None else processes,
            time.sleep if sleep is None else sleep,
        )
    except _Stop as stop:
        errors.write(f"{LEFTOVERS_PREFIX} {stop}\n")
        return _FAILED
    return _DONE


def _parse(arguments: list[str]) -> str:
    if len(arguments) != 2 or arguments[0] != _USER_OPTION or not arguments[1]:
        raise _Stop(USAGE)
    return arguments[1]


def _end_the_others(
    own: Identity,
    kill: Callable[[int], None],
    processes: Callable[[], list[ProcessEntry]],
    sleep: Callable[[float], None],
) -> None:
    # Never waits with `kill -0 -1`: Linux counts a process it may not signal as found.
    left: list[int] = []
    for round_number in range(1, LEFTOVER_ROUNDS + 1):
        try:
            kill(signal.SIGKILL)
        except OSError as error:
            raise _Stop(f"cannot signal the processes: {error}") from error
        try:
            left = leftover_pids(processes(), own)
        except (OSError, ValueError) as error:
            raise _Stop(f"cannot list the processes: {error}") from error
        if not left:
            return
        if round_number < LEFTOVER_ROUNDS:
            sleep(LEFTOVER_PAUSE_SECONDS)
    ids = ", ".join(str(pid) for pid in left)
    raise _Stop(f"{len(left)} processes left after {LEFTOVER_ROUNDS} rounds: {ids}")


if __name__ == "__main__":
    sys.exit(main())
