"""The document check reads the folder READMEs and `operator/README.md` like the guides."""

import re
from pathlib import Path

import pytest

from factory.entry.check_documents import main
from factory.shared.domain.documents import CHECKED_DOCUMENTS, PROJECT_GUIDE
from factory.shared.domain.folder_readmes import FOLDER_READMES
from support.check_documents_support import REPORT_HEADING, TIME_LINE, line_of
from support.minimal_documents_support import add_and_commit, minimal_documents

MISSING_NAME = "factory.nothing_here"
NAMING_LINE = f"See `{MISSING_NAME}`."
FOLDER_README = FOLDER_READMES[0]
OPERATOR_README = "operator/README.md"
FOLDER_README_TEXT = f"# A folder\n\nWhat the folder holds.\n{NAMING_LINE}\n"
# A section and prose after it: a form `readme_problems` would refuse, which the
# operator's README may keep.
OPERATOR_README_TEXT = (
    "# The operator's files\n\n"
    "What the operator runs.\n\n"
    "## What is here\n\n"
    "Prose after the section.\n\n"
    f"{NAMING_LINE}\n"
)


def _run(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    status = main(["--root", str(root)])
    return status, [line.strip() for line in capsys.readouterr().out.splitlines()]


@pytest.mark.parametrize(
    ("document", "text"),
    [
        pytest.param(FOLDER_README, FOLDER_README_TEXT, id="folder-readme"),
        pytest.param(OPERATOR_README, OPERATOR_README_TEXT, id="operator-readme"),
    ],
)
@pytest.mark.parametrize("listed", [True, False], ids=["listed", "not-listed"])
def test_a_missing_name_in_a_readme_blocks_when_listed_and_is_reported_otherwise(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    document: str,
    text: str,
    listed: bool,
) -> None:
    root = minimal_documents(tmp_path / "root")
    checked = document if listed else PROJECT_GUIDE
    add_and_commit(root, {document: text, CHECKED_DOCUMENTS: f"{checked}\n"})

    status, lines = _run(root, capsys)

    finding = f"{document}:{line_of(text, NAMING_LINE)}: {MISSING_NAME} does not exist"
    assert finding in lines, lines
    assert not any("has a section" in line or "no part of the form" in line for line in lines)
    if listed:
        assert status == 1
        assert REPORT_HEADING not in lines
    else:
        assert status == 0
        assert lines.index(finding) > lines.index(REPORT_HEADING)
        assert re.fullmatch(TIME_LINE, lines[-1])


def test_a_listed_folder_readme_that_does_not_exist_is_no_document_of_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = minimal_documents(tmp_path / "root")
    add_and_commit(root, {CHECKED_DOCUMENTS: f"{FOLDER_README}\n"})

    status, lines = _run(root, capsys)

    assert lines == [f"{CHECKED_DOCUMENTS}: {FOLDER_README} is no document of the check"]
    assert status == 1
