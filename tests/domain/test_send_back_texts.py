"""The texts of a send-back: the close entry, the send-back entry and the send-back question."""

import pytest

from factory.domain.post_texts import (
    CLOSE_ENTRY_TEXT,
    SEND_BACK_QUESTION,
    send_back_entry_text,
    send_back_question,
)

NO_COMMENT = "The pull request was closed without a comment. "


def test_the_close_entry_text_says_the_pull_request_was_closed() -> None:
    assert CLOSE_ENTRY_TEXT == "closed the pull request."


def test_the_send_back_question_offers_comment_close_again_and_merge() -> None:
    assert SEND_BACK_QUESTION == (
        "What should happen? 1. Comment what should change; the story is reworked with exactly "
        "that. 2. Close the pull request again to discard the story: it goes back to the backlog "
        "as you wrote it, and its branch is deleted. 3. If closing was a mistake: mark the pull "
        "request ready for review and merge it, which accepts the story as it is."
    )
    assert "1. Comment" in SEND_BACK_QUESTION
    assert "2. Close the pull request again to discard" in SEND_BACK_QUESTION
    assert "3. If closing was a mistake: mark the pull request ready" in SEND_BACK_QUESTION
    assert "merge it" in SEND_BACK_QUESTION


def test_the_send_back_entry_names_the_target_and_the_round() -> None:
    assert send_back_entry_text("doing", 3) == "sent back to doing, round 3."


@pytest.mark.parametrize(
    ("round_number", "cap", "has_reason", "expected"),
    [
        (3, 3, True, None),
        (9, None, True, None),
        (2, 3, False, NO_COMMENT + SEND_BACK_QUESTION),
    ],
    ids=["round-equals-cap", "no-cap", "no-reason"],
)
def test_within_the_cap_only_a_missing_reason_asks(
    round_number: int, cap: int | None, *, has_reason: bool, expected: str | None
) -> None:
    assert send_back_question(round_number, cap, has_reason) == expected


@pytest.mark.parametrize("has_reason", [True, False])
def test_past_the_cap_the_cap_question_wins_with_or_without_a_reason(*, has_reason: bool) -> None:
    expected = "This story has now been sent back 4 times, more than 3. " + SEND_BACK_QUESTION

    assert send_back_question(4, 3, has_reason) == expected
