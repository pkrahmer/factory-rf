"""The interface through which the factory resets, advances and compares the stage's dataset."""

from abc import ABC, abstractmethod
from pathlib import Path

from factory.domain.git import ChangedPath


class Snapshots(ABC):
    """One dataset and its base snapshot: the reset to it, the move of it, the diff against it."""

    @property
    @abstractmethod
    def mount_point(self) -> Path:
        """The dataset's path on the host; `changed_paths` are relative to it."""

    @abstractmethod
    def reset(self) -> None:
        """Put the dataset back to the base; `SnapshotError` without a base or on a tool fault."""

    @abstractmethod
    def advance(self) -> None:
        """Move the base to the dataset's current state; `SnapshotError` when the tool fails."""

    @abstractmethod
    def changed_paths(self) -> list[ChangedPath]:
        """Every non-directory entry that differs from the base, relative to the mount point.

        Sorted by path. Added, modified and deleted entries; a rename is a deletion and an addition.
        `SnapshotError` when there is no base or the tool fails.
        """
