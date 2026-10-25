"""The texts of a stall: its cause and the note posted on the pull request."""

import pytest

from factory.domain.decisions import StallReason
from factory.domain.post_texts import stall_cause, stall_note

CAP_REACHED = "The attempts cap is reached; the factory asks you next."
SENTENCES: list[tuple[StallReason, str]] = [
    ("died", "the agent run died without a result"),
    ("time_limit", "the agent run reached its time limit"),
    ("budget", "the agent run spent its budget, and the resume too"),
    ("no_result", "the agent gave no valid decision and entry"),
    ("decision_not_allowed", "the agent's decision is not an allowed one"),
    ("left_branch", "the agent left the work item's branch"),
    ("form_invalid", "the work item's form broke during the stage"),
    ("check_red", "a check is red after the stage"),
    ("merge_conflict", "merging the main branch conflicts and the merge was aborted"),
]


@pytest.mark.parametrize(("reason", "sentence"), SENTENCES)
def test_each_stall_cause_is_its_sentence_alone_or_with_the_detail(
    reason: StallReason, sentence: str
) -> None:
    assert stall_cause(reason) == sentence
    assert stall_cause(reason, "make check: 3 failed") == f"{sentence}: make check: 3 failed"
    assert "retry" not in sentence.lower()


def test_the_first_note_of_two_attempts_says_it_retries() -> None:
    assert stall_note("died", 1, 2) == (
        "Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick."
    )


@pytest.mark.parametrize(("attempts", "retrying"), [(1, True), (2, False), (3, False)])
def test_the_note_says_retrying_only_below_the_attempts_cap(attempts: int, retrying: bool) -> None:
    note = stall_note("check_red", attempts, 2, detail="make check: 3 failed")

    if retrying:
        assert "retrying" in note.lower()
    else:
        assert "retry" not in note.lower()
        assert note.endswith(CAP_REACHED)
