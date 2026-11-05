"""The interfaces to the machine: its clock, the log, health status, disks, readings and power."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

from factory.pipeline.domain.stops import HealthStatus
from factory.watching.domain.machine import MachineTotals


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


class MachineReadings(ABC):
    """Reads what the kernel counts for the user whose containers the factory runs."""

    @abstractmethod
    def totals(self) -> MachineTotals:
        """The running totals of CPU time and of the waits for a CPU and for memory now."""

    @abstractmethod
    def memory_peak_bytes(self) -> int | None:
        """The high-water mark of the user's memory since its slice began; `None` when unread."""

    @abstractmethod
    def memory_total_bytes(self) -> int | None:
        """The machine's memory in bytes; `None` when unread."""


class PowerOff(ABC):
    """The machine's power, which the factory may switch off."""

    @abstractmethod
    def power_off(self) -> None:
        """Ask the machine to power off; `PowerOffError` when it cannot be asked or refuses."""
