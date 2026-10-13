"""The interfaces to the machine: its clock, the factory log and the health status store."""

from abc import ABC, abstractmethod
from datetime import datetime

from factory.domain.stops import HealthStatus


class Clock(ABC):
    """Tells the time; the factory reads no clock of its own."""

    @abstractmethod
    def now(self) -> datetime:
        """The current time, timezone-aware, in UTC."""


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
