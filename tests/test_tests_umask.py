"""The tests' umask: every test runs under `0o022`, whatever umask pytest was started under."""

import os
import stat
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import TESTS_UMASK
from factory.adapters.process import ProcessRequest, run_process

ROOT = Path(__file__).parent.parent
TEST_ID = "tests/test_tests_umask.py::test_a_test_runs_under_the_tests_umask"


def test_a_test_runs_under_the_tests_umask(tmp_path: Path) -> None:
    current = os.umask(0)
    os.umask(current)
    file = tmp_path / "file"
    file.write_text("text\n", encoding="utf-8")
    folder = tmp_path / "folder"
    folder.mkdir()

    assert current == 0o022
    assert current == TESTS_UMASK
    assert stat.S_IMODE(file.stat().st_mode) == 0o644
    assert stat.S_IMODE(folder.stat().st_mode) == 0o755


@pytest.mark.parametrize("starting_umask", ["000", "002", "022", "077"])
def test_the_tests_umask_holds_whatever_umask_pytest_was_started_under(
    tmp_path: Path, starting_umask: str
) -> None:
    result = run_process(
        ProcessRequest(
            argv=[
                "sh",
                "-c",
                f'umask {starting_umask}; exec "$@"',
                "sh",
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "--no-header",
                TEST_ID,
            ],
            cwd=ROOT,
            env={
                "PATH": os.environ["PATH"],
                "HOME": os.environ["HOME"],
                "TMPDIR": str(tmp_path),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            time_limit=timedelta(seconds=60),
            merge_stderr=True,
        )
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert result.exit_status == 0, result.stdout
    assert lines[-1].startswith("1 passed in "), result.stdout
