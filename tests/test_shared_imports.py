"""No module under `tests/` imports a test module: what two test modules share lives elsewhere."""

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).parent


def _is_test_module(module: str) -> bool:
    return module.rsplit(".", 1)[-1].startswith("test_")


def imported_test_modules(source: str) -> list[tuple[int, str]]:
    """Each import of a test module in `source`: its statement's first line and the module."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            path = "." * node.level + (node.module or "")
            if _is_test_module(path):
                modules = [path]
            else:
                prefix = path if path.endswith(".") or not path else f"{path}."
                modules = [f"{prefix}{alias.name}" for alias in node.names]
        else:
            continue
        found.extend((node.lineno, module) for module in modules if _is_test_module(module))
    return sorted(found)


def import_messages(file: str, source: str) -> list[str]:
    """Each import of a test module in `source`, rendered as `<file>:<line>: <module>`."""
    return [f"{file}:{line}: {module}" for line, module in imported_test_modules(source)]


def test_no_module_under_tests_imports_a_test_module() -> None:
    messages = [
        message
        for path in sorted(TESTS.rglob("*.py"))
        for message in import_messages(
            path.relative_to(TESTS.parent).as_posix(), path.read_text(encoding="utf-8")
        )
    ]

    assert messages == [], "\n".join(messages)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param("from adapters.test_x import A\n", [(1, "adapters.test_x")], id="from-path"),
        pytest.param("from test_x import A\n", [(1, "test_x")], id="from-top"),
        pytest.param("import application.test_y\n", [(1, "application.test_y")], id="import"),
        pytest.param("import test_y as y\n", [(1, "test_y")], id="import-as"),
        pytest.param("from adapters import test_z\n", [(1, "adapters.test_z")], id="from-name"),
        pytest.param(
            "from adapters import test_z as z\n", [(1, "adapters.test_z")], id="from-name-as"
        ),
        pytest.param(
            "from adapters.test_x import (\n    A,\n    B,\n)\n",
            [(1, "adapters.test_x")],
            id="parenthesised",
        ),
        pytest.param("from take_support import x\n", [], id="support"),
        pytest.param("from testing_support import x\n", [], id="testing-prefix"),
        pytest.param("import factory.application.tick\n", [], id="package"),
        pytest.param("from adapters import support_test\n", [], id="test-suffix"),
    ],
)
def test_the_guard_finds_every_form_of_a_test_module_import(
    source: str, expected: list[tuple[int, str]]
) -> None:
    assert imported_test_modules(source) == expected


def test_the_guard_names_each_import_by_file_line_and_module() -> None:
    source = "x = 1\nfrom adapters.test_x import A\n"

    assert import_messages("tests/adapters/test_a.py", source) == [
        "tests/adapters/test_a.py:2: adapters.test_x"
    ]
