"""A stage from its start to its result: the run, the decision, the checks and the result commit."""

import re
from collections import Counter
from collections.abc import Mapping
from datetime import timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.costs import CostRecorder, CostRun
from factory.application.handlers.recording import commit_subject
from factory.application.known_results import KnownResults
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.provider_limits import PatientRuns
from factory.application.stage_environment import StageEnvironment, stage_environment_of
from factory.application.stalls import StallContext, StallResult, StallService
from factory.application.take import TakeReport
from factory.application.task import StoryFormChecker, TaskComposer, TaskContext
from factory.domain.acceptance import acceptance_description
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.checks import CheckResult, command_line
from factory.domain.decisions import StageMove, StallReason, agent_entry, decide, stall_reason_of
from factory.domain.errors import HostingServiceError, PushFailed
from factory.domain.git import CommitId
from factory.domain.hand_over import hand_over_description
from factory.domain.hosting import PullRequestView
from factory.domain.identifiers import Name, WorkItemId, is_acceptance
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.labels import labels_for
from factory.domain.paths import MAIN_BRANCH, cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition, ProjectCommandDefinition
from factory.domain.story_form import FormFinding
from factory.domain.work_item import WorkItemDocument, require_state

STALL_TAIL_LINES = 15


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
    cost: CostRun
    nested_repositories: list[str] = []


