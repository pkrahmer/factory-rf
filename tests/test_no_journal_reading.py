"""No code under `src/factory` turns the journal's text into data."""

import ast

import pytest

from source_search import modules, string_literals

ALLOWED = {
    "entry_text": {
        "factory.domain.journal",
        "factory.application.handlers.hand_over",
        "factory.application.handlers.questions",
    },
    "JOURNAL": {
        "factory.domain.sections",
        "factory.domain.journal",
        "factory.domain.story_form",
        "factory.adapters.work_item_markdown",
        "factory.application.opening",
    },
}
LITERALS = {"Journal", "## Journal"}
LITERAL_MODULE = "factory.domain.sections"
OUTSIDE = "factory.application.example"


def _referenced_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def violations(trees: dict[str, ast.Module]) -> list[str]:
    """Every reference to a journal name or literal outside the modules allowed to hold it."""
    found: list[str] = []
    for module, tree in sorted(trees.items()):
        referenced = _referenced_names(tree)
        for name, allowed in ALLOWED.items():
            if name in referenced and module not in allowed:
                found.append(f"{module} references {name}")
        if module != LITERAL_MODULE:
            found.extend(
                f"{module} holds the literal {literal!r}"
                for literal in sorted(LITERALS.intersection(string_literals(tree)))
            )
    return found


def test_no_module_reads_data_from_the_journal_text() -> None:
    assert violations(modules()) == []


@pytest.mark.parametrize(
    "source",
    [
        "from factory.domain.journal import entry_text\n",
        "entry_text(document, 1)\n",
        "journal.entry_text(document, 1)\n",
        "from factory.domain.sections import JOURNAL\n",
        "heading = JOURNAL\n",
        "heading = sections.JOURNAL\n",
        'section_text(body, "Journal")\n',
        'section_text(body, "## Journal")\n',
    ],
    ids=[
        "entry-text-import",
        "entry-text-name",
        "entry-text-attribute",
        "journal-import",
        "journal-name",
        "journal-attribute",
        "literal-journal",
        "literal-journal-heading",
    ],
)
def test_a_journal_reference_outside_the_allowed_modules_is_found(source: str) -> None:
    assert violations({OUTSIDE: ast.parse(source)}) != []


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("factory.domain.journal", "entry_text(document, 1)\n"),
        ("factory.application.opening", "heading = JOURNAL\n"),
        ("factory.domain.sections", 'JOURNAL = "Journal"\n'),
    ],
    ids=["entry-text", "journal", "literal"],
)
def test_a_journal_reference_in_an_allowed_module_is_not_found(module: str, source: str) -> None:
    assert violations({module: ast.parse(source)}) == []
