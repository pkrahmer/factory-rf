"""Stops of the repository and the machine go to the health status and the factory log."""

import dataclasses
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.health_file import JsonHealthStatusFile
from factory.application.boundaries import Boundaries
from factory.application.machine import HealthStatusStore
from factory.application.stops import StopService
from factory.domain.stops import HealthStatus, RepositoryStop

LOG = Path("state") / "factory.log"
HEALTH = Path("state") / "health.json"


def _stop(
    clock: ManualClock, reason: str = "fetch_failed", detail: str = "origin unreachable"
) -> RepositoryStop:
    scope = "machine" if reason == "preflight_failed" else "repository"
    return RepositoryStop.model_validate(
        {"scope": scope, "reason": reason, "detail": detail, "at": clock.now()}
    )


def _blocker(tmp_path: Path, name: str) -> Path:
    """A regular file that a destination's directory cannot be created at."""
    path = tmp_path / name
    path.write_text("not a directory\n", encoding="utf-8")
    return path


class _UnwritableHealth(HealthStatusStore):
    """A health status store that reads its status and refuses every write."""

    def __init__(self, status: HealthStatus) -> None:
        self._status = status

    @override
    def read(self) -> HealthStatus:
        return self._status

    @override
    def write(self, status: HealthStatus) -> None:
        raise OSError("the health status cannot be written")


def test_a_raised_stop_is_in_the_health_status(boundaries: Boundaries, clock: ManualClock) -> None:
    stop = _stop(clock)

    StopService(boundaries).raise_stop(stop)

    status = boundaries.health.read()
    assert status.stops == [stop]
    assert not status.healthy


def test_a_raised_stop_writes_one_stamped_line_to_output_and_log_file(
    boundaries: Boundaries,
    clock: ManualClock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    clock.advance(timedelta(seconds=7, microseconds=987654))

    StopService(boundaries).raise_stop(_stop(clock))

    expected = "2026-10-12T12:00:07Z stop repository fetch_failed: origin unreachable\n"
    assert capsys.readouterr().out == expected
    assert (tmp_path / LOG).read_text(encoding="utf-8") == expected


def test_a_stop_of_a_known_reason_replaces_it_in_place_and_a_new_reason_is_appended(
    boundaries: Boundaries, clock: ManualClock
) -> None:
    service = StopService(boundaries)
    first = _stop(clock, "fetch_failed", "origin unreachable")
    second = _stop(clock, "checkout_restore_failed", "index locked")
    again = _stop(clock, "fetch_failed", "origin refused the connection")
    new = _stop(clock, "preflight_failed", "disk full")

    service.raise_stop(first)
    service.raise_stop(second)
    service.raise_stop(again)

    assert boundaries.health.read().stops == [again, second]

    service.raise_stop(new)

    assert boundaries.health.read().stops == [again, second, new]


def test_a_stop_reaches_the_log_when_the_health_status_cannot_be_written(
    boundaries: Boundaries,
    clock: ManualClock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    health = JsonHealthStatusFile(_blocker(tmp_path, "health-blocker") / "health.json")
    service = StopService(dataclasses.replace(boundaries, health=health))

    with pytest.raises(OSError):
        service.raise_stop(_stop(clock))

    expected = "2026-10-12T12:00:00Z stop repository fetch_failed: origin unreachable\n"
    assert capsys.readouterr().out == expected
    assert (tmp_path / LOG).read_text(encoding="utf-8") == expected


def test_a_stop_reaches_the_health_status_when_the_log_file_cannot_be_written(
    boundaries: Boundaries,
    clock: ManualClock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log = TimestampedFactoryLog(_blocker(tmp_path, "log-blocker") / "factory.log", clock)
    service = StopService(dataclasses.replace(boundaries, log=log))
    stop = _stop(clock)

    with pytest.raises(OSError):
        service.raise_stop(stop)

    assert boundaries.health.read().stops == [stop]
    expected = "2026-10-12T12:00:00Z stop repository fetch_failed: origin unreachable\n"
    assert capsys.readouterr().out == expected


def test_the_log_error_is_raised_when_neither_destination_can_be_written(
    boundaries: Boundaries, clock: ManualClock, tmp_path: Path
) -> None:
    log_blocker = _blocker(tmp_path, "log-blocker")
    health_blocker = _blocker(tmp_path, "health-blocker")
    service = StopService(
        dataclasses.replace(
            boundaries,
            log=TimestampedFactoryLog(log_blocker / "factory.log", clock),
            health=JsonHealthStatusFile(health_blocker / "health.json"),
        )
    )

    with pytest.raises(OSError) as raised:
        service.raise_stop(_stop(clock))

    filename = Path(str(raised.value.filename))
    assert filename == log_blocker or log_blocker in filename.parents
    assert filename != health_blocker
    assert health_blocker not in filename.parents


def test_a_raised_stop_opens_no_pull_request(
    boundaries: Boundaries, hosting: FakeHostingService, clock: ManualClock
) -> None:
    StopService(boundaries).raise_stop(_stop(clock))

    assert hosting.pull_requests() == []


def test_clearing_a_stop_removes_only_it_and_writes_the_cleared_line(
    boundaries: Boundaries,
    clock: ManualClock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = StopService(boundaries)
    fetch = _stop(clock, "fetch_failed")
    restore = _stop(clock, "checkout_restore_failed", "index locked")
    service.raise_stop(fetch)
    service.raise_stop(restore)
    capsys.readouterr()
    clock.advance(timedelta(seconds=5))

    service.clear_stop("fetch_failed")

    assert boundaries.health.read().stops == [restore]
    assert capsys.readouterr().out == "2026-10-12T12:00:05Z stop cleared fetch_failed\n"
    lines = (tmp_path / LOG).read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "2026-10-12T12:00:05Z stop cleared fetch_failed"


def test_clearing_a_reason_that_is_not_stopped_does_nothing(
    boundaries: Boundaries, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    StopService(boundaries).clear_stop("fetch_failed")

    assert capsys.readouterr().out == ""
    assert not (tmp_path / LOG).exists()
    assert not (tmp_path / HEALTH).exists()


def test_clearing_a_reason_that_is_not_stopped_keeps_the_other_stops_silently(
    boundaries: Boundaries, clock: ManualClock, capsys: pytest.CaptureFixture[str]
) -> None:
    service = StopService(boundaries)
    restore = _stop(clock, "checkout_restore_failed", "index locked")
    service.raise_stop(restore)
    capsys.readouterr()

    service.clear_stop("fetch_failed")

    assert capsys.readouterr().out == ""
    assert boundaries.health.read().stops == [restore]


def test_clearing_raises_and_writes_no_line_when_the_health_status_cannot_be_written(
    boundaries: Boundaries,
    clock: ManualClock,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    health = _UnwritableHealth(HealthStatus(stops=[_stop(clock)]))
    service = StopService(dataclasses.replace(boundaries, health=health))

    with pytest.raises(OSError):
        service.clear_stop("fetch_failed")

    assert capsys.readouterr().out == ""
    assert not (tmp_path / LOG).exists()


def test_clearing_removes_the_stop_and_raises_when_the_log_file_cannot_be_written(
    boundaries: Boundaries, clock: ManualClock, tmp_path: Path
) -> None:
    StopService(boundaries).raise_stop(_stop(clock))
    log = TimestampedFactoryLog(_blocker(tmp_path, "log-blocker") / "factory.log", clock)
    service = StopService(dataclasses.replace(boundaries, log=log))

    with pytest.raises(OSError):
        service.clear_stop("fetch_failed")

    assert boundaries.health.read().stops == []