class StageLauncher:
    """Starts a prepared work item's stage: claim pushed, pull request ensured, agent run."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
        *,
        stage_environment: StageEnvironment | None = None,
    ) -> None:
        """Launch as `instance` under `definition`; agent runs get `environment` unchanged.

        The agent runs in `stage_environment`, by default the one the boundaries describe.
        """
        self._boundaries = boundaries
        self._definition = definition
        self._stage_environment = stage_environment or stage_environment_of(boundaries)
        self._claims = ClaimService(boundaries, instance, definition)
        self._opening = WorkItemOpening(boundaries, definition)
        self._composer = TaskComposer(boundaries, definition, environment)
        self._costs = CostRecorder(boundaries)

    def launch(self, prepared: PreparedWorkItem) -> LaunchedStage:
        """Push the claim, ensure the pull request, prepare the environment and run the agent.

        Nothing reaches the remote but the claim, and no agent runs before it is pushed. The
        run's cost record is begun before it and completed after it, in the work tree only; a
        run that waits out the provider's spend limit and resumes is one run and one record.
        `ValueError` for a conflicted work item or a stage without a role, before anything is
        read or pushed; `PushFailed`, `AgentDefinitionMissing`, `AgentRuntimeError`,
        `RepositoryUnsealed`, and the environment's `SnapshotError` and `ContainerError`
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
        )
        request = self._composer.compose(context, agent)
        self._stage_environment.prepare(
            started.stage_start.commit, started.branch, sync_time_limit=self._sync_time_limit()
        )
        begun = self._costs.begin(started, _role_of(self._definition, stage))
        sealed = self._stage_environment.run_agent(request, run=PatientRuns(self._boundaries).run)
        cost = self._costs.complete(begun, sealed.result)
        return LaunchedStage(
            started=started,
            request=request,
            result=sealed.result,
            cost=cost,
            nested_repositories=sealed.nested_repositories,
        )

    def _sync_time_limit(self) -> timedelta:
        sync = self._definition.project_commands.get("sync", ProjectCommandDefinition())
        return timedelta(minutes=sync.time_limit)

    def _launchable_stage(self, prepared: PreparedWorkItem) -> str:
        if prepared.merge_conflict:
            raise ValueError(f"{prepared.branch} has a merge conflict with the main branch")
        error = ValueError(f"the work item {prepared.work_item} has no state")
        return require_state(prepared.document, error).stage

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
    """A run the factory can keep: its decision, the taken work item, the entry and the form."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    decision: str
    document: WorkItemDocument
    entry: NewEntry
    take: TakeReport
    form_findings: list[FormFinding]
    cost: CostRun


class AfterAgent:
    """Turns a launched stage into what the factory observes, or into a stall."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        *,
        stage_environment: StageEnvironment | None = None,
    ) -> None:
        """Process as `instance` under `definition`, taking the result from `stage_environment`.

        By default the environment is the one the boundaries describe.
        """
        self._boundaries = boundaries
        self._definition = definition
        self._stage_environment = stage_environment or stage_environment_of(boundaries)
        self._stalls = StallService(
            boundaries, instance, definition, stage_environment=self._stage_environment
        )
        self._costs = CostRecorder(boundaries)

    def process(self, launched: LaunchedStage) -> AgentAftermath | StallResult:
        """Test the work tree, the branch and the result, take, build the entry, check the form.

        Stops at the first step that cannot be kept and stalls it, one attempt counted: first a
        git repository the agent left in the work tree, which the run already removed. The
        entry is not appended to the returned document.
        """
        started = launched.started
        result = launched.result
        early = self._early_stall(launched)
        if early is not None:
            return self._stall(launched, *early)
        decision = result.decision
        allowed = launched.request.allowed_decisions
        if decision is None or decision not in allowed:
            detail = f"decision '{decision}' is not one of {', '.join(allowed)}"
            return self._stall(launched, "decision_not_allowed", detail)
        take = self._stage_environment.take(started.stage_start, started.path)
        # The take leaves the sidecar like any path outside the write paths.
        self._costs.write(launched.cost)
        document = self._boundaries.work_item_reader.read(self._boundaries.checkout / started.path)
        entry = self._entry(started, decision, result.entry or "", take)
        if entry is None:
            return self._stall(launched, "no_result", "the entry is empty")
        findings = StoryFormChecker(self._boundaries).findings(document)
        new = _new_findings(started.findings, findings)
        if new:
            detail = "; ".join(finding.message for finding in new)
            appended = append_entry(
                document, entry, at=self._boundaries.clock.now(), run=launched.cost.run
            )
            return self._stall(launched, "form_invalid", detail, appended)
        return AgentAftermath(
            started=started,
            request=launched.request,
            result=result,
            decision=decision,
            document=document,
            entry=entry,
            take=take,
            form_findings=findings,
            cost=launched.cost,
        )

    def _early_stall(self, launched: LaunchedStage) -> tuple[StallReason, str] | None:
        # A nested repository goes first: it is gone already, and the stall must name it
        # whatever else the agent did.
        if launched.nested_repositories:
            return "nested_repository", ", ".join(launched.nested_repositories)
        if self._boundaries.git.status().branch != launched.started.branch:
            return "left_branch", ""
        reason = stall_reason_of(launched.result)
        if reason is not None:
            return reason, _first_denial(launched.result)
        return None

    def _entry(
        self, started: StartedStage, decision: str, text: str, take: TakeReport
    ) -> NewEntry | None:
        role = _role_of(self._definition, started.stage)
        # The factory rewrites its own cost records after the take; that is no news to the agent.
        sidecar = cost_records_path(started.path)
        undone = sorted(path for path in take.left if path != sidecar)
        return agent_entry(
            role=role, stage=started.stage, decision=decision, text=text, undone=undone
        )

    def _stall(
        self,
        launched: LaunchedStage,
        reason: StallReason,
        detail: str = "",
        document: WorkItemDocument | None = None,
    ) -> StallResult:
        started = launched.started
        context = StallContext(
            work_item=started.work_item,
            stage=started.stage,
            branch=started.branch,
            path=started.path,
            stage_start=started.stage_start,
            document=document,
            pull_request=started.pull_request,
            cost=launched.cost,
        )
        return self._stalls.stall(context, reason, detail)


