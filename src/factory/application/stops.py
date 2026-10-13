"""Raising and clearing the stops of the repository and the machine; posting a work item's."""

from factory.application.boundaries import Boundaries
from factory.domain.errors import HostingServiceError
from factory.domain.paths import MAIN_BRANCH
from factory.domain.post_texts import opened_for_stop_description
from factory.domain.stops import (
    HealthStatus,
    RepositoryStop,
    RepositoryStopReason,
    StopPosted,
    WorkItemStop,
)

_REMOTE = "origin/"


class StopService:
    """Reports the stops of the repository, the machine and one work item.

    A stop of the repository or the machine goes to the factory log and the health status;
    a stop of one work item goes to that work item's pull request.
    """

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

    def post(self, stop: WorkItemStop) -> StopPosted:
        """Post the stop once on its pull request, opening a draft first when there is none.

        Writes no state: the caller records the number when `opened` is true.
        Raises `HostingServiceError` and `GitError`.
        """
        number = stop.pull_request
        if number is None:
            number = self._open_pull_request_of(stop)
        # The key alone makes a repeat a no-op, so a post before or after the state write is safe.
        outcome = self._boundaries.hosting.post_comment(number, stop.text, stop.key)
        return StopPosted(pull_request=number, opened=stop.pull_request is None, outcome=outcome)

    def _open_pull_request_of(self, stop: WorkItemStop) -> int:
        hosting = self._boundaries.hosting
        found = hosting.find_open_pull_request(stop.branch)
        if found is not None:
            return found.number
        self._require_commit_beyond_main(stop.branch)
        description = opened_for_stop_description(stop.key.work_item)
        return hosting.create_pull_request(stop.branch, stop.title, description, draft=True).number

    def _require_commit_beyond_main(self, branch: str) -> None:
        # The hosting service refuses a pull request without such a commit; refusing it here
        # makes the fake and the production service fail alike.
        git = self._boundaries.git
        tip = git.resolve(_REMOTE + branch)
        if tip is None or git.is_ancestor(tip, _REMOTE + MAIN_BRANCH):
            raise HostingServiceError(
                "create_pull_request",
                f"branch {branch} is not on the remote with a commit beyond main",
            )


def _with_stop(status: HealthStatus, stop: RepositoryStop) -> HealthStatus:
    if any(known.reason == stop.reason for known in status.stops):
        return HealthStatus(
            stops=[stop if known.reason == stop.reason else known for known in status.stops]
        )
    return HealthStatus(stops=[*status.stops, stop])


def _without_stop(status: HealthStatus, reason: RepositoryStopReason) -> HealthStatus:
    return HealthStatus(stops=[stop for stop in status.stops if stop.reason != reason])
