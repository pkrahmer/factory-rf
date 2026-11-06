"""Pipeline definitions shared by the tests of whether a stage lies before the approval."""

from typing import Final

from factory.pipeline.domain.pipeline_definition import PipelineDefinition

ROLES: Final[dict[str, object]] = {
    "intake": {"write_paths": ["{work_item}"]},
    "tester": {"write_paths": ["tests/*"]},
    "coder": {"write_paths": ["src/*"]},
    "reviewer": {"write_paths": ["{work_item}"]},
    "documenter": {"write_paths": ["README.md", "docs/*"]},
    "smoke-tester": {"write_paths": ["{work_item}"]},
    "acceptance-reviewer": {"write_paths": ["{work_item}", "{feature}/backlog/*"]},
}

# The stages of the test remote's pipeline definition (`PIPELINE_YAML`), in its order.
FIXTURE: Final[PipelineDefinition] = PipelineDefinition.model_validate(
    {
        "contract": "1.0",
        "acceptance_stage": "acceptance",
        "roles": ROLES,
        "stages": {
            "intake": {"role": "intake", "next": ["tests"]},
            "tests": {"role": "tester", "next": ["doing"], "checks": ["lint"], "reports": ["test"]},
            "doing": {"role": "coder", "next": ["review", "tests"], "checks": ["check"]},
            "review": {"role": "reviewer", "next": ["docs", "doing"], "round_cap": 3},
            "docs": {"role": "documenter", "next": ["smoke-test", "doing"], "checks": ["check"]},
            "smoke-test": {"role": "smoke-tester", "next": ["approval", "doing"]},
            "acceptance": {"role": "acceptance-reviewer", "next": ["approval"]},
            "approval": {"approval": True, "next": ["done", "doing"]},
            "done": {},
        },
    }
)


def without_approval() -> PipelineDefinition:
    """Return a definition whose acceptance stage leads straight to `done`, with no approval."""
    return PipelineDefinition.model_validate(
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
