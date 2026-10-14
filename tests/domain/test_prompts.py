"""The allowed decisions and the prompt composed from a stage's facts."""

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.prompts import END_LINE, PromptFacts, allowed_decisions, compose_prompt
from factory.domain.story_form import FormFinding

PATH = "factory/features/F0001-demo/in-progress/F0001-S0003-demo.md"
MODE_LINE = "Mode: a test change the human approved; the coder's journal entry 4 names it."
VALID: dict[str, Any] = {
    "work_item": "F0001-S0003",
    "path": PATH,
    "stage": "doing",
    "allowed_decisions": ["review", "tests", "question"],
    "branch": "work-item/F0001-S0003",
    "pull_request": 7,
    "round": 1,
}


def _facts(**changes: Any) -> PromptFacts:
    return PromptFacts.model_validate({**VALID, **changes})


def _lines(**changes: Any) -> list[str]:
    return compose_prompt(_facts(**changes)).split("\n")


def test_allowed_decisions_are_the_next_stages_in_order_then_question() -> None:
    assert allowed_decisions(["review", "doing"]) == ["review", "doing", "question"]


def test_question_is_allowed_at_a_stage_without_next() -> None:
    assert allowed_decisions([]) == ["question"]


def test_the_prompt_holds_the_facts_line_by_line_and_ends_with_the_end_line() -> None:
    prompt = compose_prompt(_facts())

    assert prompt.split("\n") == [
        f"Work item: {PATH}",
        "Id: F0001-S0003",
        "Stage: doing",
        "Allowed decisions: review, tests, question",
        "Branch: work-item/F0001-S0003",
        "Pull request: 7",
        "Round: 1",
        END_LINE,
    ]
    assert not prompt.endswith("\n")


def test_the_end_line_says_what_the_factory_does_after_the_agent() -> None:
    assert END_LINE == (
        "End with your decision and your journal entry; "
        "the factory commits, pushes and moves the work item."
    )


def test_no_findings_give_a_passed_format_check_after_the_round() -> None:
    lines = _lines(findings=[])

    assert lines[6:] == ["Round: 1", "Format check: passed", END_LINE]


def test_findings_are_numbered_on_one_format_check_line() -> None:
    findings = [FormFinding(line=None, message="a"), FormFinding(line=3, message="b")]

    lines = _lines(findings=findings)

    assert lines[6:] == ["Round: 1", "Format check found: 1. a 2. b", END_LINE]


def test_without_findings_the_prompt_has_no_format_check_line() -> None:
    lines = _lines(findings=None)

    assert not [line for line in lines if line.startswith("Format check")]


def test_a_test_change_adds_the_mode_line_between_round_and_format_check() -> None:
    lines = _lines(test_change_entry=4, findings=[])

    assert lines[6:] == ["Round: 1", MODE_LINE, "Format check: passed", END_LINE]


def test_without_a_test_change_the_prompt_has_no_mode_line() -> None:
    lines = _lines(test_change_entry=None, findings=[])

    assert not [line for line in lines if line.startswith("Mode:")]


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        ("round", 0, True),
        ("round", -1, False),
        ("pull_request", 1, True),
        ("pull_request", 0, False),
        ("test_change_entry", 1, True),
        ("test_change_entry", 0, False),
    ],
)
def test_prompt_facts_hold_their_limits_on_both_sides(
    field: str, value: int, accepted: bool
) -> None:
    if accepted:
        assert getattr(_facts(**{field: value}), field) == value
    else:
        with pytest.raises(ValidationError):
            _facts(**{field: value})


def test_prompt_facts_are_frozen() -> None:
    facts = _facts()
    field = "round"

    with pytest.raises(ValidationError):
        setattr(facts, field, 2)


def test_prompt_facts_refuse_an_unknown_key() -> None:
    model: type[BaseModel] = PromptFacts

    with pytest.raises(ValidationError):
        model(**VALID, colour="red")
