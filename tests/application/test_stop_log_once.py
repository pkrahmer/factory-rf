"""A standing stop writes its log line once, and again only when its detail changes."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.stops import RepositoryStop, StopRecord
from factory.shared.adapters.clock import ManualClock
from factory.shared.domain.settings import InstanceSettings
from factory.watching.adapters.record_log_jsonl import JsonLinesRecordLog
from log_support import log_lines

FIRST = "origin unreachable"
OTHER = "origin refused the connection"

Step = Callable[[StopService, ManualClock], None]


def _stop(clock: ManualClock, detail: str) -> RepositoryStop:
    return RepositoryStop(scope="repository", reason="fetch_failed", detail=detail, at=clock.now())


def _raising(detail: str) -> Step:
    return lambda service, clock: service.raise_stop(_stop(clock, detail))


def _clearing(service: StopService, _clock: ManualClock) -> None:
    service.clear_stop("fetch_failed")


def _line(detail: str) -> str:
    return f"stop repository fetch_failed: {detail}"


CLEARED = "stop cleared fetch_failed"

SEQUENCES = {
    "same-detail": [_raising(FIRST), _raising(FIRST), _raising(FIRST)],
    "other-detail": [_raising(FIRST), _raising(FIRST), _raising(OTHER)],
    "raise-after-clear": [_raising(FIRST), _clearing, _raising(FIRST)],
}


@pytest.fixture
def service(
    boundaries: Boundaries,
    local_settings: InstanceSettings,
    records: JsonLinesRecordLog[StopRecord],
) -> StopService:
    """The stop service writing its records to the test's stop records."""
    return StopService(replace(boundaries, stop_records=records, settings=local_settings))


def _run(steps: list[Step], service: StopService, clock: ManualClock) -> None:
    for step in steps:
        step(service, clock)


@pytest.mark.parametrize(
    ("sequence", "expected"),
    [
        pytest.param("same-detail", [_line(FIRST)], id="same-detail"),
        pytest.param("other-detail", [_line(FIRST), _line(OTHER)], id="other-detail"),
        pytest.param(
            "raise-after-clear", [_line(FIRST), CLEARED, _line(FIRST)], id="raise-after-clear"
        ),
    ],
)
def test_a_standing_stop_writes_its_line_once_and_again_only_when_something_changes(
    service: StopService,
    clock: ManualClock,
    tmp_path: Path,
    *,
    sequence: str,
    expected: list[str],
) -> None:
    _run(SEQUENCES[sequence], service, clock)

    assert [line.split(" ", 1)[1] for line in log_lines(tmp_path)] == expected


@pytest.mark.parametrize(
    ("sequence", "detail", "events"),
    [
        pytest.param("same-detail", FIRST, ["raised"], id="same-detail"),
        pytest.param("other-detail", OTHER, ["raised"], id="other-detail"),
        pytest.param(
            "raise-after-clear", FIRST, ["raised", "cleared", "raised"], id="raise-after-clear"
        ),
    ],
)
def test_the_health_status_holds_the_newest_detail_and_the_records_the_first_raise_and_clear(
    service: StopService,
    boundaries: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    clock: ManualClock,
    *,
    sequence: str,
    detail: str,
    events: list[str],
) -> None:
    _run(SEQUENCES[sequence], service, clock)

    assert [stop.detail for stop in boundaries.health.read().stops] == [detail]
    assert [record.event for record in records.read()] == events


@pytest.mark.parametrize("blank", ["", " \t "], ids=["empty", "blank"])
def test_an_empty_or_blank_detail_is_replaced_by_no_detail_given(
    service: StopService,
    boundaries: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    clock: ManualClock,
    tmp_path: Path,
    *,
    blank: str,
) -> None:
    # The model refuses a blank detail, so only a stop built without validation carries one.
    stop = RepositoryStop.model_construct(
        scope="repository", reason="fetch_failed", detail=blank, at=clock.now()
    )

    service.raise_stop(stop)

    assert [line.split(" ", 1)[1] for line in log_lines(tmp_path)] == [
        "stop repository fetch_failed: no detail given"
    ]
    assert [stop.detail for stop in boundaries.health.read().stops] == ["no detail given"]
    assert [(record.event, record.reason) for record in records.read()] == [
        ("raised", "fetch_failed")
    ]
