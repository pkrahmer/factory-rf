"""The kill at a time limit, a stop or an error ends every process of the child's group."""

import contextlib
import os
import signal
import time
from collections.abc import Callable, Iterator
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.process import (
    ProcessRequest,
    ProcessResult,
    Stream,
    run_process,
    run_streaming,
)
from process_support import Recorder, is_gone, python_argv
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

# A child that starts a sleeping grandchild with its streams on /dev/null, placed by the keyword
# arguments in `sys.argv[2]`, writes its pid to `sys.argv[1]`, prints `started` and sleeps.
CHILD = (
    "import pathlib, subprocess, sys, time; "
    "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
    "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, "
    "**eval(sys.argv[2])); "
    "pathlib.Path(sys.argv[1]).write_text(str(p.pid)); "
    "print('started', flush=True); "
    "time.sleep(60)"
)
OWN_GROUP = "{'process_group': 0}"
OWN_SESSION = "{'start_new_session': True}"

Runner = Callable[[ProcessRequest], ProcessResult]


def _streaming(request: ProcessRequest) -> ProcessResult:
    return run_streaming(request, Recorder())


@pytest.fixture
def pid_file(tmp_path: Path) -> Iterator[Path]:
    """The grandchild's pid file; a grandchild still running at the end is killed."""
    path = tmp_path / "grandchild.pid"
    yield path
    if path.exists():
        pid = int(path.read_text(encoding="utf-8"))
        if not is_gone(pid, within=0):
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)


def _grandchild(pid_file: Path) -> int:
    return int(pid_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("runner", "placement", "ended"),
    [
        pytest.param(run_process, "{}", True, id="run_process-group"),
        pytest.param(run_process, OWN_GROUP, False, id="run_process-own-group"),
        pytest.param(run_process, OWN_SESSION, False, id="run_process-own-session"),
        pytest.param(_streaming, "{}", True, id="run_streaming-group"),
        pytest.param(_streaming, OWN_GROUP, False, id="run_streaming-own-group"),
        pytest.param(_streaming, OWN_SESSION, False, id="run_streaming-own-session"),
    ],
)
def test_time_limit_ends_every_process_of_the_group(
    tmp_path: Path, pid_file: Path, runner: Runner, placement: str, *, ended: bool
) -> None:
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), placement), cwd=tmp_path, time_limit=ROOMY_LIMIT
    )
    start = time.monotonic()

    result = runner(request)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is True
    assert result.exit_status is None
    if ended:
        assert is_gone(_grandchild(pid_file))
    else:
        assert is_gone(_grandchild(pid_file), within=0) is False


def _stop_on_started(_stream: Stream, line: str) -> bool:
    return line == "started"


def _raise_on_started(_stream: Stream, line: str) -> bool:
    if line == "started":
        raise RuntimeError("callback failed")
    return False


@pytest.mark.parametrize(
    ("on_line", "raises"),
    [
        pytest.param(_stop_on_started, False, id="stop"),
        pytest.param(_raise_on_started, True, id="raise"),
    ],
)
def test_stop_and_error_of_the_callback_end_every_process_of_the_group(
    tmp_path: Path, pid_file: Path, on_line: Callable[[Stream, str], bool], raises: bool
) -> None:
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), "{}"), cwd=tmp_path, time_limit=ROOMY_LIMIT
    )
    start = time.monotonic()

    if raises:
        with pytest.raises(RuntimeError, match="callback failed"):
            run_streaming(request, on_line)
    else:
        assert run_streaming(request, on_line).stopped is True

    assert time.monotonic() - start < ROOMY_LIMIT.total_seconds()
    assert is_gone(_grandchild(pid_file))


def _group_already_gone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProcessResult:
    real_killpg = os.killpg

    def killpg_then_gone(group: int, sig: int) -> None:
        real_killpg(group, sig)
        raise ProcessLookupError(group)

    monkeypatch.setattr(os, "killpg", killpg_then_gone)
    request = ProcessRequest(
        argv=python_argv("import time; time.sleep(60)"),
        cwd=tmp_path,
        time_limit=timedelta(seconds=1),
    )
    return run_process(request)


def _ends_by_itself(runner: Runner) -> Callable[[Path, pytest.MonkeyPatch], ProcessResult]:
    def call(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> ProcessResult:
        request = ProcessRequest(
            argv=python_argv("import sys; sys.exit(3)"), cwd=tmp_path, time_limit=ROOMY_LIMIT
        )
        return runner(request)

    return call


@pytest.mark.parametrize(
    ("call", "timed_out", "exit_status"),
    [
        pytest.param(_group_already_gone, True, None, id="group-already-gone"),
        pytest.param(_ends_by_itself(run_process), False, 3, id="run_process-ends-by-itself"),
        pytest.param(_ends_by_itself(_streaming), False, 3, id="run_streaming-ends-by-itself"),
    ],
)
def test_a_call_without_a_group_to_kill_ends_as_its_child_does(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    call: Callable[[Path, pytest.MonkeyPatch], ProcessResult],
    *,
    timed_out: bool,
    exit_status: int | None,
) -> None:
    start = time.monotonic()

    result = call(tmp_path, monkeypatch)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is timed_out
    assert result.exit_status == exit_status
