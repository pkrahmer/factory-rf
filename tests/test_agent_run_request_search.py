"""The agent run's environment has one source: where `AgentRunRequest` is built, no `os.environ`."""

import ast

from source_search import imported_modules, modules

BUILDERS = {"factory.application.task", "factory.application.preflight"}
WITHOUT_PROCESS_ENVIRONMENT = ("factory.domain", "factory.application")


def _builds_a_request(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id == "AgentRunRequest":
                return True
            if isinstance(function, ast.Attribute) and function.attr == "AgentRunRequest":
                return True
    return False


def _reads_os_environ(tree: ast.Module) -> bool:
    if "os.environ" in imported_modules(tree):
        return True
    return any(
        isinstance(node, ast.Attribute)
        and node.attr == "environ"
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
        for node in ast.walk(tree)
    )


def _must_not_read_the_process_environment(name: str) -> bool:
    return name == "factory.adapters.claude_runtime" or any(
        name == layer or name.startswith(f"{layer}.") for layer in WITHOUT_PROCESS_ENVIRONMENT
    )


def test_agent_run_requests_are_built_only_by_the_task_and_the_preflight() -> None:
    builders = {name for name, tree in modules().items() if _builds_a_request(tree)}

    assert "factory.application.task" in builders
    assert builders <= BUILDERS


def test_no_inner_layer_and_not_the_claude_runtime_reads_os_environ() -> None:
    readers = [
        name
        for name, tree in modules().items()
        if _must_not_read_the_process_environment(name) and _reads_os_environ(tree)
    ]

    assert readers == []
