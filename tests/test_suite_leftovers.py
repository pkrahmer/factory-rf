"""The suite's own pipeline definition and the preparer's test, as the shipped ones have them."""

import ast
from pathlib import Path

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from git_support import PIPELINE_YAML

TESTS = Path(__file__).parent
PREPARER_TESTS = TESTS / "application" / "test_checkout_preparer.py"


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _row_ids(test: ast.FunctionDef) -> set[str]:
    return {
        keyword.value.value
        for decorator in test.decorator_list
        for node in ast.walk(decorator)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "id" and isinstance(keyword.value, ast.Constant)
        if isinstance(keyword.value.value, str)
    }


def test_the_suite_s_smoke_test_moves_back_to_doing_or_docs() -> None:
    definition = RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)

    assert definition.stages["smoke-test"].next == ["approval", "doing", "docs"]


def test_the_preparer_s_test_of_its_parameters_is_one_plain_check_of_log() -> None:
    tree = ast.parse(PREPARER_TESTS.read_text(encoding="utf-8"), filename=str(PREPARER_TESTS))
    plain = _function(tree, "test_the_preparer_takes_only_the_git_and_the_settings")
    body = ast.unparse(plain)

    assert not [d for d in plain.decorator_list if "parametrize" in ast.unparse(d)]
    assert plain.args.args == []
    assert "assert 'log' not in inspect.signature(CheckoutPreparer.__init__).parameters" in body
    clones = _function(tree, "test_the_preparer_clones_only_a_missing_checkout_and_checks_none")
    assert {"missing-is-cloned", "group-writable-git-is-kept"} <= _row_ids(clones)
