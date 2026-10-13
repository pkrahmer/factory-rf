"""Exactly one fake and one real client implement the hosting service's posting."""

import ast
from pathlib import Path

from source_search import modules

TESTS = Path(__file__).parent


def _is_abstract(node: ast.ClassDef) -> bool:
    return any(
        (isinstance(base, ast.Name) and base.id == "ABC")
        or (isinstance(base, ast.Attribute) and base.attr == "ABC")
        for base in node.bases
    )


def _posting_classes(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and not _is_abstract(node)
        and any(
            isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
            and member.name == "post_comment"
            for member in node.body
        )
    }


def test_only_the_fake_and_the_pygithub_client_define_post_comment() -> None:
    found: set[str] = set()
    for tree in modules().values():
        found |= _posting_classes(tree)

    assert found == {"FakeHostingService", "PyGithubHostingService"}


def test_no_test_class_defines_post_comment() -> None:
    found: set[str] = set()
    for path in sorted(TESTS.rglob("*.py")):
        found |= _posting_classes(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))

    assert found == set()
