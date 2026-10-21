"""Raising and clearing the stops of the repository and the machine; posting a work item's."""

from datetime import datetime

from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import WorkItemRecorder
from factory.domain.errors import HostingServiceError
from factory.domain.paths import MAIN_BRANCH, REMOTE, STOP_RECORDS_FILE
from factory.domain.post_texts import opened_for_stop_description
from factory.domain.stops import (
    HealthStatus,
    RepositoryStop,
    RepositoryStopReason,
    StopEvent,
    StopPosted,
    StopRecord,
    WorkItemStop,
    parse_stop_records,
    stop_records_text,
)


class StopService:
    """Reports the stops of the repository, the machine and one work item.

    A stop of the repository or the machine goes to the factory log and the health status,
    and its first raise and its clear to the stop records; a stop of one work item goes to
    that work item's pull request.
    """

    def __init__(self, boundaries: Boundaries) -> None:
        """Report through the log, health status, hosting service and git of `boundaries`."""
        self._boundaries = boundaries

    def raise_stop(self, stop: RepositoryStop) -> None:
        """Write the stop's line, put it into the health status and record a first raise.

        Raises `OSError` after every destination was tried.
        """
        # Every destination is tried: one that cannot be written never loses the stop.
        errors: list[OSError] = []
        try:
            self._boundaries.log.line(f"stop {stop.scope} {stop.reason}: {stop.detail}")
        except OSError as error:
            errors.append(error)
        # Without a readable status no record: the records stay paired with the health status.
        standing = True
        try:
            status = self._boundaries.health.read()
            standing = _stands(status, stop.reason)
            self._boundaries.health.write(status.with_stop(stop))
        except OSError as error:
            errors.append(error)
        if not standing:
            try:
                self._record("raised", stop, stop.at)
            except OSError as error:
                errors.append(error)
        if errors:
            raise errors[0]

    def clear_stop(self, reason: RepositoryStopReason) -> None:
        """Remove the stop of `reason` from the health status, say so and record the clear.

        Nothing happens when no stop of `reason` stands.
        """
        status = self._boundaries.health.read()
        standing = next((stop for stop in status.stops if stop.reason == reason), None)
        if standing is None:
            return
        # The status first: no line may say a stop is cleared that is still in force.
        self._boundaries.health.write(_without_stop(status, reason))
        self._boundaries.log.line(f"stop cleared {reason}")
        self._record("cleared", standing, self._boundaries.clock.now())

    def _record(self, event: StopEvent, stop: RepositoryStop, at: datetime) -> None:
        self._boundaries.stop_records.append(
            StopRecord(
                event=event,
                scope=stop.scope,
                reason=stop.reason,
                at=at,
                instance=self._boundaries.settings.instance,
            )
        )

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
        tip = git.resolve(f"{REMOTE}/{branch}")
        if tip is None or git.is_ancestor(tip, f"{REMOTE}/{MAIN_BRANCH}"):
            raise HostingServiceError(
                "create_pull_request",
                f"branch {branch} is not on the remote with a commit beyond main",
            )


class StopPublisher:
    """Pushes the stop records the remote's main does not hold yet to its stop records file."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read the stop records of `boundaries` and publish them through its git."""
        self._boundaries = boundaries

    def publish(self) -> list[StopRecord]:
        """Push the missing records to `STOP_RECORDS_FILE` on main; return them.

        Raises `GitError`, `PushFailed`, and `OSError` when the file cannot be written.
        """
        local = self._boundaries.stop_records.read()
        if not local:
            return []
        text = self._boundaries.git.show_file(f"{REMOTE}/{MAIN_BRANCH}", STOP_RECORDS_FILE) or ""
        missing = _missing_records(local, parse_stop_records(text))
        if not missing:
            return []
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(MAIN_BRANCH)
        if text and not text.endswith("\n"):
            text += "\n"
        path = self._boundaries.checkout / STOP_RECORDS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + stop_records_text(missing), encoding="utf-8", newline="\n")
        recorder.publish(MAIN_BRANCH, "stops recorded")
        return missing


def _missing_records(local: list[StopRecord], published: list[StopRecord]) -> list[StopRecord]:
    missing: list[StopRecord] = []
    for record in local:
        if record not in published and record not in missing:
            missing.append(record)
    return missing


def _stands(status: HealthStatus, reason: RepositoryStopReason) -> bool:
    return any(stop.reason == reason for stop in status.stops)


def _without_stop(status: HealthStatus, reason: RepositoryStopReason) -> HealthStatus:
    return HealthStatus(stops=[stop for stop in status.stops if stop.reason != reason])
