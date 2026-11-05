"""Reading the test remote's pipeline definition outside a fixture."""

from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.domain.pipeline_definition import PipelineDefinition
from support.git_support import PIPELINE_YAML


def pipeline_definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, read through the boundaries' reader."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)
