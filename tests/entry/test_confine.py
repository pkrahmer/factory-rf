"""The start wrapper: it confines its writes, sets `TMPDIR` and becomes the command, or stops."""

import io
import json
import os
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.confine import main

USAGE = "factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]\n"
WRAPPER = [sys.executable, "-m", "factory.entry.confine"]


def _rules(tmp_path: Path, folders: list[Path], files: list[Path], temporary: Path | str) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {
                "folders": [str(folder) for folder in folders],
                "files": [str(file) for file in files],
                "temporary_directory": str(temporary),
            }
        ),
        encoding="utf-8",
    )
    return path


def _confine(
    rules: Path, *command: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603  (fixed interpreter, arguments written by the test)
        [*WRAPPER, "--rules", str(rules), "--", *command],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _main(argv: list[str], abi: int) -> tuple[int, str]:
    stderr = io.StringIO()
    status = main(argv, stderr=stderr, abi=lambda: abi)
    return status, stderr.getvalue()


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Folders A and P under `tmp_path`, an existing file f.txt in P, and its rules file."""
    (tmp_path / "A").mkdir()
    (tmp_path / "P").mkdir()
    (tmp_path / "P" / "f.txt").write_text("f\n", encoding="utf-8")
    return _rules(tmp_path, [tmp_path / "A"], [tmp_path / "P" / "f.txt"], tmp_path / "run")


@pytest.mark.parametrize(
    ("script", "relative", "content"),
    [
        pytest.param('echo x > "$1/A/new.txt"', "A/new.txt", "x\n", id="new-file-in-folder"),
        pytest.param('echo y >> "$1/P/f.txt"', "P/f.txt", "f\ny\n", id="append-to-file"),
        pytest.param('echo x > "$TMPDIR/new.txt"', "run/new.txt", "x\n", id="new-file-in-tmpdir"),
        pytest.param('echo x > "$1/P/new.txt"', "P/new.txt", None, id="new-file-beside-file"),
        pytest.param('echo x > "$1/new.txt"', "new.txt", None, id="new-file-in-tmp-path"),
        pytest.param('sh -c "echo x > $1/c"', "c", None, id="new-file-from-a-child"),
    ],
)
def test_the_command_writes_only_within_the_rules(
    tmp_path: Path, tree: Path, script: str, relative: str, content: str | None
) -> None:
    result = _confine(tree, "sh", "-c", script, "sh", str(tmp_path))

    if content is None:
        assert result.returncode != 0
        assert "Permission denied" in result.stderr
        assert not (tmp_path / relative).exists()
    else:
        assert result.returncode == 0, result.stderr
        assert (tmp_path / relative).read_text(encoding="utf-8") == content


def test_the_command_gets_its_own_temporary_folder_and_the_wrapper_environment(
    tmp_path: Path, tree: Path
) -> None:
    code = (
        "import os, stat; t = os.environ['TMPDIR']; m = os.lstat(t).st_mode; "
        "print(t); print(stat.S_ISDIR(m)); print(oct(stat.S_IMODE(m))); print(os.environ['EXTRA'])"
    )

    result = _confine(tree, sys.executable, "-c", code, env={**os.environ, "EXTRA": "kept"})

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [str(tmp_path / "run"), "True", "0o700", "kept"]


def test_the_wrapper_exits_and_prints_as_the_command(tree: Path) -> None:
    result = _confine(tree, "sh", "-c", "echo out; exit 7")

    assert (result.stdout, result.returncode) == ("out\n", 7)


@pytest.mark.parametrize(
    ("folder", "script", "outcome"),
    [
        pytest.param("new/deeper", 'echo x > "$1/new/deeper/a.txt"', "written", id="made"),
        pytest.param("new/deeper", 'echo x > "$1/new/a.txt"', "denied", id="parent-not-allowed"),
        pytest.param("f/sub", 'touch "$1/ran"', "stopped", id="under-a-file"),
    ],
)
def test_a_missing_folder_of_the_rules_is_made_or_stops_the_wrapper(
    tmp_path: Path, folder: str, script: str, outcome: str
) -> None:
    (tmp_path / "f").write_text("f\n", encoding="utf-8")
    rules = _rules(tmp_path, [tmp_path / folder], [], tmp_path / "run")

    result = _confine(rules, "sh", "-c", script, "sh", str(tmp_path))

    if outcome == "written":
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "new" / "deeper" / "a.txt").read_text(encoding="utf-8") == "x\n"
    elif outcome == "denied":
        assert result.returncode != 0
        assert "Permission denied" in result.stderr
        assert not (tmp_path / "new" / "a.txt").exists()
    else:
        assert result.returncode == 1
        assert result.stderr == (
            f"factory-confine: cannot make the folder {tmp_path}/f/sub: Not a directory\n"
        )
        assert not (tmp_path / "ran").exists()
        assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        pytest.param([], id="none"),
        pytest.param(["--rules"], id="rules-without-file"),
        pytest.param(["--rules", "F"], id="no-separator"),
        pytest.param(["--rules", "F", "--"], id="no-command"),
        pytest.param(["--", "touch", "M"], id="no-rules"),
        pytest.param(["--rules", "F", "touch", "M"], id="separator-missing"),
        pytest.param(["--settings", "F", "--", "touch", "M"], id="other-option"),
    ],
)
def test_wrong_arguments_print_the_usage_and_return_1(
    tmp_path: Path, tree: Path, arguments: list[str]
) -> None:
    marker = tmp_path / "ran"
    names = {"F": str(tree), "M": str(marker)}

    status, stderr = _main([names.get(word, word) for word in arguments], abi=0)

    assert (status, stderr) == (1, USAGE)
    assert not marker.exists()


def _no_file(_rules: Path, _run: Path) -> None:
    pass


def _not_utf_8(rules: Path, _run: Path) -> None:
    rules.write_bytes(b"\xff\n")


def _not_json(rules: Path, _run: Path) -> None:
    rules.write_text("not json\n", encoding="utf-8")


def _relative_path(rules: Path, run: Path) -> None:
    rules.write_text(
        json.dumps({"folders": ["relative"], "files": [], "temporary_directory": str(run)}),
        encoding="utf-8",
    )


def _unknown_key(rules: Path, run: Path) -> None:
    rules.write_text(
        json.dumps({"folders": [], "files": [], "temporary_directory": str(run), "other": []}),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "write",
    [
        pytest.param(_no_file, id="missing"),
        pytest.param(_not_utf_8, id="not-utf-8"),
        pytest.param(_not_json, id="not-json"),
        pytest.param(_relative_path, id="relative-path"),
        pytest.param(_unknown_key, id="unknown-key"),
    ],
)
def test_rules_that_cannot_be_read_return_1_with_one_line(
    tmp_path: Path, write: Callable[[Path, Path], None]
) -> None:
    rules = tmp_path / "rules.json"
    write(rules, tmp_path / "run")

    status, stderr = _main(["--rules", str(rules), "--", "touch", str(tmp_path / "ran")], abi=0)

    assert status == 1
    assert stderr.startswith(f"factory-confine: cannot read the rules {rules}: ")
    assert stderr.endswith("\n")
    assert stderr.count("\n") == 1
    assert not (tmp_path / "run").exists()
    assert not (tmp_path / "ran").exists()


@pytest.mark.parametrize("abi", [0, 2])
def test_a_kernel_below_abi_3_stops_the_wrapper_before_any_folder_is_made(
    tmp_path: Path, abi: int
) -> None:
    rules = _rules(tmp_path, [tmp_path / "missing"], [], tmp_path / "run")

    status, stderr = _main(["--rules", str(rules), "--", "touch", str(tmp_path / "ran")], abi=abi)

    assert (status, stderr) == (
        1,
        f"factory-confine: the kernel offers Landlock ABI {abi}, "
        "the write guard needs ABI 3 or higher\n",
    )
    assert not (tmp_path / "missing").exists()
    assert not (tmp_path / "run").exists()
    assert not (tmp_path / "ran").exists()


@pytest.mark.parametrize(
    "make",
    [
        pytest.param(lambda run, _target: run.mkdir(), id="folder"),
        pytest.param(lambda run, target: run.symlink_to(target), id="symbolic-link"),
    ],
)
def test_an_existing_temporary_folder_stops_the_wrapper(
    tmp_path: Path, make: Callable[[Path, Path], None]
) -> None:
    (tmp_path / "target").mkdir()
    run = tmp_path / "run"
    make(run, tmp_path / "target")
    rules = _rules(tmp_path, [], [], run)

    status, stderr = _main(["--rules", str(rules), "--", "touch", str(tmp_path / "ran")], abi=3)

    assert (status, stderr) == (
        1,
        f"factory-confine: cannot make the temporary folder {run}: File exists\n",
    )
    assert not (tmp_path / "ran").exists()


@pytest.mark.parametrize("fault", ["missing-file", "linked-folder"])
def test_a_rule_the_kernel_cannot_take_stops_the_wrapper(tmp_path: Path, fault: str) -> None:
    (tmp_path / "target").mkdir()
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "target")
    missing = tmp_path / "missing.txt"
    if fault == "missing-file":
        rules = _rules(tmp_path, [], [missing], tmp_path / "run")
        line = f"factory-confine: cannot open {missing}: No such file or directory\n"
    else:
        rules = _rules(tmp_path, [link], [], tmp_path / "run")
        line = f"factory-confine: {link} is a symbolic link\n"

    result = _confine(rules, "touch", str(tmp_path / "ran"))

    assert (result.returncode, result.stderr) == (1, line)
    assert not (tmp_path / "ran").exists()


def test_a_command_that_cannot_start_stops_the_wrapper(tmp_path: Path) -> None:
    rules = _rules(tmp_path, [], [], tmp_path / "run")

    result = _confine(rules, "no-such-program")

    assert (result.returncode, result.stderr) == (
        1,
        "factory-confine: cannot start no-such-program: No such file or directory\n",
    )


def test_the_console_script_beside_the_interpreter_prints_the_usage() -> None:
    script = Path(sys.executable).parent / "factory-confine"

    result = subprocess.run(  # noqa: S603  (the installed script, no arguments)
        [str(script)], capture_output=True, text=True, check=False
    )

    assert stat.S_ISREG(script.stat().st_mode)
    assert (result.returncode, result.stderr) == (1, USAGE)
