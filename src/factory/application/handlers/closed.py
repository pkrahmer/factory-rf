"""The closed handler: a close before the approval discards the story, at it sends it back."""

from datetime import UTC

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.comments import CommentCopier
from factory.application.handlers.recording import (
    Target,
    WorkItemRecorder,
    commit_subject,
    require_pull_request,
    target_of,
)
from factory.domain.archive import destination_path
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.journal import FACTORY, HUMAN, NewEntry, append_entry
from factory.domain.labels import labels_for
from factory.domain.paths import MAIN_BRANCH
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import CLOSE_ENTRY_TEXT, send_back_entry_text, send_back_question
from factory.domain.send_back import (
    reason_given,
    recorded_since_latest_result,
    send_back_cap,
    send_back_target,
)
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

_KIND = "closed"


def _state_of(document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise ValueError("a work item without a state cannot be sent back")
    return document.state


def _with_state(document: WorkItemDocument, **changes: object) -> WorkItemDocument:
    state = _state_of(document).model_copy(update=changes)
    return document.model_copy(update={"state": state})


class ClosedHandler(Handler):
    """Discards a story closed before its approval and sends back one closed at its approval."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Record through the boundaries' git; read the approval stages from the definition."""
        self._boundaries = boundaries
        self._definition = definition

    def handle(self, event: Event) -> None:
        """Send the story back at an approval stage, discard it before one; post nothing."""
        target = target_of(event)
        if self._definition.stages[target.state.stage].approval:
            self._send_back(target)
            return
        self._discard(target.snapshot)

    def _discard(self, snapshot: WorkItemSnapshot) -> None:
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(MAIN_BRANCH)
        # Moved, not rewritten: main holds the human's text, the branch the factory's.
        self._boundaries.git.move(snapshot.path, destination_path(snapshot.path, "backlog"))
        subject = commit_subject(snapshot.id, "closed before the approval, back in the backlog")
        recorder.publish(MAIN_BRANCH, subject)
        recorder.delete_branch(snapshot.branch)

    def _send_back(self, target: Target) -> None:
        pull_request = require_pull_request(target, _KIND)
        approval = target.state.stage
        stage = send_back_target(self._definition, approval)
        if stage is None:
            raise CannotHandle(_KIND, f"approval stage {approval} has no stage to send back to")
        cap = send_back_cap(self._definition, approval)
        # Recorded before the reopen, so that a failed reopen cannot lose the human's close.
        closed = self._record_close(target.snapshot, pull_request)
        hosting = self._boundaries.hosting
        hosting.reopen(pull_request)
        hosting.set_draft(pull_request, True)
        decided = self._record_decision(target.snapshot, closed, stage, cap)
        hosting.set_labels(pull_request, labels_for(_state_of(decided)))

    def _record_close(self, snapshot: WorkItemSnapshot, pull_request: int) -> WorkItemDocument:
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        document = recorder.read(snapshot.path)
        copier = CommentCopier(self._boundaries)
        closed = copier.append(document, copier.unread(_state_of(document), pull_request))
        # A retry after a failed reopen finds its close recorded and must not close again.
        if not recorded_since_latest_result(closed, "close"):
            on = self._boundaries.clock.now().astimezone(UTC).date()
            entry = NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=on)
            closed = append_entry(closed, entry)
        closed = _with_state(closed, handed_over=None)
        if closed != document:
            subject = commit_subject(snapshot.id, "close recorded")
            recorder.record(snapshot.branch, snapshot.path, closed, subject)
        return closed

    def _record_decision(
        self, snapshot: WorkItemSnapshot, closed: WorkItemDocument, stage: str, cap: int | None
    ) -> WorkItemDocument:
        new_round = _state_of(closed).round + 1
        text = send_back_entry_text(stage, new_round)
        decided = append_entry(closed, NewEntry(speaker=FACTORY, kind="send_back", text=text))
        question = send_back_question(new_round, cap, reason_given(closed))
        blocked = None
        if question is not None:
            entry = NewEntry(speaker=FACTORY, kind="question", text=question)
            decided = append_entry(decided, entry)
            blocked = "send_back"
        # Released here, not through the claim service, which needs an instance name.
        decided = _with_state(decided, stage=stage, round=new_round, claim=None, blocked=blocked)
        subject = commit_subject(snapshot.id, "sent back")
        WorkItemRecorder(self._boundaries).record(snapshot.branch, snapshot.path, decided, subject)
        return decided
