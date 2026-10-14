"""No handler swallows an error: no bare `except`, none naming `Exception` or `BaseException`."""

import ast
import pkgutil

import pytest

import factory.application.handlers as handlers_package
from source_search import modules

PACKAGE = handlers_package.__name__
REQUIRED = {"recording", "comments", "questions", "merged", "closed", "reject", "lookups"}
BROAD = {"Exception", "BaseException"}


def _handler_modules() -> list[str]:
    return [info.name for info in pkgutil.walk_packages(handlers_package.__path__, f"{PACKAGE}.")]


def _names(node: ast.expr) -> set[str]:
    if isinstance(node, ast.Tuple):
        return {name for element in node.elts for name in _names(element)}
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.Attribute):
        return {node.attr}
    return set()


def _swallowing_clauses(tree: ast.Module) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler)
        and (node.type is None or bool(_names(node.type) & BROAD))
    ]


def test_the_walk_finds_every_handler_module_of_the_feature() -> None:
    found = {name.removeprefix(f"{PACKAGE}.") for name in _handler_modules()}

    assert found >= REQUIRED


@pytest.mark.parametrize("module", _handler_modules())
def test_no_handler_module_catches_every_exception_or_has_a_bare_except(module: str) -> None:
    tree = modules()[module]

    assert _swallowing_clauses(tree) == []
