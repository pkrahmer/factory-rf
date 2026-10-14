"""The stall note of a multi-line detail: its first line in the sentence, the rest fenced."""

import pytest

from factory.domain.post_texts import stall_note

RED = "Stalled (attempt 1 of 2): a check is red after the stage"
ONE_LINE_NOTE = f"{RED}: 3 failed. Retrying on the next tick."
TRACEBACK_LINE = '  File "x.py", line 1, in <module>'
MAKE_ERROR = "make: *** [Makefile:6: check] Error 1"


def test_a_multi_line_detail_puts_its_rest_in_a_fenced_block() -> None:
    note = stall_note("check_red", 1, 2, detail="`check`\nline a\nline b")

    assert note == "\n".join(
        [
            f"{RED}: `check`. Retrying on the next tick.",
            "",
            "```text",
            "line a",
            "line b",
            "```",
        ]
    )


def test_at_the_cap_the_first_line_says_the_factory_asks_you_next() -> None:
    note = stall_note("check_red", 2, 2, detail="`check`\nline a")

    lines = note.split("\n")
    assert lines[0] == (
        "Stalled (attempt 2 of 2): a check is red after the stage: `check`. "
        "The attempts cap is reached; the factory asks you next."
    )
    assert lines[-1] == "```"
    assert "retry" not in note.lower()


def test_a_one_line_or_empty_detail_gives_the_note_as_before() -> None:
    assert stall_note("check_red", 1, 2, detail="3 failed") == ONE_LINE_NOTE
    assert stall_note("died", 1, 2) == (
        "Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick."
    )


def test_trailing_line_breaks_neither_make_a_block_nor_reach_one() -> None:
    assert stall_note("check_red", 1, 2, detail="3 failed\n\n") == ONE_LINE_NOTE

    trailing = stall_note("check_red", 1, 2, detail="`check`\nline a\n\n")

    assert trailing == stall_note("check_red", 1, 2, detail="`check`\nline a")
    assert trailing.split("\n")[-2:] == ["line a", "```"]


def test_the_remaining_lines_are_kept_unchanged_in_the_block() -> None:
    note = stall_note("check_red", 1, 2, detail=f"`check`\n{TRACEBACK_LINE}\n{MAKE_ERROR}")

    assert note.split("\n")[3:5] == [TRACEBACK_LINE, MAKE_ERROR]


@pytest.mark.parametrize(
    ("line", "fence"),
    [
        ("``x``", "```"),
        ("```", "````"),
        ("`````", "``````"),
    ],
    ids=["run-of-two", "run-of-three", "run-of-five"],
)
def test_the_fence_is_longer_than_any_run_of_three_or_more_backticks(line: str, fence: str) -> None:
    note = stall_note("check_red", 1, 2, detail=f"`check`\n{line}")

    assert note.split("\n")[1:] == ["", f"{fence}text", line, fence]
