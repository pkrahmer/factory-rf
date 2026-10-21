"""The tick reads the free space of the work and the state directory first, before the fetch."""

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest

from disk_support import FakeDiskSpace
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.disk import GIGABYTE, disk_low_detail
from factory.domain.events import EventKind
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop
from git_support import CHECKOUT, remote_commit
from human_clone import HumanClone
from log_support import log_lines

INSTANCE = "factory-1"
MIN_FREE_GB = 2
ENOUGH = MIN_FREE_GB * GIGABYTE
SHORT = ENOUGH - 1


pytestmark = pytest.mark.usefixtures("installed_agents")


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Return settings whose checkout and state directory lie under `tmp_path`."""
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": INSTANCE,
            "checkout": tmp_path / CHECKOUT,
            "state_directory": tmp_path / "state",
            "min_free_gb": MIN_FREE_GB,
        }
    )


@pytest.fixture
def work(settings: InstanceSettings) -> Path:
    """Return the work directory, the checkout's parent."""
    return settings.checkout.parent


@pytest.fixture
def state(settings: InstanceSettings) -> Path:
    """Return the state directory."""
    return settings.state_directory


def _handlers(_definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
    return {"idle": IdleHandler()}


def _tick(
    boundaries: Boundaries, disk: FakeDiskSpace | None, settings: InstanceSettings | None
) -> TickOutcome:
    return Tick(replace(boundaries, disk=disk, settings=settings), INSTANCE, _handlers).run()


def _disk_stops(boundaries: Boundaries) -> list[RepositoryStop]:
    return [stop for stop in boundaries.health.read().stops if stop.reason == "disk_low"]


def test_exactly_the_minimum_free_on_both_paths_lets_the_tick_run_on(
    boundaries: Boundaries, settings: InstanceSettings, work: Path, state: Path
) -> None:
    disk = FakeDiskSpace(free={work: ENOUGH, state: ENOUGH})

    outcome = _tick(boundaries, disk, settings)

    assert outcome.stopped is None
    assert _disk_stops(boundaries) == []


def test_a_short_work_directory_stops_the_tick_before_the_fetch(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    work: Path,
    state: Path,
    remote: Path,
    human: HumanClone,
) -> None:
    human.push_file("main", "notes.txt", "pushed after the clone\n")
    pushed = remote_commit(remote, "main")
    disk = FakeDiskSpace(free={work: SHORT, state: ENOUGH})

    outcome = _tick(boundaries, disk, settings)

    assert outcome == TickOutcome(stopped="disk_low")
    assert boundaries.git.resolve("origin/main") != pushed


def test_the_low_disk_stop_reaches_the_health_status_and_the_factory_log(
    tmp_path: Path, boundaries: Boundaries, settings: InstanceSettings, work: Path, state: Path
) -> None:
    free = {work: SHORT, state: ENOUGH}
    detail = disk_low_detail(free, MIN_FREE_GB)
    assert detail is not None

    _tick(boundaries, FakeDiskSpace(free=dict(free)), settings)

    stops = _disk_stops(boundaries)
    assert [(stop.scope, stop.detail) for stop in stops] == [("machine", detail)]
    lines = [
        line for line in log_lines(tmp_path) if line.endswith(f"stop machine disk_low: {detail}")
    ]
    assert len(lines) == 1


@pytest.mark.parametrize(
    ("work_free", "state_free", "named"),
    [
        (ENOUGH, SHORT, ("state",)),
        (SHORT, SHORT, ("work", "state")),
    ],
    ids=["state-short", "both-short"],
)
def test_the_detail_names_the_short_paths_the_work_directory_first(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    work: Path,
    state: Path,
    work_free: int,
    state_free: int,
    named: tuple[str, ...],
) -> None:
    paths = {"work": work, "state": state}

    outcome = _tick(boundaries, FakeDiskSpace(free={work: work_free, state: state_free}), settings)

    assert outcome == TickOutcome(stopped="disk_low")
    expected = disk_low_detail({paths[name]: SHORT for name in named}, MIN_FREE_GB)
    assert [stop.detail for stop in _disk_stops(boundaries)] == [expected]


@pytest.mark.parametrize(
    ("failing", "state_free", "asked"),
    [
        ("state", ENOUGH, ("work", "state")),
        ("work", ENOUGH, ("work",)),
        ("work", SHORT, ("work",)),
    ],
    ids=["state-unreadable", "work-unreadable", "work-unreadable-state-short"],
)
def test_an_unreadable_free_space_stops_the_tick_with_the_error(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    work: Path,
    state: Path,
    failing: str,
    state_free: int,
    asked: tuple[str, ...],
) -> None:
    paths = {"work": work, "state": state}
    free: dict[Path, int | OSError] = {work: ENOUGH, state: state_free}
    free[paths[failing]] = OSError("no such device")
    disk = FakeDiskSpace(free=free)

    outcome = _tick(boundaries, disk, settings)

    assert outcome == TickOutcome(stopped="disk_low")
    assert [stop.detail for stop in _disk_stops(boundaries)] == [
        f"cannot read the free space of {paths[failing]}: no such device"
    ]
    assert disk.asked == [paths[name] for name in asked]


def test_a_tick_with_enough_room_clears_the_low_disk_stop(
    tmp_path: Path, boundaries: Boundaries, settings: InstanceSettings, work: Path, state: Path
) -> None:
    disk = FakeDiskSpace(free={work: SHORT, state: ENOUGH})
    _tick(boundaries, disk, settings)
    disk.free[work] = ENOUGH

    outcome = _tick(boundaries, disk, settings)

    assert outcome.stopped is None
    assert _disk_stops(boundaries) == []
    assert any(line.endswith("stop cleared disk_low") for line in log_lines(tmp_path))


@pytest.mark.parametrize(
    ("with_disk", "with_settings"),
    [(True, False), (False, True)],
    ids=["without-settings", "without-disk"],
)
def test_a_tick_without_a_disk_or_settings_reads_nothing_and_runs_on(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    work: Path,
    state: Path,
    with_disk: bool,
    with_settings: bool,
) -> None:
    disk = FakeDiskSpace(free={work: SHORT, state: SHORT})

    outcome = _tick(boundaries, disk if with_disk else None, settings if with_settings else None)

    assert outcome.stopped is None
    assert disk.asked == []
