"""What the test modules share is defined once, in a support module, and imported from there."""

import ast
from collections.abc import Callable
from pathlib import Path

import pytest

TESTS = Path(__file__).parent


def _tree(relative: str) -> ast.Module:
    path = TESTS / relative
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _defined(tree: ast.Module) -> set[str]:
    """The names a module defines at its top level: its functions, classes and assignments."""
    names: set[str] = set()
    for node in tree.body:
        match node:
            case ast.FunctionDef(name=name) | ast.ClassDef(name=name):
                names.add(name)
            case ast.Assign(targets=targets):
                names.update(target.id for target in targets if isinstance(target, ast.Name))
            case ast.AnnAssign(target=ast.Name(id=name)):
                names.add(name)
            case _:
                pass
    return names


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _definers(name: str) -> list[str]:
    """The modules under `tests/` that define `name` at their top level, relative and sorted."""
    return sorted(
        path.relative_to(TESTS).as_posix()
        for path in TESTS.rglob("*.py")
        if name in _defined(ast.parse(path.read_text(encoding="utf-8")))
    )


def _imports_from(tree: ast.Module) -> set[tuple[str, str]]:
    """The pairs (module, name) of the module's `from ... import ...` statements."""
    return {
        (node.module or "", alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def _runtime_end_once() -> None:
    tree = _tree("adapters/test_runtimes_without_wrapper.py")
    constructors = _function(tree, "test_no_constructor_takes_the_wrapper_or_its_folders")
    calls = [
        node.func.id
        for node in ast.walk(constructors)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]

    assert not {"_claude_end", "_opencode_end"} & _defined(tree)
    assert "hasattr" not in calls


def _container_once() -> None:
    for module in (
        "domain/test_settings_agent_user_unread.py",
        "domain/test_settings_one_environment.py",
        "domain/test_settings_stage_environment.py",
    ):
        assert "CONTAINER" not in _defined(_tree(module)), module


def _get_repo_recorder_once() -> None:
    assert _definers("record_get_repo") == ["wiring_support.py"]


def _get_repo_recorder_public() -> None:
    assert _definers("record_get_repo") == ["wiring_support.py"]
    assert _definers("_record_get_repo") == []


def _vm_setup_helpers_once() -> None:
    for name in ("in_order", "lines_with"):
        assert _definers(name) == ["vm_support.py"], name
        assert _definers(f"_{name}") == [], name


def _schemas_once() -> None:
    assert _definers("SCHEMAS") == ["contract_support.py"]


def _contract_login_helpers_once() -> None:
    for name in ("committed", "values"):
        assert _definers(name) == ["contract_login_support.py"], name
        assert _definers(f"_{name}") == [], name


def _recording_once() -> None:
    for module in (
        "entry/test_wiring_container_extra.py",
        "entry/test_wiring_stage_environment.py",
    ):
        assert not {"_recording", "_recording_stand_in", "_calls"} & _defined(_tree(module))


def _ca_names_once() -> None:
    assert "CA_NAMES" not in _defined(_tree("container_extra_support.py"))


def _reset_prefix_once() -> None:
    literals = [
        node.value
        for node in ast.walk(_tree("test_suite_fixtures.py"))
        if isinstance(node, ast.Constant)
    ]

    assert "stage environment: reset" not in literals
    assert "RESET_PREFIX" not in _defined(_tree("application/test_stage_on_container_fakes.py"))


def _hook_test_plain() -> None:
    test = _function(
        _tree("adapters/test_claude_runtime_no_hook.py"), "test_no_run_registers_a_hook"
    )

    assert not [
        decorator for decorator in test.decorator_list if "parametrize" in ast.unparse(decorator)
    ]


def _shared_from_support() -> None:
    shared = {
        "run_end": ("run_layout_support", ["adapters/test_runtimes_without_wrapper.py"]),
        "recording_stand_in": (
            "recording_stand_in_support",
            ["entry/test_wiring_container_extra.py", "entry/test_wiring_stage_environment.py"],
        ),
        "recorded_calls": (
            "recording_stand_in_support",
            ["entry/test_wiring_container_extra.py", "entry/test_wiring_stage_environment.py"],
        ),
        "RESET_PREFIX": (
            "container_support",
            ["test_suite_fixtures.py", "application/test_stage_on_container_fakes.py"],
        ),
    }
    for name, (support, users) in shared.items():
        assert _definers(name) == [f"{support}.py"], name
        for user in users:
            assert (support, name) in _imports_from(_tree(user)), (user, name)


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(_runtime_end_once, id="runtime-end"),
        pytest.param(_container_once, id="container-settings"),
        pytest.param(_get_repo_recorder_once, id="record-get-repo"),
        pytest.param(_get_repo_recorder_public, id="record-get-repo-public"),
        pytest.param(_vm_setup_helpers_once, id="vm-setup-helpers"),
        pytest.param(_schemas_once, id="contract-schemas"),
        pytest.param(_contract_login_helpers_once, id="contract-login-helpers"),
        pytest.param(_recording_once, id="recording-stand-in"),
        pytest.param(_ca_names_once, id="ca-bundle-names"),
        pytest.param(_reset_prefix_once, id="reset-prefix"),
        pytest.param(_hook_test_plain, id="hook-test-plain"),
        pytest.param(_shared_from_support, id="shared-from-support"),
    ],
)
def test_each_shared_helper_and_constant_is_held_once(check: Callable[[], None]) -> None:
    check()
