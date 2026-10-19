"""A stop on a stream's last line, one without a newline, stops `run_streaming` at once."""

import time
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, Stream, run_streaming
from process_support import Recorder, is_gone, python_argv

RETURNS_WITHIN_SECONDS = 10

# Writes its pid, then `line` without a newline on descriptor `fd`, closes that descriptor and
# sleeps with the other one open, or exits at once when told to (a run that is not stopped).
CHILD = (
    "import os, pathlib, sys, time; "
    "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); "
    "fd = int(sys.argv[2]); "
    "os.write(fd, sys.argv[3].encode()); "
    "os.close(fd); "
    "os._exit(0) if sys.argv[4] == 'exit' else time.sleep(60)"
)


@pytest.mark.parametrize(
    ("stream", "line", "stopped", "exit_status"),
    [
        pytest.param("stdout", "go", True, None, id="stdout"),
        pytest.param("stderr", "go", True, None, id="stderr"),
        pytest.param("stdout", "gone", False, 0, id="no-stop"),
    ],
)
def test_a_stop_on_a_last_line_without_a_newline_stops_the_call_at_once(
    tmp_path: Path,
    stream: Stream,
    line: str,
    stopped: bool,  # noqa: FBT001 - a column of the table
    exit_status: int | None,
) -> None:
    pid_file = tmp_path / "child.pid"
    fd = "1" if stream == "stdout" else "2"
    recorder = Recorder(stop_on=frozenset({"go"}))
    request = ProcessRequest(
        argv=python_argv(CHILD, str(pid_file), fd, line, "sleep" if stopped else "exit"),
        cwd=tmp_path,
        time_limit=timedelta(seconds=30),
    )

    started = time.monotonic()
    result = run_streaming(request, recorder)
    elapsed = time.monotonic() - started

    assert recorder.calls == [(stream, line)]
    assert result.stopped is stopped
    assert result.exit_status == exit_status
    if stopped:
        assert result.timed_out is False
        assert elapsed < RETURNS_WITHIN_SECONDS
        assert is_gone(int(pid_file.read_text(encoding="utf-8")))
