"""The walk that clears an agent's home of its own user's entries but the kept paths."""

import os
import stat
from collections.abc import Callable, Sequence
from pathlib import Path

from factory.domain.agent_home import fate, removed_when_empty


def own_entry(path: Path) -> bool:
    """Whether the entry at `path`, not followed if it is a link, belongs to this process's user."""
    return path.lstat().st_uid == os.geteuid()


def clear_home(
    home: Path, kept: Sequence[str], *, owned: Callable[[Path], bool] = own_entry
) -> list[str]:
    """Remove what `fate` gives `remove` and the folders left empty.

    Returns:
        The faults met, each `<relative>: <reason>`, in the order met.
    """
    walk = _Walk(home, kept, owned)
    walk.clear_folder(home)
    return walk.faults


class _Walk:
    def __init__(self, home: Path, kept: Sequence[str], owned: Callable[[Path], bool]) -> None:
        self.home = home
        self.kept = kept
        self.owned = owned
        self.faults: list[str] = []

    def clear_folder(self, folder: Path) -> None:
        try:
            entries = sorted(folder.iterdir(), key=lambda entry: entry.name)
        except OSError as error:
            self._record(folder, error)
            return
        for entry in entries:
            try:
                self._clear_entry(entry)
            except OSError as error:
                self._record(entry, error)

    def _clear_entry(self, entry: Path) -> None:
        relative = entry.relative_to(self.home).as_posix()
        # `lstat` so that a link to a folder is never taken for one, and never followed.
        folder = stat.S_ISDIR(entry.lstat().st_mode)
        owned = self.owned(entry)
        match fate(relative, owned=owned, folder=folder, kept=self.kept):
            case "remove":
                entry.unlink()
            case "descend":
                self._descend(entry, relative, owned=owned)
            case "keep":
                pass

    def _descend(self, folder: Path, relative: str, *, owned: bool) -> None:
        if owned:
            # An agent may have closed its own folder to itself; the owner can always reopen it.
            folder.chmod(stat.S_IMODE(folder.lstat().st_mode) | stat.S_IRWXU)
        self.clear_folder(folder)
        if removed_when_empty(relative, owned=owned, kept=self.kept) and _empty(folder):
            folder.rmdir()

    def _record(self, entry: Path, error: OSError) -> None:
        relative = entry.relative_to(self.home).as_posix()
        self.faults.append(f"{relative}: {error.strerror}")


def _empty(folder: Path) -> bool:
    return next(folder.iterdir(), None) is None
