"""The text a died run leaves: its error reply, else its standard error, else its exit status."""

import pytest

from factory.adapters.agent_launch import died_text


@pytest.mark.parametrize(
    ("error_text", "stderr", "exit_status", "expected"),
    [
        pytest.param("boom", "", 1, "boom", id="reply"),
        pytest.param("boom", "first\nsecond\n", 1, "boom", id="reply-wins-over-stderr"),
        pytest.param("", "first\n", 1, "first", id="empty-reply-falls-to-stderr"),
        pytest.param(" \n\t\n", "first\n", 1, "first", id="blank-reply-falls-to-stderr"),
        pytest.param(None, "one\ntwo\nthree\n", 1, "one / two / three", id="three-stderr-lines"),
        pytest.param(None, "one\ntwo\nthree\nfour\n", 1, "two / three / four", id="last-three"),
        pytest.param(None, "one\n\n  two \n\n\nthree\n", 1, "one / two / three", id="blanks"),
        pytest.param(None, "", 1, "exit 1", id="empty-stderr"),
        pytest.param(None, " \n\n", 2, "exit 2", id="blank-stderr"),
        pytest.param("", "", 3, "exit 3", id="empty-reply-and-stderr"),
        pytest.param("  first \n\n second  \n", "", 1, "first / second", id="reply-lines"),
    ],
)
def test_the_died_text_prefers_the_reply_then_standard_error_then_the_exit_status(
    error_text: str | None, stderr: str, exit_status: int, expected: str
) -> None:
    assert died_text(error_text, stderr, exit_status) == expected


@pytest.mark.parametrize(
    ("length", "expected"),
    [
        pytest.param(300, "a" * 300, id="300-whole"),
        pytest.param(301, "a" * 300 + "…", id="301-cut"),
    ],
)
def test_a_died_text_past_300_characters_is_cut_with_an_ellipsis(
    length: int, expected: str
) -> None:
    assert died_text("a" * length, "", 1) == expected
