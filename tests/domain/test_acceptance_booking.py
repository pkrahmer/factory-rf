"""Booking an acceptance's result: accepted by the merge, refused with the human's reason."""

from collections.abc import Callable
from datetime import UTC, date, datetime

import pytest

from acceptance_support import report_of
from bill_support import completed_records
from factory.domain.acceptance import (
    NO_REASON,
    AcceptanceState,
    book_merge,
    book_refusal,
    refusal_reason,
)
from factory.domain.bills import Bill, bill, cost_line
from factory.domain.journal import FACTORY, HUMAN, JournalKind, JournalRecord, entry_text
from factory.domain.post_texts import done_entry_text
from factory.domain.sections import section_text, sections
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState

ROLE = "acceptance-reviewer"
ON = date(2026, 10, 12)
REASON = "Too wide. Cut the second story."
REFUSAL = f"Refused by the human on 2026-10-12: {REASON}"
BODY = (
    "# Acceptance of Todo service\n\n## Recommendation\n\nnot accepted\n\n"
    "## Proposed stories\n\n- one story\n\n## Journal\n\n1. factory: started.\n"
    "2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n"
    "4. 2026-10-12 human: Cut the second story.\n"
)
JOURNAL = [
    JournalRecord(number=1, speaker=FACTORY, kind="started"),
    JournalRecord(number=2, speaker=ROLE, kind="result"),
    JournalRecord(number=3, speaker=HUMAN, kind="comment"),
    JournalRecord(number=4, speaker=HUMAN, kind="comment"),
]
CLOSED_COST = "done (pull request closed by the human); cost: "


def _report(state: AcceptanceState | None = None, body: str = BODY) -> WorkItemDocument:
    if state is None:
        state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=JOURNAL)
    return WorkItemDocument(state=state, body=body)


def _busy_state() -> AcceptanceState:
    claim = Claim(
        instance="night",
        stage="approval",
        started_at=datetime(2026, 10, 12, 11, 0, tzinfo=UTC),
        lease_duration=60,
    )
    return AcceptanceState(
        stage="approval",
        blocked="question",
        round=2,
        attempts=1,
        crashes=1,
        pull_request=7,
        comments_read=[3, 5],
        handed_over="approval",
        claim=claim,
        journal=JOURNAL,
        stories=["F0002-S0001", "F0002-S0002"],
    )


def _state(document: WorkItemDocument) -> WorkItemState:
    assert document.state is not None
    return document.state


def _refuse(document: WorkItemDocument, records: Bill | None = None) -> WorkItemDocument:
    return book_refusal(document, role=ROLE, on=ON, bill=bill([]) if records is None else records)


def test_a_merge_books_the_acceptance_done_and_accepted_and_keeps_the_other_fields() -> None:
    state = _busy_state()

    booked = _state(book_merge(_report(state), bill([])))

    done = JournalRecord(number=5, speaker=FACTORY, kind="done")
    expected = state.model_copy(
        update={
            "stage": "done",
            "outcome": "accepted",
            "blocked": None,
            "claim": None,
            "journal": [*JOURNAL, done],
        }
    )
    assert booked == expected


def test_a_merge_appends_one_done_entry_of_the_factory_with_the_bill() -> None:
    records = bill(completed_records("F0002-A0001", 2))

    booked = book_merge(_report(), records)

    assert _state(booked).journal == [
        *JOURNAL,
        JournalRecord(number=5, speaker=FACTORY, kind="done"),
    ]
    assert entry_text(booked, 5) == done_entry_text(records)


def _merge(document: WorkItemDocument) -> WorkItemDocument:
    return book_merge(document, bill([]))


@pytest.mark.parametrize("booking", [_merge, _refuse], ids=["merge", "refusal"])
def test_booking_a_document_whose_state_is_not_an_acceptance_state_is_refused(
    booking: Callable[[WorkItemDocument], WorkItemDocument],
) -> None:
    plain = WorkItemState(stage="approval", journal=JOURNAL)

    with pytest.raises(ValueError):
        booking(WorkItemDocument(state=plain, body=BODY))


def test_the_refusal_reason_joins_the_human_comments_after_the_last_result_with_a_space() -> None:
    assert refusal_reason(_report(), ROLE) == REASON


