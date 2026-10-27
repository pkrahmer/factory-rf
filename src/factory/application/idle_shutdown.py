"""The idle shutdown: the machine is powered off after a long enough stretch of idle ticks."""

from datetime import timedelta

from factory.application.machine import Clock, FactoryLog, PowerOff
from factory.application.tick import TickOutcome
from factory.domain.errors import PowerOffError

_PREFIX = "idle shutdown: "


class IdleShutdown:
    """Powers the machine off right after an idle tick that ends an idle stretch of `limit`."""

    def __init__(self, limit: timedelta, clock: Clock, power: PowerOff, log: FactoryLog) -> None:
        """Count from now; a `limit` of zero or less raises `ValueError`."""
        if limit <= timedelta(0):
            raise ValueError(f"the idle limit must be positive, not {limit}")
        self._limit = limit
        self._clock = clock
        self._power = power
        self._log = log
        self._stretch_start = clock.now()

    @property
    def limit(self) -> timedelta:
        """The idle stretch after which the machine is powered off."""
        return self._limit

    @property
    def power(self) -> PowerOff:
        """The power switch it uses."""
        return self._power

    def observe(self, outcome: TickOutcome) -> None:
        """Count `outcome` into the stretch; power off when an idle one ends it at the limit."""
        if not _is_idle(outcome):
            self._start_stretch()
            return
        if self._clock.now() - self._stretch_start < self._limit:
            return
        self._power_off()
        self._start_stretch()

    def _power_off(self) -> None:
        minutes = int(self._limit.total_seconds() // 60)
        self._log.line(f"{_PREFIX}idle for {minutes} minutes, powering the machine off")
        try:
            self._power.power_off()
        except PowerOffError as error:
            # The instance runs on: a refusal must not end the loop that serves the project.
            self._log.line(f"{_PREFIX}{error}; the factory runs on")

    def _start_stretch(self) -> None:
        self._stretch_start = self._clock.now()


def _is_idle(outcome: TickOutcome) -> bool:
    return (
        outcome.stopped is None
        and outcome.event is not None
        and outcome.event.kind == "idle"
        and outcome.dispatch == "handled"
    )
