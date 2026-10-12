"""The one place that starts a subprocess: every command-line tool is reached through it."""

import contextlib
import os
import signal
import subprocess  # noqa: S404  # nosec B404
import time
from datetime import timedelta
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ProcessRequest(BaseModel):
    """A program to run, where, with which environment and for how long at most."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    argv: Annotated[list[str], Field(min_length=1)]
    cwd: Path
    env: dict[str, str] | None = None
    time_limit: Annotated[timedelta | None, Field(gt=timedelta(0))] = None
    merge_stderr: bool = False


class ProcessResult(BaseModel):
    """What a finished or killed process left: its status, its output and how long it ran."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exit_status: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration: timedelta


def _decode(output: bytes | None) -> str:
    return (output or b"").decode("utf-8", errors="replace")


def _seconds(time_limit: timedelta | None) -> float | None:
    return None if time_limit is None else time_limit.total_seconds()


def _kill_group(process: subprocess.Popen[bytes]) -> None:
    # The child leads its own session, so its group holds everything it started.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)


def run_process(request: ProcessRequest) -> ProcessResult:
    """Run `request.argv` without a shell and kill its whole process group at the time limit.

    A failure to start the program, such as `FileNotFoundError`, is raised to the caller.
    """
    stderr = subprocess.STDOUT if request.merge_stderr else subprocess.PIPE
    start = time.monotonic()
    process = subprocess.Popen(  # noqa: S603  # nosec B603
        request.argv,
        cwd=request.cwd,
        env=request.env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=stderr,
        start_new_session=True,
    )
    with process:
        timed_out = False
        try:
            out, err = process.communicate(timeout=_seconds(request.time_limit))
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(process)
            # Once the group is dead the pipes close, so this collects what was written.
            out, err = process.communicate()
    return ProcessResult(
        exit_status=None if timed_out else process.returncode,
        stdout=_decode(out),
        stderr=_decode(err),
        timed_out=timed_out,
        duration=timedelta(seconds=time.monotonic() - start),
    )
