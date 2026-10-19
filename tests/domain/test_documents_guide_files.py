"""The project guide as an index and its other files: the paths and the check of their words."""

import pytest

from document_texts import clean_texts
from factory.domain.documents import (
    DECISION_LOG,
    DOCUMENT_PATHS,
    PROJECT_GUIDE,
    PROJECT_GUIDE_FOLDER,
    DocumentFinding,
    check_documents,
    is_guide_file,
)

AGENTS = "docs/project-guide/agents.md"


def test_the_guide_is_an_index_in_its_folder() -> None:
    assert PROJECT_GUIDE == "docs/project-guide/README.md"
    assert PROJECT_GUIDE_FOLDER == "docs/project-guide"
    assert DOCUMENT_PATHS == (
        "README.md",
        "docs/operator-guide.md",
        "docs/project-guide/README.md",
        "docs/decisions.md",
    )


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("docs/project-guide/agents.md", True),
        ("docs/project-guide/a.b.md", True),
        ("docs/project-guide/README.md", False),
        ("docs/project-guide/sub/x.md", False),
        ("docs/project-guide/notes.txt", False),
        ("docs/project-guide/.md", False),
        ("docs/project-guide/X.MD", False),
        ("docs/project-guide.md", False),
        ("docs/project-guidex/a.md", False),
        ("docs/a.md", False),
        ("docs/project-guide/", False),
    ],
)
def test_a_guide_file_is_an_md_file_directly_beside_the_index(path: str, expected: bool) -> None:
    assert is_guide_file(path) is expected


@pytest.mark.parametrize(
    ("text", "messages"),
    [
        pytest.param("# Agents\n\nThe factory runs agents.\n", [], id="clean"),
        pytest.param(
            "# Agents\n\nEach ticket moves on.\n", ["uses the v1 word 'ticket'"], id="v1-word"
        ),
        pytest.param(
            "# Agents\n\nThe run record is gone.\n",
            ["describes a replaced behaviour: 'run record'"],
            id="replaced-phrase",
        ),
        pytest.param("  \n", ["empty"], id="blank"),
        pytest.param(None, ["missing"], id="none"),
        pytest.param(
            "# Agents\n\n## Replaced from v1\n\n| ticket | work item |\n", [], id="replaced-section"
        ),
    ],
)
def test_a_guide_file_is_checked_for_its_words_only(text: str | None, messages: list[str]) -> None:
    texts = clean_texts()
    texts[AGENTS] = text

    assert check_documents(texts) == [
        DocumentFinding(document=AGENTS, message=message) for message in messages
    ]


def test_guide_files_follow_the_four_documents_in_path_order_and_other_keys_are_ignored() -> None:
    texts = clean_texts()
    texts[DECISION_LOG] = "  \n"
    for path in (
        "docs/project-guide/b.md",
        "docs/project-guide/a.md",
        "docs/other.md",
        "docs/project-guide/sub/c.md",
    ):
        texts[path] = "A ticket.\n"

    assert check_documents(texts) == [
        DocumentFinding(document="docs/decisions.md", message="empty"),
        DocumentFinding(document="docs/project-guide/a.md", message="uses the v1 word 'ticket'"),
        DocumentFinding(document="docs/project-guide/b.md", message="uses the v1 word 'ticket'"),
    ]
