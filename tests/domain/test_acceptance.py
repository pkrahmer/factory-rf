"""The feature acceptance as data: its id, its report file name, its order and its state."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.acceptance import (
    AcceptanceState,
    acceptance_file_name,
    acceptance_id,
    next_acceptance_id,
)
from factory.domain.identifiers import (
    parse_feature_directory_name,
    parse_work_item_file_name,
    work_item_order,
)
from factory.domain.work_item import WorkItemState

ORDERED = ["F0002-S0001", "F0002-S0009", "F0002-A0001", "F0003-S0001"]


@pytest.mark.parametrize(
    ("feature", "number", "expected"),
    [("F0001", 1, "F0001-A0001"), ("F0012", 345, "F0012-A0345")],
)
def test_acceptance_id_is_the_feature_and_a_four_digit_number(
    feature: str, number: int, expected: str
) -> None:
    assert acceptance_id(feature, number) == expected


@pytest.mark.parametrize(
    ("number", "expected"),
    [(0, None), (1, "F0001-A0001"), (9999, "F0001-A9999"), (10000, None)],
)
def test_acceptance_id_takes_numbers_from_1_to_9999(number: int, expected: str | None) -> None:
    if expected is None:
        with pytest.raises(ValueError):
            acceptance_id("F0001", number)
    else:
        assert acceptance_id("F0001", number) == expected


def test_first_acceptance_of_a_feature_is_number_one() -> None:
    assert next_acceptance_id("F0001", []) == "F0001-A0001"


def test_next_acceptance_follows_the_highest_of_the_feature() -> None:
    existing = ["F0001-A0001", "F0001-A0003", "F0001-S0009", "F0002-A0007"]

    assert next_acceptance_id("F0001", existing) == "F0001-A0004"


@pytest.mark.parametrize(
    ("highest", "expected"),
    [("F0001-A9998", "F0001-A9999"), ("F0001-A9999", None)],
)
def test_next_acceptance_ends_at_9999(highest: str, expected: str | None) -> None:
    if expected is None:
        with pytest.raises(ValueError):
            next_acceptance_id("F0001", [highest])
    else:
        assert next_acceptance_id("F0001", [highest]) == expected


def test_acceptance_file_name_reads_back_to_its_id_and_slug() -> None:
    name = acceptance_file_name("F0001-A0004")

    parsed = parse_work_item_file_name(name)

    assert name == "F0001-A0004-acceptance.md"
    assert parsed is not None
    assert (parsed.id, parsed.slug) == ("F0001-A0004", "acceptance")


def test_acceptance_file_name_refuses_a_story_id() -> None:
    with pytest.raises(ValueError):
        acceptance_file_name("F0001-S0004")


@pytest.mark.parametrize("directory", ["F0002-2fa", "F0002"])
def test_acceptance_sorts_after_the_stories_of_its_feature(directory: str) -> None:
    parsed = parse_feature_directory_name(directory)
    assert parsed is not None
    ids = ["F0003-S0001", acceptance_id(parsed.id, 1), "F0002-S0009", "F0002-S0001"]

    assert sorted(ids, key=work_item_order) == ORDERED


def test_acceptance_state_defaults_to_no_stories_and_no_outcome() -> None:
    state = AcceptanceState(stage="acceptance")

    assert state.stories == []
    assert state.outcome is None
    assert state.model_dump(exclude={"stories", "outcome"}) == (
        WorkItemState(stage="acceptance").model_dump()
    )


@pytest.mark.parametrize(
    ("stories", "valid"),
    [
        (["F0001-S0002", "F0001-S0001"], False),
        (["F0001-S0001", "F0001-S0001"], False),
        (["F0001-S0001", "F0001-S0002"], True),
    ],
)
def test_acceptance_stories_ascend_strictly(stories: list[str], valid: bool) -> None:
    if valid:
        assert AcceptanceState(stage="acceptance", stories=stories).stories == stories
    else:
        with pytest.raises(ValidationError):
            AcceptanceState(stage="acceptance", stories=stories)


def test_acceptance_stories_refuse_an_acceptance_id() -> None:
    with pytest.raises(ValidationError):
        AcceptanceState(stage="acceptance", stories=["F0001-A0001"])


@pytest.mark.parametrize(
    ("stage", "outcome", "valid"),
    [("acceptance", "accepted", False), ("done", None, False), ("done", "refused", True)],
)
def test_acceptance_outcome_is_set_exactly_when_done(
    stage: str, outcome: str | None, valid: bool
) -> None:
    model: type[BaseModel] = AcceptanceState
    if valid:
        model(stage=stage, outcome=outcome)
    else:
        with pytest.raises(ValidationError):
            model(stage=stage, outcome=outcome)


@pytest.mark.parametrize(
    ("values", "valid"),
    [
        ({"stage": "acceptance", "verdict": "fine"}, False),
        ({"stage": "acceptance", "stories": ["F0001-S0001"]}, True),
        ({"stage": "acceptance", "stories": ["F001-S0001"]}, False),
        ({"stage": "done", "outcome": "refused"}, True),
        ({"stage": "done", "outcome": "maybe"}, False),
    ],
)
def test_acceptance_state_is_closed_and_typed(values: dict[str, object], valid: bool) -> None:
    model: type[BaseModel] = AcceptanceState
    if valid:
        model(**values)
    else:
        with pytest.raises(ValidationError):
            model(**values)


def test_acceptance_state_refuses_an_assignment() -> None:
    model: type[BaseModel] = AcceptanceState
    state = model(stage="acceptance")
    field = "stories"

    with pytest.raises(ValidationError):
        setattr(state, field, ["F0001-S0001"])
