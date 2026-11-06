"""The documents command runs a real example in the git repository of the `documents` copy."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from support.document_texts import FENCE
from support.git_support import commit_all, run_git

LISTED = "docs/project-guide/style.md"
UNLISTED = "docs/project-guide/shared.md"
REPORT_HEADING = "Report (not checked yet):"


def _append_block(root: Path, document: str, command: str, output: str) -> int:
    """Append a `console` block to `document`, list the listed page, commit; the block's line."""
    if document == LISTED:
        (root / "docs" / "checked-documents.txt").write_text(f"{LISTED}\n", encoding="utf-8")
    path = root / document
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    first_line = len(text.splitlines()) + 2
    text += f"\n{FENCE}console\n$ {command}\n{output}\n{FENCE}\n"
    path.write_text(text, encoding="utf-8")
    commit_all(root, "An example")
    return first_line


def _findings_from(lines: list[str], document: str, first_line: int) -> list[str]:
    pattern = re.compile(rf"{re.escape(document)}:(\d+): ")
    return [
        line
        for line in lines
        if (found := pattern.match(line)) is not None and int(found.group(1)) >= first_line
    ]


@pytest.mark.parametrize("document", [UNLISTED, LISTED], ids=["unlisted", "listed"])
def test_a_matching_example_in_a_copied_document_gives_no_finding(
    documents: Path, capsys: pytest.CaptureFixture[str], document: str
) -> None:
    first_line = _append_block(documents, document, "echo hi", "hi")

    main(["--root", str(documents)])

    lines = capsys.readouterr().out.splitlines()
    assert _findings_from(lines, document, first_line) == []


@pytest.mark.parametrize(
    ("document", "blocks", "exit_status"),
    [
        pytest.param(UNLISTED, False, 0, id="unlisted-reported"),
        pytest.param(LISTED, True, 1, id="listed-fails"),
    ],
)
def test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one(
    documents: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    document: str,
    blocks: bool,
    exit_status: int,
) -> None:
    first_line = _append_block(documents, document, "echo one", "two")

    status = main(["--root", str(documents)])

    printed = capsys.readouterr().out.splitlines()
    lines = [line for line in printed if not line.endswith(" does not exist")]
    findings = _findings_from(lines, document, first_line)
    assert len(findings) == 1
    assert re.fullmatch(rf"{re.escape(document)}:\d+: the example printed one", findings[0])
    report = lines.index(REPORT_HEADING) if REPORT_HEADING in lines else len(lines)
    assert (lines.index(findings[0]) < report) is blocks
    assert status == exit_status


def test_the_copied_documents_are_a_clean_git_work_tree(documents: Path) -> None:
    assert run_git(documents, "status", "--porcelain") == ""
    assert run_git(documents, "rev-parse", "--is-inside-work-tree") == "true\n"
