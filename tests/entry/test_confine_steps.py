"""The start wrapper's steps in the test process, with the restriction and the `exec` recorded."""

import ast
import errno
import inspect
import io
import json
import os
import stat
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NoReturn

import pytest

from factory.domain.errors import ConfinementError
from factory.entry import confine
from factory.entry.confine import main

USAGE = "factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]\n"


class Replaced(Exception):
    """Raised by the recording `replace` in place of becoming the command."""


class Steps:
    """Records the calls to `restrict` and `replace` and what the disk held at `restrict`."""

    def __init__(
        self,
        restrict_fault: Exception | None = None,
        replace_fault: Exception | None = None,
    ) -> None:
        """Record every call; raise the given faults instead of returning."""
        self.calls: list[str] = []
        self.restricted: list[tuple[list[Path], list[Path]]] = []
        self.replaced: list[tuple[list[str], dict[str, str]]] = []
        self.watched: list[Path] = []
        self.seen: dict[Path, int | None] = {}
        self.restrict_fault = restrict_fault
        self.replace_fault = replace_fault

    def restrict(self, folders: Sequence[Path], files: Sequence[Path]) -> None:
        """Record the rules and the mode of every watched path at this moment."""
        self.calls.append("restrict")
        self.restricted.append((list(folders), list(files)))
        for path in self.watched:
            self.seen[path] = stat.S_IMODE(path.lstat().st_mode) if path.is_dir() else None
        if self.restrict_fault is not None:
            raise self.restrict_fault

    def replace(self, command: Sequence[str], environment: Mapping[str, str]) -> NoReturn:
        """Record the command and its environment, then stop the wrapper's run."""
        self.calls.append("replace")
        self.replaced.append((list(command), dict(environment)))
        raise self.replace_fault if self.replace_fault is not None else Replaced


@pytest.fixture
def rules(tmp_path: Path) -> Path:
    """Rules of a missing folder a/b, an existing file f and a missing temporary folder t."""
    (tmp_path / "f").write_text("f\n", encoding="utf-8")
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {
                "folders": [str(tmp_path / "a" / "b")],
                "files": [str(tmp_path / "f")],
                "temporary_directory": str(tmp_path / "t"),
            }
        ),
        encoding="utf-8",
    )
    return path


def _run(argv: list[str], steps: Steps, abi: int = 3) -> tuple[int, str]:
    stderr = io.StringIO()
    status = main(
        argv, stderr=stderr, abi=lambda: abi, restrict=steps.restrict, replace=steps.replace
    )
    return status, stderr.getvalue()


def test_restrict_gets_the_folders_the_temporary_folder_and_the_files_once_they_exist(
    tmp_path: Path, rules: Path
) -> None:
    steps = Steps()
    steps.watched = [tmp_path / "a" / "b", tmp_path / "t"]

    with pytest.raises(Replaced):
        _run(["--rules", str(rules), "--", "prog", "x"], steps)

    assert steps.restricted == [([tmp_path / "a" / "b", tmp_path / "t"], [tmp_path / "f"])]
    assert steps.seen[tmp_path / "a" / "b"] is not None
    assert steps.seen[tmp_path / "t"] == 0o700


def test_replace_gets_the_command_and_the_environment_with_tmpdir_after_restrict(
    tmp_path: Path, rules: Path
) -> None:
    steps = Steps()
    expected = {**os.environ, "TMPDIR": str(tmp_path / "t")}

    with pytest.raises(Replaced):
        _run(["--rules", str(rules), "--", "prog", "x"], steps)

    assert steps.calls == ["restrict", "replace"]
    assert steps.replaced == [(["prog", "x"], expected)]


@pytest.mark.parametrize(
    ("tail", "reaches"),
    [
        pytest.param(["--", "prog"], True, id="four-arguments"),
        pytest.param(["--"], False, id="three-arguments"),
    ],
)
def test_four_arguments_reach_the_command_and_three_print_the_usage(
    rules: Path, tail: list[str], reaches: bool
) -> None:
    steps = Steps()
    argv = ["--rules", str(rules), *tail]

    if reaches:
        with pytest.raises(Replaced):
            _run(argv, steps)
        assert [command for command, _environment in steps.replaced] == [["prog"]]
    else:
        assert _run(argv, steps) == (1, USAGE)
        assert steps.calls == []


def _restrict_fails(tmp_path: Path) -> tuple[Steps, str, list[str]]:
    detail = f"{tmp_path}/l is a symbolic link"
    return (
        Steps(restrict_fault=ConfinementError(detail)),
        f"factory-confine: {detail}\n",
        ["restrict"],
    )


def _replace_fails(_tmp_path: Path) -> tuple[Steps, str, list[str]]:
    fault = OSError(errno.ENOENT, "No such file or directory")
    line = "factory-confine: cannot start prog: No such file or directory\n"
    return Steps(replace_fault=fault), line, ["restrict", "replace"]


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(_restrict_fails, id="restrict"),
        pytest.param(_replace_fails, id="replace"),
    ],
)
def test_a_fault_of_restrict_or_replace_stops_the_wrapper_with_one_line(
    tmp_path: Path, rules: Path, fault: Callable[[Path], tuple[Steps, str, list[str]]]
) -> None:
    steps, line, calls = fault(tmp_path)

    status, stderr = _run(["--rules", str(rules), "--", "prog"], steps)

    assert (status, stderr) == (1, line)
    assert steps.calls == calls


@pytest.mark.parametrize(
    ("abi", "proceeds"),
    [
        pytest.param(0, False, id="0"),
        pytest.param(2, False, id="2"),
        pytest.param(3, True, id="3"),
    ],
)
def test_a_kernel_below_abi_3_makes_no_folder_and_calls_neither_step(
    tmp_path: Path, rules: Path, abi: int, proceeds: bool
) -> None:
    steps = Steps()
    argv = ["--rules", str(rules), "--", "prog", "x"]

    if proceeds:
        with pytest.raises(Replaced):
            _run(argv, steps, abi=abi)
        assert steps.calls == ["restrict", "replace"]
    else:
        assert _run(argv, steps, abi=abi)[0] == 1
        assert steps.calls == []
    assert (tmp_path / "a" / "b").exists() is proceeds
    assert (tmp_path / "t").exists() is proceeds


def _default_of(tree: ast.AST, parameter: str) -> str | None:
    # `<default> if <parameter> is None else <parameter>`, the way `main` already takes `abi`.
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.IfExp)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == parameter
            and isinstance(node.test.ops[0], ast.Is)
            and isinstance(node.body, ast.Name)
        ):
            return node.body.id
    return None


def test_restrict_and_replace_left_none_are_the_adapters_functions() -> None:
    tree = ast.parse(inspect.getsource(confine))
    main_tree = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    imported = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    parameters = inspect.signature(main).parameters

    assert ("factory.adapters.landlock", "restrict_writes") in imported
    assert ("factory.adapters.process", "replace_process") in imported
    assert parameters["restrict"].default is None
    assert parameters["replace"].default is None
    assert _default_of(main_tree, "restrict") == "restrict_writes"
    assert _default_of(main_tree, "replace") == "replace_process"
