"""The smallest documents the document check accepts, written from the code's own tables."""

from collections.abc import Mapping
from pathlib import Path

import factory
from factory.shared.domain import documents
from support.document_texts import clean_texts, write_documents
from support.git_support import commit_all, run_git


def _area_page(area: str) -> str:
    return f"# The {area} area\n\n## Its modules\n\nThe factory works on work items.\n"


def _areas() -> list[str]:
    package = Path(factory.__file__).parent
    return sorted(entry.name for entry in package.iterdir() if (entry / "domain").is_dir())


def _texts() -> dict[str, str | None]:
    texts = clean_texts()
    for area in _areas():
        texts[f"{documents.PROJECT_GUIDE_FOLDER}/{area}.md"] = _area_page(area)
    texts[documents.CHECKED_DOCUMENTS] = ""
    return texts


def minimal_documents(root: Path) -> Path:
    """A git repository at `root`, in one commit, with the smallest documents the check accepts."""
    root.mkdir(parents=True, exist_ok=True)
    write_documents(root, _texts())
    run_git(root, "init", "-q")
    commit_all(root, "The minimal documents")
    return root


def add_and_commit(root: Path, files: Mapping[str, str]) -> None:
    """Write `files` (path relative to `root`, text) into the repository and commit them."""
    write_documents(root, dict(files))
    # An unchanged file would make the commit empty, and `commit_all` would fail.
    if run_git(root, "status", "--porcelain"):
        commit_all(root, "Files of the test")
