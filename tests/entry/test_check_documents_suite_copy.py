"""The suite's copy of the repository: a skipped block or a checkout example keeps it green."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from support.check_documents_support import without_report_lines
from support.document_texts import FENCE
from support.documents_copy_support import copy_of
from support.git_support import commit_all, run_git

MACHINE = "docs/project-guide/machine.md"
ABOUT_MACHINE = re.compile(rf"{re.escape(MACHINE)}:(\d+): ")
NO_INDEX = "docs/operator-guide/README.md: missing\n"


def _append_block(root: Path, info: str, lines: list[str]) -> int:
    """Append a block to the machine page and commit; the line of its opening fence."""
    path = root / MACHINE
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    first_line = len(text.splitlines()) + 2
    text += "\n" + "\n".join([f"{FENCE}{info}", *lines, FENCE]) + "\n"
    path.write_text(text, encoding="utf-8")
    commit_all(root, "A block")
    return first_line


@pytest.mark.parametrize(
    ("info", "lines", "added"),
    [
        pytest.param("console vm", ["$ systemctl is-active factory-vm", "active"], None, id="vm"),
        pytest.param("console github", ["$ gh pr list", "..."], None, id="github"),
        pytest.param("console model", ["$ claude -p hello", "..."], None, id="model"),
        pytest.param("console", ["$ make test", "test: green"], None, id="suite"),
        pytest.param(
            "console",
            ["$ echo one", "two"],
            rf"{re.escape(MACHINE)}:\d+: the example printed one\n",
            id="wrong-example",
        ),
    ],
)
def test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line(
    documents: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    info: str,
    lines: list[str],
    added: str | None,
) -> None:
    _append_block(documents, info, lines)
    (documents / "docs" / "operator-guide" / "README.md").unlink()

    status = main(["--root", str(documents)])

    output = without_report_lines(capsys.readouterr().out.splitlines(keepends=True))
    if added is None:
        assert output == NO_INDEX
    else:
        assert re.fullmatch(re.escape(NO_INDEX) + added, output) or re.fullmatch(
            added + re.escape(NO_INDEX), output
        )
    assert status == 1


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("operator/vm/setup.sh", [], id="tracked-file"),
        pytest.param(
            "operator/vm/nothing.sh",
            [
                rf"{re.escape(MACHINE)}:\d+: the example printed ls: cannot access "
                r"'operator/vm/nothing\.sh': No such file or directory"
            ],
            id="missing-file",
        ),
    ],
)
def test_an_example_reads_the_tracked_files_of_the_repository(
    documents: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    name: str,
    expected: list[str],
) -> None:
    first_line = _append_block(documents, "console", [f"$ ls {name}", name])

    main(["--root", str(documents)])

    about_machine = [
        line
        for line in capsys.readouterr().out.splitlines()
        if (found := ABOUT_MACHINE.match(line)) is not None and int(found.group(1)) >= first_line
    ]
    assert len(about_machine) == len(expected)
    for line, pattern in zip(about_machine, expected, strict=True):
        assert re.fullmatch(pattern, line)


def test_the_copy_holds_the_tracked_files_and_nothing_untracked(documents: Path) -> None:
    assert (documents / "pyproject.toml").is_file()
    assert (documents / "src" / "factory" / "shared" / "domain" / "documents.py").is_file()
    assert not (documents / ".venv").exists()
    assert run_git(documents, "status", "--porcelain") == ""


def test_two_copies_of_the_session_repository_are_separate(
    tracked_files: Path, tmp_path: Path
) -> None:
    first = copy_of(tracked_files, tmp_path / "first")
    (first / "added.md").write_text("added\n", encoding="utf-8")
    commit_all(first, "An added file")
    (first / "pyproject.toml").write_text("changed\n", encoding="utf-8")

    second = copy_of(tracked_files, tmp_path / "second")

    assert not (second / "added.md").exists()
    assert (second / "pyproject.toml").read_text(encoding="utf-8") != "changed\n"
    assert run_git(second, "status", "--porcelain") == ""
