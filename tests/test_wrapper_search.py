"""Only the three wrappers start processes through the process module."""

from source_search import imports, modules


def test_only_the_three_wrappers_import_the_process_module() -> None:
    importers = {
        name
        for name, tree in modules().items()
        if name != "factory.adapters.process" and imports(tree, "factory.adapters.process")
    }

    assert importers == {
        "factory.adapters.git_cli",
        "factory.adapters.make_commands",
        "factory.adapters.agent_home",
        "factory.adapters.fake_containers",
        "factory.adapters.claude_runtime",
        "factory.adapters.opencode_runtime",
        "factory.entry.confine",
        "factory.entry.leftovers",
    }
