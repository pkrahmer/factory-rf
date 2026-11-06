"""The list of checked documents a test writes: its text, its commit, a page listed twice."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import CHECKED_DOCUMENTS
from support.check_documents_support import (
    append_block,
    findings_from,
    write_checked_list,
)
from support.git_support import commit_all, head_of, run_git
from support.minimal_documents_support import add_and_commit

_SHARED = "docs/project-guide/shared.md"
_STYLE = "docs/project-guide/style.md"


@pytest.mark.parametrize("times", [pytest.param(1, id="listed-once"), pytest.param(2, id="twice")])
def test_a_page_listed_once_more_gives_no_second_finding(
    minimal: Path, capsys: pytest.CaptureFixture[str], times: int
) -> None:
    add_and_commit(minimal, {CHECKED_DOCUMENTS: f"{_SHARED}\n" * times})
    first_line = append_block(minimal, _SHARED, "console", ["$ echo one", "two"])

    status = main(["--root", str(minimal)])

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert findings_from(lines, _SHARED, first_line) == lines
    assert re.fullmatch(rf"{re.escape(_SHARED)}:\d+: the example printed one", lines[0])
    assert status == 1


@pytest.mark.parametrize(
    ("paths", "text"),
    [
        pytest.param([], "", id="empty"),
        pytest.param([_STYLE], f"{_STYLE}\n", id="one"),
    ],
)
def test_the_written_list_holds_one_path_per_line_and_is_committed(
    minimal: Path, paths: list[str], text: str
) -> None:
    add_and_commit(minimal, {CHECKED_DOCUMENTS: "something else\n"})

    write_checked_list(minimal, paths)

    assert (minimal / CHECKED_DOCUMENTS).read_text(encoding="utf-8") == text
    assert run_git(minimal, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("held", "commits"),
    [
        pytest.param(None, True, id="changed"),
        pytest.param(f"{_STYLE}\n", False, id="unchanged"),
    ],
)
def test_the_written_list_is_committed_only_when_its_text_changes(
    minimal: Path, held: str | None, commits: bool
) -> None:
    if held is not None:
        (minimal / CHECKED_DOCUMENTS).write_text(held, encoding="utf-8")
        commit_all(minimal, "The list the repository holds")
    before = head_of(minimal)

    write_checked_list(minimal, [_STYLE])

    assert (head_of(minimal) != before) is commits
    assert run_git(minimal, "status", "--porcelain") == ""
