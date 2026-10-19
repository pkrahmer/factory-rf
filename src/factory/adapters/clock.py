"""The system clock and the sleeping waiter, and the manual clock and waiter tests advance."""

import time
from datetime import UTC, datetime, timedelta
from typing import override

from factory.application.machine import Clock, Waiter


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


class SleepingWaiter(Waiter):
    """Waits by sleeping."""

    @override
    def wait(self, duration: timedelta) -> None:
        _refuse_negative(duration)
        time.sleep(duration.total_seconds())


class ManualWaiter(Waiter):
    """Waits by advancing a manual clock at once, and records each wait."""

    def __init__(self, clock: ManualClock) -> None:
        """Advance `clock` on each wait."""
        self._clock = clock
        self._waits: list[timedelta] = []

    @property
    def waits(self) -> list[timedelta]:
        """The waits so far, in order."""
        return list(self._waits)

    @override
    def wait(self, duration: timedelta) -> None:
        _refuse_negative(duration)
        self._clock.advance(duration)
        self._waits.append(duration)


def _refuse_negative(duration: timedelta) -> None:
    if duration < timedelta(0):
        raise ValueError(f"a wait cannot be negative, got {duration}")
