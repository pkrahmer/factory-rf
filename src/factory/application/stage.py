"""A stage's start and run, and what the factory makes of the run before it decides anything."""

import re
from collections import Counter
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.stalls import StallContext, StallResult, StallService
from factory.application.task import StoryFormChecker, TaskComposer, TaskContext
from factory.application.undo import UndoReport, UndoService
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.decisions import StallReason, agent_entry, stall_reason_of
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.journal import NewEntry, append_entry
from factory.domain.paths import cost_records_path
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
        return state.stage

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


class AgentAftermath(BaseModel):
    """A run the factory can keep: its decision, the undone work item, the entry and the form."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    decision: str
    document: WorkItemDocument
    entry: NewEntry
    undo: UndoReport
    form_findings: list[FormFinding]


class AfterAgent:
    """Turns a launched stage into what the factory observes, or into a stall."""

    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None:
        """Process as `instance` under `definition`."""
        self._boundaries = boundaries
        self._definition = definition
        self._stalls = StallService(boundaries, instance, definition)

    def process(self, launched: LaunchedStage) -> AgentAftermath | StallResult:
        """Test the branch and the result, undo, build the entry and check the form again.

        Stops at the first step that cannot be kept and stalls it, one attempt counted. The
        entry is not appended to the returned document.
        """
        started = launched.started
        if self._boundaries.git.status().branch != started.branch:
            return self._stall(started, "left_branch")
        result = launched.result
        reason = stall_reason_of(result)
        if reason is not None:
            return self._stall(started, reason, _first_denial(result))
        decision = result.decision
        allowed = launched.request.allowed_decisions
        if decision is None or decision not in allowed:
            detail = f"decision '{decision}' is not one of {', '.join(allowed)}"
            return self._stall(started, "decision_not_allowed", detail)
        undo = UndoService(self._boundaries).undo(started.stage_start, started.path)
        document = self._boundaries.work_item_reader.read(self._boundaries.checkout / started.path)
        entry = self._entry(started, decision, result.entry or "", undo)
        if entry is None:
            return self._stall(started, "no_result", "the entry is empty")
        findings = StoryFormChecker(self._boundaries).findings(document)
        new = _new_findings(started.findings, findings)
        if new:
            detail = "; ".join(finding.message for finding in new)
            return self._stall(started, "form_invalid", detail, append_entry(document, entry))
        return AgentAftermath(
            started=started,
            request=launched.request,
            result=result,
            decision=decision,
            document=document,
            entry=entry,
            undo=undo,
            form_findings=findings,
        )

    def _entry(
        self, started: StartedStage, decision: str, text: str, undo: UndoReport
    ) -> NewEntry | None:
        role = self._definition.stages[started.stage].role
        if role is None:
            raise ValueError(f"stage {started.stage} has no role, so no agent ran there")
        # The factory rewrites its own cost records after the undo; that is no news to the agent.
        sidecar = cost_records_path(started.path)
        undone = sorted(path for path in [*undo.reverted, *undo.deleted] if path != sidecar)
        return agent_entry(
            role=role, stage=started.stage, decision=decision, text=text, undone=undone
        )

    def _stall(
        self,
        started: StartedStage,
        reason: StallReason,
        detail: str = "",
        document: WorkItemDocument | None = None,
    ) -> StallResult:
        context = StallContext(
            work_item=started.work_item,
            stage=started.stage,
            branch=started.branch,
            path=started.path,
            stage_start=started.stage_start,
            document=document,
            pull_request=started.pull_request,
        )
        return self._stalls.stall(context, reason, detail)


def _first_denial(result: AgentRunResult) -> str:
    if not result.permission_denials:
        return ""
    denial = result.permission_denials[0]
    return f"denied: {denial.tool}: {denial.detail}"


def _masked(message: str) -> str:
    # Messages embed line numbers, which move when the agent edits above them.
    return re.sub(r"\d+", "#", message)


def _new_findings(before: list[FormFinding], after: list[FormFinding]) -> list[FormFinding]:
    # Of equal messages the first ones count as the old ones.
    old = Counter(_masked(finding.message) for finding in before)
    new = []
    for finding in after:
        key = _masked(finding.message)
        if old[key] > 0:
            old[key] -= 1
        else:
            new.append(finding)
    return new
