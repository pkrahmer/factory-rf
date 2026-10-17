"""The documents command: the findings of the four documents under a root, one per line."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from factory.domain.documents import DOCUMENT_PATHS, check_documents

_PROGRAM = "check-documents"
_CLEAN = 0
_FINDINGS = 1


def _read(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Print `documents ok` and return 0, or print one line per finding and return 1."""
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    root: Path = arguments.root
    findings = check_documents({path: _read(root / path) for path in DOCUMENT_PATHS})
    if not findings:
        print("documents ok")
        return _CLEAN
    for finding in findings:
        print(f"{finding.document}: {finding.message}")
    return _FINDINGS


if __name__ == "__main__":
    raise SystemExit(main())
