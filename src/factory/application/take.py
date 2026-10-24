"""The take that copies from the dataset into the work tree what the stage's role may write."""

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

DATASET_CHECKOUT = "checkout"
GIT_FOLDER = ".git"


class TakeReport(BaseModel):
    """What a take left in the dataset, and whether the work item's state and journal came back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    left: list[str]
    restored_work_item: bool


def copy_changed(source: Path, target: Path, changed: Sequence[ChangedPath]) -> None:
    """Mirror each of `changed` from the tree at `source` into the tree at `target`.

    A file keeps its bytes and mode, a link its target text; no link is ever followed, and
    whatever stood at the target is removed first. A path that is absolute or holds a `..`
    segment raises `ValueError` before anything is copied.
    """
    for change in changed:
        check_repository_path(change.path)
    for change in changed:
        _remove_entry(target / change.path)
        if change.change != "deleted":
            _place_entry(source / change.path, target / change.path)


class TakeService:
    """Takes from the dataset into the work tree what the stage's role may write; the rest stays."""

    def __init__(self, boundaries: Boundaries, mount_point: Path) -> None:
        """Take into the checkout of `boundaries` from the dataset mounted at `mount_point`."""
        self._boundaries = boundaries
        self._mount_point = mount_point

    def take(
        self, stage_start: StageStart, work_item_path: str, changed_paths: Sequence[ChangedPath]
    ) -> TakeReport:
        """Copy the changed paths the role may write, then restore the work item's state.

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
        copy_changed(self._mount_point / DATASET_CHECKOUT, self._boundaries.checkout, taken)
        restored = work_item_path not in left and restore_work_item(
            self._boundaries, stage_start.commit, work_item_path, baseline
        )
        return TakeReport(left=left, restored_work_item=restored)

    def _candidates(self, changed_paths: Sequence[ChangedPath]) -> list[ChangedPath]:
        in_checkout = [
            ChangedPath(path=path, change=change.change)
            for change in changed_paths
            if (path := _in_dataset_checkout(change.path)) is not None
            and GIT_FOLDER not in PurePosixPath(path).parts
        ]
        # The host's own ignore rules decide, never the dataset's git, which the agent could edit.
        ignored = set(self._boundaries.git.ignored([change.path for change in in_checkout]))
        return [change for change in in_checkout if change.path not in ignored]


def _in_dataset_checkout(path: str) -> str | None:
    prefix = DATASET_CHECKOUT + "/"
    return path.removeprefix(prefix) if path.startswith(prefix) else None


def _remove_entry(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if stat.S_ISDIR(path.lstat().st_mode):
        shutil.rmtree(path)
    else:
        path.unlink()


def _place_entry(source: Path, target: Path) -> None:
    if not os.path.lexists(source):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
        return
    shutil.copyfile(source, target, follow_symlinks=False)
    shutil.copymode(source, target, follow_symlinks=False)
