"""The kill at a time limit, a stop or an error ends every process of the child's session."""

import contextlib
import os
import signal
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from factory.adapters.make_commands import MakeProjectCommands
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
    ("runner", "placement", "gone"),
    [
        pytest.param(run_process, "{}", True, id="run_process-group"),
        pytest.param(run_process, OWN_GROUP, True, id="run_process-own-group"),
        pytest.param(
            run_process, "{'start_new_session': True}", False, id="run_process-own-session"
        ),
        pytest.param(_streaming, "{}", True, id="run_streaming-group"),
        pytest.param(_streaming, OWN_GROUP, True, id="run_streaming-own-group"),
        pytest.param(
            _streaming, "{'start_new_session': True}", False, id="run_streaming-own-session"
        ),
    ],
)
def test_time_limit_ends_every_process_of_the_session(
    tmp_path: Path, pid_file: Path, runner: Runner, placement: str, gone: bool
) -> None:
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), placement), cwd=tmp_path, time_limit=ROOMY_LIMIT
    )
    start = time.monotonic()

    result = runner(request)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is True
    assert result.exit_status is None
    assert is_gone(_grandchild(pid_file), within=0) is gone


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
def test_stop_and_error_of_the_callback_end_every_process_of_the_session(
    tmp_path: Path, pid_file: Path, on_line: Callable[[Stream, str], bool], raises: bool
) -> None:
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), OWN_GROUP), cwd=tmp_path, time_limit=ROOMY_LIMIT
    )
    start = time.monotonic()

    if raises:
        with pytest.raises(RuntimeError, match="callback failed"):
            run_streaming(request, on_line)
    else:
        assert run_streaming(request, on_line).stopped is True

    assert time.monotonic() - start < ROOMY_LIMIT.total_seconds()
    assert is_gone(_grandchild(pid_file), within=0)


@pytest.mark.parametrize(
    "flag",
    [
        pytest.param("", id="own-group"),
        pytest.param("--foreground ", id="foreground"),
    ],
)
def test_time_limit_of_a_make_target_ends_what_timeout_started(
    tmp_path: Path, pid_file: Path, flag: str
) -> None:
    recipe = (
        f"timeout {flag}60 sh -c 'echo $$$$ > {pid_file.name}; exec sleep 60' 2>&1 | tee run.txt"
    )
    (tmp_path / "Makefile").write_text(
        f"SHELL := /bin/bash\n.SHELLFLAGS := -eu -o pipefail -c\nslow:\n\t{recipe}\n",
        encoding="utf-8",
    )
    start = time.monotonic()

    result = MakeProjectCommands(tmp_path).run("slow", time_limit=ROOMY_LIMIT)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.status == "time_limit"
    assert is_gone(_grandchild(pid_file), within=0)


def test_process_the_factory_may_not_signal_is_left_not_waited_for(
    tmp_path: Path, pid_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_kill = os.kill

    def refusing_kill(pid: int, sig: int) -> None:
        if pid_file.exists() and pid == _grandchild(pid_file):
            raise PermissionError(pid)
        real_kill(pid, sig)

    monkeypatch.setattr(os, "kill", refusing_kill)
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), OWN_GROUP), cwd=tmp_path, time_limit=ROOMY_LIMIT
    )
    start = time.monotonic()

    result = run_process(request)

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is True
    grandchild = _grandchild(pid_file)
    assert not is_gone(grandchild, within=0)
    monkeypatch.undo()
    os.kill(grandchild, signal.SIGKILL)
