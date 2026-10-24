"""The take: what the stage's role may write goes from the dataset into the work tree."""

import os
import shutil
import stat
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.undo import is_refused, read_baseline, restore_work_item
from factory.application.write_paths import WritePathService
from factory.domain.git import ChangedPath, check_repository_path

_MOUNTED_CHECKOUT = "checkout"
_GIT_FOLDER = ".git"


class TakeReport(BaseModel):
    """What a take left in the dataset, and whether the work item's state and journal came back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    left: list[str]
    restored_work_item: bool


def copy_changed(source: Path, target: Path, changed: Sequence[ChangedPath]) -> None:
    """Mirror each of `changed` from the tree at `source` into the tree at `target`."""
    for change in changed:
        check_repository_path(change.path)
    for change in changed:
        entry = target / change.path
        _remove_entry(entry)
        if change.change != "deleted":
            _place(source / change.path, entry)


class TakeService:
    """Takes from the dataset into the work tree what the stage's role may write; the rest stays."""

    def __init__(self, boundaries: Boundaries, mount_point: Path) -> None:
        """Write into the checkout of `boundaries`, read the dataset mounted at `mount_point`."""
        self._boundaries = boundaries
        self._mount_point = mount_point

    def take(
        self, stage_start: StageStart, work_item_path: str, changed_paths: Sequence[ChangedPath]
    ) -> TakeReport:
        """Copy what the role may write, then restore the work item's state and journal.

        `WorkItemFormatError` naming `work_item_path` when the work item is absent or
        unreadable at the stage-start commit; the work tree is then left untouched.
        """
        baseline = read_baseline(self._boundaries, stage_start.commit, work_item_path)
        settings = WritePathService(self._boundaries).at(stage_start, work_item_path)
        candidates = self._candidates(changed_paths)
        left = sorted(
            {
                change.path
                for change in candidates
                if is_refused(change.path, settings, work_item_path)
            }
        )
        taken = [change for change in candidates if change.path not in left]
        copy_changed(self._mount_point / _MOUNTED_CHECKOUT, self._boundaries.checkout, taken)
        restored = work_item_path not in left and restore_work_item(
            self._boundaries, stage_start.commit, work_item_path, baseline
        )
        return TakeReport(left=left, restored_work_item=restored)

    def _candidates(self, changed_paths: Sequence[ChangedPath]) -> list[ChangedPath]:
        # The agent's home and the dataset's git are never the work tree's; what the host's
        # ignore rules ignore is the build's, never the agent's work.
        prefix = _MOUNTED_CHECKOUT + "/"
        inside = [
            ChangedPath(path=change.path.removeprefix(prefix), change=change.change)
            for change in changed_paths
            if change.path.startswith(prefix)
        ]
        outside_git = [
            change for change in inside if _GIT_FOLDER not in PurePosixPath(change.path).parts
        ]
        ignored = set(self._boundaries.git.ignored([change.path for change in outside_git]))
        return [change for change in outside_git if change.path not in ignored]


def _remove_entry(entry: Path) -> None:
    # A link goes as the link, never through it; a missing entry is no fault.
    if not os.path.lexists(entry):
        return
    if stat.S_ISDIR(entry.lstat().st_mode):
        shutil.rmtree(entry)
    else:
        entry.unlink()


def _place(source: Path, entry: Path) -> None:
    entry.parent.mkdir(parents=True, exist_ok=True)
    mode = source.lstat().st_mode
    if stat.S_ISLNK(mode):
        entry.symlink_to(source.readlink())
        return
    shutil.copyfile(source, entry, follow_symlinks=False)
    entry.chmod(stat.S_IMODE(mode))
