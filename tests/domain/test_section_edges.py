"""The section readers and the journal at a section's edge: no blank line, an empty block."""

import pytest

from factory.domain.errors import WorkItemFormatError
from factory.domain.journal import entry_text
from factory.domain.sections import CodeBlock, code_blocks, section_text
from factory.domain.work_item import WorkItemDocument, initial_state
from sections_support import TICKS


@pytest.mark.parametrize(
    "body",
    [
        pytest.param("# T\n## A\nfirst\nsecond\n## B\n", id="no-blank-lines"),
        pytest.param("# T\n\n## A\n\nfirst\nsecond\n\n## B\n", id="blank-lines"),
    ],
)
def test_section_text_starts_on_the_line_right_after_the_heading(body: str) -> None:
    assert section_text(body, "A") == "first\nsecond"


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        pytest.param([TICKS, TICKS], [CodeBlock(start=0, end=1)], id="alone"),
        pytest.param(
            [TICKS, TICKS, "text", TICKS],
            [CodeBlock(start=0, end=1), CodeBlock(start=3, end=None)],
            id="followed-by-an-open-block",
        ),
    ],
)
def test_an_empty_fenced_block_closes_on_the_line_after_its_opening(
    lines: list[str], expected: list[CodeBlock]
) -> None:
    assert code_blocks(lines) == expected


@pytest.mark.parametrize(
    ("body", "texts", "missing"),
    [
        pytest.param(
            "# T\n\n## Journal\n1. 2026-10-12 human: created.\n2. intake: accepted.\n",
            ["created.", "accepted."],
            None,
            id="entry-right-under-the-heading",
        ),
        pytest.param(
            "# T\n\n## Smoke test\n\n1. a numbered line\n## Journal\n\n"
            "1. 2026-10-12 human: created.\n",
            ["created."],
            2,
            id="numbered-line-right-above-the-heading",
        ),
    ],
)
def test_the_journal_starts_right_after_its_heading_and_not_above_it(
    body: str, texts: list[str], missing: int | None
) -> None:
    document = WorkItemDocument(state=initial_state("intake"), body=body)

    assert [entry_text(document, number) for number in range(1, len(texts) + 1)] == texts
    if missing is not None:
        with pytest.raises(WorkItemFormatError) as caught:
            entry_text(document, missing)
        assert caught.value.fault == f"no journal entry {missing}"
