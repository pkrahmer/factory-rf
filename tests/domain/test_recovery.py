"""A crash raises the crash count and nothing else, and its journal entry names the discard."""

from datetime import UTC, datetime

import pytest

from factory.domain.journal import JournalRecord
from factory.domain.recovery import crash_entry_text, crashed
from factory.domain.work_item import Claim, WorkItemState

CLAIM = Claim(
    instance="factory-1",
    stage="doing",
    started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    lease_duration=60,
)
CLAIMED = WorkItemState(
    stage="doing",
    round=1,
    attempts=1,
    crashes=0,
    pull_request=7,
    comments_read=[3],
    claim=CLAIM,
    journal=[
        JournalRecord(number=1, speaker="human", kind="created"),
        JournalRecord(number=2, speaker="factory", kind="started"),
    ],
)
UNCLAIMED = WorkItemState(stage="review", blocked="question", crashes=5, handed_over="factory-2")


@pytest.mark.parametrize("state", [CLAIMED, UNCLAIMED], ids=["crashes-0-claimed", "crashes-5"])
def test_crashed_raises_the_crash_count_and_keeps_every_other_field(state: WorkItemState) -> None:
    before = state.model_dump()

    after = crashed(state)

    assert after.crashes == state.crashes + 1
    assert after.model_dump(exclude={"crashes"}) == state.model_dump(exclude={"crashes"})
    assert after.claim == state.claim
    assert state.model_dump() == before


def test_the_crash_entry_text_names_the_stage_the_count_and_the_commit() -> None:
    expected = (
        "crash 1: the run of stage doing ended without a result. "
        "Its work is discarded back to commit " + "a" * 40 + "."
    )

    assert crash_entry_text("doing", 1, "a" * 40) == expected
