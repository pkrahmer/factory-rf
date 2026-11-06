"""Whether a stage lies before the approval, read from its forward moves on every route."""

import pytest

from factory.pipeline.domain.pipeline_definition import PipelineDefinition
from factory.work.domain.acceptance import is_before_approval

ROLES: dict[str, object] = {
    "intake": {"write_paths": ["{work_item}"]},
    "tester": {"write_paths": ["tests/*"]},
    "coder": {"write_paths": ["src/*"]},
    "reviewer": {"write_paths": ["{work_item}"]},
    "documenter": {"write_paths": ["README.md", "docs/*"]},
    "smoke-tester": {"write_paths": ["{work_item}"]},
    "acceptance-reviewer": {"write_paths": ["{work_item}", "{feature}/backlog/*"]},
}


def _definition(stages: dict[str, object]) -> PipelineDefinition:
    return PipelineDefinition.model_validate(
        {"contract": "1.0", "acceptance_stage": "acceptance", "roles": ROLES, "stages": stages}
    )


# The stages of the shipped `factory/pipeline.yml`, in its order.
SHIPPED = _definition(
    {
        "intake": {"role": "intake", "next": ["tests", "docs-only"]},
        "tests": {"role": "tester", "next": ["doing"]},
        "doing": {"role": "coder", "next": ["review", "tests"]},
        "review": {"role": "reviewer", "next": ["docs", "doing"]},
        "docs": {"role": "documenter", "next": ["smoke-test", "doing"]},
        "smoke-test": {"role": "smoke-tester", "next": ["approval", "doing", "docs"]},
        "docs-only": {"role": "documenter", "next": ["docs-review", "tests"]},
        "docs-review": {"role": "reviewer", "next": ["docs-approval", "docs-only"]},
        "docs-approval": {"approval": True, "next": ["done", "docs-only"]},
        "acceptance": {"role": "acceptance-reviewer", "next": ["approval"]},
        "approval": {"approval": True, "next": ["done", "doing"]},
        "done": {},
    }
)

# The single route of the test remote's pipeline definition (`PIPELINE_YAML`), in its order.
SINGLE_ROUTE = _definition(
    {
        "intake": {"role": "intake", "next": ["tests"]},
        "tests": {"role": "tester", "next": ["doing"]},
        "doing": {"role": "coder", "next": ["review", "tests"]},
        "review": {"role": "reviewer", "next": ["docs", "doing"]},
        "docs": {"role": "documenter", "next": ["smoke-test", "doing"]},
        "smoke-test": {"role": "smoke-tester", "next": ["approval", "doing"]},
        "acceptance": {"role": "acceptance-reviewer", "next": ["approval"]},
        "approval": {"approval": True, "next": ["done", "doing"]},
        "done": {},
    }
)

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

WITHOUT_APPROVAL = PipelineDefinition.model_validate(
    {
        "contract": "1.0",
        "acceptance_stage": "acceptance",
        "roles": {"acceptance-reviewer": {"write_paths": ["{work_item}"]}},
        "stages": {
            "acceptance": {"role": "acceptance-reviewer", "next": ["done"]},
            "done": {},
        },
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
    [("acceptance", True), ("approval", False), ("done", False)],
)
def test_the_single_route_keeps_its_results(stage: str, *, expected: bool) -> None:
    assert is_before_approval(SINGLE_ROUTE, stage) is expected


@pytest.mark.parametrize(
    ("stage", "expected"),
    [("a", False), ("dead-end", False), ("first", True)],
    ids=["loop", "dead-end-at-done", "three-moves"],
)
def test_a_forward_chain_is_before_approval_only_when_it_reaches_one(
    stage: str, *, expected: bool
) -> None:
    assert is_before_approval(CHAINS, stage) is expected


@pytest.mark.parametrize(
    ("definition", "stage", "error"),
    [(SHIPPED, "nowhere", KeyError), (WITHOUT_APPROVAL, "acceptance", ValueError)],
    ids=["unknown-stage", "no-approval-stage"],
)
def test_an_unknown_stage_or_a_definition_without_approval_is_refused(
    definition: PipelineDefinition, stage: str, error: type[Exception]
) -> None:
    with pytest.raises(error):
        is_before_approval(definition, stage)
