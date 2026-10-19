"""The two waiters: the sleeping one, and the manual one that advances a manual clock."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from factory.adapters.clock import ManualClock, ManualWaiter, SleepingWaiter
from factory.application.machine import Waiter

START = datetime(2026, 10, 18, tzinfo=UTC)


def test_a_manual_wait_advances_the_clock_and_is_recorded() -> None:
    clock = ManualClock(START)
    waiter = ManualWaiter(clock)

    waiter.wait(timedelta(minutes=10))

    assert clock.now() == START + timedelta(minutes=10)
    assert waiter.waits == [timedelta(minutes=10)]


def _sleeping() -> Waiter:
    return SleepingWaiter()


def _manual() -> Waiter:
    return ManualWaiter(ManualClock(START))


@pytest.mark.parametrize("make", [_sleeping, _manual], ids=["sleeping", "manual"])
@pytest.mark.parametrize(
    ("duration", "refused"),
    [
        pytest.param(timedelta(0), False, id="zero"),
        pytest.param(timedelta(seconds=-1), True, id="minus-one-second"),
    ],
)
def test_a_wait_of_zero_returns_and_a_negative_one_is_refused(
    make: Callable[[], Waiter], *, duration: timedelta, refused: bool
) -> None:
    waiter = make()

    if refused:
        with pytest.raises(ValueError, match=r"."):
            waiter.wait(duration)
        return
    waiter.wait(duration)
