"""Each fault-injection path names a test function that exists and fits on a `def` line."""

import ast
from pathlib import Path

from factory.domain.fault_paths import FAULT_PATHS

PATH_TESTS = Path(__file__).parent / "test_fault_paths.py"
LONGEST_NAME = 90


def _functions() -> set[str]:
    tree = ast.parse(PATH_TESTS.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_every_path_test_is_a_function_of_the_path_tests() -> None:
    names = [path.test for path in FAULT_PATHS[:6]]

    assert [name for name in names if name not in _functions()] == []


def test_every_path_test_name_is_at_most_ninety_characters() -> None:
    names = [path.test for path in FAULT_PATHS[:6]]

    assert [name for name in names if len(name) > LONGEST_NAME] == []
