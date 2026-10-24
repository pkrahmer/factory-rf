"""Searches the test modules under `tests` for a pattern."""

import ast
import re
from pathlib import Path

TESTS = Path(__file__).parent


def modules_matching(pattern: str, leave_out: str) -> list[str]:
    """The sorted paths, relative to `tests`, of the modules that match `pattern`.

    The module named `leave_out` is not searched, so that a test's own source does not count.
    """
    found = re.compile(pattern, re.MULTILINE | re.DOTALL)
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if path.name != leave_out and found.search(path.read_text(encoding="utf-8"))
    )


def top_level_copies(source: str, value: str) -> list[str]:
    """The names that a top-level assignment in `source` gives the string `value`."""
    names: list[str] = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            targets, assigned = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, assigned = [node.target], node.value
        else:
            continue
        if isinstance(assigned, ast.Constant) and assigned.value == value:
            names.extend(target.id for target in targets if isinstance(target, ast.Name))
    return names


def modules_assigning(value: str) -> list[str]:
    """The sorted paths, relative to `tests`, of the modules that assign `value` at top level."""
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if top_level_copies(path.read_text(encoding="utf-8"), value)
    )
