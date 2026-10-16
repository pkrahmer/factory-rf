"""Loading the pipeline definition at a git ref, its agents checked, a refusal reported."""

from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.errors import (
    AgentDefinitionError,
    AgentDefinitionInvalid,
    PipelineDefinitionInvalid,
)
from factory.domain.paths import MAIN_BRANCH, PIPELINE_DEFINITION_FILE, REMOTE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.stops import RepositoryStop, RepositoryStopReason

PIPELINE_REF = f"{REMOTE}/{MAIN_BRANCH}"


class PipelineLoader:
    """The one place that loads the pipeline definition and raises or clears its stops.

    The stops, `pipeline_definition_invalid` and `agent_definition_invalid`, belong to the
    definition on `PIPELINE_REF`: a load at any other ref raises the same refusal but leaves
    the health status as it is.
    """

    def __init__(self, boundaries: Boundaries) -> None:
        """Read through the git, readers, clock, log and health status of `boundaries`."""
        self._boundaries = boundaries
        self._stops = StopService(boundaries)

    def load(self, ref: str = PIPELINE_REF) -> PipelineDefinition:
        """The definition at `ref`, every role's agent file read; the refusal otherwise.

        `PipelineDefinitionInvalid` names a fault of the definition, `AgentDefinitionInvalid`
        an agent file the agent runtime cannot apply. At `PIPELINE_REF` a refusal first
        raises its stop and a success first clears it. `GitError` propagates and touches no
        stop.
        """
        on_main = ref == PIPELINE_REF
        definition = self._load_definition(ref, on_main)
        self._check_agent_files(definition, on_main)
        return definition

    def _load_definition(self, ref: str, on_main: bool) -> PipelineDefinition:
        try:
            definition = self._read(ref)
        except PipelineDefinitionInvalid as error:
            if on_main:
                self._stops.raise_stop(self._stop("pipeline_definition_invalid", error.fault))
            raise
        if on_main:
            self._stops.clear_stop("pipeline_definition_invalid")
        return definition

    def _check_agent_files(self, definition: PipelineDefinition, on_main: bool) -> None:
        try:
            for role in definition.roles:
                self._boundaries.agent_definitions.read(role)
        except AgentDefinitionInvalid as error:
            if on_main:
                detail = f"{error.name}: {error.fault}"
                self._stops.raise_stop(self._stop("agent_definition_invalid", detail))
            raise
        if on_main:
            self._stops.clear_stop("agent_definition_invalid")

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

    def _stop(self, reason: RepositoryStopReason, detail: str) -> RepositoryStop:
        return RepositoryStop(
            scope="repository",
            reason=reason,
            detail=detail,
            at=self._boundaries.clock.now(),
        )