def test_the_refusal_reason_ignores_earlier_comments_human_closes_and_factory_records() -> None:
    document = report_of(
        [
            (FACTORY, "started", "started."),
            (HUMAN, "comment", "Before the result."),
            (ROLE, "result", "not accepted"),
            (HUMAN, "comment", "Too wide."),
            (HUMAN, "close", "closed the pull request."),
            (FACTORY, "comment", "A note of the factory."),
            (FACTORY, "stall", "stalled."),
        ]
    )

    assert refusal_reason(document, ROLE) == "Too wide."


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        (
            [
                (HUMAN, "comment", "Before."),
                (ROLE, "result", "not accepted"),
                (FACTORY, "stall", "stalled."),
            ],
            "no reason given",
        ),
        (
            [
                (HUMAN, "comment", "Too wide."),
                (FACTORY, "started", "started."),
                (HUMAN, "comment", "Cut the second story."),
            ],
            REASON,
        ),
    ],
    ids=["no-comment-after-the-result", "no-result"],
)
def test_the_refusal_reason_without_a_later_comment_or_without_a_result(
    entries: list[tuple[str, JournalKind, str]], expected: str
) -> None:
    assert refusal_reason(report_of(entries), ROLE) == expected


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        (["   Too  wide.   ", "Cut it."], "Too  wide. Cut it."),
        (["Too wide.\n   Cut it.", "Really."], "Too wide.\nCut it. Really."),
        (["Too wide.", "   "], "Too wide."),
        (["   "], NO_REASON),
    ],
    ids=["stripped-ends", "lines-kept", "blank-skipped", "only-blank"],
)
def test_the_refusal_reason_strips_each_comment_and_skips_blank_ones(
    texts: list[str], expected: str
) -> None:
    entries: list[tuple[str, JournalKind, str]] = [(ROLE, "result", "not accepted")]
    entries += [(HUMAN, "comment", text) for text in texts]

    assert refusal_reason(report_of(entries), ROLE) == expected


def test_a_refusal_books_the_acceptance_done_and_refused_and_keeps_the_other_fields() -> None:
    state = _busy_state()

    booked = _state(_refuse(_report(state)))

    done = JournalRecord(number=5, speaker=FACTORY, kind="done")
    expected = state.model_copy(
        update={
            "stage": "done",
            "outcome": "refused",
            "blocked": None,
            "claim": None,
            "journal": [*JOURNAL, done],
        }
    )
    assert booked == expected


def test_a_refusal_puts_its_paragraph_first_under_the_recommendation_and_keeps_the_rest() -> None:
    refused = _refuse(_report())

    assert refused.body == (
        "# Acceptance of Todo service\n\n## Recommendation\n\n"
        f"{REFUSAL}\n\nnot accepted\n\n"
        "## Proposed stories\n\n- one story\n\n## Journal\n\n1. factory: started.\n"
        "2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n"
        "4. 2026-10-12 human: Cut the second story.\n"
        f"5. factory: {CLOSED_COST}{cost_line(bill([]))}\n"
    )


def test_a_refusal_adds_the_recommendation_section_just_before_the_journal() -> None:
    body = (
        "# Acceptance of Todo service\n\n## Findings in short\n\ntoo wide\n\n"
        "## Journal\n\n1. factory: started.\n"
    )
    state = AcceptanceState(
        stage="approval",
        stories=["F0002-S0001"],
        journal=[JournalRecord(number=1, speaker=FACTORY, kind="started")],
    )

    refused = _refuse(_report(state, body))

    headings = [found.heading for found in sections(refused.body)]
    assert headings == ["Findings in short", "Recommendation", "Journal"]
    assert section_text(refused.body, "Recommendation") == (
        "Refused by the human on 2026-10-12: no reason given"
    )
    assert section_text(refused.body, "Findings in short") == "too wide"


def test_a_refusal_adds_the_recommendation_section_at_the_end_of_a_body_without_a_journal() -> None:
    head = "# Acceptance of Todo service\n\nSome text.\n"
    state = AcceptanceState(stage="approval", stories=["F0002-S0001"])

    refused = _refuse(_report(state, head))

    before, heading, _ = refused.body.partition("## Recommendation\n")
    assert heading
    assert before.strip() == head.strip()
    assert sections(refused.body)[0].heading == "Recommendation"
    assert section_text(refused.body, "Recommendation") == (
        "Refused by the human on 2026-10-12: no reason given"
    )


def test_a_refusal_appends_one_done_entry_of_the_factory_with_the_bill() -> None:
    records = bill(completed_records("F0002-A0001", 2))

    refused = _refuse(_report(), records)

    assert _state(refused).journal == [
        *JOURNAL,
        JournalRecord(number=5, speaker=FACTORY, kind="done"),
    ]
    assert entry_text(refused, 5) == CLOSED_COST + cost_line(records)
