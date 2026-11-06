"""The smallest documents the document check accepts, written from the code's own tables."""

from collections.abc import Mapping
from pathlib import Path

import factory
from factory.shared.domain import documents, settings
from support.document_texts import decision_log, readme, stop_row, write_documents
from support.git_support import commit_all, run_git

_BODY = "The factory works on work items."


def _page(title: str, sections: tuple[str, ...], rows: Mapping[str, list[str]]) -> str:
    """A page with one `##` section per name, each holding a sentence and its rows."""
    lines = [f"# {title}", ""]
    for name in sections:
        lines += [f"## {name}", "", _BODY, ""]
        if rows.get(name):
            lines += [*rows[name], ""]
    return "\n".join(lines)


def _settings_rows() -> list[str]:
    return [
        "| Variable | Meaning |",
        "|---|---|",
        *(f"| `{setting.name}` | A setting. |" for setting in settings.SETTINGS),
    ]


def _install() -> str:
    sections = documents.OPERATOR_GUIDE_SECTIONS
    return _page("Install", sections, {documents.SETTINGS_SECTION: _settings_rows()})


def _stops() -> str:
    rows = [stop_row(row) for row in documents.STOP_TABLE]
    return _page("The stops", documents.OPERATOR_GUIDE_SECTIONS, {}) + "\n".join(["", *rows, ""])


def _project_guide() -> str:
    rows = [f"| `{case.id}` | {case.dies} |" for case in documents.KILL_POINT_CASES]
    rows += [f"| {path.number} | `{path.test}` |" for path in documents.FAULT_PATHS]
    return _page("Project guide", documents.PROJECT_GUIDE_SECTIONS, {}) + "\n".join(["", *rows, ""])


def _areas() -> list[str]:
    package = Path(factory.__file__).parent
    return sorted(entry.name for entry in package.iterdir() if (entry / "domain").is_dir())


def _texts() -> dict[str, str | None]:
    texts: dict[str, str | None] = {
        documents.README: readme(),
        documents.OPERATOR_GUIDE: _page("Operator guide", ("Topics",), {}),
    }
    for path in documents.OPERATOR_GUIDE_FILES:
        texts[path] = _page("A topic", ("Running it",), {})
    texts[documents.OPERATOR_INSTALL] = _install()
    texts[documents.OPERATOR_STOPS] = _stops()
    texts[documents.PROJECT_GUIDE] = _project_guide()
    for area in _areas():
        texts[f"{documents.PROJECT_GUIDE_FOLDER}/{area}.md"] = _page(
            f"The {area} area", ("Its modules",), {}
        )
    texts[documents.DECISION_LOG] = decision_log()
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
