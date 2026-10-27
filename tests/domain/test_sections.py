"""Titles, sections and fenced blocks of a Markdown body."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import WorkItemFormatError
from factory.domain.sections import (
    ACCEPTANCE_CRITERIA,
    JOURNAL,
    SMOKE_TEST,
    CodeBlock,
    Section,
    code_blocks,
    insert_paragraph,
    opening_fence,
    required_sections,
    section_text,
    sections,
    split_lines,
    title,
)
from sections_support import TICKS

TILDES = "~" * 3


@pytest.mark.parametrize(
    ("body", "lines"),
    [
        ("a\nb\n", ["a", "b"]),
        ("a\nb", ["a", "b"]),
        ("", []),
        ("\n", [""]),
        ("a\n\n", ["a", ""]),
    ],
)
def test_split_lines_drops_only_an_empty_last_element(body: str, lines: list[str]) -> None:
    assert split_lines(body) == lines


def test_backtick_and_tilde_blocks_are_found() -> None:
    lines = ["x", TICKS + "python", "a", TICKS, "y", TILDES, "b", TILDES]

    assert code_blocks(lines) == [CodeBlock(start=1, end=3), CodeBlock(start=5, end=7)]


def test_indented_opening_and_closing_lines_are_recognised() -> None:
    lines = ["x", "  " + TICKS, "a", "\t" + TICKS]

    assert code_blocks(lines) == [CodeBlock(start=1, end=3)]


@pytest.mark.parametrize(
    ("lines", "blocks"),
    [
        (["````", TICKS, "````"], [CodeBlock(start=0, end=2)]),
        (["````", "a", "`````"], [CodeBlock(start=0, end=2)]),
        ([TICKS, TILDES, TICKS], [CodeBlock(start=0, end=2)]),
        ([TICKS, TICKS + " x", TICKS], [CodeBlock(start=0, end=2)]),
        ([TICKS, "a", TICKS + "  "], [CodeBlock(start=0, end=2)]),
        (["x", TICKS, "a", "## b", TICKS + " x"], [CodeBlock(start=1, end=None)]),
        (["````", TICKS], [CodeBlock(start=0, end=None)]),
    ],
)
def test_a_block_closes_only_at_a_run_of_its_own_character_at_least_as_long(
    lines: list[str], blocks: list[CodeBlock]
) -> None:
    assert code_blocks(lines) == blocks


@pytest.mark.parametrize("line", ["``", "~~", "`x` is inline code"])
def test_a_line_starting_with_a_short_run_opens_no_block(line: str) -> None:
    assert code_blocks([line, "## A"]) == []
    assert sections(f"{line}\n## A\n") == [Section(heading="A", start=1, end=2)]


def test_sections_run_from_heading_to_next_heading() -> None:
    body = "# T\n\nintro\n\n## A\n\ntext\n\n## B"

    assert sections(body) == [
        Section(heading="A", start=4, end=8),
        Section(heading="B", start=8, end=9),
    ]


@pytest.mark.parametrize("fence", [TICKS, TILDES])
def test_a_heading_inside_a_fenced_block_is_not_a_heading(fence: str) -> None:
    body = f"## A\n{fence}\n## B\n{fence}\n## C"

    assert sections(body) == [
        Section(heading="A", start=0, end=4),
        Section(heading="C", start=4, end=5),
    ]


def test_a_heading_after_an_unclosed_block_is_not_a_heading() -> None:
    body = f"## A\n{TICKS}\n## B\ntext\n## C\n"

    assert sections(body) == [Section(heading="A", start=0, end=5)]


@pytest.mark.parametrize("line", ["### x", " ## x", "##x", "##", "# x"])
def test_lines_that_are_not_level_two_headings_open_no_section(line: str) -> None:
    assert sections(f"text\n{line}\nmore\n") == []


def test_a_heading_text_is_stripped_of_trailing_whitespace() -> None:
    assert sections("## A  \t\ntext\n") == [Section(heading="A", start=0, end=2)]


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("# T  \nx\n# U\n", "T"),
        ("intro\n## x\ntext\n", None),
        ("", None),
        (f"{TICKS}\n# comment\n{TICKS}\n# Real\n", "Real"),
        (f"{TILDES}\n# comment\n", None),
        ("#x\n# Real\n", "Real"),
        ("## x\n# Real\n", "Real"),
        ("#x\n## x\n", None),
        (" # x\n# y\n", "y"),
    ],
)
def test_the_title_is_the_first_level_one_heading_outside_blocks(
    body: str, expected: str | None
) -> None:
    assert title(body) == expected


SECTIONED = (
    f"# T\n\n## A\n\nline 1\n\nline 2\n{TICKS}\ncode\n{TICKS}\n\n\n## Empty\n\n\n## A\nsecond\n"
)


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("A", f"line 1\n\nline 2\n{TICKS}\ncode\n{TICKS}"),
        ("Empty", ""),
        ("Missing", None),
        ("a", None),
    ],
)
def test_section_text_is_the_trimmed_text_under_the_first_matching_heading(
    heading: str, expected: str | None
) -> None:
    assert section_text(SECTIONED, heading) == expected


def test_section_text_keeps_a_fenced_block_with_heading_lines_whole() -> None:
    body = f"# T\n## Demo\n\n{TICKS}\n## x\n# y\n{TICKS}\nafter\n\n## End\n"

    assert section_text(body, "Demo") == f"{TICKS}\n## x\n# y\n{TICKS}\nafter"
    assert section_text(body, "x") is None


def test_a_paragraph_goes_first_under_the_heading() -> None:
    result = insert_paragraph("## Verdict\n\nAccepted.\n", "Verdict", "Reason.")

    assert result == "## Verdict\n\nReason.\n\nAccepted.\n"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("## A\n", "## A\n\nX\n"),
        ("## A\n\n## B\n", "## A\n\nX\n\n## B\n"),
        ("## A\n\nold", "## A\n\nX\n\nold"),
    ],
)
def test_a_paragraph_in_an_empty_section_or_a_body_without_final_newline(
    body: str, expected: str
) -> None:
    assert insert_paragraph(body, "A", "X") == expected


def test_a_paragraph_of_several_lines_goes_whole_under_the_first_heading() -> None:
    body = "intro\n## Other\nkeep\n## Verdict\nold 1\n\nold 2\n## Verdict\nsecond\n"

    result = insert_paragraph(body, "Verdict", "P1\nP2")

    assert result == (
        "intro\n## Other\nkeep\n## Verdict\n\nP1\nP2\n\nold 1\n\nold 2\n## Verdict\nsecond\n"
    )


@pytest.mark.parametrize(
    "body",
    ["## Other\ntext\n", f"## Other\n{TICKS}\n## Verdict\n{TICKS}\n"],
)
def test_inserting_under_a_missing_heading_is_a_format_error(body: str) -> None:
    with pytest.raises(WorkItemFormatError) as caught:
        insert_paragraph(body, "Verdict", "Reason.")

    assert caught.value.fault == "missing section: ## Verdict"


@pytest.mark.parametrize("paragraph", ["", "  \n"])
def test_a_blank_paragraph_is_refused(paragraph: str) -> None:
    with pytest.raises(ValueError):
        insert_paragraph("## Verdict\n\nAccepted.\n", "Verdict", paragraph)


def test_required_sections_are_the_form_headings_in_order() -> None:
    form = (
        "# Story form\n"
        "<!-- comment -->\n"
        "\n"
        "## Description\n"
        "\n"
        "text\n"
        "\n"
        "## Interface\n"
        "\n"
        "### Sub\n"
        "\n"
        f"{TICKS}\n"
        "## Hidden\n"
        f"{TICKS}\n"
        "\n"
        "## Journal\n"
    )

    assert required_sections(form) == ["Description", "Interface", "Journal"]


def test_the_three_known_section_names() -> None:
    assert ACCEPTANCE_CRITERIA == "Acceptance criteria"
    assert SMOKE_TEST == "Smoke test"
    assert JOURNAL == "Journal"


@pytest.mark.parametrize(
    ("model", "field", "value", "accepted"),
    [
        (Section, "start", 0, True),
        (Section, "start", -1, False),
        (Section, "end", 0, True),
        (Section, "end", -1, False),
        (CodeBlock, "start", 0, True),
        (CodeBlock, "start", -1, False),
        (CodeBlock, "end", 0, True),
        (CodeBlock, "end", -1, False),
        (CodeBlock, "end", None, True),
    ],
)
def test_indices_are_not_negative(
    model: type[BaseModel], field: str, value: int | None, accepted: bool
) -> None:
    fields: dict[str, object] = {"start": 0, "end": 0, field: value}
    if model is Section:
        fields["heading"] = "A"
    if accepted:
        assert model(**fields).model_dump()[field] == value
    else:
        with pytest.raises(ValidationError):
            model(**fields)


@pytest.mark.parametrize(
    ("line", "fence"),
    [
        ("  ````python", "````"),
        ("~~~", "~~~"),
        (TICKS, TICKS),
        ("``x", None),
        ("x " + TICKS, None),
        ("", None),
    ],
)
def test_opening_fence_is_the_run_a_line_opens_a_block_with(line: str, fence: str | None) -> None:
    assert opening_fence(line) == fence
