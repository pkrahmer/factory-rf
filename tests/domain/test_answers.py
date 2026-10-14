"""An answer ends the wait: what `unblock` clears and what it resets."""

import pytest

from factory.domain.answers import unblock
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.work_item import Blocked, WorkItemState

CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")


def _state(blocked: Blocked | None) -> WorkItemState:
    return WorkItemState(
        stage="doing",
        blocked=blocked,
        round=2,
        attempts=2,
        crashes=2,
        pull_request=7,
        comments_read=[3, 5],
        handed_over="coder",
        journal=[CREATED],
    )


@pytest.mark.parametrize("blocked", ["question", "round_cap", "send_back"])
def test_unblock_clears_the_wait_and_changes_nothing_else(blocked: Blocked) -> None:
    state = _state(blocked)

    after = unblock(state)

    assert after == state.model_copy(update={"blocked": None})
    assert after.round == 2


def test_unblock_at_the_attempts_cap_resets_the_attempts_only() -> None:
    state = _state("attempts_cap")

    after = unblock(state)

    assert after == state.model_copy(update={"blocked": None, "attempts": 0})
    assert after.round == 2
    assert after.crashes == 2


def test_unblock_at_the_crash_cap_resets_the_crashes_only() -> None:
    state = _state("crash_cap")

    after = unblock(state)

    assert after == state.model_copy(update={"blocked": None, "crashes": 0})
    assert after.round == 2
    assert after.attempts == 2


def test_unblock_of_a_state_that_waits_for_nothing_returns_an_equal_state() -> None:
    state = _state(None)

    assert unblock(state) == state
