"""The minimal documents: a skipped block adds its `not run` line, a checkout example runs."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from support.check_documents_support import (
    REPORT_HEADING,
    append_block,
    findings_from,
)

MACHINE = "docs/project-guide/machine.md"
NO_INDEX = "docs/operator-guide/README.md: missing\n"


@pytest.mark.parametrize(
    ("info", "lines", "offset", "added"),
    [
        pytest.param(
            "console vm", ["$ systemctl is-active factory-vm", "active"], 0, "not run (vm)", id="vm"
        ),
        pytest.param("console github", ["$ gh pr list", "..."], 0, "not run (github)", id="github"),
        pytest.param(
            "console model", ["$ claude -p hello", "..."], 0, "not run (model)", id="model"
        ),
        pytest.param("console", ["$ make test", "test: green"], 0, "not run (suite)", id="suite"),
        pytest.param("console", ["$ echo one", "two"], 1, "the example printed one", id="wrong"),
    ],
)
def test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line(
    minimal: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    info: str,
    lines: list[str],
    offset: int,
    added: str,
) -> None:
    (minimal / "docs" / "operator-guide" / "README.md").unlink()
    status_before = main(["--root", str(minimal)])
    before = capsys.readouterr().out
    first_line = append_block(minimal, MACHINE, info, lines)

    status = main(["--root", str(minimal)])

    assert before == NO_INDEX
    assert capsys.readouterr().out == (
        f"{NO_INDEX}{REPORT_HEADING}\n{MACHINE}:{first_line + offset}: {added}\n"
    )
    assert status == status_before == 1


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("README.md", [], id="tracked-file"),
        pytest.param(
            "nothing.md",
            [
                rf"{re.escape(MACHINE)}:\d+: the example printed ls: cannot access "
                r"'nothing\.md': No such file or directory"
            ],
            id="missing-file",
        ),
    ],
)
def test_an_example_reads_a_file_git_tracks_in_the_repository(
    minimal: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    name: str,
    expected: list[str],
) -> None:
    first_line = append_block(minimal, MACHINE, "console", [f"$ ls {name}", name])

    main(["--root", str(minimal)])

    about_machine = findings_from(capsys.readouterr().out.splitlines(), MACHINE, first_line)
    assert len(about_machine) == len(expected)
    for line, pattern in zip(about_machine, expected, strict=True):
        assert re.fullmatch(pattern, line)
