"""The merged handler: a merged story is archived on main with its bill, then its branch goes."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    WorkItemRecorder,
    commit_subject,
    move_with_cost_records,
    target_of,
)
from factory.domain.bills import bill
from factory.domain.events import Event
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.paths import MAIN_BRANCH, cost_records_path
from factory.domain.pipeline_definition import DONE_STAGE
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument, require_state


class MergedHandler(Handler):
    """Archives a merged story under `done/` on main, then deletes its branch; posts nothing."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Record through the boundaries' git, work item and cost record readers and writers."""
        self._boundaries = boundaries

    def handle(self, event: Event) -> None:
        """Archive the story with its bill on main, push it, then delete its branch."""
        snapshot = target_of(event).snapshot
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(MAIN_BRANCH)
        archived = self._archived(recorder.read(snapshot.path), snapshot.path)
        destination = move_with_cost_records(self._boundaries.git, snapshot.path, "done")
        recorder.write(destination, archived)
        recorder.publish(MAIN_BRANCH, commit_subject(snapshot.id, "merged, archived"))
        recorder.delete_branch(snapshot.branch)

    def _archived(self, document: WorkItemDocument, path: str) -> WorkItemDocument:
        sidecar = self._boundaries.checkout / cost_records_path(path)
        text = done_entry_text(bill(self._boundaries.cost_reader.read(sidecar)))
        appended = append_entry(document, NewEntry(speaker=FACTORY, kind="done", text=text))
        error = ValueError(f"the work item at {path} has no state to archive")
        # The claim is dropped in the state: the merge ends the work, whoever held it.
        state = require_state(appended, error).model_copy(
            update={"stage": DONE_STAGE, "blocked": None, "claim": None}
        )
        return appended.model_copy(update={"state": state})
