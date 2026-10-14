"""The reject handler: an illegal stage change is put back by a new commit on the branch."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import WorkItemRecorder, commit_subject, target_of
from factory.application.work_items import RemoteWorkItems
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.hosting import PostKey
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.labels import labels_for
from factory.domain.move_rule import StageChange
from factory.domain.post_texts import MOVED_BACK_MARKER, correction_note, move_back_entry_text
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

_KIND = "reject"


def _state_of(document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise CannotHandle(_KIND, "a work item without a state has no stage to move back")
    return document.state


class RejectHandler(Handler):
    """Puts an illegal stage change back on the work item's branch, never touching main."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read, record and post through the boundaries."""
        self._boundaries = boundaries

    def handle(self, event: Event) -> None:
        """Note the correction on the pull request, record the move back, then set the label."""
        snapshot = target_of(event).snapshot
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        change = self._illegal_change(snapshot)
        document = recorder.read(snapshot.path)
        state = _state_of(document)
        if state.pull_request is not None:
            self._post_note(snapshot.id, state, change, state.pull_request)
        moved_back = self._moved_back(document, change)
        text = f"stage {change.to_stage} -> {change.from_stage}, {MOVED_BACK_MARKER}"
        subject = commit_subject(snapshot.id, text)
        recorder.record(snapshot.branch, snapshot.path, moved_back, subject)
        if state.pull_request is not None:
            labels = labels_for(_state_of(moved_back))
            self._boundaries.hosting.set_labels(state.pull_request, labels)

    def _illegal_change(self, snapshot: WorkItemSnapshot) -> StageChange:
        # The same source the watcher judged, so the handler corrects what was rejected.
        work_items = RemoteWorkItems(self._boundaries.git, self._boundaries.work_item_reader)
        change = work_items.last_stage_change(snapshot)
        if change is None:
            raise CannotHandle(_KIND, f"work item {snapshot.id} has no stage change to move back")
        if change.correction:
            raise CannotHandle(_KIND, f"work item {snapshot.id}'s stage change is a correction")
        return change

    def _post_note(
        self, work_item: str, state: WorkItemState, change: StageChange, pull_request: int
    ) -> None:
        # Posted before the record and keyed by the entry to come, so a retry posts no twin.
        key = PostKey(work_item=work_item, kind="correction", n=str(len(state.journal) + 1))
        text = correction_note(change.from_stage, change.to_stage)
        self._boundaries.hosting.post_comment(pull_request, text, key)

    def _moved_back(self, document: WorkItemDocument, change: StageChange) -> WorkItemDocument:
        text = move_back_entry_text(change.from_stage, change.to_stage)
        appended = append_entry(document, NewEntry(speaker=FACTORY, kind="move_back", text=text))
        # A claim is for the stage at the branch's head, so it never outlives the move back.
        state = _state_of(appended).model_copy(update={"stage": change.from_stage, "claim": None})
        return appended.model_copy(update={"state": state})
