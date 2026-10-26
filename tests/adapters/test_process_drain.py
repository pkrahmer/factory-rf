"""A call reads on for at most `PIPE_DRAIN` once its child ended or was killed."""

import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import process
from factory.adapters.process import (
    ProcessRequest,
    Stream,
    run_process,
    run_streaming,
)
from process_support import Recorder, is_gone, python_argv

SHORT_DRAIN = timedelta(seconds=2)

# Sleeps in a session of its own after writing its pid to `sys.argv[1]`.
HOLDER = (
    "import os, pathlib, sys, time; "
    "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); "
    "time.sleep(60)"
)

# Starts a holder on the stream named by `sys.argv[2]` (`stdout`, `stderr` or `none`), with the
# pid file `sys.argv[1]`, waits until the holder wrote its pid, then runs the code `sys.argv[3]`.
CHILD = f"""
import pathlib, subprocess, sys, time
held = sys.argv[2]
pid_file = pathlib.Path(sys.argv[1])
if held != "none":
    subprocess.Popen(
        [sys.executable, "-c", {HOLDER!r}, str(pid_file)],
        stdin=subprocess.DEVNULL,
        stdout=None if held == "stdout" else subprocess.DEVNULL,
        stderr=None if held == "stderr" else subprocess.DEVNULL,
        start_new_session=True,
    )
    while not pid_file.exists() or not pid_file.read_text():
        time.sleep(0.01)
exec(sys.argv[3])
"""

DONE = "print('done', flush=True); sys.exit(0)"
STARTED = "print('started', flush=True); time.sleep(60)"

# Starts, in a session of its own, a grandchild on the inherited standard output that writes
# `late` after `sys.argv[1]` seconds and then exits; the child itself exits at once.
LATE_CHILD = (
    "import subprocess, sys; "
    "subprocess.Popen([sys.executable, '-c', "
    "'import sys, time; time.sleep(float(sys.argv[1])); print(\"late\", flush=True)', "
    "sys.argv[1]], stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, "
    "start_new_session=True); "
    "sys.exit(0)"
)


