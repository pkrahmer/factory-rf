"""Give the owner back every folder and file under a test's tmp_path, so pytest can remove it."""

import os
import stat
from pathlib import Path

_FILE_BITS = stat.S_IRUSR | stat.S_IWUSR


def _add(path: Path, bits: int) -> None:
    mode = stat.S_IMODE(path.lstat().st_mode)
    if mode & bits != bits:
        path.chmod(mode | bits)


def reopen(root: Path) -> None:
    """Give the owner read, write and search on every folder under `root`, read and write elsewhere.

    Every other bit stays, the setgid bit included. Symbolic links are neither changed nor
    followed, and a missing `root` is no error.
    """
    if not os.path.lexists(root) or root.is_symlink():
        return
    if not root.is_dir():
        _add(root, _FILE_BITS)
        return
    _add(root, stat.S_IRWXU)
    for current, folders, files in os.walk(root, followlinks=False):
        base = Path(current)
        for name in folders:
            folder = base / name
            # os.walk lists a link to a folder among the folders; chmod would change its target.
            if not folder.is_symlink():
                _add(folder, stat.S_IRWXU)
        for name in files:
            entry = base / name
            if not entry.is_symlink():
                _add(entry, _FILE_BITS)
