"""Handlers for tick and dispatcher tests: a factory of fixed handlers and a failing one."""

from collections.abc import Mapping

from factory.application.dispatcher import Handler
from factory.application.tick import HandlerFactory
from factory.domain.events import Event, EventKind
from factory.domain.pipeline_definition import PipelineDefinition


def handlers_of(handlers: Mapping[EventKind, Handler]) -> HandlerFactory:
    """A handler factory that returns `handlers` under every pipeline definition."""

    def build(_definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
        return handlers

    return build


class Failing(Handler):
    """Records every event it is handed and raises the given error."""

    def __init__(self, error: BaseException | None = None) -> None:
        self.calls: list[Event] = []
        self._error = error if error is not None else ValueError("boom")

    def handle(self, event: Event) -> None:
        self.calls.append(event)
        raise self._error
