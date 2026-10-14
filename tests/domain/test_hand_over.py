"""The pull request description at the approval and the text of the cost table post."""

from datetime import UTC, datetime

import pytest

from factory.domain.git import CommitInfo
from factory.domain.hand_over import HAND_OVER_CLOSING, REPORT_SECTIONS, hand_over_description
from factory.domain.journal import HUMAN, JournalKind, JournalRecord
from factory.domain.post_texts import cost_table_post
from factory.domain.sections import DESCRIPTION
from factory.domain.work_item import WorkItemDocument, WorkItemState

DESCRIPTION_TEXT = "Build it.\n\nWith care, and\n  an indented line."
CRITERIA_TEXT = "1. One.\n2. Two,\n   continued."
CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")
HEADINGS = [
    "## Description",
    "## Acceptance criteria",
    "## Tests",
    "## Review",
    "## Documentation",
    "## Smoke test",
    "## Commits",
]
CLOSING = (
    "Merge to accept the story. To send it back, close the pull request with a comment that says "
    "what should change; a close without one is answered with a question. Comments written while "
    "the story waits here are recorded in its journal and become the reason if you then close."
)


def _body(sections: str, journal_lines: list[str]) -> str:
    journal = "\n".join(["1. 2026-10-12 human: created.", *journal_lines])
    return f"# First story\n\n{sections}## Journal\n\n{journal}\n"


def _story_sections() -> str:
    return (
        f"## {DESCRIPTION}\n\n{DESCRIPTION_TEXT}\n\n"
        f"## Interface\n\nNot shown.\n\n"
        f"## Acceptance criteria\n\n{CRITERIA_TEXT}\n\n"
    )


def _document(
    entries: list[tuple[str, JournalKind, str]], *, sections: str | None = None
) -> WorkItemDocument:
    """A document whose journal records come from `entries`, visible lines and records apart.

    Each entry is the record's speaker and kind and the visible line's text after the number.
    """
    records = [CREATED]
    lines: list[str] = []
    for number, (speaker, kind, visible) in enumerate(entries, start=2):
        records.append(JournalRecord(number=number, speaker=speaker, kind=kind))
        lines.append(f"{number}. {visible}")
    state = WorkItemState(stage="approval", pull_request=7, journal=records)
    body = _body(_story_sections() if sections is None else sections, lines)
    return WorkItemDocument(state=state, body=body)


def _commit(commit: str, subject: str) -> CommitInfo:
    return CommitInfo(
        commit=commit,
        parents=[],
        subject=subject,
        author="coder",
        committed_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    )


def _section(text: str, heading: str) -> str:
    """The text between `## heading` and the next `## ` heading."""
    after = f"\n{text}".split(f"\n## {heading}\n\n", 1)[1]
    return after.split("\n\n## ", 1)[0]


ALL_RESULTS: list[tuple[str, JournalKind, str]] = [
    ("tester", "result", "tester: wrote the tests."),
    ("coder", "result", "coder: built it."),
    ("reviewer", "result", "reviewer: no findings."),
    ("documenter", "result", "documenter: updated the guide."),
    ("smoke-tester", "result", "smoke-tester: the demo ran."),
]


def test_the_description_has_its_headings_in_order_and_ends_with_the_closing_paragraph() -> None:
    text = hand_over_description(_document(ALL_RESULTS), [_commit("a" * 40, "feat: build it")])

    headings = [line for line in text.split("\n") if line.startswith("## ")]
    assert headings == HEADINGS
    assert text.endswith(f"\n\n{HAND_OVER_CLOSING}\n")
    assert not text.endswith("\n\n")
    assert text.startswith("## Description\n\n")


def test_the_description_and_criteria_sections_hold_the_story_sections_verbatim() -> None:
    text = hand_over_description(_document(ALL_RESULTS), [])

    assert f"## Description\n\n{DESCRIPTION_TEXT}\n\n## Acceptance criteria\n\n" in text
    assert f"## Acceptance criteria\n\n{CRITERIA_TEXT}\n\n## Tests\n\n" in text


@pytest.mark.parametrize(
    "sections",
    [
        "## Interface\n\nNot shown.\n\n",
        f"## {DESCRIPTION}\n\n## Interface\n\nNot shown.\n\n## Acceptance criteria\n\n",
    ],
    ids=["missing", "empty"],
)
def test_a_missing_or_empty_story_section_gives_none(sections: str) -> None:
    text = hand_over_description(_document(ALL_RESULTS, sections=sections), [])

    assert "## Description\n\nnone\n\n## Acceptance criteria\n\nnone\n\n## Tests\n\n" in text


def test_each_report_section_holds_the_latest_result_text_of_its_speaker() -> None:
    entries: list[tuple[str, JournalKind, str]] = [
        *ALL_RESULTS,
        ("reviewer", "question", "reviewer: should this change?"),
        ("tester", "result", "tester: rewrote the tests."),
    ]

    text = hand_over_description(_document(entries), [])

    assert _section(text, "Tests") == "rewrote the tests."
    assert _section(text, "Review") == "no findings."
    assert _section(text, "Documentation") == "updated the guide."
    assert _section(text, "Smoke test") == "the demo ran."


@pytest.mark.parametrize(("title", "speaker"), REPORT_SECTIONS)
def test_a_report_section_whose_speaker_has_no_result_record_holds_none(
    title: str, speaker: str
) -> None:
    entries = [entry for entry in ALL_RESULTS if entry[0] != speaker]
    entries.append((speaker, "question", f"{speaker}: a question, not a result."))

    text = hand_over_description(_document(entries), [])

    assert _section(text, title) == "none"


def test_a_report_section_is_found_by_the_record_and_not_by_the_visible_speaker() -> None:
    entries: list[tuple[str, JournalKind, str]] = [
        ("tester", "result", "reviewer: wrote the tests."),
    ]

    text = hand_over_description(_document(entries), [])

    assert _section(text, "Tests") == "wrote the tests."
    assert _section(text, "Review") == "none"


@pytest.mark.parametrize(
    ("commits", "block"),
    [
        (
            [_commit("a" * 40, "feat: build it"), _commit("b" * 40, "fix: mend it")],
            "```\naaaaaaa feat: build it\nbbbbbbb fix: mend it\n```",
        ),
        ([], "```\n```"),
    ],
    ids=["two-commits", "no-commit"],
)
def test_the_commits_section_is_a_fenced_block_of_short_ids_and_subjects(
    commits: list[CommitInfo], block: str
) -> None:
    text = hand_over_description(_document(ALL_RESULTS), commits)

    assert text.endswith(f"## Commits\n\n{block}\n\n{HAND_OVER_CLOSING}\n")


def test_the_cost_table_post_is_a_heading_line_a_blank_line_and_the_table() -> None:
    assert cost_table_post("T") == "Cost of this work item so far\n\nT"


def test_the_closing_paragraph_says_how_to_accept_send_back_and_what_a_bare_close_does() -> None:
    assert HAND_OVER_CLOSING == CLOSING
    assert "Merge to accept the story." in HAND_OVER_CLOSING
    assert "close the pull request with a comment" in HAND_OVER_CLOSING
    assert "a close without one is answered with a question" in HAND_OVER_CLOSING
