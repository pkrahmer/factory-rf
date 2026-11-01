"""The idle shutdown: the stretch of idle ticks, the power-off at its limit, a refusal."""

from datetime import datetime, timedelta

import pytest

from factory.adapters.clock import ManualClock
from factory.application.idle_shutdown import IdleShutdown
from factory.application.tick import TickOutcome
from factory.domain.errors import PowerOffError
from power_support import IDLE, IDLE_ERROR, OTHER, STOPPED, WAITS, CountingPower
from recording_log import RecordingLog

LIMIT = timedelta(minutes=30)
REFUSAL = "sudo: a password is required"
PREFIX = "idle shutdown: "

# (minutes, seconds after the object was made, outcome, calls of power_off after it)
Step = tuple[int, int, TickOutcome, int]


def _at(clock: ManualClock, made: datetime, minutes: int, seconds: int) -> None:
    clock.advance(made + timedelta(minutes=minutes, seconds=seconds) - clock.now())


@pytest.mark.parametrize(
    "steps",
    [
        pytest.param([(0, 0, IDLE, 0), (29, 0, IDLE, 0), (29, 59, IDLE, 0)], id="below-the-limit"),
        pytest.param([(30, 0, IDLE, 1)], id="at-the-limit"),
        pytest.param([(30, 0, WAITS, 1)], id="waiting-for-the-human"),
        pytest.param(
            [(30, 0, IDLE, 1), (59, 59, IDLE, 1), (60, 0, IDLE, 2)], id="a-new-stretch-after-it"
        ),
        pytest.param(
            [(5, 0, IDLE, 0), (10, 0, OTHER, 0), (39, 59, IDLE, 0), (40, 0, IDLE, 1)],
            id="another-event-ends-the-stretch",
        ),
        pytest.param(
            [(20, 0, STOPPED, 0), (49, 59, IDLE, 0), (50, 0, IDLE, 1)],
            id="a-stop-ends-the-stretch",
        ),
        pytest.param([(30, 0, IDLE_ERROR, 0)], id="an-idle-error-is-not-idle"),
        pytest.param([(31, 0, IDLE, 1)], id="the-first-stretch-starts-when-made"),
    ],
)
def test_the_machine_powers_off_after_an_idle_stretch_of_the_limit(
    clock: ManualClock, steps: list[Step]
) -> None:
    made = clock.now()
    power = CountingPower()
    log = RecordingLog()
    shutdown = IdleShutdown(LIMIT, clock, power, log)

    for minutes, seconds, outcome, calls in steps:
        _at(clock, made, minutes, seconds)
        shutdown.observe(outcome)
        assert power.calls == calls, (minutes, seconds)
    lines = [line for line in log.lines if line.startswith(PREFIX)]
    assert len(lines) == power.calls
    assert all("30" in line for line in lines)


def test_a_refused_power_off_is_logged_and_starts_a_new_stretch(clock: ManualClock) -> None:
    made = clock.now()
    power = CountingPower(PowerOffError(REFUSAL))
    log = RecordingLog()
    shutdown = IdleShutdown(LIMIT, clock, power, log)

    _at(clock, made, 30, 0)
    shutdown.observe(IDLE)
    assert power.calls == 1
    assert log.lines[-1].startswith(PREFIX)
    assert REFUSAL in log.lines[-1]
    _at(clock, made, 59, 59)
    shutdown.observe(IDLE)
    assert power.calls == 1
    _at(clock, made, 60, 0)
    shutdown.observe(IDLE)
    assert power.calls == 2


@pytest.mark.parametrize(
    ("limit", "accepted"),
    [
        pytest.param(timedelta(0), False, id="zero"),
        pytest.param(timedelta(minutes=-1), False, id="negative"),
        pytest.param(timedelta(minutes=1), True, id="one-minute"),
    ],
)
def test_the_idle_limit_is_at_least_one_minute(
    clock: ManualClock, limit: timedelta, *, accepted: bool
) -> None:
    if accepted:
        assert IdleShutdown(limit, clock, CountingPower(), RecordingLog()).limit == limit
        return
    with pytest.raises(ValueError, match=r".+"):
        IdleShutdown(limit, clock, CountingPower(), RecordingLog())


@pytest.mark.parametrize(
    ("action", "line"),
    [
        pytest.param(
            "ending the factory's process",
            "idle shutdown: idle for 1 minutes, ending the factory's process",
            id="given",
        ),
        pytest.param(
            None, "idle shutdown: idle for 1 minutes, powering the machine off", id="default"
        ),
    ],
)
def test_the_idle_line_names_the_action(clock: ManualClock, action: str | None, line: str) -> None:
    made = clock.now()
    log = RecordingLog()
    shutdown = (
        IdleShutdown(timedelta(minutes=1), clock, CountingPower(), log)
        if action is None
        else IdleShutdown(timedelta(minutes=1), clock, CountingPower(), log, action=action)
    )

    _at(clock, made, 1, 0)
    shutdown.observe(IDLE)

    assert [each for each in log.lines if each.startswith(PREFIX)] == [line]
