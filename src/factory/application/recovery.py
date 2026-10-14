"""The recovery of an own crash: discard the dead stage's work, record the crash, rerun at once."""

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    target_of,
)
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.recovery import crash_entry_text, crashed
from factory.domain.work_item import WorkItemDocument

_KIND = "crash"


class RecoveryHandler(Handler):
    """Handles the crash of a stage this instance claimed: discard, record, push and rerun."""

    def __init__(
        self,
        boundaries: Boundaries,
        definition: PipelineDefinition,
        claims: ClaimService,
        run: Handler,
    ) -> None:
        """Recover through the boundaries, judge claims with `claims` and rerun with `run`."""
        self._boundaries = boundaries
        self._definition = definition
        self._claims = claims
        self._run = run

    @property
    def run(self) -> Handler:
        """The handler that reruns the stage after the crash is recorded."""
        return self._run

    def handle(self, event: Event) -> None:
        """Discard the dead stage's work back to the remote, record the crash, then rerun it."""
        target = self._own_crash(event)
        snapshot = target.snapshot
        branch = snapshot.branch
        recorder = WorkItemRecorder(self._boundaries)
        # The remote holds everything worth keeping; the dead run's leftovers are not trusted.
        recorder.check_out(branch)
        head = self._remote_head(branch)
        document = self._crash_recorded(target, head)
        subject = commit_subject(snapshot.id, f"crash of stage {target.state.stage} recorded")
        commit = recorder.record(branch, snapshot.path, document, subject)
        rerun = snapshot.model_copy(update={"branch_commit": commit, "document": document})
        self._run.handle(
            Event(
                kind="run",
                work_item=rerun,
                pull_request=event.pull_request,
                remote_state=commit,
            )
        )

    def _own_crash(self, event: Event) -> Target:
        if event.kind != _KIND:
            raise CannotHandle(event.kind, f"the recovery handler handles {_KIND} events only")
        target = target_of(event)
        work_item = target.snapshot.id
        status = self._claims.status(target.state)
        # Only an own claim is a crash; another instance's claim is its lease's business.
        if status != "own":
            raise CannotHandle(_KIND, f"work item {work_item}'s claim is {status}, not own")
        if target.snapshot.branch_commit is None:
            raise CannotHandle(_KIND, f"work item {work_item} has no branch on the remote")
        return target

    def _remote_head(self, branch: str) -> CommitId:
        head = self._boundaries.git.resolve(f"origin/{branch}")
        # The discard has just checked this ref out; the git interface only types it optional.
        if head is None:
            raise CannotHandle(_KIND, f"branch {branch} is gone from the remote")
        return head

    def _crash_recorded(self, target: Target, head: CommitId) -> WorkItemDocument:
        state = crashed(target.state)
        document = target.snapshot.document.model_copy(update={"state": state})
        document = self._claims.release(document)
        text = crash_entry_text(target.state.stage, state.crashes, head)
        return append_entry(document, NewEntry(speaker=FACTORY, kind=_KIND, text=text))
