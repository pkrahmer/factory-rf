"""The start wrapper's defaults, folders and rules faults, in the test process."""

import errno
import io
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from confine_support import USAGE, Replaced, Steps, write_rules
from factory.domain.confinement import Confinement
from factory.entry.confine import main

NOT_FOUND = "No such file or directory"


class Case:
    """One call of `main` with some defaults left `None`, and what it must leave behind."""

    def __init__(self, status: int, stderr: str, calls: list[str]) -> None:
        """Hold the expected status, standard error and calls of the recorded steps."""
        self.status = status
        self.stderr = stderr
        self.calls = calls


_Row = Callable[[Path, pytest.MonkeyPatch, Steps], tuple[int, Case]]


def _argv_from_sys_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, steps: Steps
) -> tuple[int, Case]:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(sys, "argv", ["factory-confine", "--rules", str(missing), "--", "prog"])
    status = main(restrict=steps.restrict, replace=steps.replace)
    line = f"factory-confine: cannot read the rules {missing}: [Errno 2] {NOT_FOUND}: '{missing}'\n"
    return status, Case(1, line, [])


def _usage_from_sys_argv(
    _tmp_path: Path, monkeypatch: pytest.MonkeyPatch, steps: Steps
) -> tuple[int, Case]:
    monkeypatch.setattr(sys, "argv", ["factory-confine"])
    status = main(restrict=steps.restrict, replace=steps.replace)
    return status, Case(1, USAGE, [])


def _kernel_abi(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch, steps: Steps) -> tuple[int, Case]:
    rules = write_rules(tmp_path, [tmp_path / "A"], [], tmp_path / "t")
    steps.replace_fault = OSError(errno.ENOENT, NOT_FOUND)
    status = main(
        ["--rules", str(rules), "--", "prog"], restrict=steps.restrict, replace=steps.replace
    )
    line = f"factory-confine: cannot start prog: {NOT_FOUND}\n"
    return status, Case(1, line, ["restrict", "replace"])


def _restrict_writes(
    tmp_path: Path, _monkeypatch: pytest.MonkeyPatch, steps: Steps
) -> tuple[int, Case]:
    missing = tmp_path / "missing.txt"
    rules = write_rules(tmp_path, [], [missing], tmp_path / "t")
    status = main(["--rules", str(rules), "--", "prog"], abi=lambda: 3, replace=steps.replace)
    return status, Case(1, f"factory-confine: cannot open {missing}: {NOT_FOUND}\n", [])


def _replace_process(
    tmp_path: Path, _monkeypatch: pytest.MonkeyPatch, steps: Steps
) -> tuple[int, Case]:
    program = tmp_path / "no-such-program"
    rules = write_rules(tmp_path, [], [], tmp_path / "t")
    status = main(
        ["--rules", str(rules), "--", str(program)], abi=lambda: 3, restrict=steps.restrict
    )
    return status, Case(1, f"factory-confine: cannot start {program}: {NOT_FOUND}\n", ["restrict"])


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(_argv_from_sys_argv, id="argv"),
        pytest.param(_usage_from_sys_argv, id="argv-usage"),
        pytest.param(_kernel_abi, id="abi"),
        pytest.param(_restrict_writes, id="restrict"),
        pytest.param(_replace_process, id="replace"),
    ],
)
def test_main_left_its_defaults_uses_sys_argv_sys_stderr_and_the_adapters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    row: _Row,
) -> None:
    steps = Steps()

    status, case = row(tmp_path, monkeypatch, steps)

    assert status == case.status
    assert capsys.readouterr().err == case.stderr
    assert steps.calls == case.calls


@pytest.mark.parametrize(
    ("make", "line"),
    [
        pytest.param(lambda base: (base / "A").mkdir(), None, id="existing-folder"),
        pytest.param(
            lambda base: (base / "f").write_text("f\n", encoding="utf-8"),
            "factory-confine: cannot make the folder <tmp>/f/sub: Not a directory\n",
            id="under-a-file",
        ),
    ],
)
def test_a_folder_of_the_rules_that_exists_is_no_fault_and_one_under_a_file_stops_the_wrapper(
    tmp_path: Path, make: Callable[[Path], object], line: str | None
) -> None:
    make(tmp_path)
    folder = tmp_path / ("A" if line is None else "f/sub")
    rules = write_rules(tmp_path, [folder], [], tmp_path / "t")
    steps = Steps()
    stderr = io.StringIO()

    def run() -> int:
        return main(
            ["--rules", str(rules), "--", "prog"],
            stderr=stderr,
            abi=lambda: 3,
            restrict=steps.restrict,
            replace=steps.replace,
        )

    if line is None:
        with pytest.raises(Replaced):
            run()
        assert [folders for folders, _files in steps.restricted] == [[folder, tmp_path / "t"]]
        assert stderr.getvalue() == ""
    else:
        assert run() == 1
        assert stderr.getvalue() == line.replace("<tmp>", str(tmp_path))
        assert steps.calls == []


def _validation_text(text: str) -> str:
    with pytest.raises(ValidationError) as raised:
        Confinement.model_validate_json(text)
    return str(raised.value)


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        pytest.param(None, lambda path: f"[Errno 2] {NOT_FOUND}: '{path}'", id="missing"),
        pytest.param(
            "not json\n",
            lambda _path: _validation_text("not json\n").replace("\n", " "),
            id="not-json",
        ),
    ],
)
def test_rules_that_cannot_be_read_are_one_line_with_the_errors_text(
    tmp_path: Path, text: str | None, fault: Callable[[Path], str]
) -> None:
    path = tmp_path / "rules.json"
    if text is not None:
        path.write_text(text, encoding="utf-8")
    steps = Steps()
    stderr = io.StringIO()

    status = main(
        ["--rules", str(path), "--", "prog"],
        stderr=stderr,
        abi=lambda: 3,
        restrict=steps.restrict,
        replace=steps.replace,
    )

    assert status == 1
    assert stderr.getvalue() == f"factory-confine: cannot read the rules {path}: {fault(path)}\n"
    assert steps.calls == []
