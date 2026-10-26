"""The decision rules on the template's smoke test: a slip in a document goes to `docs`."""

from pathlib import Path

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.decisions import StageMove, decide
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import round_cap_question
from factory.domain.work_item import WorkItemState

TEMPLATE = Path(__file__).parent.parent.parent / "template" / "factory" / "pipeline.yml"


@pytest.fixture
def template() -> PipelineDefinition:
    """Return the pipeline definition the template ships."""
    return RuamelPipelineDefinitionReader().parse(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("rounds", "decision", "expected"),
    [
        pytest.param(
            0,
            "docs",
            StageMove(rule=3, stage="docs", blocked=None, round=1, question=None),
            id="docs-first-rework",
        ),
        pytest.param(
            2,
            "docs",
            StageMove(rule=3, stage="docs", blocked=None, round=3, question=None),
            id="docs-at-the-cap",
        ),
        pytest.param(
            3,
            "docs",
            StageMove(
                rule=4,
                stage="smoke-test",
                blocked="round_cap",
                round=4,
                question=round_cap_question(4, 3),
            ),
            id="docs-past-the-cap",
        ),
        pytest.param(
            0,
            "doing",
            StageMove(rule=3, stage="doing", blocked=None, round=1, question=None),
            id="doing-rework",
        ),
        pytest.param(
            2,
            "approval",
            StageMove(rule=6, stage="approval", blocked=None, round=2, question=None),
            id="approval-forward",
        ),
        pytest.param(0, "review", None, id="review-outside-next"),
    ],
)
def test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework(
    template: PipelineDefinition, rounds: int, decision: str, expected: StageMove | None
) -> None:
    state = WorkItemState(stage="smoke-test", round=rounds)

    if expected is None:
        with pytest.raises(ValueError, match="not allowed"):
            decide(template, state, decision)
    else:
        assert decide(template, state, decision) == expected
