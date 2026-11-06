"""The documents command: the findings of the documents and the guide's files, one per line."""

import argparse
import importlib
from collections.abc import Callable, Sequence
from pathlib import Path

from factory.shared.domain import settings
from factory.shared.domain.documents import (
    DOCUMENT_PATHS,
    OPERATOR_GUIDE_FOLDER,
    OPERATOR_INSTALL,
    PROJECT_GUIDE_FOLDER,
    README,
    SETTINGS_SECTION,
    Reference,
    check_documents,
    guide_tables,
    is_guide_file,
    named_references,
    refusal_findings,
    settings_findings,
    unresolved,
)

_PROGRAM = "check-documents"
_CLEAN = 0
_FINDINGS = 1


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _guide_files(root: Path) -> list[str]:
    folder = root / PROJECT_GUIDE_FOLDER
    if not folder.is_dir():
        return []
    files = (entry for entry in folder.iterdir() if entry.is_file())
    paths = (f"{PROJECT_GUIDE_FOLDER}/{entry.name}" for entry in files)
    return [path for path in paths if is_guide_file(path)]


def _named_documents(root: Path) -> list[str]:
    folders = (root / OPERATOR_GUIDE_FOLDER, root / PROJECT_GUIDE_FOLDER)
    inside = sorted(
        path
        for folder in folders
        if folder.is_dir()
        for path in folder.rglob("*.md")
        if path.is_file()
    )
    readme = [root / README] if (root / README).is_file() else []
    return [path.relative_to(root).as_posix() for path in [*readme, *inside]]


def _module_or_attribute_exists(name: str) -> bool:
    parts = name.split(".")
    for length in range(len(parts), 0, -1):
        try:
            found: object = importlib.import_module(".".join(parts[:length]))
        except ImportError:
            continue
        for attribute in parts[length:]:
            if not hasattr(found, attribute):
                return False
            found = getattr(found, attribute)
        return True
    return False


def _path_exists(root: Path, name: str) -> bool:
    target = (root / name).resolve()
    return target.is_relative_to(root.resolve()) and target.exists()


def _existence(root: Path) -> Callable[[Reference], bool]:
    def exists(reference: Reference) -> bool:
        if reference.kind == "module":
            return _module_or_attribute_exists(reference.name)
        return _path_exists(root, reference.name)

    return exists


def _name_findings(root: Path) -> list[str]:
    top_level = frozenset(entry.name for entry in root.iterdir())
    references = [
        reference
        for document in _named_documents(root)
        for reference in named_references(
            document, (root / document).read_text(encoding="utf-8"), top_level
        )
    ]
    return unresolved(references, _existence(root))


def _settings_guide_findings(root: Path) -> list[str]:
    text = _read(root / OPERATOR_INSTALL)
    if text is None:
        return []
    tables = guide_tables(text, SETTINGS_SECTION)
    source = Path(settings.__file__).read_text(encoding="utf-8")
    return [
        *settings_findings(tables, settings.SETTINGS),
        *refusal_findings(tables, source),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Print `documents ok` and return 0, or one line per finding and return 1.

    The names, paths and links the documents name that do not exist follow, one per line,
    then where the operator guide's settings disagree with the settings code; neither
    changes the exit status.
    """
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    root: Path = arguments.root
    paths = [*DOCUMENT_PATHS, *_guide_files(root)]
    findings = check_documents({path: _read(root / path) for path in paths})
    if not findings:
        print("documents ok")
    for finding in findings:
        print(f"{finding.document}: {finding.message}")
    for name_finding in _name_findings(root):
        print(name_finding)
    for settings_finding in _settings_guide_findings(root):
        print(f"{OPERATOR_INSTALL}: {settings_finding}")
    return _FINDINGS if findings else _CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
