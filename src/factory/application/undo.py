"""The undo that puts back every mark an agent may not leave, by the stage-start commit."""

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.write_paths import WritePathService
from factory.domain.agent_runs import GuardSettings
from factory.domain.errors import WorkItemFormatError
from factory.domain.git import ChangedPath
from factory.domain.journal import restore_state_and_journal
from factory.domain.paths import FEATURES_DIRECTORY
from factory.domain.work_item import WorkItemDocument
from factory.domain.write_paths import refusal

_IN_PROGRESS = "in-progress"


class UndoReport(BaseModel):
    """What an undo put back: the reverted and deleted paths and the work item's restore."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reverted: list[str]
    deleted: list[str]
    restored_work_item: bool


class UndoService:
    """Puts the work tree back wherever an agent left a mark outside what it may write."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Work through the git, the work item files and the checkout of `boundaries`."""
        self._boundaries = boundaries

    def undo(self, stage_start: StageStart, work_item_path: str) -> UndoReport:
        """Revert the refused paths, then restore the work item's state and journal.

        `WorkItemFormatError` naming `work_item_path` when the work item is absent or
        unreadable at the stage-start commit; the work tree is then left untouched.
        """
        settings = WritePathService(self._boundaries).at(stage_start, work_item_path)
        baseline = read_baseline(self._boundaries, stage_start.commit, work_item_path)
        refused = [
            change
            for change in self._boundaries.git.changed_paths(stage_start.commit)
            if is_refused(change.path, settings, work_item_path)
        ]
        if refused:
            paths = [change.path for change in refused]
            self._boundaries.git.revert_paths(stage_start.commit, paths)
        restored = restore_work_item(self._boundaries, stage_start.commit, work_item_path, baseline)
        return UndoReport(
            reverted=_paths_of(refused, added=False),
            deleted=_paths_of(refused, added=True),
            restored_work_item=restored,
        )


def read_baseline(boundaries: Boundaries, commit: str, work_item_path: str) -> WorkItemDocument:
    """The work item at `commit`; `WorkItemFormatError` naming it when absent or unreadable."""
    # Read before any path changes, so a fault here leaves the agent's work tree as it is.
    text = boundaries.git.show_file(commit, work_item_path)
    if text is None:
        raise WorkItemFormatError(f"missing at {commit}", work_item_path)
    try:
        return boundaries.work_item_reader.parse(text)
    except WorkItemFormatError as error:
        raise WorkItemFormatError(error.fault, work_item_path) from error


def restore_work_item(
    boundaries: Boundaries, commit: str, work_item_path: str, baseline: WorkItemDocument
) -> bool:
    """Put the checkout's work item's state and journal back from `baseline`; whether it changed.

    A deleted or unreadable work item comes back whole from `commit`.
    """
    target = boundaries.checkout / work_item_path
    try:
        current = boundaries.work_item_reader.read(target)
    except WorkItemFormatError:
        # A deleted or broken work item has no sections worth keeping: it comes back whole.
        boundaries.git.revert_paths(commit, [work_item_path])
        return True
    restored = restore_state_and_journal(current, baseline)
    if restored == current:
        return False
    boundaries.work_item_writer.write(target, restored)
    return True


def is_refused(path: str, settings: GuardSettings, work_item_path: str) -> bool:
    """Whether the role may not leave `path` changed: a refusal, or another in-progress file."""
    if refusal(path, settings) is not None:
        return True
    return path != work_item_path and _is_in_an_in_progress_folder(path)


def _is_in_an_in_progress_folder(path: str) -> bool:
    # On the string, not `folder_of`: that knows only work items, not cost records or notes.
    prefix = FEATURES_DIRECTORY + "/"
    if not path.startswith(prefix):
        return False
    segments = path.removeprefix(prefix).split("/")
    return len(segments) == 3 and segments[1] == _IN_PROGRESS


def _paths_of(changes: list[ChangedPath], *, added: bool) -> list[str]:
    return sorted({change.path for change in changes if (change.change == "added") == added})
