"""The document tests write the list they need, so the repository's list leaves them as they are."""

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import CHECKED_DOCUMENTS, OPERATOR_GUIDE, OPERATOR_INSTALL
from support.check_documents_support import (
    REPORT_HEADING,
    append_block,
    drop_settings_row,
    findings_from,
    without_report_lines,
    write_checked_list,
)
from support.git_support import commit_all, run_git

_SHARED = "docs/project-guide/shared.md"
_NEWLY_LISTED = (OPERATOR_GUIDE, OPERATOR_INSTALL, _SHARED)
_NO_INDEX = f"{OPERATOR_GUIDE}: missing\n"

Steps = Callable[[Path, pytest.CaptureFixture[str]], None]


@pytest.fixture
def listed(documents: Path) -> Path:
    """The `documents` copy whose list also names the three pages, committed."""
    path = documents / CHECKED_DOCUMENTS
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + "".join(f"{page}\n" for page in _NEWLY_LISTED), encoding="utf-8")
    commit_all(documents, "List three more pages")
    return documents


def _settings_steps(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_checked_list(root, [])
    status_with_row = main(["--root", str(root)])
    capsys.readouterr()
    drop_settings_row(root, "FACTORY_ZFS")

    status_without_row = main(["--root", str(root)])
    capsys.readouterr()

    assert status_without_row == status_with_row


def _no_index_steps(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_checked_list(root, [])
    (root / OPERATOR_GUIDE).unlink()

    status = main(["--root", str(root)])

    assert without_report_lines(capsys.readouterr().out.splitlines(keepends=True)) == _NO_INDEX
    assert status == 1


def _shared_example_steps(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_checked_list(root, [])
    first_line = append_block(root, _SHARED, "console", ["$ echo one", "two"])

    status = main(["--root", str(root)])

    printed = capsys.readouterr().out.splitlines()
    lines = [line for line in printed if not line.endswith(" does not exist")]
    findings = findings_from(lines, _SHARED, first_line)
    assert len(findings) == 1
    assert re.fullmatch(rf"{re.escape(_SHARED)}:\d+: the example printed one", findings[0])
    assert lines.index(findings[0]) > lines.index(REPORT_HEADING)
    assert status == 0


@pytest.mark.parametrize(
    "steps",
    [
        pytest.param(_settings_steps, id="install"),
        pytest.param(_no_index_steps, id="operator-guide-index"),
        pytest.param(_shared_example_steps, id="shared"),
    ],
)
def test_a_test_that_writes_its_list_keeps_its_outcome_when_the_repository_lists_more_pages(
    listed: Path, capsys: pytest.CaptureFixture[str], steps: Steps
) -> None:
    steps(listed, capsys)


def test_without_its_own_list_the_repository_list_reaches_the_output(
    listed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (listed / OPERATOR_GUIDE).unlink()

    main(["--root", str(listed)])

    printed = without_report_lines(capsys.readouterr().out.splitlines(keepends=True))
    assert sorted(printed.splitlines(keepends=True)) == sorted(
        [_NO_INDEX, f"{CHECKED_DOCUMENTS}: {OPERATOR_GUIDE} is no document of the check\n"]
    )


@pytest.mark.parametrize(
    ("paths", "text"),
    [
        pytest.param([], "", id="empty"),
        pytest.param(["docs/project-guide/style.md"], "docs/project-guide/style.md\n", id="one"),
    ],
)
def test_the_written_list_holds_one_path_per_line_and_is_committed(
    documents: Path, paths: list[str], text: str
) -> None:
    write_checked_list(documents, paths)

    assert (documents / CHECKED_DOCUMENTS).read_text(encoding="utf-8") == text
    assert run_git(documents, "status", "--porcelain") == ""
