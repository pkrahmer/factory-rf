"""The document tests write the list they need, so the repository's list leaves them as they are."""

import re
from collections.abc import Callable, Sequence
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
from support.git_support import commit_all, head_of, run_git

_SHARED = "docs/project-guide/shared.md"
_NEWLY_LISTED = (OPERATOR_GUIDE, OPERATOR_INSTALL, _SHARED)
_NO_INDEX = f"{OPERATOR_GUIDE}: missing\n"

Steps = Callable[[Path, pytest.CaptureFixture[str]], None]


def _names(text: str, page: str) -> int:
    """How many lines of the list `text` name `page`."""
    return sum(1 for line in text.splitlines() if line.strip() == page)


def _list_newly(root: Path) -> None:
    """Append to the list under `root` each of the three pages it does not name yet; commit."""
    path = root / CHECKED_DOCUMENTS
    text = path.read_text(encoding="utf-8")
    missing = [page for page in _NEWLY_LISTED if _names(text, page) == 0]
    if not missing:
        return
    _append_to_list(root, missing)


def _append_to_list(root: Path, pages: Sequence[str]) -> None:
    """Append `pages` to the list under `root` without looking at it, and commit."""
    path = root / CHECKED_DOCUMENTS
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + "".join(f"{page}\n" for page in pages), encoding="utf-8")
    commit_all(root, "List pages")


def _unlist_the_three(root: Path) -> None:
    """Remove from the list under `root` every line that names one of the three pages; commit."""
    path = root / CHECKED_DOCUMENTS
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept = [line for line in lines if line.strip() not in _NEWLY_LISTED]
    if kept != lines:
        path.write_text("".join(kept), encoding="utf-8")
        commit_all(root, "Unlist the three pages")


@pytest.fixture
def listed(documents: Path) -> Path:
    """The `documents` copy whose list also names the three pages, each once, committed."""
    _list_newly(documents)
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


@pytest.mark.parametrize(
    ("already", "commits"),
    [
        pytest.param((), True, id="none-listed"),
        pytest.param((OPERATOR_GUIDE,), True, id="index-listed"),
        pytest.param(_NEWLY_LISTED, False, id="all-listed"),
    ],
)
def test_listing_the_three_pages_names_each_once_whatever_the_list_already_names(
    documents: Path, already: tuple[str, ...], commits: bool
) -> None:
    _unlist_the_three(documents)
    before_text = (documents / CHECKED_DOCUMENTS).read_text(encoding="utf-8")
    assert all(_names(before_text, page) == 0 for page in _NEWLY_LISTED)
    if already:
        _append_to_list(documents, already)
    before = head_of(documents)

    _list_newly(documents)

    text = (documents / CHECKED_DOCUMENTS).read_text(encoding="utf-8")
    assert [_names(text, page) for page in _NEWLY_LISTED] == [1, 1, 1]
    assert run_git(documents, "status", "--porcelain") == ""
    assert (head_of(documents) != before) is commits


def _list_without_looking(root: Path) -> None:
    _append_to_list(root, _NEWLY_LISTED)


_NOT_A_DOCUMENT = f"{CHECKED_DOCUMENTS}: {OPERATOR_GUIDE} is no document of the check\n"


@pytest.mark.parametrize(
    ("listing", "times"),
    [
        pytest.param(_list_newly, 1, id="added-once"),
        pytest.param(_list_without_looking, 2, id="appended-again"),
    ],
)
def test_a_page_the_repository_list_already_names_is_reported_once_unless_appended_again(
    documents: Path,
    capsys: pytest.CaptureFixture[str],
    listing: Callable[[Path], None],
    times: int,
) -> None:
    _unlist_the_three(documents)
    _append_to_list(documents, [OPERATOR_GUIDE])
    listing(documents)
    (documents / OPERATOR_GUIDE).unlink()

    main(["--root", str(documents)])

    printed = without_report_lines(capsys.readouterr().out.splitlines(keepends=True))
    assert sorted(printed.splitlines(keepends=True)) == sorted(
        [_NO_INDEX] + [_NOT_A_DOCUMENT] * times
    )


_STYLE = "docs/project-guide/style.md"


@pytest.mark.parametrize(
    ("held", "commits"),
    [
        pytest.param(None, True, id="changed"),
        pytest.param(f"{_STYLE}\n", False, id="unchanged"),
    ],
)
def test_the_written_list_is_committed_only_when_its_text_changes(
    documents: Path, held: str | None, commits: bool
) -> None:
    if held is not None:
        (documents / CHECKED_DOCUMENTS).write_text(held, encoding="utf-8")
        commit_all(documents, "The list the copy holds")
    before = head_of(documents)

    write_checked_list(documents, [_STYLE])

    assert (head_of(documents) != before) is commits
    assert run_git(documents, "status", "--porcelain") == ""
