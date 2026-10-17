"""The decision rules: what an agent's decision does to the stage, `blocked` and `round`."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.decisions import StageMove, decide
from factory.domain.pipeline_definition import (
    PipelineDefinition,
    RoleDefinition,
    StageDefinition,
)
from factory.domain.post_texts import findings_question, round_cap_question
from factory.domain.story_form import FormFinding
from factory.domain.work_item import WorkItemState

FINDINGS = (FormFinding(line=3, message="The story has no Interface section."),)


@pytest.fixture
def definition() -> PipelineDefinition:
    """Return a pipeline whose `review` has a round cap of 3 and whose `doing` has none."""
    return PipelineDefinition(
        contract="1.0",
        roles={
            "coder": RoleDefinition(write_paths=["src/*"]),
            "tester": RoleDefinition(write_paths=["tests/*"]),
            "reviewer": RoleDefinition(write_paths=["{work_item}"]),
        },
        stages={
            "doing": StageDefinition(role="coder", next=["review", "tests"]),
            "tests": StageDefinition(role="tester", next=["doing"]),
            "review": StageDefinition(role="reviewer", next=["docs", "doing"], round_cap=3),
            "docs": StageDefinition(role="reviewer", next=["done"]),
            "done": StageDefinition(),
        },
    )


def test_a_forward_decision_without_findings_moves_to_the_first_next_stage(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="review", round=2), "docs")

    assert move == StageMove(rule=6, stage="docs", blocked=None, round=2, question=None)


def test_a_forward_decision_with_findings_becomes_a_question(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="doing", round=1), "review", FINDINGS)

    assert move == StageMove(
        rule=1,
        stage="doing",
        blocked="question",
        round=1,
        question=findings_question(FINDINGS),
    )


def test_the_decision_question_blocks_the_work_item_at_its_stage(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="review", round=1), "question")

    assert move == StageMove(rule=2, stage="review", blocked="question", round=1, question=None)


def test_findings_do_not_add_a_question_to_the_decision_question(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="doing", round=1), "question", FINDINGS)

    assert move == StageMove(rule=2, stage="doing", blocked="question", round=1, question=None)


def test_a_rework_within_the_round_cap_moves_and_counts_a_round(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="review", round=0), "doing")

    assert move == StageMove(rule=3, stage="doing", blocked=None, round=1, question=None)


@pytest.mark.parametrize(
    ("rounds", "rule"),
    [(0, 3), (1, 3), (2, 3), (3, 4)],
)
def test_a_rework_past_the_round_cap_asks_the_human(
    definition: PipelineDefinition, rounds: int, rule: int
) -> None:
    move = decide(definition, WorkItemState(stage="review", round=rounds), "doing")

    assert move.rule == rule
    assert move.round == rounds + 1


def test_a_rework_past_the_round_cap_stays_blocked_with_the_round_cap_question(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="review", round=3), "doing")

    assert move == StageMove(
        rule=4,
        stage="review",
        blocked="round_cap",
        round=4,
        question=round_cap_question(4, 3),
    )


def test_a_rework_at_a_stage_without_round_cap_moves_without_counting(
    definition: PipelineDefinition,
) -> None:
    move = decide(definition, WorkItemState(stage="doing", round=2), "tests")

    assert move == StageMove(rule=7, stage="tests", blocked=None, round=2, question=None)


def test_findings_do_not_change_a_rework(definition: PipelineDefinition) -> None:
    move = decide(definition, WorkItemState(stage="review", round=0), "doing", FINDINGS)

    assert move == StageMove(rule=3, stage="doing", blocked=None, round=1, question=None)


@pytest.mark.parametrize(
    ("stage", "decision", "rule"),
    [("review", "doing", 3), ("review", "docs", 6), ("doing", "tests", 7)],
)
def test_a_move_clears_a_blocked_question(
    definition: PipelineDefinition, stage: str, decision: str, rule: int
) -> None:
    state = WorkItemState(stage=stage, blocked="question")

    move = decide(definition, state, decision)

    assert move.rule == rule
    assert move.blocked is None


def test_a_decision_outside_next_is_refused_by_name(definition: PipelineDefinition) -> None:
    with pytest.raises(ValueError, match="done"):
        decide(definition, WorkItemState(stage="review"), "done")


def test_a_stage_outside_the_pipeline_definition_is_refused_by_name(
    definition: PipelineDefinition,
) -> None:
    with pytest.raises(ValueError, match="nowhere"):
        decide(definition, WorkItemState(stage="nowhere"), "docs")


def test_a_stage_move_has_no_attempts_or_crashes() -> None:
    assert set(StageMove.model_fields) == {"rule", "stage", "blocked", "round", "question"}


@pytest.mark.parametrize("rule", [1, 2, 3, 4, 6, 7])
def test_a_stage_move_accepts_each_rule(rule: int) -> None:
    model: type[BaseModel] = StageMove

    move = model(rule=rule, stage="doing", blocked=None, round=0, question=None)

    assert move.model_dump()["rule"] == rule


@pytest.mark.parametrize(
    ("field", "value"),
    [("rule", 5), ("round", -1), ("unknown", "x")],
)
def test_a_stage_move_refuses_what_its_types_refuse(field: str, value: object) -> None:
    model: type[BaseModel] = StageMove
    values: dict[str, object] = {
        "rule": 6,
        "stage": "doing",
        "blocked": None,
        "round": 0,
        "question": None,
    }
    values[field] = value

    with pytest.raises(ValidationError):
        model(**values)
