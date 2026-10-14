"""The question the factory posts when a stage reaches the crash cap."""

from factory.domain.post_texts import crash_cap_question


def test_the_crash_cap_question_names_the_stage_the_count_and_the_cap() -> None:
    text = crash_cap_question("tests", 2, 2)

    assert text == (
        "Stage tests crashed 2 times, which is the crash cap of 2. The factory has not rerun it."
        " Write a comment here and the stage reruns with the crash counter reset to 0"
        " (your comment is copied into the journal). Close the pull request to discard the"
        " story instead: it goes back to the backlog as you wrote it, and its branch and bill"
        " are deleted."
    )
    assert "Stage tests" in text
    assert "crashed 2 times" in text
    assert "crash cap of 2" in text
