"""Every handler error the dispatcher counts writes one line to the factory's log."""

import pytest

from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.dispatcher import Dispatcher
from factory.pipeline.application.stops import StopService
from factory.pipeline.domain.events import Event
from factory.pipeline.domain.tick_status import TickStatus
from recording_log import RecordingLog
from tick_support import Failing

STATE = "a" * 40
PREFIX = "handler error "


def _lines(log: RecordingLog) -> list[str]:
    return [line for line in log.lines if line.startswith(PREFIX)]


def _dispatch(boundaries: Boundaries, error: Exception, times: int) -> tuple[Event, RecordingLog]:
    log = RecordingLog()
    event = Event(kind="idle", work_item=None, remote_state=STATE)
    dispatcher = Dispatcher({"idle": Failing(error)}, TickStatus(), StopService(boundaries), log)
    for _ in range(times):
        dispatcher.dispatch(event)
    return event, log


def test_each_counted_error_writes_its_key_count_cap_type_and_text(
    boundaries: Boundaries,
) -> None:
    event, log = _dispatch(boundaries, ValueError("boom"), 3)

    assert _lines(log) == [
        f"handler error {event.key} {n} of 3: ValueError: boom" for n in (1, 2, 3)
    ]


def test_an_error_text_with_a_line_break_is_written_on_one_line(boundaries: Boundaries) -> None:
    _event, log = _dispatch(boundaries, ValueError("first\nsecond"), 1)

    [line] = _lines(log)
    assert "\n" not in line
    assert "first" in line
    assert line.endswith("second")


@pytest.mark.parametrize(
    ("length", "kept"),
    [pytest.param(300, 300, id="300-kept"), pytest.param(301, 300, id="301-cut")],
)
def test_an_error_text_is_written_with_at_most_300_characters(
    boundaries: Boundaries, length: int, kept: int
) -> None:
    text = "".join(str(index % 10) for index in range(length))
    event, log = _dispatch(boundaries, ValueError(text), 1)

    assert _lines(log) == [f"handler error {event.key} 1 of 3: ValueError: {text[:kept]}"]
