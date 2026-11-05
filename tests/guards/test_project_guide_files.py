"""The project guide's index names its pages and areas, and nothing names a file it lost."""

import re
from pathlib import Path

from support.guide_files_support import index_problems, searched_files

ROOT = Path(__file__).parents[2]
GUIDE = ROOT / "docs" / "project-guide"
AREA_FILES = (
    "shared.md",
    "hosting.md",
    "work.md",
    "agents.md",
    "watching.md",
    "machine.md",
    "pipeline.md",
)
REMOVED_FILES = (
    "git-and-hosting.md",
    "work-items.md",
    "write-paths.md",
    "costs.md",
    "stages.md",
    "stage-environment.md",
    "processes-and-checks.md",
)
SEARCHED = (ROOT / "agents", ROOT / "docs", ROOT / "README.md")
NOT_SEARCHED = (
    ROOT / "docs" / "runs",
    ROOT / "docs" / "decisions.md",
    ROOT / "docs" / "operator-guide",
)


def test_the_guide_holds_the_index_and_its_named_files() -> None:
    assert index_problems(GUIDE, AREA_FILES) == []


def test_every_source_path_the_index_names_exists() -> None:
    text = (GUIDE / "README.md").read_text(encoding="utf-8")
    paths = set(re.findall(r"src/factory/[\w./]*\w", text))
    assert [path for path in sorted(paths) if not (ROOT / path).exists()] == []


def test_no_file_names_a_removed_guide_file() -> None:
    pattern = re.compile(
        r"(?<![\w.-])(?<!operator-guide/)(?:project-guide/)?(?:"
        + "|".join(re.escape(name) for name in REMOVED_FILES)
        + r")"
    )
    found = [
        f"{path.relative_to(ROOT)}:{number}: {match.group(0)}"
        for path in searched_files(SEARCHED, NOT_SEARCHED)
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        )
        for match in pattern.finditer(line)
    ]
    assert found == []
