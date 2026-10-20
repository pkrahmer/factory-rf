"""The one place that starts a process: every command-line tool is reached through it."""

import contextlib
import os
import pwd
import selectors
import signal
import subprocess  # noqa: S404  # nosec B404
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import timedelta
from pathlib import Path
from typing import IO, Annotated, Literal, NoReturn

from pydantic import BaseModel, ConfigDict, Field

from factory.domain.leftovers import Identity
from factory.domain.sessions import ProcessEntry, left_to_kill, parse_stat

Stream = Literal["stdout", "stderr"]

_READ_SIZE = 65536
_PROCESS_TABLE = Path("/proc")
_ROUND_PAUSE_SECONDS = 0.05


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


def read_process_table(proc: Path = _PROCESS_TABLE) -> list[ProcessEntry]:
    """Every process of the table under `proc`, sorted by id, each with its folder's owner.

    A process that ends while it is read is left out; a status line that cannot be read
    raises `ValueError`, and a table that cannot be listed the `OSError` of the listing.
    """
    entries: list[ProcessEntry] = []
    for folder in proc.iterdir():
        if not folder.name.isdigit():
            continue
        try:
            stat = (folder / "stat").read_bytes()
            # The folder's owner, not a file's: a process that is not dumpable gets
            # root-owned files, while its folder keeps its user.
            uid = folder.stat().st_uid
        except OSError:
            # The process ended between the listing and the read.
            continue
        entries.append(parse_stat(int(folder.name), _decode(stat), uid=uid))
    return sorted(entries, key=lambda entry: entry.pid)


def own_identity() -> Identity:
    """The user id, the user's name and the process id this process runs with."""
    uid = os.getuid()
    return Identity(uid=uid, user=pwd.getpwuid(uid).pw_name, pid=os.getpid())


def signal_every_other(signal_number: int) -> None:
    """Send `signal_number` to every process this user may signal, this process spared."""
    with contextlib.suppress(ProcessLookupError):
        os.kill(-1, signal_number)


def _kill_one(pid: int, refused: set[int]) -> None:
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        # Another user's process, such as root's `sudo`: the agent's own `timeout` ends it.
        refused.add(pid)


def _kill_session(process: subprocess.Popen[bytes]) -> None:
    # The child leads its own session. A descendant may take a group of its own, as
    # `timeout` does, but it keeps the session; only `setsid` leaves it. The child is not
    # reaped yet, so the session's id cannot belong to an unrelated process meanwhile.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    refused: set[int] = set()
    while left := left_to_kill(read_process_table(), session=process.pid, refused=refused):
        for pid in left:
            _kill_one(pid, refused)
        time.sleep(_ROUND_PAUSE_SECONDS)


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


def run_process(request: ProcessRequest) -> ProcessResult:
    """Run `request.argv` without a shell and kill every process of its session at the time limit.

    A failure to start the program, such as `FileNotFoundError`, is raised to the caller.
    """
    start = time.monotonic()
    process = _start(request)
    with process:
        timed_out = False
        try:
            out, err = process.communicate(timeout=_seconds(request.time_limit))
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_session(process)
            # Once the session is dead the pipes close, so this collects what was written.
            out, err = process.communicate()
    return ProcessResult(
        exit_status=None if timed_out else process.returncode,
        stdout=_decode(out),
        stderr=_decode(err),
        timed_out=timed_out,
        duration=timedelta(seconds=time.monotonic() - start),
    )


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


def _remaining(deadline: float | None) -> float | None:
    return None if deadline is None else max(deadline - time.monotonic(), 0.0)


def _read_until_end(reader: _LineReader, deadline: float | None) -> tuple[bool, bool]:
    """Pass every line until the streams end; returns (stopped, timed_out)."""
    while reader.has_open_stream():
        remaining = _remaining(deadline)
        if remaining == 0.0:
            return False, True
        if reader.read_ready(remaining):
            return True, False
    return False, False


def _wait_for_exit(process: subprocess.Popen[bytes], deadline: float | None) -> bool:
    """Wait for a process whose streams have ended; True when the time limit passed first."""
    try:
        process.wait(timeout=_remaining(deadline))
    except subprocess.TimeoutExpired:
        return True
    return False


def run_streaming(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult:
    """Run `request.argv` as `run_process` does and hand `on_line` each line as it arrives.

    `on_line` returning True kills the session at once and passes no further line; so
    does the time limit. An exception from `on_line` kills the session and propagates.
    """
    start = time.monotonic()
    time_limit = _seconds(request.time_limit)
    deadline = None if time_limit is None else start + time_limit
    process = _start(request)
    with process:
        reader = _LineReader(process, on_line)
        try:
            stopped, timed_out = _read_until_end(reader, deadline)
            if not (stopped or timed_out):
                timed_out = _wait_for_exit(process, deadline)
        except BaseException:
            _kill_session(process)
            raise
        finally:
            reader.close()
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


def replace_process(argv: Sequence[str], env: Mapping[str, str]) -> NoReturn:
    """Replace this process with `argv`, its program found on the `PATH` of `env`.

    An empty `argv` raises `ValueError`; a program that cannot be started raises the
    `OSError` of the `exec`, and this process then goes on.
    """
    if not argv:
        raise ValueError("replace_process needs a program to start")
    os.execvpe(argv[0], list(argv), dict(env))  # noqa: S606  # nosec B606
