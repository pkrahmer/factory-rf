"""The wording check finds a v1 word at the edges of a line and of the text."""

import pytest

from document_texts import clean_texts
from factory.domain.documents import DocumentFinding, check_documents

AGENTS = "docs/project-guide/agents.md"
TICKET = [DocumentFinding(document=AGENTS, message="uses the v1 word 'ticket'")]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("# Agents\n\nEach ticket\nmoves on.\n", TICKET, id="end-of-line"),
        pytest.param("# Agents\n\nThe run\nticket moves on.\n", TICKET, id="start-of-line"),
        pytest.param("# Agents\n\nThe last ticket", TICKET, id="end-of-text"),
        pytest.param("# Agents\n\nEach ticketed\nmoves on.\n", [], id="longer-at-end-of-line"),
        pytest.param("# Agents\n\nThe run\nsubticket moves.\n", [], id="longer-at-start-of-line"),
    ],
)
def test_a_v1_word_is_found_at_a_line_edge_and_a_longer_word_is_not(
    text: str, expected: list[DocumentFinding]
) -> None:
    texts = clean_texts()
    texts[AGENTS] = text

    assert check_documents(texts) == expected
