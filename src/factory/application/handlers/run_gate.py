"""The run gate: the pull request is read before a stage runs, and the human's act comes first."""

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import target_of
from factory.domain.events import Event


class RunGate(Handler):
    """Reads the pull request before a run and hands a closed or merged one to its handler."""

    def __init__(
        self, boundaries: Boundaries, run: Handler, closed: Handler, merged: Handler
    ) -> None:
        """Read through the boundaries' hosting service; pass the event to one of three handlers."""
        self._boundaries = boundaries
        self._run = run
        self._closed = closed
        self._merged = merged

    @property
    def run(self) -> Handler:
        """The handler that runs the stage."""
        return self._run

    @property
    def closed(self) -> Handler:
        """The handler of a pull request the human closed."""
        return self._closed

    @property
    def merged(self) -> Handler:
        """The handler of a pull request the human merged."""
        return self._merged

    def handle(self, event: Event) -> None:
        """Run the stage unless the pull request, read first, is closed or merged."""
        number = target_of(event).pull_request
        if number is None:
            self._run.handle(event)
            return
        view = self._boundaries.hosting.get_pull_request(number)
        if view.state == "closed":
            self._closed.handle(event.model_copy(update={"kind": "closed", "pull_request": view}))
        elif view.state == "merged":
            self._merged.handle(event.model_copy(update={"kind": "merged", "pull_request": view}))
        else:
            self._run.handle(event.model_copy(update={"pull_request": view}))
