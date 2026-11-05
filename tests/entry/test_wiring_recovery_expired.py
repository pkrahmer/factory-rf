"""The production wiring registers the crash's recovery handler for expired leases as well."""

from factory.entry.wiring import build_handlers
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.recovery import RecoveryHandler
from factory.pipeline.domain.pipeline_definition import PipelineDefinition
from support.git_support import PIPELINE_YAML
from support.stage_run_support import INSTANCE
from support.wiring_support import ENVIRONMENT


def test_expired_shares_the_crash_handler(
    boundaries: Boundaries,
) -> None:
    definition: PipelineDefinition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    handlers = build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)

    assert isinstance(handlers["crash"], RecoveryHandler)
    assert handlers["expired"] is handlers["crash"]
