"""Waiting for a process that a test expects to be killed, without sleeping."""

import os
import select
import sys

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
    return [sys.executable, "-c", code, *args]
