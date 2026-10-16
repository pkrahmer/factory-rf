"""Files are replaced atomically through one module function, not by copies of it."""

import ast

from source_search import modules


def _replace_calls(tree: ast.Module) -> int:
    from_os = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "os"
        for alias in node.names
        if alias.name == "replace"
    }
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and function.attr == "replace"
            and isinstance(function.value, ast.Name)
            and function.value.id == "os"
        ) or (isinstance(function, ast.Name) and function.id in from_os):
            count += 1
    return count


def test_exactly_one_call_of_os_replace_exists_in_the_package() -> None:
    snippet = ast.parse("import os\nos.replace('a', 'b')\n'text'.replace('a', 'b')\n")
    calls = {name: found for name, tree in modules().items() if (found := _replace_calls(tree))}

    assert _replace_calls(snippet) == 1
    assert sum(calls.values()) == 1
