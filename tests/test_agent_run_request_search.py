"""The agent run's environment has one source: where `AgentRunRequest` is built, no `os.environ`."""

import ast

from source_search import modules, reads_os_environ

BUILDERS = {"factory.pipeline.application.task", "factory.machine.application.preflight"}
WITHOUT_PROCESS_ENVIRONMENT = ("factory.pipeline.domain", "factory.pipeline.application")


def _builds_a_request(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id == "AgentRunRequest":
                return True
            if isinstance(function, ast.Attribute) and function.attr == "AgentRunRequest":
                return True
    return False


def _must_not_read_the_process_environment(name: str) -> bool:
    return name == "factory.agents.adapters.claude_runtime" or any(
        name == layer or name.startswith(f"{layer}.") for layer in WITHOUT_PROCESS_ENVIRONMENT
    )


def test_agent_run_requests_are_built_only_by_the_task_and_the_preflight() -> None:
    builders = {name for name, tree in modules().items() if _builds_a_request(tree)}

    assert "factory.pipeline.application.task" in builders
    assert builders <= BUILDERS


def test_no_inner_layer_and_not_the_claude_runtime_reads_os_environ() -> None:
    readers = [
        name
        for name, tree in modules().items()
        if _must_not_read_the_process_environment(name) and reads_os_environ(tree)
    ]

    assert readers == []