class StageReport(BaseModel):
    """How a stage ended: the rule applied, the stage it leaves the work item in, its commit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    stage: Name
    next_stage: Name
    rule: Literal[1, 2, 3, 4, 5, 6, 7] | None
    commit: CommitId
    pull_request: PositiveInt
    stall: StallResult | None


class StageFinisher:
    """Decides, runs the checks and reports, then commits, pushes and labels the stage's result."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        *,
        stage_environment: StageEnvironment | None = None,
    ) -> None:
        """Finish as `instance` under `definition`; a stall takes from `stage_environment`.

        By default the environment is the one the boundaries describe.
        """
        self._boundaries = boundaries
        self._definition = definition
        self._claims = ClaimService(boundaries, instance, definition)
        self._stalls = StallService(
            boundaries,
            instance,
            definition,
            stage_environment=stage_environment or stage_environment_of(boundaries),
        )
        self._known_results = KnownResults(boundaries, definition)

    def finish(self, aftermath: AgentAftermath) -> StageReport:
        """Decide on the aftermath, run the checks and reports of a forward move, push the result.

        The first red check stalls the stage, rule 5. `PushFailed` from the push and a
        `HostingServiceError` from the label write after it propagate.
        """
        started = aftermath.started
        move = decide(
            self._definition,
            require_state(aftermath.document, _no_state()),
            aftermath.decision,
            aftermath.form_findings,
        )
        ran: list[CheckResult] = []
        if move.rule == 6:
            ran, red = self._run_checks_and_reports(started.stage)
            if red is not None:
                return self._stall_red(aftermath, ran, red)
        now = self._boundaries.clock.now()
        run = aftermath.cost.run
        entry = _with_command_lines(aftermath.entry, ran)
        agent_block = move.blocked if entry.kind == "question" else None
        document = append_entry(aftermath.document, entry, at=now, run=run, blocked=agent_block)
        if move.question is not None:
            question = NewEntry(speaker=FACTORY, kind="question", text=move.question)
            document = append_entry(document, question, at=now, run=run, blocked=move.blocked)
        moved = self._moved(document, move, started.pull_request.number)
        subject = commit_subject(started.work_item, f"{started.stage} ends: {move.stage}")
        approval = self._definition.stages[move.stage].approval
        commit = self._commit_and_push(started, moved, subject, describe=approval)
        self._boundaries.hosting.set_labels(
            started.pull_request.number, labels_for(require_state(moved, _no_state()))
        )
        return StageReport(
            work_item=started.work_item,
            stage=started.stage,
            next_stage=move.stage,
            rule=move.rule,
            commit=commit,
            pull_request=started.pull_request.number,
            stall=None,
        )

    def _run_checks_and_reports(
        self, stage_name: str
    ) -> tuple[list[CheckResult], CheckResult | None]:
        stage = self._definition.stages[stage_name]
        green: list[CheckResult] = []
        for check in stage.checks:
            result = self._known_results.run(check)
            if not result.passed:
                return green, result
            green.append(result)
        reports = [self._known_results.run(report) for report in stage.reports]
        return green + reports, None

    def _stall_red(
        self, aftermath: AgentAftermath, green: list[CheckResult], red: CheckResult
    ) -> StageReport:
        started = aftermath.started
        document = append_entry(
            aftermath.document,
            _with_command_lines(aftermath.entry, green),
            at=self._boundaries.clock.now(),
            run=aftermath.cost.run,
        )
        context = StallContext(
            work_item=started.work_item,
            stage=started.stage,
            branch=started.branch,
            path=started.path,
            stage_start=started.stage_start,
            document=document,
            pull_request=started.pull_request,
            cost=aftermath.cost,
        )
        tail = "\n".join(red.output_tail.splitlines()[-STALL_TAIL_LINES:])
        stall = self._stalls.stall(context, "check_red", f"`{red.command}`\n{tail}")
        return _stalled_report(started.work_item, started.stage, stall, rule=5)

    def _moved(
        self, document: WorkItemDocument, move: StageMove, pull_request: int
    ) -> WorkItemDocument:
        state = require_state(document, _no_state())
        moved_state = state.model_copy(
            update={
                "stage": move.stage,
                "blocked": move.blocked,
                "round": move.round,
                "pull_request": pull_request,
                # Only a forward move shows the stage works again, so only it forgives crashes.
                "crashes": 0 if move.rule == 6 else state.crashes,
            }
        )
        return self._claims.release(document.model_copy(update={"state": moved_state}))

    def _commit_and_push(
        self, started: StartedStage, document: WorkItemDocument, message: str, *, describe: bool
    ) -> CommitId:
        self._boundaries.work_item_writer.write(self._boundaries.checkout / started.path, document)
        git = self._boundaries.git
        commit = git.commit(message)
        if describe:
            self._describe(started, document)
        outcome = git.push(started.branch)
        if outcome != "pushed":
            raise PushFailed(started.branch, outcome)
        return commit

    def _describe(self, started: StartedStage, moved: WorkItemDocument) -> None:
        # The push shows the approval on the board; the description must already be complete.
        number = started.pull_request.number
        try:
            self._boundaries.hosting.set_description(number, self._description(started, moved))
        except HostingServiceError as error:
            # The hand-over on the next tick writes the same description again.
            self._boundaries.log.line(
                f"pull request #{number}: description not written before the push: {error}"
            )

    def _description(self, started: StartedStage, moved: WorkItemDocument) -> str:
        if is_acceptance(started.work_item):
            return acceptance_description(moved, _role_of(self._definition, started.stage))
        commits = self._boundaries.git.log("HEAD", since=f"origin/{MAIN_BRANCH}")
        return hand_over_description(moved, commits)


