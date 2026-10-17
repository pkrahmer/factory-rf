"""The free space of a file system and the bytes a folder takes, read with the standard library."""

import os
import shutil
import stat
from pathlib import Path
from typing import override

from factory.application.machine import DiskSpace


class ShutilDiskSpace(DiskSpace):
    """Reads the free space with `shutil.disk_usage` and walks folders for their size."""

    @override
    def free_bytes(self, path: Path) -> int:
        return shutil.disk_usage(path).free

    @override
    def used_bytes(self, path: Path) -> int:
        total = 0
        for folder, _folders, files in os.walk(path, followlinks=False):
            for name in files:
                total += _regular_file_size(Path(folder) / name)
        return total


def _regular_file_size(path: Path) -> int:
    # `lstat` neither follows a link nor opens a named pipe.
    status = path.lstat()
    return status.st_size if stat.S_ISREG(status.st_mode) else 0
