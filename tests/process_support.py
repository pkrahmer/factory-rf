"""Real child processes in tests: their command line, a line callback, a wait for their end."""

import os
import select
import sys
import threading

from factory.adapters.process import Stream

# A kill takes effect asynchronously: right after it, a busy machine may still run the process.
GONE_WITHIN_SECONDS = 5.0


def is_gone(pid: int, within: float = GONE_WITHIN_SECONDS) -> bool:
    """Whether the process `pid` has ended within `within` seconds (a zombie has ended)."""
    try:
        descriptor = os.pidfd_open(pid)
    except ProcessLookupError:
        return True
    try:
        readable, _, _ = select.select([descriptor], [], [], within)
    finally:
        os.close(descriptor)
    return bool(readable)


def python_argv(code: str, *args: str) -> list[str]:
    """The command line that runs `code` in this test run's Python, with `args` after it."""
    return [sys.executable, "-B", "-c", code, *args]


class Recorder:
    """A callback that records each call and says stop on the lines it is given."""

    def __init__(self, stop_on: frozenset[str] = frozenset()) -> None:
        self.calls: list[tuple[Stream, str]] = []
        self.threads: list[int] = []
        self._stop_on = stop_on

    def __call__(self, stream: Stream, line: str) -> bool:
        self.calls.append((stream, line))
        self.threads.append(threading.get_ident())
        return line in self._stop_on
