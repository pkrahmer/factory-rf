"""Only the post texts say "retrying": no other string in the code promises a retry."""

import ast

from source_search import modules

TEXTS_MODULE = "factory.domain.post_texts"


def _docstrings(tree: ast.Module) -> set[int]:
    """The ids of the module, class and function docstring nodes in `tree`."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))
    return found


def _literals(tree: ast.Module) -> list[str]:
    """Every string literal in `tree` that is not a docstring."""
    docstrings = _docstrings(tree)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_no_string_outside_the_post_texts_says_retrying() -> None:
    found = modules()
    assert TEXTS_MODULE in found

    offenders = [
        (name, literal)
        for name, tree in found.items()
        if name != TEXTS_MODULE
        for literal in _literals(tree)
        if "retrying" in literal.lower()
    ]

    assert offenders == []
