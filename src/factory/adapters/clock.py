"""The system clock, and the manual clock that tests advance by hand."""

from datetime import UTC, datetime, timedelta
from typing import override

from factory.application.machine import Clock


class SystemClock(Clock):
    """The machine's own clock, in UTC."""

    @override
    def now(self) -> datetime:
        return datetime.now(UTC)


class ManualClock(Clock):
    """A clock that stands still until it is advanced."""

    def __init__(self, start: datetime) -> None:
        """Start at `start`, which must be timezone-aware; a naive start raises `ValueError`."""
        if start.utcoffset() is None:
            raise ValueError("a manual clock needs a timezone-aware start")
        self._now = start.astimezone(UTC)

    @override
    def now(self) -> datetime:
        return self._now

    def advance(self, by: timedelta) -> None:
        """Move the clock forward by `by`."""
        self._now += by
