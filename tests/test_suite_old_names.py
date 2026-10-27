"""The test names speak of no removed layer, log or contract version."""

import ast
import re
from collections.abc import Callable
from pathlib import Path

import pytest

TESTS = Path(__file__).parent
OLD_NAMES = (
    "test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user",
    "test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user",
    "test_an_existing_checkout_is_kept_without_a_log_line",
    "test_the_committed_schemas_list_provider_limit_at_version_1_2",
    "test_the_records_contract_is_at_version_2_without_tool_paths",
    "test_the_records_contract_is_at_version_3_without_nested_repository",
)
CONTRACT_MODULES = (
    "domain/test_contract_provider_limit.py",
    "domain/test_contract_without_tool_paths.py",
    "domain/test_contract_without_nested_repository.py",
)


def _no_definition_of(name: str) -> Callable[[], None]:
    def check() -> None:
        pattern = re.compile(rf"^\s*def {name}\(", re.MULTILINE)
        defining = [path for path in TESTS.rglob("*.py") if pattern.search(path.read_text("utf-8"))]

        assert defining == []

    return check


def _no_seal_module() -> None:
    assert list(TESTS.rglob("test_checkout_preparer_seal.py")) == []


def _no_contract_version() -> None:
    for module in CONTRACT_MODULES:
        tree = ast.parse((TESTS / module).read_text(encoding="utf-8"))
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        strings = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

        assert [name for name in functions if re.search(r"version_[0-9]|at_version", name)] == []
        assert [text for text in strings if re.fullmatch(r"[0-9]+\.[0-9]+", text)] == []
        assert "RECORDS_CONTRACT" not in names


@pytest.mark.parametrize(
    "check",
    [
        *(pytest.param(_no_definition_of(name), id=name) for name in OLD_NAMES),
        pytest.param(_no_seal_module, id="seal-module"),
        pytest.param(_no_contract_version, id="contract-version"),
    ],
)
def test_no_test_keeps_an_old_name_or_a_contract_version(check: Callable[[], None]) -> None:
    check()
