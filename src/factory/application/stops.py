"""Raising and clearing the stops of the repository and the machine."""

from factory.application.boundaries import Boundaries
from factory.domain.stops import HealthStatus, RepositoryStop, RepositoryStopReason


class StopService:
    """Reports a stop to the factory log and the health status, never to a pull request."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Report through the log and the health status store of `boundaries`."""
        self._boundaries = boundaries

    def raise_stop(self, stop: RepositoryStop) -> None:
        """Write the stop's line and put the stop into the health status; `OSError` after both."""
        # Both destinations are tried: one that cannot be written never loses the stop.
        errors: list[OSError] = []
        try:
            self._boundaries.log.line(f"stop {stop.scope} {stop.reason}: {stop.detail}")
        except OSError as error:
            errors.append(error)
        try:
            status = self._boundaries.health.read()
            self._boundaries.health.write(_with_stop(status, stop))
        except OSError as error:
            errors.append(error)
        if errors:
            raise errors[0]

    def clear_stop(self, reason: RepositoryStopReason) -> None:
        """Remove the stop of `reason` from the health status and say so; nothing if absent."""
        status = self._boundaries.health.read()
        if all(stop.reason != reason for stop in status.stops):
            return
        # The status first: no line may say a stop is cleared that is still in force.
        self._boundaries.health.write(_without_stop(status, reason))
        self._boundaries.log.line(f"stop cleared {reason}")


def _with_stop(status: HealthStatus, stop: RepositoryStop) -> HealthStatus:
    stops = [stop if known.reason == stop.reason else known for known in status.stops]
    if stop not in stops:
        stops.append(stop)
    return HealthStatus(stops=stops)


def _without_stop(status: HealthStatus, reason: RepositoryStopReason) -> HealthStatus:
    return HealthStatus(stops=[stop for stop in status.stops if stop.reason != reason])
