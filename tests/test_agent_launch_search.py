"""The shared launch module starts no process, and neither runtime module reads `os.environ`."""

import ast

from source_search import imports, modules, reads_os_environ

LAUNCH = "factory.adapters.agent_launch"
SEARCHED = (LAUNCH, "factory.adapters.claude_runtime")


def test_neither_runtime_module_reads_os_environ() -> None:
    snippet = ast.parse('import os\nhome = os.environ.get("HOME")\n')
    found = modules()
    readers = [name for name in SEARCHED if reads_os_environ(found[name])]

    assert reads_os_environ(snippet)
    assert readers == []


def test_the_launch_module_does_not_import_the_process_module() -> None:
    assert not imports(modules()[LAUNCH], "factory.adapters.process")
