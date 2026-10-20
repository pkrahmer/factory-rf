"""Streaming a process's output line by line, against real Python child processes."""

import threading
import time
from datetime import timedelta
from pathlib import Path

import pytest

import factory.adapters.process
from factory.adapters.process import (
    ProcessRequest,
    ProcessResult,
    Stream,
    run_process,
    run_streaming,
)
from process_support import Recorder, is_gone, python_argv
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

# A child that starts a grandchild, writes its pid to `sys.argv[1]` and then runs `REST`.
GRANDCHILD = (
    "import pathlib, subprocess, sys, time; "
    "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
    "pathlib.Path(sys.argv[1]).write_text(str(p.pid)); "
)
RETURNS_WITHIN_SECONDS = 20


def test_every_line_of_both_streams_reaches_the_callback_on_the_calling_thread(
    tmp_path: Path,
) -> None:
    code = (
        "import sys; "
        "print('one', flush=True); "
        "print('two', flush=True); "
        "print('err', file=sys.stderr, flush=True); "
        "sys.exit(3)"
    )
    recorder = Recorder()

    result = run_streaming(ProcessRequest(argv=python_argv(code), cwd=tmp_path), recorder)

    assert [line for stream, line in recorder.calls if stream == "stdout"] == ["one", "two"]
    assert [line for stream, line in recorder.calls if stream == "stderr"] == ["err"]
    assert len(recorder.calls) == 3
    assert set(recorder.threads) == {threading.get_ident()}
    assert result.exit_status == 3
    assert result.stdout == "one\ntwo\n"
    assert result.stderr == "err\n"
    assert result.stopped is False
    assert result.timed_out is False


@pytest.mark.parametrize(
    ("code", "line", "stdout"),
    [
        pytest.param("import sys; sys.stdout.write('tail')", "tail", "tail", id="no-line-feed"),
        pytest.param(
            "import sys; sys.stdout.buffer.write(b'\\xff ok\\n')",
            "� ok",
            "� ok\n",
            id="not-utf-8",
        ),
    ],
)
def test_last_line_and_undecodable_bytes_reach_the_callback(
    tmp_path: Path, code: str, line: str, stdout: str
) -> None:
    recorder = Recorder()

    result = run_streaming(ProcessRequest(argv=python_argv(code), cwd=tmp_path), recorder)

    assert recorder.calls == [("stdout", line)]
    assert result.stdout == stdout


@pytest.mark.parametrize(
    ("rest", "stdout"),
    [
        pytest.param(
            "print('go', flush=True); time.sleep(60); print('after', flush=True)",
            "go\n",
            id="before-a-sleep",
        ),
        pytest.param(
            "sys.stdout.write('go\\nlater\\n'); sys.stdout.flush(); time.sleep(60)",
            None,
            id="same-chunk",
        ),
    ],
)
def test_callback_saying_stop_on_standard_output_kills_the_group_at_once(
    tmp_path: Path, rest: str, stdout: str | None
) -> None:
    pid_file = tmp_path / "grandchild.pid"
    recorder = Recorder(stop_on=frozenset({"go"}))
    start = time.monotonic()

    result = run_streaming(
        ProcessRequest(argv=python_argv(GRANDCHILD + rest, str(pid_file)), cwd=tmp_path),
        recorder,
    )

    assert time.monotonic() - start < RETURNS_WITHIN_SECONDS
    assert recorder.calls == [("stdout", "go")]
    assert result.stopped is True
    assert result.exit_status is None
    assert result.timed_out is False
    if stdout is not None:
        assert result.stdout == stdout
    assert is_gone(int(pid_file.read_text(encoding="utf-8")))


def test_callback_saying_stop_on_standard_error_kills_the_group_at_once(
    tmp_path: Path,
) -> None:
    pid_file = tmp_path / "grandchild.pid"
    rest = (
        "print('go', file=sys.stderr, flush=True); "
        "time.sleep(60); "
        "print('after', file=sys.stderr, flush=True)"
    )
    recorder = Recorder(stop_on=frozenset({"go"}))
    start = time.monotonic()

    result = run_streaming(
        ProcessRequest(argv=python_argv(GRANDCHILD + rest, str(pid_file)), cwd=tmp_path),
        recorder,
    )

    assert time.monotonic() - start < RETURNS_WITHIN_SECONDS
    assert recorder.calls == [("stderr", "go")]
    assert result.stopped is True
    assert result.exit_status is None
    assert result.timed_out is False
    assert result.stderr == "go\n"
    assert is_gone(int(pid_file.read_text(encoding="utf-8")))


def test_child_is_killed_at_the_time_limit_and_no_later_line_is_passed(tmp_path: Path) -> None:
    code = "import time; print('started', flush=True); time.sleep(60); print('late', flush=True)"
    recorder = Recorder()
    start = time.monotonic()

    result = run_streaming(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, time_limit=ROOMY_LIMIT),
        recorder,
    )

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is True
    assert result.stopped is False
    assert result.exit_status is None
    assert "started" in result.stdout
    assert "late" not in [line for _, line in recorder.calls]


