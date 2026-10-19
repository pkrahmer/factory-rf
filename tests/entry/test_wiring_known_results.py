"""The wired boundaries keep the known results in the state directory."""

from datetime import UTC, datetime
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.known_results import ResultKey, ResultRecord
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from git_support import clone
from wiring_support import CREDENTIAL

RECORD = ResultRecord(
    key=ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None),
    at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    status="passed",
    last_line="check: green",
    duration_seconds=12.5,
)


def test_the_built_known_results_are_written_to_the_state_directory(
    remote: Path, local_settings: InstanceSettings
) -> None:
    clone(remote, local_settings.checkout)
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.result_records, JsonLinesRecordLog)
    boundaries.result_records.append(RECORD)

    path = local_settings.state_directory / "records" / "known-results.jsonl"
    assert JsonLinesRecordLog(path, ResultRecord).read() == [RECORD]
    assert isinstance(boundaries.project_commands, RecordingProjectCommands)
