"""An answer at the round cap starts the count of rounds over; other waits keep it."""

import pytest

from factory.domain.answers import unblock
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.work_item import Blocked, WorkItemState

CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")


@pytest.mark.parametrize(
    ("blocked", "round_after"),
    [
        pytest.param("round_cap", 0, id="round_cap"),
        pytest.param("question", 4, id="question"),
        pytest.param("send_back", 4, id="send_back"),
    ],
)
def test_unblock_resets_the_round_only_at_the_round_cap(blocked: Blocked, round_after: int) -> None:
    state = WorkItemState(
        stage="review",
        blocked=blocked,
        round=4,
        attempts=2,
        crashes=2,
        journal=[CREATED],
    )

    after = unblock(state)

    assert after == state.model_copy(update={"blocked": None, "round": round_after})
    assert after.attempts == 2
    assert after.crashes == 2
