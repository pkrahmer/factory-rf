"""Today's documents name no missing file for the log file and git addresses."""

import pytest

from factory.shared.domain.documents import named_references
from support.operator_support import ROOT


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
    document: str, text: str
) -> None:
    top_level = frozenset(entry.name for entry in ROOT.iterdir())
    content = (ROOT / document).read_text(encoding="utf-8")
    assert text in content

    references = named_references(document, content, top_level)

    assert [reference for reference in references if reference.name == text] == []
