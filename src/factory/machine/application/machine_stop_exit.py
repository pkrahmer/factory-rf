"""In a job, a machine stop that stands long enough ends the factory's process."""

from collections.abc import Callable
from datetime import datetime, timedelta

from factory.pipeline.domain.stops import RepositoryStop, RepositoryStopReason
from factory.watching.application.machine import Clock, FactoryLog, HealthStatusStore

MACHINE_STOP_LIMIT = timedelta(minutes=10)


class MachineStopExit:
    """Ends the loop through `request_stop` once a machine stop has stood for the limit.

    Nobody can fix the machine of a job, so a stop of its own would hold it forever.
    """

    def __init__(
        self,
        health: HealthStatusStore,
        clock: Clock,
        log: FactoryLog,
        request_stop: Callable[[], None],
    ) -> None:
        """Read the stops in `health` on `clock`; the ending line goes to `log`."""
        self._health = health
        self._clock = clock
        self._log = log
        self._request_stop = request_stop
        self._since: dict[RepositoryStopReason, datetime] = {}
        self._ended = False

    @property
    def ended(self) -> bool:
        """True once a standing machine stop has ended the loop."""
        return self._ended

    def observe(self) -> None:
        """Count the machine stops that stand now; end the loop when one reached the limit."""
        standing = [stop for stop in self._health.read().stops if stop.scope == "machine"]
        # A stop raised again on every tick moves its own time forward; the first time of
        # an unbroken stretch is the one that counts.
        self._since = {
            stop.reason: min(stop.at, self._since.get(stop.reason, stop.at)) for stop in standing
        }
        due = next((stop for stop in standing if self._has_stood(stop)), None)
        if due is None or self._ended:
            return
        minutes = int(MACHINE_STOP_LIMIT.total_seconds() // 60)
        self._log.line(
            f"machine stop: standing for {minutes} minutes in a job, "
            f"ending the factory's process: {due.reason}: {due.detail}"
        )
        self._ended = True
        self._request_stop()

    def _has_stood(self, stop: RepositoryStop) -> bool:
        return self._clock.now() - self._since[stop.reason] >= MACHINE_STOP_LIMIT
