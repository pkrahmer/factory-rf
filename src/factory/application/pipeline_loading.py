"""Loading the pipeline definition at a git ref, its agents checked, a refusal reported."""

from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.errors import AgentDefinitionError, PipelineDefinitionInvalid
from factory.domain.paths import MAIN_BRANCH, PIPELINE_DEFINITION_FILE, REMOTE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.stops import RepositoryStop

PIPELINE_REF = f"{REMOTE}/{MAIN_BRANCH}"


class PipelineLoader:
    """The one place that loads the pipeline definition and raises or clears its stop.

    The stop belongs to the definition on `PIPELINE_REF`: a load at any other ref raises
    the same refusal but leaves the health status as it is.
    """

    def __init__(self, boundaries: Boundaries) -> None:
        """Read through the git, readers, clock, log and health status of `boundaries`."""
        self._boundaries = boundaries
        self._stops = StopService(boundaries)

    def load(self, ref: str = PIPELINE_REF) -> PipelineDefinition:
        """The definition at `ref`; `PipelineDefinitionInvalid` naming the fault otherwise.

        At `PIPELINE_REF` a refusal first raises the stop and a success first clears it.
        `GitError` propagates and touches no stop.
        """
        try:
            definition = self._read(ref)
        except PipelineDefinitionInvalid as error:
            if ref == PIPELINE_REF:
                self._stops.raise_stop(self._stop(error.fault))
            raise
        if ref == PIPELINE_REF:
            self._stops.clear_stop("pipeline_definition_invalid")
        return definition

    def _read(self, ref: str) -> PipelineDefinition:
        text = self._boundaries.git.show_file(ref, PIPELINE_DEFINITION_FILE)
        if text is None:
            raise PipelineDefinitionInvalid(f"{PIPELINE_DEFINITION_FILE} is missing at {ref}")
        definition = self._boundaries.pipeline_reader.parse(text)
        self._require_agents(definition)
        return definition

    def _require_agents(self, definition: PipelineDefinition) -> None:
        try:
            installed = set(self._boundaries.agent_definitions.names())
        except AgentDefinitionError as error:
            raise PipelineDefinitionInvalid(f"agent home unavailable: {error.fault}") from error
        faults = [
            f"role {role}: agent is not installed"
            for role in definition.roles
            if role not in installed
        ]
        if faults:
            raise PipelineDefinitionInvalid("; ".join(faults))

    def _stop(self, fault: str) -> RepositoryStop:
        return RepositoryStop(
            scope="repository",
            reason="pipeline_definition_invalid",
            detail=fault,
            at=self._boundaries.clock.now(),
        )
