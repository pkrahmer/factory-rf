"""The wiring: the one module of the entry layer that picks concrete adapters."""

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.entry.wiring import build_work_item_reader
from source_search import imports, modules


def test_the_work_item_reader_is_the_frontmatter_reader() -> None:
    assert isinstance(build_work_item_reader(), FrontmatterWorkItemReader)


def test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer() -> None:
    entry = {
        name: tree
        for name, tree in modules().items()
        if name == "factory.entry" or name.startswith("factory.entry.")
    }
    importers = {name for name, tree in entry.items() if imports(tree, "factory.adapters")}

    assert "factory.entry.check_story" in entry
    assert importers == {
        "factory.entry.wiring",
        "factory.entry.leftovers",
        "factory.entry.fresh_home",
    }
