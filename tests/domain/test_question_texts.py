"""The questions the factory asks the human by itself."""

from factory.domain.post_texts import findings_question, round_cap_question
from factory.domain.story_form import FormFinding


def test_the_round_cap_question_names_the_rounds_and_the_cap() -> None:
    assert round_cap_question(4, 3) == (
        "This work item has now been sent back 4 times, more than 3."
        " What should happen? Answer with a comment, which starts the count of rounds over;"
        " close the pull request to discard the work item."
    )


def test_the_findings_question_numbers_the_findings_messages() -> None:
    findings = [FormFinding(line=None, message="a"), FormFinding(line=2, message="b")]

    assert findings_question(findings) == (
        "The work item's form has findings, so the stage cannot move forward: 1. a 2. b."
        " What should happen? Answer with a comment; the stage then runs again."
        " Close the pull request to discard the work item."
    )
