"""The one place that starts a process: every command-line tool is reached through it."""

import contextlib
import os
import selectors
import signal
import subprocess  # noqa: S404  # nosec B404
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import IO, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Stream = Literal["stdout", "stderr"]

_READ_SIZE = 65536
_END_POLL_SECONDS = 0.05

PIPE_DRAIN = timedelta(seconds=5)


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
    stopped: bool = False


def _decode(output: bytes | None) -> str:
    return (output or b"").decode("utf-8", errors="replace")


def _seconds(time_limit: timedelta | None) -> float | None:
    return None if time_limit is None else time_limit.total_seconds()


def _kill_session(process: subprocess.Popen[bytes]) -> None:
    # The child leads its own process group. No agent code runs on the host, so nothing
    # the factory starts there leaves the group. The child is not reaped yet, so the
    # group's id cannot belong to an unrelated process meanwhile.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)


def _start(request: ProcessRequest) -> subprocess.Popen[bytes]:
    stderr = subprocess.STDOUT if request.merge_stderr else subprocess.PIPE
    return subprocess.Popen(  # noqa: S603  # nosec B603
        request.argv,
        cwd=request.cwd,
        env=request.env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=stderr,
        start_new_session=True,
    )


def _deadline(start: float, time_limit: timedelta | None) -> float | None:
    seconds = _seconds(time_limit)
    return None if seconds is None else start + seconds


class _LineReader:
    """Reads the open streams of a process and hands each complete line to the callback."""

    def __init__(
        self, process: subprocess.Popen[bytes], on_line: Callable[[Stream, str], bool]
    ) -> None:
        self._on_line = on_line
        self._selector = selectors.DefaultSelector()
        self._pending: dict[Stream, bytes] = {}
        self.read_bytes: dict[Stream, bytes] = {"stdout": b"", "stderr": b""}
        self._register("stdout", process.stdout)
        self._register("stderr", process.stderr)

    def _register(self, stream: Stream, pipe: IO[bytes] | None) -> None:
        if pipe is not None:
            self._pending[stream] = b""
            self._selector.register(pipe, selectors.EVENT_READ, stream)

    def has_open_stream(self) -> bool:
        """Whether a stream is still open."""
        return bool(self._selector.get_map())

    def read_ready(self, timeout: float | None) -> bool:
        """Read what the streams hold within `timeout` and pass its lines; True means stop."""
        for key, _ in self._selector.select(timeout):
            stream: Stream = key.data
            chunk = os.read(key.fd, _READ_SIZE)
            if chunk:
                self.read_bytes[stream] += chunk
                self._pending[stream] += chunk
                if self._pass_complete_lines(stream):
                    return True
            else:
                self._selector.unregister(key.fileobj)
                if self._pass_last_line(stream):
                    return True
        return False

    def _pass_complete_lines(self, stream: Stream) -> bool:
        *lines, self._pending[stream] = self._pending[stream].split(b"\n")
        return any(self._on_line(stream, _decode(line)) for line in lines)

    def _pass_last_line(self, stream: Stream) -> bool:
        last = self._pending.pop(stream)
        return bool(last) and self._on_line(stream, _decode(last))

    def close(self) -> None:
        """Release the selector; the pipes are closed with the process."""
        self._selector.close()


def _keep_reading(_stream: Stream, _line: str) -> bool:
    return False


def _remaining(deadline: float | None) -> float | None:
    return None if deadline is None else max(deadline - time.monotonic(), 0.0)


def _has_ended(process: subprocess.Popen[bytes]) -> bool:
    # WNOWAIT leaves the child unreaped, so its id, the group's, stays reserved for a kill.
    flags = os.WEXITED | os.WNOHANG | os.WNOWAIT
    return os.waitid(os.P_PID, process.pid, flags) is not None


_ReadOutcome = Literal["closed", "stopped", "timed_out", "abandoned"]


