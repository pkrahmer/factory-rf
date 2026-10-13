"""The project is reached through its project commands only, and the result names no layers."""

import ast

from source_search import SRC, modules, string_literals

CHECK_MODULES = (
    "domain/checks.py",
    "application/project_commands.py",
    "adapters/make_commands.py",
)


def _identifiers(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.alias):
            names.add(node.asname or node.name)
    return names


def test_only_the_make_class_names_make() -> None:
    naming = {name for name, tree in modules().items() if "make" in string_literals(tree)}

    assert naming == {"factory.adapters.make_commands"}


def test_no_identifier_in_the_check_modules_names_a_layer() -> None:
    found: dict[str, list[str]] = {}
    for module in CHECK_MODULES:
        tree = ast.parse((SRC / module).read_text(encoding="utf-8"))
        found[module] = sorted(name for name in _identifiers(tree) if "layer" in name.lower())

    assert found == {module: [] for module in CHECK_MODULES}
