"""The production wiring registers the recovery handler for crashes, rerunning through the gate."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.run_gate import RunGate
from factory.application.recovery import RecoveryHandler
from factory.domain.events import EventKind
from factory.domain.pipeline_definition import PipelineDefinition
from factory.entry.wiring import build_handlers
from git_support import PIPELINE_YAML
from stage_run_support import INSTANCE
from wiring_support import ENVIRONMENT


def _handlers(boundaries: Boundaries) -> dict[EventKind, Handler]:
    definition: PipelineDefinition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return build_handlers(boundaries, definition, INSTANCE, ENVIRONMENT)


def test_the_crash_handler_reruns_through_the_very_gate_registered_for_run(
    boundaries: Boundaries,
) -> None:
    handlers = _handlers(boundaries)

    recovery = handlers["crash"]
    assert isinstance(recovery, RecoveryHandler)
    assert isinstance(handlers["run"], RunGate)
    assert recovery.run is handlers["run"]


def test_crash_is_handled(
    boundaries: Boundaries,
) -> None:
    handlers = _handlers(boundaries)

    assert "crash" in handlers
