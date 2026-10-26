"""The process result's fields, and the drain that stays once the child has ended."""

import contextlib
import os
import signal
import time
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters import process
from factory.adapters.process import ProcessRequest, ProcessResult, run_process, run_streaming
from process_support import Recorder, python_argv
from search_support import modules_matching
from source_search import SRC
from time_limits import ROOMY_BOUND_SECONDS

DRAIN = timedelta(seconds=1)

# Starts a grandchild in a session of its own on the inherited standard output, which sleeps 60
# seconds; writes its pid to `sys.argv[1]`, then prints `a` and exits.
HELD_CHILD = (
    "import pathlib, subprocess, sys; "
    "holder = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
    "stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True); "
    "pathlib.Path(sys.argv[1]).write_text(str(holder.pid)); "
    "print('a', flush=True); "
    "sys.exit(0)"
)

TWO_LINES = "import sys; print('one'); print('two'); sys.exit(3)"


@pytest.fixture
def holder_file(tmp_path: Path) -> Iterator[Path]:
    """The grandchild's pid file; a grandchild still running after the test is killed."""
    path = tmp_path / "holder.pid"
    yield path
    if path.exists() and path.read_text(encoding="utf-8"):
        with contextlib.suppress(ProcessLookupError):
            os.kill(int(path.read_text(encoding="utf-8")), signal.SIGKILL)


def test_the_result_has_no_output_abandoned_field() -> None:
    model: type[BaseModel] = ProcessResult

    assert list(ProcessResult.model_fields) == [
        "exit_status",
        "stdout",
        "stderr",
        "timed_out",
        "duration",
        "stopped",
    ]
    with pytest.raises(ValidationError):
        model(
            exit_status=0,
            stdout="",
            stderr="",
            timed_out=False,
            duration=timedelta(0),
            output_abandoned=True,
        )


@pytest.mark.parametrize(
    ("streaming", "held", "exit_status", "lines", "at_least"),
    [
        pytest.param(False, True, 0, ["a"], DRAIN.total_seconds(), id="run_process-held"),
        pytest.param(True, True, 0, ["a"], DRAIN.total_seconds(), id="run_streaming-held"),
        pytest.param(False, False, 3, ["one", "two"], 0.0, id="run_process-closed"),
    ],
)
def test_the_call_reads_for_the_drain_after_the_child_ended(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    holder_file: Path,
    streaming: bool,
    held: bool,
    exit_status: int,
    lines: list[str],
    at_least: float,
) -> None:
    monkeypatch.setattr(process, "PIPE_DRAIN", DRAIN)
    argv = python_argv(HELD_CHILD, str(holder_file)) if held else python_argv(TWO_LINES)
    request = ProcessRequest(argv=argv, cwd=tmp_path, time_limit=timedelta(seconds=60))
    recorder = Recorder()
    start = time.monotonic()

    result = run_streaming(request, recorder) if streaming else run_process(request)

    took = time.monotonic() - start
    assert result.exit_status == exit_status
    assert result.timed_out is False
    assert result.stdout.startswith("".join(f"{line}\n" for line in lines))
    if streaming:
        assert all(("stdout", line) in recorder.calls for line in lines)
    assert at_least <= took < ROOMY_BOUND_SECONDS


def test_no_module_holds_the_name_of_the_removed_field() -> None:
    assert modules_matching("output_abandoned", leave_out="", root=SRC) == []
