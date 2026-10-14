"""The expiry note and the stall note say "retrying" only where the factory reruns the stage."""

from typing import get_args

import pytest

from factory.domain.decisions import StallReason
from factory.domain.post_texts import expiry_note, stall_note

LEAD = "The run that held this stage ended without finishing: its lease expired"


def test_the_expiry_note_below_the_crash_cap_says_retrying() -> None:
    note = expiry_note(1, 2)

    assert note == f"{LEAD} (crash 1 of 2). Retrying."
    assert note.endswith("Retrying.")


@pytest.mark.parametrize("crashes", [2, 3])
def test_the_expiry_note_at_or_past_the_crash_cap_asks_and_does_not_say_retrying(
    crashes: int,
) -> None:
    note = expiry_note(crashes, 2)

    assert note == (
        f"{LEAD} (crash {crashes} of 2). The factory does not rerun it and asks you instead."
    )
    assert "retrying" not in note.lower()


@pytest.mark.parametrize("reason", get_args(StallReason))
@pytest.mark.parametrize(("attempts", "retrying"), [(1, True), (2, False), (3, False)])
def test_the_stall_note_says_retrying_only_below_the_attempts_cap(
    reason: StallReason, attempts: int, retrying: bool
) -> None:
    note = stall_note(reason, attempts, 2)

    assert ("retrying" in note.lower()) is retrying
