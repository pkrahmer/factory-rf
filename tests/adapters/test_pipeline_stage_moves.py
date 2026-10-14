"""A stage other than done must be able to move, or the definition is refused when read."""

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
from git_support import PIPELINE_YAML

DOING_STAGE = "  doing: {role: coder, next: [review, tests], checks: [check]}"
REVIEW_STAGE = "  review: {role: reviewer, next: [docs, doing], round_cap: 3}"
APPROVAL_STAGE = "  approval: {approval: true, next: [done, doing]}"
DONE_STAGE = "  done: {}"


def _changed(text: str, *replacements: tuple[str, str]) -> str:
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def _before_done(*stages: str) -> tuple[str, str]:
    return DONE_STAGE, "".join(f"  {stage}\n" for stage in stages) + DONE_STAGE


def _outcome(text: str) -> str | None:
    """The fault of a refused text, or `None` when the text is accepted."""
    try:
        RuamelPipelineDefinitionReader().parse(text)
    except PipelineDefinitionInvalid as error:
        return error.fault
    return None


def test_a_stage_no_next_names_is_accepted() -> None:
    assert "[acceptance" not in PIPELINE_YAML
    assert ", acceptance]" not in PIPELINE_YAML

    assert _outcome(PIPELINE_YAML) is None


@pytest.mark.parametrize(
    ("limbo", "fault"),
    [
        ("limbo: {next: [done]}", "stage limbo: has neither a role nor approval"),
        ("limbo: {role: coder, next: [done]}", None),
        ("limbo: {approval: true, next: [done]}", None),
        (
            "limbo: {}",
            "stage limbo: next is empty; stage limbo: has neither a role nor approval",
        ),
    ],
)
def test_a_stage_needs_a_role_or_approval_and_a_next(limbo: str, fault: str | None) -> None:
    text = _changed(PIPELINE_YAML, _before_done(limbo))

    assert _outcome(text) == fault


@pytest.mark.parametrize(
    ("names", "fault"), [("[]", "stage doing: next is empty"), ("[review]", None)]
)
def test_a_stage_with_a_role_and_an_empty_next_is_refused(names: str, fault: str | None) -> None:
    text = _changed(PIPELINE_YAML, (DOING_STAGE, DOING_STAGE.replace("[review, tests]", names)))

    assert _outcome(text) == fault


def test_an_approval_stage_with_an_empty_next_is_refused() -> None:
    text = _changed(PIPELINE_YAML, (APPROVAL_STAGE, APPROVAL_STAGE.replace("[done, doing]", "[]")))

    assert _outcome(text) == "stage approval: next is empty"


def test_empty_nexts_come_before_stages_without_role_or_approval_in_stage_order() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DOING_STAGE, DOING_STAGE.replace("[review, tests]", "[]")),
        (REVIEW_STAGE, REVIEW_STAGE.replace("[docs, doing]", "[]")),
        _before_done("a: {next: [done]}", "b: {next: [done]}"),
    )

    assert _outcome(text) == (
        "stage doing: next is empty; "
        "stage review: next is empty; "
        "stage a: has neither a role nor approval; "
        "stage b: has neither a role nor approval"
    )


def test_a_fault_of_the_earlier_rules_comes_before_a_stage_that_cannot_move() -> None:
    text = _changed(
        PIPELINE_YAML,
        (DOING_STAGE, DOING_STAGE.replace("[review, tests]", "[review, ship]")),
        _before_done("limbo: {next: [done]}"),
    )

    assert _outcome(text) == (
        "stage doing: next names unknown stage ship; stage limbo: has neither a role nor approval"
    )


def test_without_a_done_stage_no_stage_is_refused_for_not_moving() -> None:
    text = PIPELINE_YAML.replace("done", "finished")

    assert _outcome(text) == "stages must hold a stage named done"
