"""The READMEs of the test folders are written and on the document check's list."""

from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
CHECKED_DOCUMENTS = ROOT / "docs" / "checked-documents.txt"
TEST_FOLDER_READMES = (
    "tests/README.md",
    "tests/support/README.md",
    "tests/guards/README.md",
)


@pytest.mark.parametrize("path", TEST_FOLDER_READMES)
def test_a_test_folder_readme_is_written_so_its_guard_does_not_skip_it(path: str) -> None:
    assert (ROOT / path).is_file()


@pytest.mark.parametrize("path", TEST_FOLDER_READMES)
def test_a_test_folder_readme_is_on_the_checked_documents(path: str) -> None:
    listed = CHECKED_DOCUMENTS.read_text(encoding="utf-8").splitlines()

    assert path in [line.strip() for line in listed]
