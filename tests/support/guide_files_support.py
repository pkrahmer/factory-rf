"""Checks a guide folder against its index and lists the files a guard searches for a name."""

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


INDEX_LINE = re.compile(r"^- `([^`]+)`[^.]*\w[^.]*\.")


def _the_files_section(index: Path) -> list[str]:
    lines = lines_outside_fences(index.read_text(encoding="utf-8"))
    if "## The files" not in lines:
        return []
    section: list[str] = []
    for line in lines[lines.index("## The files") + 1 :]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def index_problems(guide: Path, required: Sequence[str]) -> list[str]:
    """What the index `README.md` of `guide` and the folder's pages disagree on, one line each."""
    named = {
        match.group(1)
        for line in _the_files_section(guide / "README.md")
        if (match := INDEX_LINE.match(line))
    }
    pages = {path.name for path in guide.glob("*.md") if path.is_file()} - {"README.md"}
    problems = {f"not in the index: {name}" for name in pages - named}
    problems |= {f"missing: {name}" for name in (*named, *required) if not (guide / name).is_file()}
    return sorted(problems)


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
