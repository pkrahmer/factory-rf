"""The recovery of an own crash: discard the dead stage's work, record the crash, rerun or ask."""

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
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.hosting import PostKey
from factory.domain.journal import FACTORY, NewEntry, append_entry, entry_text, last_record
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import crash_cap_question
from factory.domain.recovery import asking_crash_cap, at_crash_cap, crash_entry_text, crashed
from factory.domain.sections import title
from factory.domain.stops import StopPosted, WorkItemStop
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

_KIND = "crash"


def _state_of(work_item: str, document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise CannotHandle(_KIND, f"work item {work_item} has no state")
    return document.state


class RecoveryHandler(Handler):
    """Handles the crash of a stage this instance claimed: discard, record, push, rerun or ask.

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

        At the crash cap the crash-cap question is recorded with the crash and posted instead.
        """
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
        if _state_of(rerun.id, document).blocked == "crash_cap":
            self.ask_crash_cap(rerun)
            return
        self._run.handle(
            Event(
                kind="run",
                work_item=rerun,
                pull_request=event.pull_request,
                remote_state=commit,
            )
        )

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
        heading = title(document.body)
        # The same body and key as the ask handler's repost, so either one posts it only once.
        stop = WorkItemStop(
            key=PostKey(work_item=work_item.id, kind="crash_cap", n=str(question.number)),
            branch=work_item.branch,
            title=work_item.id if heading is None else f"{work_item.id}: {heading}",
            pull_request=state.pull_request,
            text=f"{FACTORY}: {entry_text(document, question.number)}",
        )
        posted = StopService(self._boundaries).post(stop)
        if posted.opened:
            self._record_pull_request(work_item, posted.pull_request)
        return posted

    def _record_pull_request(self, work_item: WorkItemSnapshot, number: int) -> None:
        recorder = WorkItemRecorder(self._boundaries)
        # The method may be called on its own, with the checkout on another branch.
        recorder.check_out(work_item.branch)
        document = recorder.read(work_item.path)
        state = _state_of(work_item.id, document)
        opened = document.model_copy(
            update={"state": state.model_copy(update={"pull_request": number})}
        )
        subject = commit_subject(work_item.id, "pull request opened")
        recorder.record(work_item.branch, work_item.path, opened, subject)

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
        crash_cap = self._definition.crash_cap
        capped = at_crash_cap(state, crash_cap)
        if capped:
            state = asking_crash_cap(state)
        document = target.snapshot.document.model_copy(update={"state": state})
        document = self._claims.release(document)
        stage = target.state.stage
        text = crash_entry_text(stage, state.crashes, head)
        document = append_entry(document, NewEntry(speaker=FACTORY, kind=_KIND, text=text))
        if not capped:
            return document
        # One commit holds the crash and the question, so neither is ever recorded alone.
        question = crash_cap_question(stage, state.crashes, crash_cap)
        return append_entry(document, NewEntry(speaker=FACTORY, kind="question", text=question))
