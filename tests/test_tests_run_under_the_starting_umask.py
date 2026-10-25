"""No test module sets the umask the whole run works under."""

import ast
from pathlib import Path

TESTS = Path(__file__).parent
EXEMPT_FILE = "adapters/test_calls_as_the_factory_user.py"
EXEMPT_FUNCTION = "umask_of"


def _umask_calls(tree: ast.AST) -> set[int]:
    return {
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "umask"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
    }


def _exempt_calls(relative: str, tree: ast.Module) -> set[int]:
    if relative != EXEMPT_FILE:
        return set()
    return {
        line
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == EXEMPT_FUNCTION
        for line in _umask_calls(node)
    }


def test_no_module_under_tests_calls_os_umask_but_the_one_fixture_that_restores_it() -> None:
    calls: list[str] = []
    for path in sorted(TESTS.rglob("*.py")):
        relative = path.relative_to(TESTS).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls += [
            f"{relative}:{line}"
            for line in sorted(_umask_calls(tree) - _exempt_calls(relative, tree))
        ]

    assert calls == []
