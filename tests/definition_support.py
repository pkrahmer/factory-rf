"""Reading the test remote's pipeline definition outside a fixture."""

from factory.application.boundaries import Boundaries
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import PIPELINE_YAML


def pipeline_definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, read through the boundaries' reader."""
    return boundaries.pipeline_reader.parse(PIPELINE_YAML)
