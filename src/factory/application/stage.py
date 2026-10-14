"""The start of a stage: the claim pushed first, then the pull request, the guard and the run."""

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.task import StoryFormChecker, TaskComposer, TaskContext
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.story_form import FormFinding
from factory.domain.work_item import WorkItemDocument


class StartedStage(BaseModel):
    """A stage whose claim is pushed: the stage-start commit, the work item and its pull request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    stage: Name
    branch: str
    path: str
    stage_start: StageStart
    document: WorkItemDocument
    pull_request: PullRequestView
    findings: list[FormFinding]


class LaunchedStage(BaseModel):
    """A started stage with the request its agent ran on and the run's result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult


class StageLauncher:
    """Starts a prepared work item's stage: claim pushed, pull request ensured, agent run."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None:
        """Launch as `instance` under `definition`; agent runs get `environment` unchanged."""
        self._boundaries = boundaries
        self._definition = definition
        self._claims = ClaimService(boundaries, instance, definition)
        self._opening = WorkItemOpening(boundaries, definition)
        self._composer = TaskComposer(boundaries, definition, environment)

    def launch(self, prepared: PreparedWorkItem) -> LaunchedStage:
        """Push the claim, then ensure the pull request, compose the request and run the agent.

        Nothing reaches the remote but the claim, and no agent runs before it is pushed.
        `ValueError` for a conflicted work item or a stage without a role, before anything is
        read or pushed; `PushFailed`, `AgentDefinitionMissing` and `AgentRuntimeError`
        propagate. A run that ends early is a result, not an error.
        """
        stage = self._launchable_stage(prepared)
        agent = self._composer.agent(stage)
        findings = StoryFormChecker(self._boundaries).findings(prepared.document)
        started = self._start(prepared, stage, findings)
        context = TaskContext(
            work_item=started.work_item,
            path=started.path,
            stage=started.stage,
            document=started.document,
            branch=started.branch,
            pull_request=started.pull_request.number,
            findings=started.findings,
            guard=WritePathService(self._boundaries).at(started.stage_start, started.path),
        )
        request = self._composer.compose(context, agent)
        result = self._boundaries.agent_runtime.run(request)
        return LaunchedStage(started=started, request=request, result=result)

    def _launchable_stage(self, prepared: PreparedWorkItem) -> str:
        if prepared.merge_conflict:
            raise ValueError(f"{prepared.branch} has a merge conflict with the main branch")
        state = prepared.document.state
        if state is None:
            raise ValueError(f"the work item {prepared.work_item} has no state")
        stage = state.stage
        if stage not in self._definition.stages:
            raise ValueError(f"{stage} is not a stage of the pipeline definition")
        if self._definition.stages[stage].role is None:
            raise ValueError(f"stage {stage} has no role, so no agent runs there")
        return stage

    def _start(
        self, prepared: PreparedWorkItem, stage: str, findings: list[FormFinding]
    ) -> StartedStage:
        stage_start = self._claims.claim(prepared.branch, prepared.path, prepared.document, stage)
        # The committed file, not the document given to the claim: the agent works on what
        # the stage-start commit holds.
        document = self._boundaries.work_item_reader.read(self._boundaries.checkout / prepared.path)
        pull_request = self._opening.ensure_pull_request(prepared.work_item, document)
        return StartedStage(
            work_item=prepared.work_item,
            stage=stage,
            branch=prepared.branch,
            path=prepared.path,
            stage_start=stage_start,
            document=document,
            pull_request=pull_request,
            findings=findings,
        )