class StageRunner:
    """Runs one stage of a work item, every step in the same order, to a report."""

    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None:
        """Run as `instance` under `definition`; agent runs get `environment` unchanged."""
        self._opening = WorkItemOpening(boundaries, definition)
        # One object sees both ends of a stage: what it prepared is what it takes from.
        stage_environment = stage_environment_of(boundaries)
        self._stalls = StallService(
            boundaries, instance, definition, stage_environment=stage_environment
        )
        self._launcher = StageLauncher(
            boundaries, instance, definition, environment, stage_environment=stage_environment
        )
        self._after = AfterAgent(
            boundaries, instance, definition, stage_environment=stage_environment
        )
        self._finisher = StageFinisher(
            boundaries, instance, definition, stage_environment=stage_environment
        )

    def run(self, work_item: WorkItemId, path: str) -> StageReport:
        """Prepare, claim and run the agent, process its run, decide, check and push the result.

        A step that cannot be kept ends the run as a stall, reported with no rule.
        """
        prepared = self._opening.prepare(work_item, path)
        stage = require_state(prepared.document, _no_state()).stage
        if prepared.merge_conflict:
            context = StallContext(
                work_item=work_item,
                stage=stage,
                branch=prepared.branch,
                path=path,
                stage_start=None,
                document=prepared.document,
                pull_request=None,
            )
            stall = self._stalls.stall(context, "merge_conflict")
            return _stalled_report(work_item, stage, stall, rule=None)
        processed = self._after.process(self._launcher.launch(prepared))
        if isinstance(processed, StallResult):
            return _stalled_report(work_item, stage, processed, rule=None)
        return self._finisher.finish(processed)


def _no_state() -> ValueError:
    return ValueError("the work item has no state")


def _role_of(definition: PipelineDefinition, stage: str) -> str:
    role = definition.stages[stage].role
    if role is None:
        raise ValueError(f"stage {stage} has no role, so no agent runs there")
    return role


def _with_command_lines(entry: NewEntry, ran: list[CheckResult]) -> NewEntry:
    if not ran:
        return entry
    lines = "\n".join(command_line(result) for result in ran)
    return entry.model_copy(update={"text": f"{entry.text}\n\n{lines}"})


def _stalled_report(
    work_item: WorkItemId, stage: str, stall: StallResult, *, rule: Literal[5] | None
) -> StageReport:
    return StageReport(
        work_item=work_item,
        stage=stage,
        next_stage=stage,
        rule=rule,
        commit=stall.commit,
        pull_request=stall.pull_request,
        stall=stall,
    )


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
