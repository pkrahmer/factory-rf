"""The question the factory asks when a work item has used all its attempts."""

from factory.domain.post_texts import attempts_cap_question


def test_the_attempts_cap_question_names_the_stage_the_stalls_and_the_answers() -> None:
    assert attempts_cap_question("doing", 2, "the agent gave no result") == (
        "Stage doing stalled 2 times. The last time: the agent gave no result\n"
        "\n"
        "Comment anything to retry: the attempts go back to 0 and the stage runs again."
        " Close the pull request to discard the story instead: it goes back to the backlog"
        " as you wrote it, and its branch and bill are deleted."
    )
