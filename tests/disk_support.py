"""A fake of the disk-space interface, told per path what to answer."""

from collections.abc import Mapping
from pathlib import Path

from factory.application.machine import DiskSpace


class FakeDiskSpace(DiskSpace):
    """Answers each path with the byte count it was given, or raises the `OSError` it was given.

    Every path asked, of either operation, is kept in `asked`, in order.
    """

    def __init__(
        self,
        free: Mapping[Path, int | OSError] | None = None,
        used: Mapping[Path, int | OSError] | None = None,
    ) -> None:
        self.free: dict[Path, int | OSError] = dict(free or {})
        self.used: dict[Path, int | OSError] = dict(used or {})
        self.asked: list[Path] = []

    def free_bytes(self, path: Path) -> int:
        self.asked.append(path)
        return _answer(self.free[path])

    def used_bytes(self, path: Path) -> int:
        self.asked.append(path)
        return _answer(self.used[path])


def _answer(given: int | OSError) -> int:
    if isinstance(given, OSError):
        raise given
    return given
