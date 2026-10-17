"""Every fault-injection path names one test function, in one of the two path modules."""

import ast
from pathlib import Path

from factory.domain.fault_paths import FAULT_PATHS

PATH_MODULES = (
    Path(__file__).parent / "test_fault_paths.py",
    Path(__file__).parent / "test_fault_paths_7_to_13.py",
)
LONGEST_NAME = 90


def _functions(module: Path) -> set[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_every_path_test_is_a_function_of_exactly_one_path_module() -> None:
    first, second = (_functions(module) for module in PATH_MODULES)
    names = [path.test for path in FAULT_PATHS]

    assert [name for name in names if name not in first | second] == []
    assert [name for name in names if name in first & second] == []


def test_every_path_test_name_is_at_most_ninety_characters() -> None:
    assert [path.test for path in FAULT_PATHS if len(path.test) > LONGEST_NAME] == []
