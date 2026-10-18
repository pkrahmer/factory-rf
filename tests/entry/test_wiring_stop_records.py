"""The wired stop records lie in the state directory's records folder."""

from datetime import UTC, datetime

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL


def test_the_built_stop_records_read_back_a_record_from_the_state_directory(
    local_settings: InstanceSettings,
) -> None:
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())
    record = StopRecord(
        event="raised",
        scope="repository",
        reason="fetch_failed",
        at=datetime(2026, 10, 18, 10, 0, tzinfo=UTC),
        instance="factory-1",
    )

    assert boundaries.stop_records is not None
    boundaries.stop_records.append(record)

    assert boundaries.stop_records.read() == [record]
    path = local_settings.state_directory / "records" / "stops.jsonl"
    assert JsonLinesRecordLog(path, StopRecord).read() == [record]
