"""The merged handler: a merged story is archived on main with its bill, then its branch goes."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import WorkItemRecorder, commit_subject, target_of
from factory.domain.archive import destination_path
from factory.domain.bills import bill
from factory.domain.errors import PushFailed
from factory.domain.events import Event
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.paths import MAIN_BRANCH, cost_records_path
from factory.domain.pipeline_definition import DONE_STAGE
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot


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
        self._move(snapshot.path)
        recorder.write(destination_path(snapshot.path, "done"), archived)
        recorder.publish(MAIN_BRANCH, commit_subject(snapshot.id, "merged, archived"))
        self._delete_branch(snapshot)

    def _archived(self, document: WorkItemDocument, path: str) -> WorkItemDocument:
        sidecar = self._boundaries.checkout / cost_records_path(path)
        text = done_entry_text(bill(self._boundaries.cost_reader.read(sidecar)))
        appended = append_entry(document, NewEntry(speaker=FACTORY, kind="done", text=text))
        if appended.state is None:
            raise ValueError(f"the work item at {path} has no state to archive")
        # The claim is dropped in the state: the merge ends the work, whoever held it.
        state = appended.state.model_copy(
            update={"stage": DONE_STAGE, "blocked": None, "claim": None}
        )
        return appended.model_copy(update={"state": state})

    def _move(self, path: str) -> None:
        git = self._boundaries.git
        destination = destination_path(path, "done")
        git.move(path, destination)
        sidecar = cost_records_path(path)
        if git.show_file("HEAD", sidecar) is not None:
            git.move(sidecar, cost_records_path(destination))

    def _delete_branch(self, snapshot: WorkItemSnapshot) -> None:
        git = self._boundaries.git
        outcome = git.delete_remote_branch(snapshot.branch)
        if outcome != "pushed":
            raise PushFailed(snapshot.branch, outcome)
        git.delete_branch(snapshot.branch)
