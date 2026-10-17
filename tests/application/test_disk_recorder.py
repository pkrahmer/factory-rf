"""The disk recorder measures the instance's folders and keeps the measure."""

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from disk_support import FakeDiskSpace
from factory.adapters.clock import ManualClock
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.disk_records import DiskRecorder
from factory.domain.disk import DiskOccasion, DiskRecord, DiskUse, disk_line
from factory.domain.settings import InstanceSettings
from git_support import CHECKOUT
from record_support import UnwritableRecordLog

STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ "
WORK_FREE = 800 * 10**9
WORK_USED = 7 * 10**8
STATE_FREE = 790 * 10**9
STATE_USED = 2_000
TEMP_FREE = 50 * 10**9
TEMP_USED = 43 * 10**8


@pytest.fixture
def settings(tmp_path: Path) -> InstanceSettings:
    """Return settings whose checkout and state directory lie under `tmp_path`."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=tmp_path / CHECKOUT,
        state_directory=tmp_path / "state",
    )


@pytest.fixture
def temporary(tmp_path: Path) -> Path:
    """Return the path of the test's temporary directory."""
    return tmp_path / "tmp"


@pytest.fixture
def disk(settings: InstanceSettings, temporary: Path) -> FakeDiskSpace:
    """Return a fake disk that answers the work, the state and the temporary directory."""
    work = settings.checkout.parent
    state = settings.state_directory
    return FakeDiskSpace(
        free={work: WORK_FREE, state: STATE_FREE, temporary: TEMP_FREE},
        used={work: WORK_USED, state: STATE_USED, temporary: TEMP_USED},
    )


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[DiskRecord]:
    """Return the disk record log of the test, in `tmp_path`."""
    return JsonLinesRecordLog(tmp_path / "state" / "records" / "disk.jsonl", DiskRecord)


@pytest.fixture
def recorded(
    boundaries: Boundaries,
    settings: InstanceSettings,
    disk: FakeDiskSpace,
    records: JsonLinesRecordLog[DiskRecord],
) -> Boundaries:
    """Return the test's boundaries given the fake disk, the record log and the settings."""
    return replace(boundaries, disk=disk, disk_records=records, settings=settings)


def _log_lines(tmp_path: Path) -> list[str]:
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _use(path: Path, free: int | None, used: int | None) -> DiskUse:
    return DiskUse(path=str(path), free_bytes=free, used_bytes=used)


def test_a_start_record_holds_the_work_and_the_state_directory_and_is_kept_and_logged(
    recorded: Boundaries,
    settings: InstanceSettings,
    records: JsonLinesRecordLog[DiskRecord],
    clock: ManualClock,
    tmp_path: Path,
) -> None:
    record = DiskRecorder(recorded).record("start")

    assert record == DiskRecord(
        at=clock.now(),
        occasion="start",
        folders=[
            _use(settings.checkout.parent, WORK_FREE, WORK_USED),
            _use(settings.state_directory, STATE_FREE, STATE_USED),
        ],
    )
    assert records.read() == [record]
    [line] = _log_lines(tmp_path)
    assert line.endswith(disk_line(record))


@pytest.mark.parametrize("with_temporary", [True, False], ids=["temporary", "no-temporary"])
def test_the_temporary_directory_is_a_third_folder_only_when_it_is_set(
    recorded: Boundaries,
    settings: InstanceSettings,
    temporary: Path,
    *,
    with_temporary: bool,
) -> None:
    given = settings.model_copy(
        update={"temporary_directory": temporary if with_temporary else None}
    )

    record = DiskRecorder(replace(recorded, settings=given)).record("start")

    assert record is not None
    expected = [str(settings.checkout.parent), str(settings.state_directory)]
    if with_temporary:
        expected.append(str(temporary))
    assert [folder.path for folder in record.folders] == expected


@pytest.mark.parametrize("failing", ["free", "used"])
def test_an_os_error_of_one_measure_leaves_only_that_value_unknown(
    recorded: Boundaries, settings: InstanceSettings, disk: FakeDiskSpace, failing: str
) -> None:
    state = settings.state_directory
    if failing == "free":
        disk.free[state] = OSError("statvfs failed")
    else:
        disk.used[state] = OSError("permission denied")

    record = DiskRecorder(recorded).record("start")

    assert record is not None
    expected = _use(state, None, STATE_USED) if failing == "free" else _use(state, STATE_FREE, None)
    assert record.folders[1] == expected


def test_a_record_that_cannot_be_appended_is_logged_with_the_error_and_still_returned(
    recorded: Boundaries, tmp_path: Path
) -> None:
    unwritable = UnwritableRecordLog[DiskRecord](OSError("disk full"))

    record = DiskRecorder(replace(recorded, disk_records=unwritable)).record("start")

    assert record is not None
    first, second = _log_lines(tmp_path)
    assert first.endswith(disk_line(record))
    assert re.fullmatch(STAMP + "cannot write the disk record: disk full", second)


@pytest.mark.parametrize(
    "without",
    [
        pytest.param(lambda b: replace(b, disk=None), id="disk"),
        pytest.param(lambda b: replace(b, disk_records=None), id="disk_records"),
        pytest.param(lambda b: replace(b, settings=None), id="settings"),
    ],
)
def test_boundaries_without_disk_records_or_settings_record_nothing(
    recorded: Boundaries,
    records: JsonLinesRecordLog[DiskRecord],
    tmp_path: Path,
    without: Callable[[Boundaries], Boundaries],
) -> None:
    given = without(recorded)

    record = DiskRecorder(given).record("start")

    assert record is None
    assert records.read() == []
    assert _log_lines(tmp_path) == []


def _at(clock: ManualClock, hours: int, occasion: DiskOccasion) -> DiskRecord:
    return DiskRecord(at=clock.now() + timedelta(hours=hours), occasion=occasion, folders=[])


@pytest.mark.parametrize(
    ("occasions", "with_log"),
    [
        pytest.param(["start", "acceptance"], True, id="acceptance-after-start"),
        pytest.param(["acceptance", "start"], True, id="start-after-acceptance"),
        pytest.param([], True, id="empty-log"),
        pytest.param([], False, id="no-record-log"),
    ],
)
def test_last_gives_the_latest_record_whatever_its_occasion(
    recorded: Boundaries,
    records: JsonLinesRecordLog[DiskRecord],
    disk: FakeDiskSpace,
    clock: ManualClock,
    *,
    occasions: list[DiskOccasion],
    with_log: bool,
) -> None:
    written = [_at(clock, hours, occasion) for hours, occasion in enumerate(occasions)]
    for record in written:
        records.append(record)
    given = recorded if with_log else replace(recorded, disk_records=None)

    last = DiskRecorder(given).last()

    assert last == (written[-1] if written else None)
    assert disk.asked == []
