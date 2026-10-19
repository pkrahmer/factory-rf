"""The mutants command: reads mutmut's results and prints the report or the names to run again."""

import re
import sys
from pathlib import Path

import pytest

from factory.entry.check_mutants import main

COMPLETE = (
    "    factory.domain.a.x_f__mutmut_1: killed\n"
    "    factory.domain.a.x_f__mutmut_2: survived\n"
    "    factory.domain.b.x_h__mutmut_1: survived\n"
)
NOT_CHECKED = COMPLETE + "    factory.domain.a.x_g__mutmut_1: not checked\n"
COMPLETE_LINES = [
    "factory.domain.a.x_f__mutmut_2: survived",
    "mutants: 1 killed, 1 survived, 0 timed out, 0 without tests, 0 not checked, "
    "0 other of 2 mutant(s) in 1 module(s)",
]
RERUN = (
    "    factory.domain.a.x_f__mutmut_1: killed\n"
    "    factory.domain.a.x_f__mutmut_2: survived\n"
    "    factory.domain.a.x_f__mutmut_3: not checked\n"
    "    factory.domain.a.x_f__mutmut_4: no tests\n"
    "    factory.domain.a.x_f__mutmut_5: caught by type check\n"
    "    factory.domain.b.x_h__mutmut_1: survived\n"
)


def _results_file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "results.txt"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("text", "options", "status", "lines", "from_sys_argv"),
    [
        pytest.param(COMPLETE, [], 0, re.escape("\n".join(COMPLETE_LINES)), False, id="complete"),
        pytest.param(
            NOT_CHECKED, [], 1, r"(?s).*\nmutants: partial, [^\n]*", False, id="not-checked"
        ),
        pytest.param(
            COMPLETE,
            ["--stopped-after", "540"],
            1,
            r"(?s).*\nmutants: [^\n]* \(stopped after 540 s\)",
            False,
            id="stopped",
        ),
        pytest.param(
            COMPLETE,
            ["--stopped-after", "1"],
            1,
            r"(?s).*\nmutants: [^\n]* \(stopped after 1 s\)",
            False,
            id="stopped-1",
        ),
        pytest.param(COMPLETE, [], 0, re.escape("\n".join(COMPLETE_LINES)), True, id="sys-argv"),
    ],
)
def test_the_report_is_printed_and_a_partial_run_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    *,
    text: str,
    options: list[str],
    status: int,
    lines: str,
    from_sys_argv: bool,
) -> None:
    arguments = [*options, str(_results_file(tmp_path, text)), "factory.domain.a"]

    if from_sys_argv:
        monkeypatch.setattr(sys, "argv", ["check-mutants", *arguments])
        result = main()
    else:
        result = main(arguments)

    out = capsys.readouterr().out
    assert result == status
    assert out.endswith("\n")
    assert re.fullmatch(lines, out.removesuffix("\n"))


def test_names_prints_the_mutants_to_run_again_and_succeeds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    results = _results_file(tmp_path, RERUN)

    result = main(["--names", str(results), "factory.domain.a", "factory.domain.c"])

    assert capsys.readouterr().out == (
        "factory.domain.a.x_f__mutmut_2\nfactory.domain.a.x_f__mutmut_3\nfactory.domain.a.x_f__mutmut_4\nfactory.domain.c.*\n"
    )
    assert result == 0


@pytest.mark.parametrize(
    ("text", "options", "modules", "error"),
    [
        pytest.param(
            None,
            [],
            ["factory.domain.a"],
            re.escape("check-mutants: cannot read ") + ".*",
            id="missing",
        ),
        pytest.param(
            "garbage\n",
            [],
            ["factory.domain.a"],
            re.escape("check-mutants: not a result line of mutmut: 'garbage'"),
            id="garbage",
        ),
        pytest.param(
            None,
            ["--names"],
            ["factory.domain.a"],
            re.escape("check-mutants: cannot read ") + ".*",
            id="names-missing",
        ),
        pytest.param(COMPLETE, [], [], None, id="no-module"),
        pytest.param(
            COMPLETE, ["--stopped-after", "0"], ["factory.domain.a"], None, id="stopped-after-0"
        ),
        pytest.param(
            COMPLETE,
            ["--stopped-after", "soon"],
            ["factory.domain.a"],
            None,
            id="stopped-after-soon",
        ),
        pytest.param(
            COMPLETE,
            ["--names", "--stopped-after", "540"],
            ["factory.domain.a"],
            None,
            id="names-and-stopped-after",
        ),
    ],
)
def test_a_fault_ends_with_status_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    text: str | None,
    options: list[str],
    modules: list[str],
    error: str | None,
) -> None:
    results = tmp_path / "results.txt" if text is None else _results_file(tmp_path, text)
    arguments = [*options, str(results), *modules]

    if error is None:
        with pytest.raises(SystemExit) as raised:
            main(arguments)
        assert raised.value.code == 2
    else:
        result = main(arguments)
        captured = capsys.readouterr()
        assert result == 2
        assert captured.out == ""
        assert captured.err.endswith("\n")
        assert captured.err.count("\n") == 1
        assert re.fullmatch(error, captured.err.removesuffix("\n"))
