"""Only the three wrappers start processes through the process module."""

from support.source_search import imports, modules


def test_only_the_three_wrappers_import_the_process_module() -> None:
    importers = {
        name
        for name, tree in modules().items()
        if name != "factory.shared.adapters.process"
        and imports(tree, "factory.shared.adapters.process")
    }

    assert importers == {
        "factory.hosting.adapters.git_cli",
        "factory.machine.adapters.make_commands",
        "factory.machine.adapters.fake_containers",
        "factory.agents.adapters.claude_runtime",
        "factory.agents.adapters.opencode_runtime",
        "factory.machine.adapters.podman_runs",
        "factory.machine.adapters.zfs_snapshots",
        "factory.machine.adapters.power_off",
        "factory.shared.adapters.document_examples",
    }
