"""The agent definitions are read from one place only: the agent home of the settings."""

import ast

from source_search import modules

READER = "FrontmatterAgentDefinitionReader"


def _called_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def test_the_agent_definition_reader_is_built_once_from_the_settings_agent_home() -> None:
    found = [
        (module, [ast.unparse(argument) for argument in node.args])
        for module, tree in modules().items()
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _called_name(node) == READER
    ]

    assert found == [("factory.entry.wiring", ["settings.agent_home"])]
