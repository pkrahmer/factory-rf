"""The tests of the document check run on documents they write, never on the repository's."""

import re
from pathlib import Path

import pytest

ENTRY_TESTS = Path(__file__).parents[1] / "entry"
_CHECK = re.compile(
    r"\bfactory\.entry\.check_documents\b|from factory\.entry import check_documents"
)
_REPOSITORY_NAMES = {
    # An import in parentheses spans lines, as ruff format writes a long one.
    "support.operator_support.ROOT": re.compile(
        r"\boperator_support\.ROOT\b"
        r"|from support\.operator_support import (?:\([^)]*|[^\n(]*)\bROOT\b"
    ),
    "tracked_files": re.compile(r"\btracked_files\b"),
    "documents_copy_support": re.compile(r"\bdocuments_copy_support\b"),
    "docs/checked-documents.txt": re.compile(r"docs/checked-documents\.txt"),
}


def repository_names(source: str) -> list[str]:
    """The names of the repository's documents that `source` uses, if it tests the check."""
    if _CHECK.search(source) is None:
        return []
    return [name for name, pattern in _REPOSITORY_NAMES.items() if pattern.search(source)]


def _offending_modules(folder: Path) -> dict[str, list[str]]:
    found = {
        path.name: repository_names(path.read_text(encoding="utf-8"))
        for path in sorted(folder.glob("*.py"))
    }
    return {name: names for name, names in found.items() if names}


def test_no_document_check_test_names_the_repositorys_documents() -> None:
    assert _offending_modules(ENTRY_TESTS) == {}


_NAMING = {
    "support.operator_support.ROOT": "from support.operator_support import ROOT\n",
    "tracked_files": "def test_x(tracked_files: Path) -> None: ...\n",
    "documents_copy_support": "from support.documents_copy_support import x\n",
    "docs/checked-documents.txt": 'LIST = Path("docs/checked-documents.txt")\n',
}


_PARENTHESIZED_ROOT = "from support.operator_support import (\n    OTHER,\n    ROOT,\n)\n"


@pytest.mark.parametrize(
    ("name", "naming"),
    [
        *(pytest.param(name, naming, id=name) for name, naming in _NAMING.items()),
        pytest.param("support.operator_support.ROOT", _PARENTHESIZED_ROOT, id="parenthesized-ROOT"),
    ],
)
def test_a_document_check_test_that_names_the_repositorys_documents_is_found(
    tmp_path: Path, name: str, naming: str
) -> None:
    text = f"from factory.entry.check_documents import main\n{naming}"
    (tmp_path / "test_written.py").write_text(text, encoding="utf-8")

    assert _offending_modules(tmp_path) == {"test_written.py": [name]}
