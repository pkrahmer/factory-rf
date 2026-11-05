"""A test that names a module at an old layer path looks for it in every area."""

import ast

import pytest

from support.module_names import is_old_layer_path
from support.search_support import TESTS
from support.source_search import string_literals

SEARCHED_ONLY_AT_ITS_PATH = "module_exists"


def _calls_module_exists(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id == SEARCHED_ONLY_AT_ITS_PATH:
                return True
            if isinstance(function, ast.Attribute) and function.attr == SEARCHED_ONLY_AT_ITS_PATH:
                return True
    return False


def _holds_an_old_layer_path(tree: ast.Module) -> bool:
    return any(is_old_layer_path(text) for text in string_literals(tree))


def _searching_old_paths_only_at_their_path(trees: dict[str, ast.Module]) -> list[str]:
    return sorted(
        name
        for name, tree in trees.items()
        if _holds_an_old_layer_path(tree) and _calls_module_exists(tree)
    )


def _test_modules() -> dict[str, ast.Module]:
    return {
        str(path.relative_to(TESTS)): ast.parse(
            path.read_text(encoding="utf-8"), filename=str(path)
        )
        for path in sorted(TESTS.rglob("*.py"))
    }


@pytest.mark.parametrize(
    ("source", "caught"),
    [
        pytest.param(
            'NAME = "factory.adapters.landlock"\nmodule_exists(name)\n', True, id="module-exists"
        ),
        pytest.param(
            'NAME = "factory.adapters.landlock"\nmodule_exists_anywhere(name)\n',
            False,
            id="module-exists-anywhere",
        ),
        pytest.param('module_exists("factory.entry.confine")\n', False, id="no-old-layer-path"),
        pytest.param('NAME = "factory.adapters"\nmodule_exists(name)\n', False, id="layer-alone"),
    ],
)
def test_a_module_that_names_an_old_layer_path_calls_module_exists_anywhere(
    source: str, caught: bool
) -> None:
    found = _searching_old_paths_only_at_their_path({"probe.py": ast.parse(source)})

    assert found == (["probe.py"] if caught else [])


def test_no_test_module_looks_for_an_old_layer_path_only_at_that_path() -> None:
    assert _searching_old_paths_only_at_their_path(_test_modules()) == []
