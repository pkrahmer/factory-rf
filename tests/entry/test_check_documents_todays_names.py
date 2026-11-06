"""The log file and git addresses in a document are no missing file."""

from pathlib import Path

import pytest

from factory.shared.domain.documents import named_references
from support.minimal_documents_support import add_and_commit


@pytest.mark.parametrize(
    ("document", "text"),
    [
        pytest.param("docs/operator-guide/machine.md", "factory.log", id="log-file"),
        pytest.param(
            "docs/operator-guide/install.md",
            "git@github.com:owner/project.git",
            id="git-address-install",
        ),
        pytest.param(
            "docs/operator-guide/cloud-run.md",
            "git@host:owner/name.git",
            id="git-address-cloud-run",
        ),
    ],
)
def test_todays_documents_give_no_finding_for_the_log_file_and_git_addresses(
    minimal: Path, document: str, text: str
) -> None:
    add_and_commit(minimal, {document: f"# A topic\n\n## Running it\n\nSee `{text}`.\n"})
    top_level = frozenset(entry.name for entry in minimal.iterdir())
    content = (minimal / document).read_text(encoding="utf-8")

    references = named_references(document, content, top_level)

    assert [reference for reference in references if reference.name == text] == []
