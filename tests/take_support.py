"""Shared helpers of the take tests: a dataset beside the host's checkout, and its snapshot."""

import shutil
import stat
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.take import TakeReport, TakeService
from factory.domain.git import ChangedPath
from undo_support import PATH

DATASET = "dataset"
MOUNTED = "checkout"
AGENT_TEXT = "written by the agent\n"

Tree = dict[str, tuple[str, int, bytes]]


def make_dataset(boundaries: Boundaries, tmp_path: Path) -> Path:
    """Copy the host's checkout without its `.git` into `<tmp_path>/dataset/checkout`.

    Return the dataset folder, the take's mount point.
    """
    mount_point = tmp_path / DATASET
    shutil.copytree(
        boundaries.checkout,
        mount_point / MOUNTED,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git"),
    )
    return mount_point


def write_dataset(mount_point: Path, files: dict[str, str]) -> None:
    """Write each text of `files` at its path under the dataset, as the agent would have."""
    for name, text in files.items():
        path = mount_point / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))


def changes(*pairs: tuple[str, str]) -> list[ChangedPath]:
    """The changed paths of `(path, change)` pairs, in the order given."""
    return [ChangedPath.model_validate({"path": path, "change": change}) for path, change in pairs]


def run_take(
    boundaries: Boundaries, start: StageStart, mount_point: Path, changed: list[ChangedPath]
) -> TakeReport:
    """Take from the dataset at `mount_point` for the work item of `start_stage`."""
    return TakeService(boundaries, mount_point).take(start, PATH, changed)


def tree(root: Path, *, skip_git: bool = False) -> Tree:
    """Every entry under `root`: its kind, its mode and its bytes or link text."""
    entries: Tree = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if skip_git and ".git" in path.relative_to(root).parts:
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            entries[name] = ("link", 0, str(path.readlink()).encode())
        elif stat.S_ISDIR(mode):
            entries[name] = ("folder", stat.S_IMODE(mode), b"")
        else:
            entries[name] = ("file", stat.S_IMODE(mode), path.read_bytes())
    return entries
