"""The documenter, the reviewer and the intake treat documents against the code."""

import pytest

from support.shipped_agents import agent_body

DOCUMENTS_HEADING = "### Documents"


def _paragraphs(text: str) -> list[str]:
    """The non-blank lines of the text, lowered: each line of an agent file is one paragraph."""
    return [line.lower() for line in text.splitlines() if line.strip()]


def _paragraphs_naming(text: str, fragments: tuple[str, ...]) -> list[str]:
    return [
        paragraph
        for paragraph in _paragraphs(text)
        if all(fragment.lower() in paragraph for fragment in fragments)
    ]


def _reviewer_checklist() -> str:
    body = agent_body("reviewer")
    start = body.index("\n## Role\n")
    end = body.index("\n## Stage\n")
    return body[start:end]


def _documents_item() -> str:
    lines = _reviewer_checklist().splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip() == DOCUMENTS_HEADING]
    assert len(starts) == 1, f"the reviewer's checklist has {len(starts)} `{DOCUMENTS_HEADING}`"
    rest = lines[starts[0] + 1 :]
    end = next((index for index, line in enumerate(rest) if line.startswith("#")), len(rest))
    return "\n".join(rest[:end])


@pytest.mark.parametrize(
    "fragments",
    [
        pytest.param(("read", "code", "before", "sentence"), id="read-the-code-first"),
        pytest.param(("*Reference*", "cut"), id="detail-kept-in-reference"),
        pytest.param(
            ("runnable", "marked", "VM", "GitHub", "model", "real run"),
            id="runnable-or-marked-examples",
        ),
        pytest.param(("`make documents`", "`documents ok`"), id="make-documents-ends-on-ok"),
    ],
)
def test_the_documenter_has_one_rule_for_each_way_a_document_stays_true(
    fragments: tuple[str, ...],
) -> None:
    assert len(_paragraphs_naming(agent_body("documenter"), fragments)) == 1


def test_the_reviewer_checklist_has_a_documents_item_naming_claims_against_code_and_examples() -> (
    None
):
    item = _documents_item().lower()

    assert "claim" in item
    assert "code" in item
    assert "example" in item


@pytest.mark.parametrize(
    "fragments",
    [
        pytest.param(("claim", "cannot find", "code", "finding"), id="claim-not-in-the-code"),
        pytest.param(("command", "runnable", "marked", "finding"), id="command-without-example"),
    ],
)
def test_the_reviewer_documents_item_counts_an_untrue_document_as_a_finding(
    fragments: tuple[str, ...],
) -> None:
    assert len(_paragraphs_naming(_documents_item(), fragments)) == 1


@pytest.mark.parametrize(
    "fragments",
    [
        pytest.param(
            ("docs criterion", "sentences", "question", "what the reader must know"),
            id="dictated-sentences-are-a-question",
        ),
        pytest.param(
            ("docs criterion", "sentences", "end with `question`"),
            id="ends-with-question",
        ),
    ],
)
def test_the_intake_asks_about_a_docs_criterion_that_dictates_sentences(
    fragments: tuple[str, ...],
) -> None:
    assert len(_paragraphs_naming(agent_body("intake"), fragments)) == 1
