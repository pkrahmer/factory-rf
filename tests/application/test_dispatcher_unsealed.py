"""The dispatcher lets a handler's `RepositoryUnsealed` pass without counting it."""

import pytest

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, Handler
from factory.application.stops import StopService
from factory.domain.errors import GitError, RepositoryUnsealed
from factory.domain.events import Event
from factory.domain.tick_status import TickStatus

STATE = "a" * 40


class Failing(Handler):
    """Records every event it is handed and raises the given error."""

    def __init__(self, error: Exception) -> None:
        self.calls: list[Event] = []
        self._error = error

    def handle(self, event: Event) -> None:
        self.calls.append(event)
        raise self._error


@pytest.mark.parametrize(
    ("error", "expected", "counted"),
    [
        pytest.param(RepositoryUnsealed(".git is a symbolic link"), "raised", 0, id="unsealed"),
        pytest.param(GitError("fetch", 1, "no remote"), "error", 1, id="other-git-error"),
    ],
)
def test_a_handlers_unsealed_repository_passes_uncounted_and_another_git_error_counts(
    boundaries: Boundaries, *, error: Exception, expected: str, counted: int
) -> None:
    dispatcher = Dispatcher({"idle": Failing(error)}, TickStatus(), StopService(boundaries))
    event = Event(kind="idle", work_item=None, remote_state=STATE)

    outcome: str
    try:
        outcome = dispatcher.dispatch(event)
    except RepositoryUnsealed:
        outcome = "raised"

    assert outcome == expected
    assert sum(entry.count for entry in dispatcher.status.errors) == counted
