"""The acceptance reviewer's facts record the disk and name the record before it."""

from dataclasses import replace

import pytest

from acceptance_walk import FEATURE, AcceptanceWalk
from disk_support import FakeDiskSpace
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.disk_records import DiskRecorder
from factory.domain.disk import DiskRecord, disk_line
from factory.domain.settings import InstanceSettings


@pytest.fixture
def recorded(
    walk: AcceptanceWalk,
    boundaries: Boundaries,
    disk_settings: InstanceSettings,
    disk_records: JsonLinesRecordLog[DiskRecord],
) -> Boundaries:
    """Return the walk's fetched boundaries with a fake disk, the record log and the settings."""
    work = disk_settings.checkout.parent
    state = disk_settings.state_directory
    disk = FakeDiskSpace(
        free={work: 800 * 10**9, state: 790 * 10**9}, used={work: 7 * 10**8, state: 2_000}
    )
    assert walk.status() == "due"
    return replace(boundaries, disk=disk, disk_records=disk_records, settings=disk_settings)


def test_the_facts_record_the_disk_at_acceptance_and_name_the_record_before(
    walk: AcceptanceWalk, recorded: Boundaries, disk_records: JsonLinesRecordLog[DiskRecord]
) -> None:
    service = AcceptanceService(recorded, walk.definition)

    first = service.facts(FEATURE)

    [record] = disk_records.read()
    assert record.occasion == "acceptance"
    assert (first.disk_now, first.disk_before) == (disk_line(record), None)

    second = service.facts(FEATURE)

    assert second.disk_before == first.disk_now
    assert len(disk_records.read()) == 2


def test_a_start_record_is_the_previous_record(walk: AcceptanceWalk, recorded: Boundaries) -> None:
    start = DiskRecorder(recorded).record("start")
    assert start is not None

    facts = AcceptanceService(recorded, walk.definition).facts(FEATURE)

    assert facts.disk_before == disk_line(start)
    assert disk_line(start).startswith("disk start: ")
