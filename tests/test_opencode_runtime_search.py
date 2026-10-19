"""Neither the opencode runtime module nor the shared launch module reads `os.environ`."""

import ast

from source_search import modules, reads_os_environ

SEARCHED = ("factory.adapters.opencode_runtime", "factory.adapters.agent_launch")


def test_neither_the_opencode_runtime_nor_the_launch_module_reads_os_environ() -> None:
    snippet = ast.parse('import os\nhome = os.environ.get("HOME")\n')
    found = modules()

    assert reads_os_environ(snippet)
    assert all(name in found for name in SEARCHED)
    assert [name for name in SEARCHED if reads_os_environ(found[name])] == []