@pytest.fixture
def short_drain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set `PIPE_DRAIN` to two seconds for the test."""
    monkeypatch.setattr(process, "PIPE_DRAIN", SHORT_DRAIN)


def _request(
    tmp_path: Path, holder_file: Path, held: str, code: str, seconds: float | None
) -> ProcessRequest:
    return ProcessRequest(
        argv=python_argv(CHILD, str(holder_file), held, code),
        cwd=tmp_path,
        time_limit=None if seconds is None else timedelta(seconds=seconds),
    )


def _holder(holder_file: Path) -> int:
    return int(holder_file.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("streaming", "held", "seconds"),
    [
        pytest.param(False, "stdout", 60, id="run_process-stdout"),
        pytest.param(False, "stderr", 60, id="run_process-stderr"),
        pytest.param(True, "stdout", 60, id="run_streaming-stdout"),
        pytest.param(False, "stdout", None, id="run_process-no-limit"),
        pytest.param(True, "stdout", None, id="run_streaming-no-limit"),
    ],
)
@pytest.mark.usefixtures("short_drain")
def test_a_child_that_ended_beside_a_holder_returns_after_the_drain(
    tmp_path: Path, holder_file: Path, streaming: bool, held: str, seconds: float | None
) -> None:
    request = _request(tmp_path, holder_file, held, DONE, seconds)
    recorder = Recorder()
    start = time.monotonic()

    result = run_streaming(request, recorder) if streaming else run_process(request)

    took = time.monotonic() - start
    assert is_gone(_holder(holder_file), within=0) is False
    assert result.exit_status == 0
    assert result.timed_out is False
    assert "done" in result.stdout
    if streaming:
        assert ("stdout", "done") in recorder.calls
    assert 2 <= took < 20


@pytest.mark.parametrize(
    "streaming", [pytest.param(False, id="run_process"), pytest.param(True, id="run_streaming")]
)
@pytest.mark.parametrize(
    "delay",
    [
        pytest.param(None, id="no-descendant"),
        pytest.param(1.0, id="late-1s"),
        pytest.param(1.5, id="late-1.5s"),
    ],
)
@pytest.mark.usefixtures("short_drain")
def test_pipes_that_close_within_the_drain_give_the_whole_output(
    tmp_path: Path, streaming: bool, delay: float | None
) -> None:
    argv = (
        python_argv("import sys; sys.exit(0)")
        if delay is None
        else python_argv(LATE_CHILD, str(delay))
    )
    request = ProcessRequest(argv=argv, cwd=tmp_path, time_limit=timedelta(seconds=60))
    start = time.monotonic()

    result = run_streaming(request, Recorder()) if streaming else run_process(request)

    took = time.monotonic() - start
    if delay is not None:
        assert "late" in result.stdout
        assert 1 <= took < 15


@pytest.mark.parametrize(
    "held", [pytest.param("stdout", id="holder"), pytest.param("none", id="no-holder")]
)
@pytest.mark.usefixtures("short_drain")
def test_the_read_after_the_kill_is_bounded_by_the_drain(
    tmp_path: Path, holder_file: Path, held: str
) -> None:
    request = _request(tmp_path, holder_file, held, STARTED, 3)
    start = time.monotonic()

    result = run_process(request)

    took = time.monotonic() - start
    assert result.exit_status is None
    assert result.timed_out is True
    assert "started" in result.stdout
    assert 3 <= took < 25


def _raise_on_started(_stream: Stream, line: str) -> bool:
    if line == "started":
        raise RuntimeError("callback failed")
    return False


@pytest.mark.parametrize(
    ("on_line", "seconds", "outcome"),
    [
        pytest.param(Recorder(), 3, "timed_out", id="time-limit"),
        pytest.param(Recorder(frozenset({"started"})), 60, "stopped", id="stop"),
        pytest.param(_raise_on_started, 60, "raised", id="raise"),
    ],
)
@pytest.mark.usefixtures("short_drain")
def test_streaming_ended_by_a_kill_does_not_abandon_output(
    tmp_path: Path,
    holder_file: Path,
    on_line: Callable[[Stream, str], bool],
    seconds: float,
    outcome: str,
) -> None:
    request = _request(tmp_path, holder_file, "stdout", STARTED, seconds)

    if outcome == "raised":
        with pytest.raises(RuntimeError, match="callback failed"):
            run_streaming(request, on_line)
        return
    result = run_streaming(request, on_line)

    assert result.timed_out is (outcome == "timed_out")
    assert result.stopped is (outcome == "stopped")


def test_drain_is_five_seconds_and_output_is_not_abandoned_by_default() -> None:
    assert timedelta(seconds=5) == process.PIPE_DRAIN


@pytest.mark.parametrize(
    "streaming", [pytest.param(False, id="run_process"), pytest.param(True, id="run_streaming")]
)
@pytest.mark.usefixtures("short_drain")
def test_a_limit_during_the_drain_times_the_call_out(
    tmp_path: Path, holder_file: Path, streaming: bool
) -> None:
    request = _request(tmp_path, holder_file, "stdout", DONE, 1)

    result = run_streaming(request, Recorder()) if streaming else run_process(request)

    assert result.timed_out is True
    if not streaming:
        assert result.exit_status is None


@pytest.mark.usefixtures("short_drain")
def test_the_last_line_without_a_line_feed_is_not_passed_after_the_drain(
    tmp_path: Path, holder_file: Path
) -> None:
    code = "sys.stdout.write('a\\nb'); sys.stdout.flush(); sys.exit(0)"
    request = _request(tmp_path, holder_file, "stdout", code, 60)
    recorder = Recorder()

    result = run_streaming(request, recorder)

    lines = [line for _stream, line in recorder.calls]
    assert "a" in lines
    assert "b" not in lines
    assert result.stdout.endswith("b")
