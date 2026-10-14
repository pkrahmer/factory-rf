"""The duplicate and pull request lookup handlers: stops with no work to do, raised as errors."""

from factory.application.dispatcher import Handler
from factory.application.handlers.recording import target_of
from factory.domain.errors import CannotHandle
from factory.domain.events import Event


def _with_detail(reason: str, event: Event) -> str:
    if not event.detail:
        return reason
    return f"{reason}: {event.detail}"


class DuplicateHandler(Handler):
    """Refuses a work item whose id two files share, so the dispatcher counts and reports it."""

    def __init__(self) -> None:
        """Need no boundary: the handler only raises."""

    def handle(self, event: Event) -> None:
        """Raise `CannotHandle` naming the shared id and the event's detail."""
        snapshot = target_of(event).snapshot
        reason = f"two work items share the id {snapshot.id}"
        raise CannotHandle("duplicate", _with_detail(reason, event))


class PullRequestLookupHandler(Handler):
    """Refuses a work item whose pull request could not be looked up, so it is reported."""

    def __init__(self) -> None:
        """Need no boundary: the handler only raises."""

    def handle(self, event: Event) -> None:
        """Raise `CannotHandle` naming the branch and the event's detail."""
        snapshot = target_of(event).snapshot
        reason = f"the pull request lookup for {snapshot.branch} failed"
        raise CannotHandle("pull_request_lookup", _with_detail(reason, event))
