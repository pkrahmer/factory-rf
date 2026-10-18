"""The `exec`'s refusals in the test process: no program, or none that runs on the given `PATH`."""

import shutil
from pathlib import Path

import pytest

from factory.adapters.process import replace_process

PROGRAM = "factory-test-prog"


@pytest.fixture
def folders(tmp_path: Path) -> Path:
    """A folder `bin` holding PROGRAM without the execute bit, and an empty folder `empty`."""
    (tmp_path / "bin").mkdir()
    (tmp_path / "empty").mkdir()
    program = tmp_path / "bin" / PROGRAM
    program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    program.chmod(0o644)
    return tmp_path


@pytest.mark.parametrize(
    ("argv", "folder", "expected"),
    [
        pytest.param([], "empty", ValueError, id="empty-argv"),
        pytest.param([PROGRAM], "bin", PermissionError, id="not-executable-on-env-path"),
        pytest.param([PROGRAM], "empty", FileNotFoundError, id="missing-on-env-path"),
    ],
)
def test_replace_process_refuses_in_the_test_process_on_the_path_of_env(
    folders: Path, argv: list[str], folder: str, expected: type[Exception]
) -> None:
    assert shutil.which(PROGRAM) is None

    with pytest.raises(expected) as raised:
        replace_process(argv, {"PATH": str(folders / folder)})

    if expected is ValueError:
        assert str(raised.value) == "replace_process needs a program to start"
