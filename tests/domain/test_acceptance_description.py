"""The pull request description of an acceptance at its approval."""

import pytest

from factory.domain.acceptance import (
    ACCEPTANCE_CLOSING,
    FINDINGS_IN_SHORT,
    NONE_TEXT,
    PROPOSED_STORIES,
    RECOMMENDATION,
    AcceptanceState,
    acceptance_description,
)
from factory.domain.journal import FACTORY, HUMAN, JournalKind, JournalRecord
from factory.domain.work_item import WorkItemDocument

ROLE = "acceptance-reviewer"
RECOMMENDATION_TEXT = "accepted with stories"
PROPOSED_TEXT = "- one story"
FINDINGS_TEXT = "accepted with stories; 1 story proposed"
TITLE = "# Acceptance of Todo service\n\n"
REPORT_SECTIONS = (
    f"## Recommendation\n\n{RECOMMENDATION_TEXT}\n\n## Proposed stories\n\n{PROPOSED_TEXT}\n\n"
)
CLOSING = (
    "Merge to accept the report and take the proposed stories into the feature's backlog, "
    "where you refine them before starting any. "
    "Close, with a comment saying why, to refuse: the report stays on the main branch as refused "
    "with your comment, the proposed stories are discarded, and the feature counts as not "
    "accepted until another story is archived and a new acceptance runs. "
    "Nobody answers comments while the acceptance waits here; they go into the report's journal."
)
REVIEWER_RESULT = (ROLE, "result", f"{ROLE}: {FINDINGS_TEXT}")


def _document(
    entries: list[tuple[str, JournalKind, str]], *, sections: str = REPORT_SECTIONS
) -> WorkItemDocument:
    """A report whose journal holds a started record and then `entries`.

    Each entry is the record's speaker and kind and the visible line's text after the number.
    """
    records = [JournalRecord(number=1, speaker=FACTORY, kind="started")]
    lines = ["1. factory: started."]
    for number, (speaker, kind, visible) in enumerate(entries, start=2):
        records.append(JournalRecord(number=number, speaker=speaker, kind=kind))
        lines.append(f"{number}. {visible}")
    journal = "\n".join(lines)
    state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=records)
    return WorkItemDocument(state=state, body=f"{TITLE}{sections}## Journal\n\n{journal}\n")


def _description(recommendation: str, findings: str, proposed: str) -> str:
    return (
        f"## Recommendation\n\n{recommendation}\n\n## Findings in short\n\n{findings}\n\n"
        f"## Proposed stories\n\n{proposed}\n\n{ACCEPTANCE_CLOSING}"
    )


def test_the_description_holds_the_recommendation_findings_proposed_stories_and_closing() -> None:
    document = _document([REVIEWER_RESULT])

    description = acceptance_description(document, ROLE)

    assert description == (
        "## Recommendation\n\naccepted with stories\n\n"
        "## Findings in short\n\naccepted with stories; 1 story proposed\n\n"
        "## Proposed stories\n\n- one story\n\n" + ACCEPTANCE_CLOSING
    )
    assert (RECOMMENDATION, FINDINGS_IN_SHORT, PROPOSED_STORIES) == (
        "Recommendation",
        "Findings in short",
        "Proposed stories",
    )


def test_the_findings_are_the_later_of_two_results_of_the_reviewer() -> None:
    document = _document([(ROLE, "result", f"{ROLE}: first findings"), REVIEWER_RESULT])

    description = acceptance_description(document, ROLE)

    assert description == _description(RECOMMENDATION_TEXT, FINDINGS_TEXT, PROPOSED_TEXT)


def test_a_result_of_another_speaker_and_a_later_human_comment_are_not_the_findings() -> None:
    document = _document(
        [
            REVIEWER_RESULT,
            ("coder", "result", "coder: built something"),
            (HUMAN, "comment", "2026-10-14 human: looks fine"),
        ]
    )

    description = acceptance_description(document, ROLE)

    assert description == _description(RECOMMENDATION_TEXT, FINDINGS_TEXT, PROPOSED_TEXT)


@pytest.mark.parametrize(
    ("entries", "sections", "expected"),
    [
        (
            [REVIEWER_RESULT],
            f"## Proposed stories\n\n{PROPOSED_TEXT}\n\n",
            (NONE_TEXT, FINDINGS_TEXT, PROPOSED_TEXT),
        ),
        (
            [REVIEWER_RESULT],
            f"## Recommendation\n\n{RECOMMENDATION_TEXT}\n\n",
            (RECOMMENDATION_TEXT, FINDINGS_TEXT, NONE_TEXT),
        ),
        (
            [REVIEWER_RESULT],
            f"## Recommendation\n\n## Proposed stories\n\n{PROPOSED_TEXT}\n\n",
            (NONE_TEXT, FINDINGS_TEXT, PROPOSED_TEXT),
        ),
        (
            [(ROLE, "question", f"{ROLE}: which feature?")],
            REPORT_SECTIONS,
            (RECOMMENDATION_TEXT, NONE_TEXT, PROPOSED_TEXT),
        ),
    ],
    ids=["no-recommendation", "no-proposed-stories", "empty-section", "no-reviewer-result"],
)
def test_a_missing_part_reads_none_and_leaves_the_others(
    entries: list[tuple[str, JournalKind, str]],
    sections: str,
    expected: tuple[str, str, str],
) -> None:
    document = _document(entries, sections=sections)

    description = acceptance_description(document, ROLE)

    assert NONE_TEXT == "none"
    assert description == _description(*expected)


@pytest.mark.parametrize("word", ["squash", "rebase", "merge commit"])
def test_the_closing_names_no_merge_method_and_ends_the_description(word: str) -> None:
    description = acceptance_description(_document([REVIEWER_RESULT]), ROLE)

    assert ACCEPTANCE_CLOSING == CLOSING
    assert word not in ACCEPTANCE_CLOSING.lower()
    assert description.endswith(f"\n\n{ACCEPTANCE_CLOSING}")
