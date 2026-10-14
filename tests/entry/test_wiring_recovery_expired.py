"""The production wiring registers the crash's recovery handler for expired leases as well."""

from typing import get_args

from factory.application.boundaries import Boundaries
from factory.application.recovery import RecoveryHandler
from factory.domain.events import EventKind
from factory.domain.pipeline_definition import PipelineDefinition
from factory.entry.wiring import NOT_YET_HANDLED, build_handlers
from git_support import PIPELINE_YAML

INSTANCE = "factory-1"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}


def test_expired_shares_the_crash_handler_and_is_no_longer_listed_as_unhandled(
    boundaries: Boundaries,
) -> None:
    definition: PipelineDefinition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    handlers = build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)

    assert isinstance(handlers["crash"], RecoveryHandler)
    assert handlers["expired"] is handlers["crash"]
    assert "expired" not in NOT_YET_HANDLED
    every: tuple[EventKind, ...] = get_args(EventKind)
    assert set(NOT_YET_HANDLED) == {kind for kind in every if kind not in handlers}
