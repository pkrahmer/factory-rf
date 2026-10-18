"""The process module's one `exec`: the process becomes the command, or the call raises."""

import subprocess
import sys
from pathlib import Path

import pytest

from factory.adapters.process import replace_process

CHILD = """
from factory.adapters.process import replace_process
replace_process(["sh", "-c", "echo $X; exit 7"], {"X": "replaced", "PATH": "/usr/bin:/bin"})
"""


@pytest.mark.parametrize(
    ("argv", "path", "expected"),
    [
        pytest.param(None, None, ("replaced\n", 7), id="becomes-the-command"),
        pytest.param(["no-such-program"], None, FileNotFoundError, id="not-on-the-path"),
        pytest.param([], "/usr/bin:/bin", ValueError, id="empty-argv"),
    ],
)
def test_replace_process_becomes_the_command_or_raises_and_this_process_goes_on(
    tmp_path: Path,
    argv: list[str] | None,
    path: str | None,
    expected: tuple[str, int] | type[Exception],
) -> None:
    if isinstance(expected, tuple):
        result = subprocess.run(  # noqa: S603  (fixed interpreter, code written by the test)
            [sys.executable, "-c", CHILD], capture_output=True, text=True, check=False
        )

        assert (result.stdout, result.returncode) == expected
        return

    env = {"PATH": str(tmp_path) if path is None else path}

    with pytest.raises(expected):
        replace_process(argv or [], env)

    assert Path.cwd().exists()
