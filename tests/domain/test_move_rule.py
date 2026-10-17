"""The move rule: the stage changes the pipeline definition allows, and the factory's moves."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.move_rule import (
    FactoryMove,
    IllegalChange,
    StageChange,
    factory_moves,
    is_legal_change,
)
from factory.domain.pipeline_definition import (
    PipelineDefinition,
    ProjectCommandDefinition,
    RoleDefinition,
    StageDefinition,
)

# The pipeline definition of the test remote (`PIPELINE_YAML`), built without the YAML reader.
FIXTURE = PipelineDefinition(
    contract="1.0",
    attempts_cap=2,
    crash_cap=2,
    acceptance_stage="acceptance",
    project_commands={
        "check": ProjectCommandDefinition(time_limit=10),
        "lint": ProjectCommandDefinition(time_limit=5),
        "test": ProjectCommandDefinition(time_limit=10),
    },
    roles={
        "intake": RoleDefinition(write_paths=["{work_item}"]),
        "tester": RoleDefinition(write_paths=["tests/*"]),
        "coder": RoleDefinition(write_paths=["src/*"]),
        "reviewer": RoleDefinition(write_paths=["{work_item}"]),
        "documenter": RoleDefinition(write_paths=["README.md", "docs/*"]),
        "smoke-tester": RoleDefinition(write_paths=["{work_item}"]),
        "acceptance-reviewer": RoleDefinition(write_paths=["{work_item}", "{feature}/backlog/*"]),
    },
    stages={
        "intake": StageDefinition(role="intake", next=["tests"]),
        "tests": StageDefinition(role="tester", next=["doing"], checks=["lint"], reports=["test"]),
        "doing": StageDefinition(role="coder", next=["review", "tests"], checks=["check"]),
        "review": StageDefinition(role="reviewer", next=["docs", "doing"], round_cap=3),
        "docs": StageDefinition(
            role="documenter", next=["smoke-test", "doing"], checks=["check"], round_cap=3
        ),
        "smoke-test": StageDefinition(role="smoke-tester", next=["approval", "doing"], round_cap=3),
        "acceptance": StageDefinition(role="acceptance-reviewer", next=["approval"]),
        "approval": StageDefinition(approval=True, next=["done", "doing"]),
        "done": StageDefinition(),
    },
)

# An approval stage whose `next` does not list done: only the human's merge archives from it.
APPROVAL_WITHOUT_DONE = PipelineDefinition(
    contract="1.0",
    stages={
        "work": StageDefinition(role="worker", next=["approval"]),
        "approval": StageDefinition(approval=True, next=["work"]),
        "done": StageDefinition(),
    },
    roles={"worker": RoleDefinition(write_paths=["{work_item}"])},
)

# An approval stage that lists only doing in `next`.
APPROVAL_ONLY_DOING = PipelineDefinition(
    contract="1.0",
    stages={
        "doing": StageDefinition(role="coder", next=["approval"]),
        "approval": StageDefinition(approval=True, next=["doing"]),
        "done": StageDefinition(),
    },
    roles={"coder": RoleDefinition(write_paths=["src/*"])},
)

FIXTURE_NEXT_PAIRS = [
    (stage, name) for stage, definition in FIXTURE.stages.items() for name in definition.next
]


def _legal(definition: PipelineDefinition, from_stage: str, to_stage: str) -> bool:
    return is_legal_change(definition, StageChange(from_stage=from_stage, to_stage=to_stage))


@pytest.mark.parametrize(("from_stage", "to_stage"), FIXTURE_NEXT_PAIRS)
def test_every_move_a_next_list_names_is_legal(from_stage: str, to_stage: str) -> None:
    assert _legal(FIXTURE, from_stage, to_stage)


@pytest.mark.parametrize(
    ("from_stage", "to_stage", "legal"),
    [("tests", "review", False), ("review", "smoke-test", False), ("tests", "tests", True)],
    ids=["tests-skips-doing", "review-skips-docs", "same-stage"],
)
def test_a_skipped_stage_is_illegal_and_the_same_stage_is_legal(
    from_stage: str, to_stage: str, legal: bool
) -> None:
    assert _legal(FIXTURE, from_stage, to_stage) is legal


@pytest.mark.parametrize(
    ("from_stage", "to_stage"),
    [("nowhere", "tests"), ("intake", "nowhere"), ("nowhere", "elsewhere")],
    ids=["unknown-from", "unknown-to", "both-unknown"],
)
def test_a_stage_the_definition_lacks_is_illegal(from_stage: str, to_stage: str) -> None:
    assert not _legal(FIXTURE, from_stage, to_stage)


@pytest.mark.parametrize(
    ("definition", "from_stage", "legal"),
    [(APPROVAL_WITHOUT_DONE, "approval", True), (FIXTURE, "review", False)],
    ids=["approval-without-done-in-next", "review-without-done-in-next"],
)
def test_done_is_legal_from_an_approval_stage_even_unlisted_and_from_no_other(
    definition: PipelineDefinition, from_stage: str, legal: bool
) -> None:
    assert _legal(definition, from_stage, "done") is legal


@pytest.mark.parametrize(
    ("from_stage", "to_stage"), [("tests", "review"), ("intake", "approval"), ("nowhere", "doing")]
)
def test_a_correction_is_legal_whatever_it_jumps(from_stage: str, to_stage: str) -> None:
    change = StageChange(from_stage=from_stage, to_stage=to_stage, correction=True)

    assert is_legal_change(FIXTURE, change)


def test_a_stage_change_is_no_correction_by_default() -> None:
    assert StageChange(from_stage="tests", to_stage="doing").correction is False


def test_factory_moves_list_every_next_in_order_and_approval_to_done_once() -> None:
    moves = [(move.from_stage, move.to_stage) for move in factory_moves(FIXTURE)]

    assert moves == FIXTURE_NEXT_PAIRS
    assert moves.count(("approval", "done")) == 1
    assert len(moves) == len(set(moves))


def test_factory_moves_add_approval_to_done_after_the_next_lists() -> None:
    moves = [(move.from_stage, move.to_stage) for move in factory_moves(APPROVAL_WITHOUT_DONE)]

    assert moves == [("work", "approval"), ("approval", "work"), ("approval", "done")]


@pytest.mark.parametrize(
    "definition", [FIXTURE, APPROVAL_ONLY_DOING], ids=["fixture", "approval-only-doing"]
)
def test_every_factory_move_is_legal(definition: PipelineDefinition) -> None:
    moves = factory_moves(definition)

    assert moves
    for move in moves:
        change = StageChange(from_stage=move.from_stage, to_stage=move.to_stage)
        assert is_legal_change(definition, change), move


CHANGE = StageChange(from_stage="tests", to_stage="review")


@pytest.mark.parametrize(("from_stage", "valid"), [("Tests", False), ("tests", True)])
@pytest.mark.parametrize("model", [StageChange, FactoryMove], ids=["stage-change", "factory-move"])
def test_a_from_stage_must_be_a_lower_case_name(
    model: type[BaseModel], from_stage: str, valid: bool
) -> None:
    fields = {"from_stage": from_stage, "to_stage": "doing"}
    if valid:
        model.model_validate(fields)
    else:
        with pytest.raises(ValidationError):
            model.model_validate(fields)


@pytest.mark.parametrize(("work_item", "valid"), [("F001-S0001", False), ("F0001-S0001", True)])
def test_an_illegal_change_needs_a_work_item_id(work_item: str, valid: bool) -> None:
    model: type[BaseModel] = IllegalChange
    fields = {"work_item": work_item, "change": CHANGE}
    if valid:
        model.model_validate(fields)
    else:
        with pytest.raises(ValidationError):
            model.model_validate(fields)
