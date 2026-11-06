"""An acceptance merged before its approval: the stages before it and the entry that says so."""

import pytest

from factory.watching.domain.bills import bill, cost_line
from factory.work.domain.acceptance import AcceptanceState, book_merge, is_before_approval
from factory.work.domain.journal import FACTORY, JournalRecord, entry_text
from factory.work.domain.work_item import WorkItemDocument
from support.before_approval_support import FIXTURE
from support.before_approval_support import without_approval as definition_without_approval
from support.bill_support import completed_records

BEFORE_APPROVAL = "done (pull request merged before approval); cost: "
JOURNAL = [JournalRecord(number=1, speaker=FACTORY, kind="started")]
BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: started.\n"


@pytest.mark.parametrize(
    ("stage", "expected"),
    [("acceptance", True), ("approval", False), ("done", False)],
)
def test_only_a_stage_before_the_first_approval_is_before_approval(
    stage: str, *, expected: bool
) -> None:
    assert is_before_approval(FIXTURE, stage) is expected


@pytest.mark.parametrize(
    ("without_approval", "stage", "error"),
    [(False, "nowhere", KeyError), (True, "acceptance", ValueError)],
    ids=["unknown-stage", "no-approval-stage"],
)
def test_an_unknown_stage_or_a_definition_without_approval_is_refused(
    stage: str, error: type[Exception], *, without_approval: bool
) -> None:
    used = definition_without_approval() if without_approval else FIXTURE

    with pytest.raises(error):
        is_before_approval(used, stage)


def test_a_merge_before_approval_books_like_a_merge_with_an_entry_that_says_so() -> None:
    state = AcceptanceState(
        stage="acceptance", stories=["F0002-S0001"], blocked="question", journal=JOURNAL
    )
    document = WorkItemDocument(state=state, body=BODY)
    records = bill(completed_records("F0002-A0001", 2))

    booked = book_merge(document, records, before_approval=True)

    plain = book_merge(document, records)
    assert booked.state == plain.state
    assert booked.state is not None
    assert booked.state.journal == [
        *JOURNAL,
        JournalRecord(number=2, speaker=FACTORY, kind="done"),
    ]
    assert entry_text(booked, 2) == BEFORE_APPROVAL + cost_line(records)
