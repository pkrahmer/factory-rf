"""The stall: a stage ended without a result, its kept writes committed and the stall said."""

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService, StageStart
from factory.application.costs import CostRecorder, CostRun
from factory.application.handlers.recording import commit_subject
from factory.application.opening import WorkItemOpening
from factory.application.undo import UndoReport, UndoService
from factory.domain.decisions import StallReason
from factory.domain.errors import PushFailed
from factory.domain.git import CommitId
from factory.domain.hosting import PostKey, PostOutcome, PullRequestView
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.labels import labels_for
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import stall_cause, stall_note
from factory.domain.work_item import WorkItemDocument, require_state


class StallContext(BaseModel):
    """The stalled stage: its work item, branch and file, and what the caller already holds."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    stage: Name
    branch: str
    path: str
    stage_start: StageStart | None
    document: WorkItemDocument | None = None
    pull_request: PullRequestView | None = None
    cost: CostRun | None = None


class StallResult(BaseModel):
    """What a stall did: the counted attempt, the pushed commit, the note and the undo."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: StallReason
    attempts: PositiveInt
    attempts_cap: PositiveInt
    commit: CommitId
    pull_request: PositiveInt
    note: PostOutcome
    undo: UndoReport | None


class StallService:
    """Ends a stage as a stall: undo, one attempt counted, claim released, pushed, then said."""

    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None:
        """Stall as `instance`, counting attempts against the cap of `definition`."""
        self._boundaries = boundaries
        self._definition = definition
        self._claims = ClaimService(boundaries, instance, definition)
        self._opening = WorkItemOpening(boundaries, definition)

    def stall(self, context: StallContext, reason: StallReason, detail: str = "") -> StallResult:
        """Undo, commit and push the stall, then post its note on the pull request.

        `PushFailed` when the push does not reach the remote, before any note. A
        `HostingServiceError` propagates: from the pull request before anything is written,
        from the note or the labels after the push.
        """
        undo = None if context.stage_start is None else self._undo(context, context.stage_start)
        if context.cost is not None:
            # The undo reverts the sidecar like any path outside the write paths.
            CostRecorder(self._boundaries).write(context.cost)
        document = context.document or self._read(context.path)
        pull_request = context.pull_request or self._opening.ensure_pull_request(
            context.work_item, document
        )
        cap = self._definition.attempts_cap
        stalled = self._stalled(document, context, pull_request.number, reason, detail)
        state = require_state(stalled, _no_state())
        commit = self._commit_and_push(context, stalled)
        key = PostKey(work_item=context.work_item, kind="stall", n=str(len(state.journal)))
        note = self._boundaries.hosting.post_comment(
            pull_request.number, stall_note(reason, state.attempts, cap, detail=detail), key
        )
        self._boundaries.hosting.set_labels(pull_request.number, labels_for(state))
        return StallResult(
            reason=reason,
            attempts=state.attempts,
            attempts_cap=cap,
            commit=commit,
            pull_request=pull_request.number,
            note=note,
            undo=undo,
        )

    def _undo(self, context: StallContext, stage_start: StageStart) -> UndoReport:
        git = self._boundaries.git
        if git.status().branch != context.branch:
            # Whatever the agent left on the other branch is dropped; its commits stay there.
            git.reset_to("HEAD")
            git.checkout(context.branch, start_point=stage_start.commit)
        return UndoService(self._boundaries).undo(stage_start, context.path)

    def _read(self, path: str) -> WorkItemDocument:
        return self._boundaries.work_item_reader.read(self._boundaries.checkout / path)

    def _stalled(
        self,
        document: WorkItemDocument,
        context: StallContext,
        pull_request: int,
        reason: StallReason,
        detail: str,
    ) -> WorkItemDocument:
        state = require_state(document, _no_state())
        attempts = state.attempts + 1
        counted_state = state.model_copy(
            update={"attempts": attempts, "pull_request": pull_request}
        )
        released = self._claims.release(document.model_copy(update={"state": counted_state}))
        cap = self._definition.attempts_cap
        cause = stall_cause(reason, detail)
        text = f"Stage {context.stage} stalled (attempt {attempts} of {cap}): {cause}"
        entry = NewEntry(speaker=FACTORY, kind="stall", text=text)
        run = None if context.cost is None else context.cost.run
        return append_entry(
            released, entry, at=self._boundaries.clock.now(), run=run, reason=reason
        )

    def _commit_and_push(self, context: StallContext, document: WorkItemDocument) -> CommitId:
        self._boundaries.work_item_writer.write(self._boundaries.checkout / context.path, document)
        git = self._boundaries.git
        commit = git.commit(commit_subject(context.work_item, f"{context.stage} stalled"))
        outcome = git.push(context.branch)
        if outcome != "pushed":
            raise PushFailed(context.branch, outcome)
        return commit


def _no_state() -> ValueError:
    return ValueError("the work item has no state to stall")