def test_child_that_closed_its_streams_is_killed_at_the_time_limit(tmp_path: Path) -> None:
    pid_file = tmp_path / "child.pid"
    code = (
        "import os, pathlib, sys, time; "
        "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); "
        "os.close(1); os.close(2); "
        "time.sleep(60)"
    )
    start = time.monotonic()

    result = run_streaming(
        ProcessRequest(
            argv=python_argv(code, str(pid_file)),
            cwd=tmp_path,
            time_limit=ROOMY_LIMIT,
        ),
        Recorder(),
    )

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.timed_out is True
    assert result.stopped is False
    assert result.exit_status is None
    assert is_gone(int(pid_file.read_text(encoding="utf-8")))


def test_callback_that_raises_kills_the_child_and_the_error_propagates(tmp_path: Path) -> None:
    code = "import os, time; print(os.getpid(), flush=True); time.sleep(60)"
    lines: list[str] = []

    def on_line(_stream: Stream, line: str) -> bool:
        lines.append(line)
        raise RuntimeError("callback failed")

    with pytest.raises(RuntimeError, match="callback failed"):
        run_streaming(ProcessRequest(argv=python_argv(code), cwd=tmp_path), on_line)

    assert is_gone(int(lines[0]))


def test_merged_standard_error_comes_as_standard_output_in_the_order_written(
    tmp_path: Path,
) -> None:
    code = (
        "import sys; "
        "print('a', flush=True); "
        "print('b', file=sys.stderr, flush=True); "
        "print('c', flush=True)"
    )
    recorder = Recorder()

    result = run_streaming(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, merge_stderr=True), recorder
    )

    assert recorder.calls == [("stdout", "a"), ("stdout", "b"), ("stdout", "c")]
    assert result.stderr == ""


def test_missing_executable_raises_file_not_found_without_a_call(tmp_path: Path) -> None:
    recorder = Recorder()

    with pytest.raises(FileNotFoundError):
        run_streaming(ProcessRequest(argv=[str(tmp_path / "missing")], cwd=tmp_path), recorder)

    assert recorder.calls == []


def test_lines_reach_the_callback_while_the_child_runs(tmp_path: Path) -> None:
    signal_file = tmp_path / "signal"
    code = (
        "import pathlib, sys, time; "
        "print('first', flush=True); "
        "signal = pathlib.Path(sys.argv[1]); "
        "[time.sleep(0.01) for _ in iter(lambda: signal.exists(), True)]; "
        "print('second', flush=True)"
    )
    lines: list[str] = []

    def on_line(_stream: Stream, line: str) -> bool:
        lines.append(line)
        if line == "first":
            signal_file.write_text("go", encoding="utf-8")
        return False

    result = run_streaming(
        ProcessRequest(
            argv=python_argv(code, str(signal_file)),
            cwd=tmp_path,
            time_limit=timedelta(seconds=RETURNS_WITHIN_SECONDS),
        ),
        on_line,
    )

    assert lines == ["first", "second"]
    assert result.timed_out is False
    assert result.exit_status == 0


@pytest.mark.parametrize(
    ("code", "env", "expected"),
    [
        pytest.param("import os; print(os.getcwd())", None, "{cwd}", id="working-directory"),
        pytest.param(
            "import os; print(os.environ.get('FACTORY_TEST_GIVEN'))",
            {"FACTORY_TEST_GIVEN": "given"},
            "given",
            id="environment",
        ),
        pytest.param("import sys; print(repr(sys.stdin.read()))", None, "''", id="standard-input"),
    ],
)
def test_child_starts_as_run_process_starts_it(
    tmp_path: Path, code: str, env: dict[str, str] | None, expected: str
) -> None:
    recorder = Recorder()

    run_streaming(
        ProcessRequest(
            argv=python_argv(code),
            cwd=tmp_path,
            env=env,
            time_limit=timedelta(seconds=RETURNS_WITHIN_SECONDS),
        ),
        recorder,
    )

    assert recorder.calls == [("stdout", expected.format(cwd=tmp_path.resolve()))]


def test_duration_covers_the_child_run_time(tmp_path: Path) -> None:
    code = "import time; print('waiting', flush=True); time.sleep(0.5)"

    result = run_streaming(ProcessRequest(argv=python_argv(code), cwd=tmp_path), Recorder())

    assert timedelta(seconds=0.5) <= result.duration < timedelta(seconds=RETURNS_WITHIN_SECONDS)


def test_run_process_shares_the_one_popen_line_and_reports_no_stop(tmp_path: Path) -> None:
    source = Path(factory.adapters.process.__file__).read_text(encoding="utf-8")
    popen_lines = [
        line for line in source.splitlines() if "subprocess.Popen(" in line.split("#")[0]
    ]

    result = run_process(ProcessRequest(argv=python_argv("print('x')"), cwd=tmp_path))
    built = ProcessResult(
        exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(0)
    )

    assert len(popen_lines) == 1
    assert result.stopped is False
    assert built.stopped is False
