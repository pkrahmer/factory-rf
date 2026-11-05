"""The areas of `src/factory`: each area's modules live in its own package, under their layer."""

import ast
import importlib
from pathlib import Path

import pytest

from source_search import SRC, imported_modules, imports

TESTS = Path(__file__).parent
LAYER_TESTS = ("domain", "application", "adapters")

AREAS: dict[str, tuple[str, ...]] = {
    "shared": (
        "domain.errors",
        "domain.times",
        "domain.identifiers",
        "domain.paths",
        "domain.settings",
        "domain.printed_lines",
        "domain.contract",
        "domain.duplicates",
        "domain.sections",
        "domain.documents",
        "domain.kill_points",
        "domain.kill_point_cases",
        "application.files",
        "adapters.clock",
        "adapters.atomic_file",
        "adapters.process",
        "adapters.printed_output",
        "adapters.validation_faults",
    ),
}

MOVES = [
    pytest.param(area, module, id=f"{area}.{module}")
    for area, area_modules in AREAS.items()
    for module in area_modules
]

PACKAGES = [
    pytest.param(package, id=package)
    for area, area_modules in AREAS.items()
    for package in [
        f"factory.{area}",
        *sorted({f"factory.{area}.{module.split('.')[0]}" for module in area_modules}),
    ]
]


@pytest.mark.parametrize(("area", "module"), MOVES)
def test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer(
    area: str, module: str
) -> None:
    importlib.import_module(f"factory.{area}.{module}")
    old = SRC.joinpath(*module.split("."))

    assert not old.with_suffix(".py").exists()
    assert not old.is_dir()


@pytest.mark.parametrize("package", PACKAGES)
def test_an_area_package_imports_and_has_a_docstring(package: str) -> None:
    imported = importlib.import_module(package)

    assert imported.__doc__
    assert imported.__doc__.strip()


@pytest.fixture(scope="module")
def python_files() -> list[tuple[str, ast.Module]]:
    """Every `.py` file under `src/` and `tests/`, parsed, by its path."""
    root = SRC.parent
    paths = [*sorted(root.rglob("*.py")), *sorted(TESTS.rglob("*.py"))]
    return [
        (path.relative_to(root.parent).as_posix(), ast.parse(path.read_text(encoding="utf-8")))
        for path in paths
    ]


@pytest.mark.parametrize(("area", "module"), MOVES)
def test_no_file_imports_a_moved_module_from_its_old_path(
    area: str, module: str, python_files: list[tuple[str, ast.Module]]
) -> None:
    old = f"factory.{module}"

    importers = [name for name, tree in python_files if imports(tree, old)]

    assert importers == [], f"{old} (now in {area}) is imported from its old path by {importers}"


def _factory_imports(tree: ast.Module) -> list[str]:
    return sorted(
        name for name in imported_modules(tree) if name == "factory" or name.startswith("factory.")
    )


def _in_a_moved_area(module: str) -> bool:
    """Whether `module` is of an area of the table, by its new path or by its old one."""
    for area, area_modules in AREAS.items():
        if module == f"factory.{area}" or module.startswith(f"factory.{area}."):
            return True
        if module in {f"factory.{old}" for old in area_modules}:
            return True
    return False


def test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved() -> None:
    left = [
        path.relative_to(TESTS.parent).as_posix()
        for layer in LAYER_TESTS
        for path in sorted((TESTS / layer).rglob("test_*.py"))
        if (found := _factory_imports(ast.parse(path.read_text(encoding="utf-8"))))
        and all(_in_a_moved_area(module) for module in found)
    ]

    assert left == [], "\n".join(left)


AREA_TESTS = [
    pytest.param(area, path, id=path.relative_to(TESTS).as_posix())
    for area in AREAS
    for path in sorted((TESTS / area).rglob("test_*.py"))
]


@pytest.mark.parametrize(("area", "path"), AREA_TESTS)
def test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own(
    area: str, path: Path
) -> None:
    found = _factory_imports(ast.parse(path.read_text(encoding="utf-8")))

    outside = [module for module in found if not _in_a_moved_area(module)]
    own = [module for module in found if module.startswith(f"factory.{area}.")]

    assert outside == [], f"{path.name} imports areas not yet moved: {outside}"
    assert own != [], f"{path.name} imports nothing of {area}"
