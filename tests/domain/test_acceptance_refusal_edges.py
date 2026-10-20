"""The refusal reason starts after the role's own last result, and the refused body is whole."""

from datetime import date

import pytest

from acceptance_support import report_of
from factory.domain.acceptance import AcceptanceState, book_refusal, refusal_reason
from factory.domain.bills import bill
from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.work_item import WorkItemDocument

ROLE = "acceptance-reviewer"
ON = date(2026, 10, 12)
COST = "0 runs, 0.0 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.00"
OTHER_ROLE_RESULT: list[tuple[str, JournalKind, str]] = [
    ("factory", "started", "started."),
    (ROLE, "result", "not accepted"),
    ("human", "comment", "Too wide."),
    ("tester", "result", "red"),
    ("human", "comment", "Cut the second story."),
]


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        pytest.param(OTHER_ROLE_RESULT, "Too wide. Cut the second story.", id="other-role-result"),
        pytest.param(
            [
                ("factory", "started", "started."),
                (ROLE, "result", "not accepted"),
                ("human", "comment", "Too wide."),
                (ROLE, "question", "Which story?"),
                ("human", "comment", "Cut the second story."),
            ],
            "Too wide. Cut the second story.",
            id="role-question",
        ),
        pytest.param(
            [
                ("factory", "started", "started."),
                (ROLE, "result", "not accepted"),
                ("human", "comment", "Too wide."),
                (ROLE, "result", "still not accepted"),
                ("human", "comment", "Cut the second story."),
            ],
            "Cut the second story.",
            id="role-result",
        ),
    ],
)
def test_the_refusal_reason_starts_after_the_roles_own_last_result(
    entries: list[tuple[str, JournalKind, str]], expected: str
) -> None:
    assert refusal_reason(report_of(entries), ROLE) == expected


def test_a_refusal_books_the_reason_after_the_roles_own_last_result() -> None:
    booked = book_refusal(report_of(OTHER_ROLE_RESULT), role=ROLE, on=ON, bill=bill([]))
    assert booked.body == (
        "# Acceptance of Todo service\n\n## Recommendation\n\n"
        "Refused by the human on 2026-10-12: Too wide. Cut the second story.\n\n"
        "## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n"
        "3. 2026-10-12 human: Too wide.\n4. tester: red\n"
        "5. 2026-10-12 human: Cut the second story.\n"
        f"6. factory: done (pull request closed by the human); cost: {COST}\n"
    )


def test_a_refusal_writes_the_whole_body_with_the_recommendation_before_the_journal() -> None:
    state = AcceptanceState(
        stage="approval",
        stories=["F0002-S0001"],
        journal=[JournalRecord(number=1, speaker="factory", kind="started")],
    )
    body = (
        "# Acceptance of Todo service\n\n## Findings in short\n\ntoo wide\n\n"
        "## Journal\n\n1. factory: started.\n"
    )
    document = WorkItemDocument(state=state, body=body)
    booked = book_refusal(document, role=ROLE, on=ON, bill=bill([]))
    assert booked.body == (
        "# Acceptance of Todo service\n\n## Findings in short\n\ntoo wide\n\n"
        "## Recommendation\n\nRefused by the human on 2026-10-12: no reason given\n\n"
        "## Journal\n\n1. factory: started.\n"
        f"2. factory: done (pull request closed by the human); cost: {COST}\n"
    )
