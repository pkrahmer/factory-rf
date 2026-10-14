"""The crash cap: a work item at it is not rerun but blocked on a question to the human."""

from datetime import UTC, datetime

import pytest

from factory.domain.journal import JournalRecord
from factory.domain.recovery import asking_crash_cap, at_crash_cap
from factory.domain.work_item import Claim, WorkItemState

STATE = WorkItemState(
    stage="doing",
    round=1,
    attempts=1,
    crashes=2,
    pull_request=7,
    comments_read=[3],
    claim=Claim(
        instance="factory-1",
        stage="doing",
        started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
        lease_duration=60,
    ),
    journal=[
        JournalRecord(number=1, speaker="human", kind="created"),
        JournalRecord(number=2, speaker="factory", kind="crash"),
    ],
)


@pytest.mark.parametrize(
    ("crashes", "crash_cap", "expected"),
    [(1, 2, False), (2, 2, True), (3, 2, True), (0, 1, False), (1, 1, True)],
)
def test_the_crash_cap_is_reached_when_the_crashes_reach_it(
    crashes: int, crash_cap: int, expected: bool
) -> None:
    state = STATE.model_copy(update={"crashes": crashes})

    assert at_crash_cap(state, crash_cap) is expected


def test_asking_at_the_crash_cap_blocks_on_it_and_changes_nothing_else() -> None:
    before = STATE.model_copy(deep=True)

    asking = asking_crash_cap(STATE)

    assert asking.blocked == "crash_cap"
    assert asking.model_copy(update={"blocked": None}) == STATE
    assert before == STATE
