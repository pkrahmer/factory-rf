"""Reads a guide folder's headings and lists the files a guard searches for a name."""

import re
from collections.abc import Sequence
from pathlib import Path


def lines_outside_fences(text: str) -> list[str]:
    """The lines of `text` that are not inside a fenced code block."""
    lines: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return lines


def guide_headings(folder: Path) -> list[str]:
    """Every `##` and `###` heading outside fences in the Markdown files of `folder`, in order."""
    return [
        line
        for path in sorted(folder.glob("*.md"))
        for line in lines_outside_fences(path.read_text(encoding="utf-8"))
        if re.match(r"#{2,3} ", line)
    ]


def searched_files(searched: Sequence[Path], not_searched: Sequence[Path]) -> list[Path]:
    """The files in or at `searched`, without caches and without what `not_searched` holds."""
    files: list[Path] = []
    for place in searched:
        candidates = [place] if place.is_file() else sorted(place.rglob("*"))
        files.extend(
            path
            for path in candidates
            if path.is_file()
            and "__pycache__" not in path.parts
            and not any(path == skip or skip in path.parents for skip in not_searched)
        )
    return files