def _read_bounded(
    reader: _LineReader,
    process: subprocess.Popen[bytes],
    deadline: float | None,
    ended_at: float | None,
) -> _ReadOutcome:
    """Read until the streams close, the reader stops, or the deadline or the drain passes.

    The drain counts from `ended_at`, or from the moment the child is seen to have ended:
    a descendant that left the group may keep a pipe open long after the child.
    """
    drain = PIPE_DRAIN.total_seconds()
    while reader.has_open_stream():
        now = time.monotonic()
        if ended_at is None and _has_ended(process):
            ended_at = now
        if deadline is not None and now >= deadline:
            return "timed_out"
        wait = _END_POLL_SECONDS if ended_at is None else ended_at + drain - now
        if wait <= 0:
            return "abandoned"
        if deadline is not None:
            wait = min(wait, deadline - now)
        if reader.read_ready(wait):
            return "stopped"
    return "closed"


def _wait_for_exit(process: subprocess.Popen[bytes], deadline: float | None) -> bool:
    """Wait for a process whose streams have ended; True when the time limit passed first."""
    try:
        process.wait(timeout=_remaining(deadline))
    except subprocess.TimeoutExpired:
        return True
    return False


def _read_to_exit(
    reader: _LineReader, process: subprocess.Popen[bytes], deadline: float | None
) -> _ReadOutcome:
    """Read the streams, then wait for the child's exit when they closed within the deadline."""
    outcome = _read_bounded(reader, process, deadline, ended_at=None)
    if outcome == "closed" and _wait_for_exit(process, deadline):
        return "timed_out"
    return outcome


def run_process(request: ProcessRequest) -> ProcessResult:
    """Run `request.argv` without a shell and kill its process group at the time limit.

    Once the child has ended, or its process group was killed, the output is read for at most
    `PIPE_DRAIN`; a pipe still open then is closed and the call returns what it read.
    A failure to start the program, such as `FileNotFoundError`, is raised to the caller.
    """
    start = time.monotonic()
    deadline = _deadline(start, request.time_limit)
    process = _start(request)
    with process:
        reader = _LineReader(process, _keep_reading)
        try:
            outcome = _read_to_exit(reader, process, deadline)
            timed_out = outcome == "timed_out"
            if timed_out:
                _kill_session(process)
                _read_bounded(reader, process, None, ended_at=time.monotonic())
        finally:
            reader.close()
    return ProcessResult(
        exit_status=None if timed_out else process.returncode,
        stdout=_decode(reader.read_bytes["stdout"]),
        stderr=_decode(reader.read_bytes["stderr"]),
        timed_out=timed_out,
        duration=timedelta(seconds=time.monotonic() - start),
    )


def run_streaming(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult:
    """Run `request.argv` as `run_process` does and hand `on_line` each line as it arrives.

    `on_line` returning True kills the process group at once and passes no further line; so
    does the time limit, and neither reads on after the kill. An exception from `on_line`
    kills the process group and propagates. Once the child has ended, the output is read for at
    most `PIPE_DRAIN`, as `run_process` does: a pipe still open then is closed, the call
    returns, and a last line without a line feed is not passed.
    """
    start = time.monotonic()
    deadline = _deadline(start, request.time_limit)
    process = _start(request)
    with process:
        reader = _LineReader(process, on_line)
        try:
            outcome = _read_to_exit(reader, process, deadline)
        except BaseException:
            _kill_session(process)
            raise
        finally:
            reader.close()
        stopped = outcome == "stopped"
        timed_out = outcome == "timed_out"
        if stopped or timed_out:
            _kill_session(process)
    return ProcessResult(
        exit_status=None if stopped or timed_out else process.returncode,
        stdout=_decode(reader.read_bytes["stdout"]),
        stderr=_decode(reader.read_bytes["stderr"]),
        timed_out=timed_out,
        stopped=stopped,
        duration=timedelta(seconds=time.monotonic() - start),
    )
