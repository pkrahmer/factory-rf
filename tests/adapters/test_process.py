"""The process wrapper, against real Python child processes."""

import time
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.adapters.process import ProcessRequest, run_process
from process_support import is_gone, python_argv
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT


def test_output_and_exit_status_come_back(tmp_path: Path) -> None:
    code = "import sys; print('out'); print('err', file=sys.stderr)"

    result = run_process(ProcessRequest(argv=python_argv(code), cwd=tmp_path))

    assert result.stdout == "out\n"
    assert result.stderr == "err\n"
    assert result.exit_status == 0
    assert result.timed_out is False
    assert result.duration >= timedelta(0)


def test_child_runs_in_the_given_working_directory(tmp_path: Path) -> None:
    code = "import os; print(os.getcwd())"

    result = run_process(ProcessRequest(argv=python_argv(code), cwd=tmp_path))

    assert Path(result.stdout.strip()) == tmp_path.resolve()


def test_non_zero_exit_status_is_returned_not_raised(tmp_path: Path) -> None:
    result = run_process(ProcessRequest(argv=python_argv("import sys; sys.exit(3)"), cwd=tmp_path))

    assert result.exit_status == 3


def test_merged_stderr_keeps_the_order_written(tmp_path: Path) -> None:
    code = (
        "import sys; "
        "print('a', flush=True); "
        "print('b', file=sys.stderr, flush=True); "
        "print('c', flush=True)"
    )

    result = run_process(ProcessRequest(argv=python_argv(code), cwd=tmp_path, merge_stderr=True))

    assert result.stdout == "a\nb\nc\n"
    assert result.stderr == ""


def test_given_env_is_the_whole_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_TEST_PARENT", "parent")
    code = (
        "import os; "
        "print(os.environ.get('FACTORY_TEST_PARENT')); "
        "print(os.environ.get('FACTORY_TEST_GIVEN'))"
    )

    given = run_process(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, env={"FACTORY_TEST_GIVEN": "given"})
    )
    inherited = run_process(ProcessRequest(argv=python_argv(code), cwd=tmp_path, env=None))

    assert given.stdout == "None\ngiven\n"
    assert inherited.stdout == "parent\nNone\n"


def test_child_is_killed_at_the_time_limit(tmp_path: Path) -> None:
    code = "import time; print('started', flush=True); time.sleep(60)"
    start = time.monotonic()

    result = run_process(
        ProcessRequest(argv=python_argv(code), cwd=tmp_path, time_limit=ROOMY_LIMIT)
    )

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert result.exit_status is None
    assert result.timed_out is True
    assert "started" in result.stdout


def test_grandchild_is_killed_with_the_child_at_the_time_limit(tmp_path: Path) -> None:
    pid_file = tmp_path / "grandchild.pid"
    code = (
        "import pathlib, subprocess, sys, time; "
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid)); "
        "print('started', flush=True); "
        "time.sleep(60)"
    )

    start = time.monotonic()

    # The roomy limit: under `make test`'s parallel workers the child may need seconds to start its
    # grandchild and write the pid file, and a kill before that leaves no pid.
    run_process(
        ProcessRequest(argv=python_argv(code, str(pid_file)), cwd=tmp_path, time_limit=ROOMY_LIMIT)
    )

    assert time.monotonic() - start < ROOMY_BOUND_SECONDS
    assert is_gone(int(pid_file.read_text(encoding="utf-8")))


def test_child_within_the_time_limit_keeps_its_exit_status(tmp_path: Path) -> None:
    result = run_process(
        ProcessRequest(
            argv=python_argv("import sys; sys.exit(4)"),
            cwd=tmp_path,
            time_limit=timedelta(seconds=30),
        )
    )

    assert result.timed_out is False
    assert result.exit_status == 4


def test_missing_executable_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        run_process(ProcessRequest(argv=[str(tmp_path / "missing")], cwd=tmp_path))


@pytest.mark.parametrize(
    ("argv", "time_limit"),
    [
        ([], None),
        (["true"], timedelta(0)),
        (["true"], timedelta(seconds=-1)),
    ],
)
def test_request_rejects_empty_argv_and_non_positive_time_limit(
    tmp_path: Path, argv: list[str], time_limit: timedelta | None
) -> None:
    with pytest.raises(ValidationError):
        ProcessRequest(argv=argv, cwd=tmp_path, time_limit=time_limit)


@pytest.mark.parametrize("time_limit", [timedelta(seconds=1), None])
def test_request_accepts_positive_or_no_time_limit(
    tmp_path: Path, time_limit: timedelta | None
) -> None:
    request = ProcessRequest(argv=["true"], cwd=tmp_path, time_limit=time_limit)

    assert request.time_limit == time_limit


def test_undecodable_output_bytes_are_replaced(tmp_path: Path) -> None:
    code = "import sys; sys.stdout.buffer.write(b'\\xff ok\\n')"

    result = run_process(ProcessRequest(argv=python_argv(code), cwd=tmp_path))

    assert result.stdout == "� ok\n"


def test_shell_characters_reach_the_child_as_written(tmp_path: Path) -> None:
    argument = "$HOME; echo x"

    result = run_process(
        ProcessRequest(argv=python_argv("import sys; print(sys.argv[1])", argument), cwd=tmp_path)
    )

    assert result.stdout == f"{argument}\n"
