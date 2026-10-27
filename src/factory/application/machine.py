"""The interfaces to the machine: its clock, the log, the health status store, disks and power."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

from factory.domain.stops import HealthStatus


class Clock(ABC):
    """Tells the time; the factory reads no clock of its own."""

    @abstractmethod
    def now(self) -> datetime:
        """The current time, timezone-aware, in UTC."""


class Waiter(ABC):
    """Waits for a time without holding anything; the factory has no sleep of its own."""

    @abstractmethod
    def wait(self, duration: timedelta) -> None:
        """Return after `duration`; a negative one raises `ValueError`."""


class FactoryLog(ABC):
    """The operator's log of what the factory does."""

    @abstractmethod
    def line(self, text: str) -> None:
        """Write each line of `text` time-stamped to standard output and the factory log file."""


class HealthStatusStore(ABC):
    """Keeps the health status the container's health check reads."""

    @abstractmethod
    def read(self) -> HealthStatus:
        """The stored status; a missing, unreadable or invalid store reads as `HealthStatus()`."""

    @abstractmethod
    def write(self, status: HealthStatus) -> None:
        """Replace the stored status with `status`; a failed write raises `OSError`."""


class DiskSpace(ABC):
    """Tells how much room the file systems have and how much a folder takes."""

    @abstractmethod
    def free_bytes(self, path: Path) -> int:
        """The bytes an unprivileged user may still write on the file system of `path`.

        Raises `OSError` when it cannot be read.
        """

    @abstractmethod
    def used_bytes(self, path: Path) -> int:
        """The sizes of the regular files under `path`; 0 for a missing path.

        Symbolic links and other non-regular files are skipped.
        """


class PowerOff(ABC):
    """The machine's power, which the factory may switch off."""

    @abstractmethod
    def power_off(self) -> None:
        """Ask the machine to power off; `PowerOffError` when it cannot be asked or refuses."""
