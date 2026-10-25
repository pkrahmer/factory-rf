"""The dispatcher: hands one event to its handler, counts its errors and reports at the cap."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Literal, get_args

from factory.application.machine import FactoryLog
from factory.application.stops import StopService
from factory.domain.errors import HostingServiceError, UnhandledEvent
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PostKey
from factory.domain.post_texts import error_report_text
from factory.domain.sections import title
from factory.domain.stops import WorkItemStop
from factory.domain.tick_status import (
    ERROR_CAP,
    ErrorCount,
    TickStatus,
    at_cap,
    clear_errors,
    find_error,
    mark_reported,
    record_error,
)
from factory.domain.work_item import WorkItemSnapshot

DispatchOutcome = Literal["handled", "error", "reported", "capped"]


class Handler(ABC):
    """Handles the events of one kind."""

    @abstractmethod
    def handle(self, event: Event) -> None:
        """Act on the event; any `Exception` it raises is counted."""


class Dispatcher:
    """Hands each event to the handler of its kind and caps the errors of each event.

    Errors are counted per event and remote state; at the cap one keyed report is made and the
    event is not tried again on that state.
    """

    def __init__(
        self,
        handlers: Mapping[EventKind, Handler],
        status: TickStatus,
        stops: StopService,
        log: FactoryLog | None = None,
    ) -> None:
        """Dispatch to `handlers`, counting from `status`, reporting through `stops` and `log`."""
        self._handlers = handlers
        self._status = status
        self._stops = stops
        self._log = log

    @property
    def status(self) -> TickStatus:
        """The current counts."""
        return self._status

    def handler_for(self, kind: EventKind) -> Handler:
        """The handler of `kind`; `UnhandledEvent` when none is registered."""
        handler = self._handlers.get(kind)
        if handler is None:
            raise UnhandledEvent(kind)
        return handler

    def dispatch(self, event: Event) -> DispatchOutcome:
        """Handle the event unless it is capped; count an error and report it at the cap."""
        known = find_error(self._status, event.key, event.remote_state)
        if known is not None and at_cap(known):
            if known.reported:
                return "capped"
            return self._report(event, known)
        try:
            self.handler_for(event.kind).handle(event)
        # Every handler error is counted, never lost; a kill is no Exception and passes through.
        except Exception as error:
            return self._count(event, f"{type(error).__name__}: {error}")
        self._status = clear_errors(self._status, event.key)
        return "handled"

    def _count(self, event: Event, last_error: str) -> DispatchOutcome:
        self._status = record_error(self._status, event.key, event.remote_state, last_error)
        entry = find_error(self._status, event.key, event.remote_state)
        if entry is None or not at_cap(entry):
            return "error"
        return self._report(event, entry)

    def _report(self, event: Event, entry: ErrorCount) -> DispatchOutcome:
        snapshot = event.work_item
        if snapshot is None:
            return self._report_to_log(event, entry)
        try:
            self._stops.post(_error_stop(snapshot, event, entry))
        except HostingServiceError:
            # Without the branch on the remote no pull request can be opened, now or later.
            if snapshot.branch_commit is None:
                return self._report_to_log(event, entry)
            return "error"
        # A failed report is made again on the next dispatch and does not count.
        except Exception:
            return "error"
        return self._mark_reported(event)

    def _report_to_log(self, event: Event, entry: ErrorCount) -> DispatchOutcome:
        if self._log is not None:
            self._log.line(f"error cap reached on {event.key}: {entry.last_error}")
        return self._mark_reported(event)

    def _mark_reported(self, event: Event) -> DispatchOutcome:
        self._status = mark_reported(self._status, event.key, event.remote_state)
        return "reported"


def unhandled_kinds(handlers: Mapping[EventKind, Handler]) -> list[EventKind]:
    """The kinds of `EventKind` with no handler, in the order of `EventKind`."""
    every: tuple[EventKind, ...] = get_args(EventKind)
    return [kind for kind in every if kind not in handlers]


def _error_stop(snapshot: WorkItemSnapshot, event: Event, entry: ErrorCount) -> WorkItemStop:
    heading = title(snapshot.document.body)
    state = snapshot.document.state
    return WorkItemStop(
        key=PostKey(work_item=snapshot.id, kind="error", n=event.remote_state[:12]),
        branch=snapshot.branch,
        title=snapshot.id if heading is None else f"{snapshot.id}: {heading}",
        pull_request=None if state is None else state.pull_request,
        text=error_report_text(event.key, entry.last_error, event.remote_state, ERROR_CAP),
    )
