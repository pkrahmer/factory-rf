"""The send-back reads no records without a state and counts every record before a result."""

import pytest

from factory.domain.journal import JournalRecord
from factory.domain.send_back import reason_given, recorded_since_latest_result
from factory.domain.work_item import WorkItemDocument, WorkItemState

COMMENT = JournalRecord(number=1, speaker="human", kind="comment")
RESULT = JournalRecord(number=2, speaker="coder", kind="result")


def _approval(*journal: JournalRecord) -> WorkItemState:
    return WorkItemState(stage="approval", journal=list(journal))


@pytest.mark.parametrize(
    ("state", "given", "closed"),
    [
        pytest.param(None, False, None, id="no-state"),
        pytest.param(_approval(COMMENT), True, False, id="comment-numbered-1"),
        pytest.param(_approval(COMMENT, RESULT), False, None, id="result-after-comment"),
    ],
)
def test_the_send_back_reads_records_only_from_a_state_and_since_the_latest_result(
    state: WorkItemState | None, given: bool, closed: bool | None
) -> None:
    document = WorkItemDocument(state=state, body="# T\n")

    assert reason_given(document) is given
    if closed is not None:
        assert recorded_since_latest_result(document, "close") is closed
