"""The recovery of a dead run: discard its work, record the crash or expiry, rerun or ask."""

from typing import Final

from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    target_of,
)
from factory.application.stops import StopService
from factory.domain.errors import CannotHandle
from factory.domain.events import Event, EventKind
from factory.domain.git import CommitId
from factory.domain.hosting import PostKey
from factory.domain.journal import (
    FACTORY,
    JournalKind,
    NewEntry,
    append_entry,
    entry_text,
    last_record,
)
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import crash_cap_question, expiry_note
from factory.domain.recovery import (
    asking_crash_cap,
    at_crash_cap,
    crash_entry_text,
    crashed,
    expiry_entry_text,
)
from factory.domain.sections import title
from factory.domain.stops import StopPosted, WorkItemStop
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

_KIND: Final = "crash"
_EXPIRED: Final = "expired"
# The claim status each handled event requires: an own claim crashed, another's expired.
_REQUIRED_STATUS: dict[EventKind, str] = {_KIND: "own", _EXPIRED: "expired"}


def _state_of(work_item: str, document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise CannotHandle(_KIND, f"work item {work_item} has no state")
    return document.state


class RecoveryHandler(Handler):
    """Handles a dead run: discard, record, push, rerun or ask.

    A `crash` is the end of a stage this instance claimed; an `expired` lease is another
    instance's claim that ran out, taken over as a crash and noted on the pull request.
    At the crash cap the stage is not rerun: the crash-cap question is recorded with the
    crash in one commit, pushed, and only then posted.
    """

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
        """Discard the dead stage's work back to the remote, record the crash, then rerun it.

        An expiry is recorded as such and noted on the pull request before the rerun. At the
        crash cap the crash-cap question is recorded with the crash and posted instead.
        """
        target = self._dead_run(event)
        snapshot = target.snapshot
        branch = snapshot.branch
        recorder = WorkItemRecorder(self._boundaries)
        # The remote holds everything worth keeping; the dead run's leftovers are not trusted.
        recorder.check_out(branch)
        head = self._remote_head(branch)
        entry_kind: JournalKind = "expiry" if event.kind == _EXPIRED else _KIND
        document = self._crash_recorded(target, head, entry_kind)
        subject = commit_subject(
            snapshot.id, f"{entry_kind} of stage {target.state.stage} recorded"
        )
        commit = recorder.record(branch, snapshot.path, document, subject)
        rerun = snapshot.model_copy(update={"branch_commit": commit, "document": document})
        if event.kind == _EXPIRED:
            rerun = self._note_expiry(rerun)
        if _state_of(rerun.id, rerun.document).blocked == "crash_cap":
            self.ask_crash_cap(rerun)
            return
        self._run.handle(
            Event(
                kind="run",
                work_item=rerun,
                pull_request=event.pull_request,
                remote_state=rerun.branch_commit,
            )
        )

    def _note_expiry(self, work_item: WorkItemSnapshot) -> WorkItemSnapshot:
        """Post the expiry note once and return the work item as last written."""
        document = work_item.document
        state = _state_of(work_item.id, document)
        expiry = last_record(document, speaker=FACTORY, kind="expiry")
        if expiry is None:
            raise CannotHandle(_EXPIRED, f"work item {work_item.id} has no expiry entry")
        stop = WorkItemStop(
            key=PostKey(work_item=work_item.id, kind="expiry", n=str(expiry.number)),
            branch=work_item.branch,
            title=_stop_title(work_item),
            pull_request=state.pull_request,
            text=expiry_note(state.crashes, self._definition.crash_cap),
        )
        posted = StopService(self._boundaries).post(stop)
        if not posted.opened:
            return work_item
        return self._record_pull_request(work_item, posted.pull_request)

    def ask_crash_cap(self, work_item: WorkItemSnapshot) -> StopPosted:
        """Post the recorded crash-cap question once, recording a newly opened pull request.

        Raises `CannotHandle` when the work item is not blocked on the crash cap or has no
        question by the factory; `HostingServiceError` from the post leaves it recorded.
        """
        state = _state_of(work_item.id, work_item.document)
        if state.blocked != "crash_cap":
            raise CannotHandle(_KIND, f"work item {work_item.id} is not blocked on the crash cap")
        document = work_item.document
        question = last_record(document, speaker=FACTORY, kind="question")
        if question is None:
            raise CannotHandle(_KIND, f"work item {work_item.id} has no question by the factory")
        # The same body and key as the ask handler's repost, so either one posts it only once.
        stop = WorkItemStop(
            key=PostKey(work_item=work_item.id, kind="crash_cap", n=str(question.number)),
            branch=work_item.branch,
            title=_stop_title(work_item),
            pull_request=state.pull_request,
            text=f"{FACTORY}: {entry_text(document, question.number)}",
        )
        posted = StopService(self._boundaries).post(stop)
        if posted.opened:
            self._record_pull_request(work_item, posted.pull_request)
        return posted

    def _record_pull_request(self, work_item: WorkItemSnapshot, number: int) -> WorkItemSnapshot:
        recorder = WorkItemRecorder(self._boundaries)
        # The method may be called on its own, with the checkout on another branch.
        recorder.check_out(work_item.branch)
        document = recorder.read(work_item.path)
        state = _state_of(work_item.id, document)
        opened = document.model_copy(
            update={"state": state.model_copy(update={"pull_request": number})}
        )
        subject = commit_subject(work_item.id, "pull request opened")
        commit = recorder.record(work_item.branch, work_item.path, opened, subject)
        return work_item.model_copy(update={"branch_commit": commit, "document": opened})

    def _dead_run(self, event: Event) -> Target:
        required = _REQUIRED_STATUS.get(event.kind)
        if required is None:
            raise CannotHandle(
                event.kind, f"the recovery handler handles {_KIND} and {_EXPIRED} events only"
            )
        target = target_of(event)
        work_item = target.snapshot.id
        status = self._claims.status(target.state)
        # Another instance's claim is not ours to take over until its lease has run out.
        if status != required:
            raise CannotHandle(
                event.kind, f"work item {work_item}'s claim is {status}, not {required}"
            )
        if target.snapshot.branch_commit is None:
            raise CannotHandle(event.kind, f"work item {work_item} has no branch on the remote")
        return target

    def _remote_head(self, branch: str) -> CommitId:
        head = self._boundaries.git.resolve(f"origin/{branch}")
        # The discard has just checked this ref out; the git interface only types it optional.
        if head is None:
            raise CannotHandle(_KIND, f"branch {branch} is gone from the remote")
        return head

    def _crash_recorded(
        self, target: Target, head: CommitId, entry_kind: JournalKind
    ) -> WorkItemDocument:
        state = crashed(target.state)
        crash_cap = self._definition.crash_cap
        capped = at_crash_cap(state, crash_cap)
        if capped:
            state = asking_crash_cap(state)
        document = target.snapshot.document.model_copy(update={"state": state})
        document = self._claims.release(document)
        stage = target.state.stage
        if entry_kind == "expiry":
            text = expiry_entry_text(stage, state.crashes, head)
        else:
            text = crash_entry_text(stage, state.crashes, head)
        document = append_entry(document, NewEntry(speaker=FACTORY, kind=entry_kind, text=text))
        if not capped:
            return document
        # One commit holds the crash and the question, so neither is ever recorded alone.
        question = crash_cap_question(stage, state.crashes, crash_cap)
        return append_entry(document, NewEntry(speaker=FACTORY, kind="question", text=question))


def _stop_title(work_item: WorkItemSnapshot) -> str:
    heading = title(work_item.document.body)
    return work_item.id if heading is None else f"{work_item.id}: {heading}"
