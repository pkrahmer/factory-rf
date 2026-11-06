"""Each area's package, and `entry`'s, names its page of the project guide in its docstring."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
GUIDE = Path("docs") / "project-guide"
PAGES = (
    ("shared", "shared.md"),
    ("hosting", "hosting.md"),
    ("work", "work.md"),
    ("agents", "agents.md"),
    ("watching", "watching.md"),
    ("machine", "machine.md"),
    ("pipeline", "pipeline.md"),
    ("entry", "README.md"),
)
LINE_START = "Guide: "


def guide_problems(root: Path, package: str, page: str) -> list[str]:
    """What is wrong with the guide line of `package` under `root`, read without importing it."""
    init = root / "src" / "factory" / package / "__init__.py"
    docstring = ast.get_docstring(ast.parse(init.read_text(encoding="utf-8"))) or ""
    expected = f"{LINE_START}{(GUIDE / page).as_posix()}"
    lines = [line for line in docstring.splitlines() if line.startswith(LINE_START)]
    if expected not in lines:
        return [f"{package}: no line {expected!r} in the docstring"]
    if not (root / GUIDE / page).is_file():
        return [f"{package}: {(GUIDE / page).as_posix()} does not exist"]
    return []


@pytest.mark.parametrize(("package", "page"), PAGES, ids=[package for package, _ in PAGES])
def test_each_package_names_its_existing_guide_page(package: str, page: str) -> None:
    assert guide_problems(ROOT, package, page) == []


def _write_copy(root: Path, docstring: str, *, page_exists: bool) -> None:
    init = root / "src" / "factory" / "work" / "__init__.py"
    init.parent.mkdir(parents=True)
    init.write_text(f'"""{docstring}"""\n', encoding="utf-8")
    if page_exists:
        guide = root / GUIDE
        guide.mkdir(parents=True)
        (guide / "work.md").write_text("# Work\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("docstring", "page_exists", "failing"),
    [
        pytest.param(
            "The work area.\n\nGuide: docs/project-guide/work.md\n", True, False, id="line-and-page"
        ),
        pytest.param("The work area.\n", True, True, id="line-missing"),
        pytest.param(
            "The work area.\n\nGuide: docs/project-guide/work.md\n", False, True, id="page-missing"
        ),
    ],
)
def test_the_guard_fails_for_a_missing_line_or_page(
    tmp_path: Path, docstring: str, *, page_exists: bool, failing: bool
) -> None:
    _write_copy(tmp_path, docstring, page_exists=page_exists)
    assert bool(guide_problems(tmp_path, "work", "work.md")) is failing
