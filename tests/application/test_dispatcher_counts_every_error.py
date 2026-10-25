"""The dispatcher counts every error a handler raises, a git error of the seal's name included."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, Handler
from factory.application.stops import StopService
from factory.domain.errors import GitError
from factory.domain.events import Event
from factory.domain.tick_status import TickStatus

STATE = "a" * 40


class Failing(Handler):
    """Raises the given error for every event."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def handle(self, event: Event) -> None:
        del event
        raise self._error


def test_a_handlers_git_error_named_seal_is_counted_as_any_error(boundaries: Boundaries) -> None:
    dispatcher = Dispatcher(
        {"idle": Failing(GitError("seal", None, "x"))}, TickStatus(), StopService(boundaries)
    )
    event = Event(kind="idle", work_item=None, remote_state=STATE)

    outcome = dispatcher.dispatch(event)

    assert outcome == "error"
    assert [(entry.remote_state, entry.count) for entry in dispatcher.status.errors] == [(STATE, 1)]
