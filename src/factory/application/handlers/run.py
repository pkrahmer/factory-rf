"""The run handler: one `run` event becomes one stage run."""

from collections.abc import Mapping

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.stage import StageRunner
from factory.domain.events import Event
from factory.domain.identifiers import Name
from factory.domain.pipeline_definition import PipelineDefinition


class RunHandler(Handler):
    """Runs the stage of the work item of a `run` event."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: Name,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None:
        """Run as `instance` under `definition`; agent runs get `environment` unchanged."""
        self._boundaries = boundaries
        self._instance = instance
        self._definition = definition
        self._environment = environment

    def handle(self, event: Event) -> None:
        """Run one stage; `ValueError` for any event that is not a `run` of a work item."""
        if event.kind != "run" or event.work_item is None:
            raise ValueError(f"not a run event: {event.kind}")
        work_item = event.work_item
        runner = StageRunner(self._boundaries, self._instance, self._definition, self._environment)
        # A stall is a result the stage has already recorded, so the report is not needed here.
        runner.run(work_item.id, work_item.path)
