"""The snapshots of a plain directory: its base is a copy of it in a directory of its own."""

import os
import shutil
from collections.abc import Callable
from pathlib import Path

from factory.application.snapshots import Snapshots
from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath

# The bytes of a file are compared this many at a time, so a large file is never held whole.
_CHUNK_BYTES = 1024 * 1024

# The mode and the size of a file, or the mode and the target of a symbolic link.
_Entry = tuple[int, int | bytes]


class CopySnapshots(Snapshots):
    """Snapshots on a folder without a file system of snapshots: the base is a copy of it."""

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
        _as_snapshot_error("reset", self._copy_base_into_folder)

    def advance(self) -> None:
        """Replace the base with a copy of the folder."""
        _as_snapshot_error("advance", self._copy_folder_to_base)

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
            elif current[path] != base[path] or not self._same_bytes(path, current[path]):
                changes.append(ChangedPath(path=path, change="modified"))
        return changes

    def _require_base(self, command: str) -> None:
        if not self._base.is_dir():
            raise SnapshotError(command, f"no base at {self._base}")

    def _copy_base_into_folder(self) -> None:
        _clear(self._folder)
        shutil.copytree(self._base, self._folder, symlinks=True, dirs_exist_ok=True)

    def _copy_folder_to_base(self) -> None:
        if self._base.exists():
            shutil.rmtree(self._base)
        shutil.copytree(self._folder, self._base, symlinks=True)

    def _same_bytes(self, path: str, entry: _Entry) -> bool:
        # A link's target is in its entry already; only a file's bytes are left to compare.
        if isinstance(entry[1], bytes):
            return True
        return _same_file_bytes(self._folder / path, self._base / path)


def _as_snapshot_error(command: str, operation: Callable[[], None]) -> None:
    try:
        operation()
    except OSError as error:
        raise SnapshotError(command, str(error)) from error


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
                facts = path.stat()
                entries[relative] = (facts.st_mode, facts.st_size)
    return entries


def _same_file_bytes(first: Path, second: Path) -> bool:
    with first.open("rb") as first_file, second.open("rb") as second_file:
        while True:
            first_chunk = first_file.read(_CHUNK_BYTES)
            if first_chunk != second_file.read(_CHUNK_BYTES):
                return False
            if not first_chunk:
                return True
