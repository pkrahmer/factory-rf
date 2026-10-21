"""The production wiring registers the crash's recovery handler for expired leases as well."""

from factory.application.boundaries import Boundaries
from factory.application.recovery import RecoveryHandler
from factory.domain.pipeline_definition import PipelineDefinition
from factory.entry.wiring import build_handlers
from git_support import PIPELINE_YAML
from stage_run_support import INSTANCE

ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}


def test_expired_shares_the_crash_handler(
    boundaries: Boundaries,
) -> None:
    definition: PipelineDefinition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    handlers = build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)

    assert isinstance(handlers["crash"], RecoveryHandler)
    assert handlers["expired"] is handlers["crash"]
