"""The pipeline definition's refusal error and the placeholders of its write paths."""

from factory.domain.errors import FactoryError, PipelineDefinitionInvalid
from factory.domain.pipeline_definition import FEATURE_PLACEHOLDER, WORK_ITEM_PLACEHOLDER


def test_pipeline_definition_invalid_carries_its_fault_as_message() -> None:
    error = PipelineDefinitionInvalid("m")

    assert error.fault == "m"
    assert str(error) == "m"
    assert isinstance(error, FactoryError)


def test_write_path_placeholders_are_spelled_in_braces() -> None:
    assert WORK_ITEM_PLACEHOLDER == "{work_item}"
    assert FEATURE_PLACEHOLDER == "{feature}"
