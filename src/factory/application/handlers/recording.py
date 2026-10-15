"""The plumbing every handler shares: the event's target and the recorder of a work item."""

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.domain.archive import destination_path
from factory.domain.errors import CannotHandle, PushFailed
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.paths import LifecycleFolder, cost_records_path
from factory.domain.work_item import (
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    require_state,
)


class Target(BaseModel):
    """The work item an event is about, its state and its pull request, if it has one."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot: WorkItemSnapshot
    state: WorkItemState
    pull_request: int | None


def target_of(event: Event) -> Target:
    """Return the event's target; `CannotHandle` without a work item or without a state."""
    snapshot = event.work_item
    if snapshot is None:
        raise CannotHandle(event.kind, "the event names no work item")
    error = CannotHandle(event.kind, f"work item {snapshot.id} has no state")
    state = require_state(snapshot.document, error)
    return Target(snapshot=snapshot, state=state, pull_request=state.pull_request)


def require_pull_request(target: Target, kind: str) -> int:
    """Return the target's pull request number; `CannotHandle` of `kind` when it has none."""
    if target.pull_request is None:
        raise CannotHandle(kind, f"work item {target.snapshot.id} has no pull request")
    return target.pull_request


def commit_subject(work_item: str, text: str) -> str:
    """Return the subject of a commit a handler makes for the work item."""
    return f"work item {work_item}: {text}"


def move_with_cost_records(git: Git, path: str, folder: LifecycleFolder) -> str:
    """Move the work item at `path` and its cost records, if any, to `folder`; return the path."""
    destination = destination_path(path, folder)
    git.move(path, destination)
    sidecar = cost_records_path(path)
    if git.show_file("HEAD", sidecar) is not None:
        git.move(sidecar, cost_records_path(destination))
    return destination


class WorkItemRecorder:
    """Records a change of a work item in its branch: check out, read, write, commit and push."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Record through the boundaries' git, work item reader and writer, in their checkout."""
        self._boundaries = boundaries

    def check_out(self, branch: str) -> None:
        """Stand on `branch` at the remote's head, with every local leftover gone."""
        git = self._boundaries.git
        remote_head = f"origin/{branch}"
        # A killed handler may have left a change that `checkout` would refuse to overwrite.
        git.reset_to("HEAD")
        git.checkout(branch, start_point=remote_head)
        git.reset_to(remote_head)

    def read(self, path: str) -> WorkItemDocument:
        """Read the work item at `path` in the checkout."""
        return self._boundaries.work_item_reader.read(self._boundaries.checkout / path)

    def write(self, path: str, document: WorkItemDocument) -> None:
        """Write the document as the work item at `path` in the checkout."""
        self._boundaries.work_item_writer.write(self._boundaries.checkout / path, document)

    def delete_branch(self, branch: str) -> None:
        """Delete `branch` on the remote, then locally; `PushFailed` if the remote refuses."""
        git = self._boundaries.git
        outcome = git.delete_remote_branch(branch)
        if outcome != "pushed":
            raise PushFailed(branch, outcome)
        git.delete_branch(branch)

    def publish(self, branch: str, subject: str) -> CommitId:
        """Commit every change with `subject` and push `branch`; `PushFailed` unless pushed."""
        git = self._boundaries.git
        commit = git.commit(subject)
        outcome = git.push(branch)
        if outcome != "pushed":
            raise PushFailed(branch, outcome)
        return commit

    def record(self, branch: str, path: str, document: WorkItemDocument, subject: str) -> CommitId:
        """Write the document at `path`, then commit and push it as `publish` does."""
        self.write(path, document)
        return self.publish(branch, subject)
