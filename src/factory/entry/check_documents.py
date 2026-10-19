"""The documents command: the findings of the four documents and the guide's files, one per line."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from factory.domain.documents import (
    DOCUMENT_PATHS,
    PROJECT_GUIDE_FOLDER,
    check_documents,
    is_guide_file,
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


def main(argv: Sequence[str] | None = None) -> int:
    """Print `documents ok` and return 0, or print one line per finding and return 1."""
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    root: Path = arguments.root
    paths = [*DOCUMENT_PATHS, *_guide_files(root)]
    findings = check_documents({path: _read(root / path) for path in paths})
    if not findings:
        print("documents ok")
        return _CLEAN
    for finding in findings:
        print(f"{finding.document}: {finding.message}")
    return _FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
