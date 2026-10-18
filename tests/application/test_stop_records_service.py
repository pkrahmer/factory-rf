"""Raising and clearing a stop also appends its raised and cleared events to the stop records."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.settings import InstanceSettings
from factory.domain.stops import (
    HealthStatus,
    RepositoryStop,
    RepositoryStopReason,
    StopRecord,
)
from record_support import UnwritableRecordLog

INSTANCE = "factory-1"
AT = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)


def _stop(reason: RepositoryStopReason, minute: int = 0) -> RepositoryStop:
    scope = "machine" if reason in ("disk_low", "preflight_failed") else "repository"
    return RepositoryStop(
        scope=scope, reason=reason, detail=f"{reason} detail", at=AT.replace(minute=minute)
    )


def _raised(reason: RepositoryStopReason, minute: int, instance: str | None) -> StopRecord:
    stop = _stop(reason, minute)
    return StopRecord(
        event="raised", scope=stop.scope, reason=reason, at=stop.at, instance=instance
    )


def _records_path(tmp_path: Path) -> Path:
    return tmp_path / "state" / "records" / "stops.jsonl"


def _log_lines(tmp_path: Path) -> list[str]:
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[StopRecord]:
    """The stop records in the test's state directory."""
    return JsonLinesRecordLog(_records_path(tmp_path), StopRecord)


@pytest.mark.parametrize(
    ("with_settings", "stops", "expected"),
    [
        pytest.param(
            True,
            [_stop("fetch_failed")],
            [_raised("fetch_failed", 0, INSTANCE)],
            id="first-raise",
        ),
        pytest.param(
            True,
            [_stop("fetch_failed"), _stop("fetch_failed", 1)],
            [_raised("fetch_failed", 0, INSTANCE)],
            id="second-raise-while-standing",
        ),
        pytest.param(
            True,
            [_stop("fetch_failed"), _stop("disk_low", 1)],
            [_raised("fetch_failed", 0, INSTANCE), _raised("disk_low", 1, INSTANCE)],
            id="other-reason-while-standing",
        ),
        pytest.param(
            False,
            [_stop("fetch_failed")],
            [_raised("fetch_failed", 0, None)],
            id="no-settings",
        ),
    ],
)
def test_a_raise_appends_a_raised_record_when_no_stop_of_its_reason_stands(
    boundaries: Boundaries,
    local_settings: InstanceSettings,
    records: JsonLinesRecordLog[StopRecord],
    *,
    with_settings: bool,
    stops: list[RepositoryStop],
    expected: list[StopRecord],
) -> None:
    settings = local_settings if with_settings else None
    service = StopService(replace(boundaries, stop_records=records, settings=settings))

    for stop in stops:
        service.raise_stop(stop)

    assert records.read() == expected


@pytest.mark.parametrize(
    ("standing", "reason", "expected"),
    [
        pytest.param(
            "fetch_failed",
            "fetch_failed",
            [("cleared", "repository", "fetch_failed")],
            id="repository-stop",
        ),
        pytest.param(
            "disk_low", "disk_low", [("cleared", "machine", "disk_low")], id="machine-stop"
        ),
        pytest.param("fetch_failed", "disk_low", [], id="not-standing"),
    ],
)
def test_a_clear_of_a_standing_stop_appends_a_cleared_record_at_the_clock_time(
    boundaries: Boundaries,
    local_settings: InstanceSettings,
    records: JsonLinesRecordLog[StopRecord],
    clock: ManualClock,
    *,
    standing: RepositoryStopReason,
    reason: RepositoryStopReason,
    expected: list[tuple[str, str, str]],
) -> None:
    boundaries.health.write(HealthStatus(stops=[_stop(standing)]))
    clock.advance(timedelta(minutes=3))
    service = StopService(replace(boundaries, stop_records=records, settings=local_settings))

    service.clear_stop(reason)

    written = records.read()
    assert [(record.event, record.scope, record.reason) for record in written] == expected
    assert all(record.at == clock.now() for record in written)
    assert all(record.instance == INSTANCE for record in written)


def test_without_stop_records_a_raise_and_a_clear_write_only_the_log_and_the_health_status(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    service = StopService(boundaries)

    service.raise_stop(_stop("fetch_failed"))
    assert boundaries.health.read().stops == [_stop("fetch_failed")]
    service.clear_stop("fetch_failed")

    assert boundaries.health.read().stops == []
    texts = [line.split(" ", 1)[1] for line in _log_lines(tmp_path)]
    assert texts == [
        "stop repository fetch_failed: fetch_failed detail",
        "stop cleared fetch_failed",
    ]
    assert sorted(path.name for path in (tmp_path / "state").iterdir()) == [
        "factory.log",
        "health.json",
    ]


def _raise(service: StopService) -> None:
    service.raise_stop(_stop("fetch_failed"))


def _clear(service: StopService) -> None:
    service.clear_stop("fetch_failed")


@pytest.mark.parametrize(
    ("standing", "act", "expected_stops", "expected_line"),
    [
        pytest.param(
            [],
            _raise,
            [_stop("fetch_failed")],
            "stop repository fetch_failed: fetch_failed detail",
            id="raise",
        ),
        pytest.param([_stop("fetch_failed")], _clear, [], "stop cleared fetch_failed", id="clear"),
    ],
)
def test_an_unwritable_record_log_raises_after_the_log_and_the_health_status_were_written(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    standing: list[RepositoryStop],
    act: Callable[[StopService], None],
    expected_stops: list[RepositoryStop],
    expected_line: str,
) -> None:
    boundaries.health.write(HealthStatus(stops=standing))
    error = OSError("no space left on the device")
    unwritable: UnwritableRecordLog[StopRecord] = UnwritableRecordLog(error)
    service = StopService(replace(boundaries, stop_records=unwritable))

    with pytest.raises(OSError) as raised:
        act(service)

    assert raised.value is error
    assert boundaries.health.read().stops == expected_stops
    assert [line.split(" ", 1)[1] for line in _log_lines(tmp_path)] == [expected_line]
