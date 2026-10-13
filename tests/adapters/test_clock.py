"""The system clock and the manual clock the tests advance."""

from datetime import datetime, timedelta, timezone

import pytest

from factory.adapters.clock import ManualClock, SystemClock


def test_the_clocks_tell_aware_utc_time() -> None:
    start = datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    clock = ManualClock(start)

    first = clock.now()
    assert first == start
    assert first.utcoffset() == timedelta(0)
    assert clock.now() == first

    clock.advance(timedelta(seconds=5))

    assert clock.now() == start + timedelta(seconds=5)
    assert clock.now().utcoffset() == timedelta(0)

    system = SystemClock().now()
    assert system.tzinfo is not None
    assert system.utcoffset() == timedelta(0)


def test_a_manual_clock_refuses_a_naive_start() -> None:
    with pytest.raises(ValueError, match=r"."):
        ManualClock(datetime(2026, 10, 12, 12, 0))  # noqa: DTZ001
