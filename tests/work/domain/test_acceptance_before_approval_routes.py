"""Whether a stage lies before the approval, read from its forward moves on every route."""

import pytest

from factory.pipeline.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.pipeline.domain.pipeline_definition import PipelineDefinition
from factory.work.domain.acceptance import is_before_approval
from support.before_approval_support import ROLES
from support.two_routes_support import TWO_ROUTES


def _definition(stages: dict[str, object]) -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {"contract": "1.0", "acceptance_stage": "acceptance", "roles": ROLES, "stages": stages}
    )


# The stages of the shipped `factory/pipeline.yml`, in its order.
SHIPPED = RuamelPipelineDefinitionReader().parse(TWO_ROUTES)

# Beside the approval: a loop that never reaches it, a dead end at `done`, and a chain of three.
CHAINS = _definition(
    {
        "a": {"role": "coder", "next": ["b"]},
        "b": {"role": "coder", "next": ["a"]},
        "dead-end": {"role": "coder", "next": ["done"]},
        "first": {"role": "coder", "next": ["second"]},
        "second": {"role": "reviewer", "next": ["third"]},
        "third": {"role": "documenter", "next": ["approval"]},
        "acceptance": {"role": "acceptance-reviewer", "next": ["approval"]},
        "approval": {"approval": True, "next": ["done", "first"]},
        "done": {},
    }
)


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        ("intake", True),
        ("tests", True),
        ("doing", True),
        ("review", True),
        ("docs", True),
        ("smoke-test", True),
        ("docs-only", True),
        ("docs-review", True),
        ("docs-approval", False),
        ("acceptance", True),
        ("approval", False),
        ("done", False),
    ],
)
def test_every_stage_of_the_shipped_order_is_before_approval_by_its_forward_moves(
    stage: str, *, expected: bool
) -> None:
    assert is_before_approval(SHIPPED, stage) is expected


@pytest.mark.parametrize(
    ("stage", "expected"),
    [("a", False), ("dead-end", False), ("first", True)],
    ids=["loop", "dead-end-at-done", "three-moves"],
)
def test_a_forward_chain_is_before_approval_only_when_it_reaches_one(
    stage: str, *, expected: bool
) -> None:
    assert is_before_approval(CHAINS, stage) is expected
