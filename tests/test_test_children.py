"""The Python children the tests start write no bytecode, and every shebang they write says `-B`."""

import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from process_support import python_argv
from run_layout_support import write_script

TESTS = Path(__file__).parent
# The braces are escaped, so this module's own text holds no shebang the pattern finds.
UNFLAGGED_SHEBANG = re.compile(r"#!\{sys\.executable\}(?! -B)")


def unflagged_shebangs(text: str) -> list[str]:
    """The shebangs of the test interpreter in `text` that `-B` does not follow."""
    return UNFLAGGED_SHEBANG.findall(text)


@pytest.mark.parametrize(
    ("command", "writes_bytecode"),
    [
        pytest.param(
            lambda d: [str(write_script(d / "child", "import standin\n"))],
            False,
            id="write-script",
        ),
        pytest.param(lambda _: python_argv("import standin"), False, id="python-argv"),
        pytest.param(lambda _: [sys.executable, "-S", "-c", "import standin"], True, id="plain"),
    ],
)
def test_a_child_started_by_the_helpers_writes_no_bytecode(
    tmp_path: Path, command: Callable[[Path], list[str]], writes_bytecode: bool
) -> None:
    (tmp_path / "standin.py").write_text("x = 1\n", encoding="utf-8")

    subprocess.run(  # noqa: S603  (the test interpreter, no input)
        command(tmp_path), cwd=tmp_path, env={}, check=True
    )

    assert (tmp_path / "__pycache__").exists() is writes_bytecode


@pytest.mark.parametrize(
    ("text", "found"),
    [
        pytest.param('f"#!' + "{sys.executable}" + '\\n"', True, id="plain"),
        pytest.param('f"#!' + "{sys.executable}" + ' -B\\n"', False, id="bytecode-off"),
    ],
)
def test_the_scan_finds_a_shebang_without_the_flag(text: str, found: bool) -> None:
    assert bool(unflagged_shebangs(text)) is found


def test_no_test_writes_a_shebang_of_the_interpreter_without_the_flag() -> None:
    found = {
        str(path.relative_to(TESTS)): unflagged_shebangs(path.read_text(encoding="utf-8"))
        for path in sorted(TESTS.rglob("*.py"))
    }

    assert {name: hits for name, hits in found.items() if hits} == {}
