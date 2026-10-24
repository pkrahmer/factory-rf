"""The fake snapshots the tests use: a folder whose base is a copy of it beside it."""

import os
import shutil
from pathlib import Path

from factory.application.snapshots import Snapshots
from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath

# The mode and the bytes of a file, or the mode and the target of a symbolic link.
_Entry = tuple[int, bytes]


class FakeSnapshots(Snapshots):
    """Snapshots on a folder: the base is a copy of it beside it."""

    def __init__(self, folder: Path, base: Path) -> None:
        """Work on `folder`, keeping its base as a copy at `base`."""
        self._folder = folder
        self._base = base

    @property
    def mount_point(self) -> Path:
        """The folder given."""
        return self._folder

    def reset(self) -> None:
        """Replace the folder's contents with a copy of the base; the folder itself stays."""
        self._require_base("reset")
        _clear(self._folder)
        shutil.copytree(self._base, self._folder, symlinks=True, dirs_exist_ok=True)

    def advance(self) -> None:
        """Replace the base with a copy of the folder."""
        if self._base.exists():
            shutil.rmtree(self._base)
        shutil.copytree(self._folder, self._base, symlinks=True)

    def changed_paths(self) -> list[ChangedPath]:
        """Every file and link whose bytes, mode or target differ from the base's, by path."""
        self._require_base("changed_paths")
        current = _entries(self._folder)
        base = _entries(self._base)
        changes: list[ChangedPath] = []
        for path in sorted(current.keys() | base.keys()):
            if path not in base:
                changes.append(ChangedPath(path=path, change="added"))
            elif path not in current:
                changes.append(ChangedPath(path=path, change="deleted"))
            elif current[path] != base[path]:
                changes.append(ChangedPath(path=path, change="modified"))
        return changes

    def _require_base(self, command: str) -> None:
        if not self._base.is_dir():
            raise SnapshotError(command, f"no base at {self._base}")


def _clear(folder: Path) -> None:
    for child in folder.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def _entries(root: Path) -> dict[str, _Entry]:
    entries: dict[str, _Entry] = {}
    # A link to a folder is listed among the folders and is not followed.
    for directory, folders, files in os.walk(root):
        for name in [*folders, *files]:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[relative] = (path.lstat().st_mode, os.fsencode(os.readlink(path)))
            elif not path.is_dir():
                entries[relative] = (path.stat().st_mode, path.read_bytes())
    return entries
