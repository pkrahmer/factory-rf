"""The append-only file of records, one JSON object per line."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.files import RecordLog
from factory.domain.checks import TargetTime
from factory.domain.command_records import CommandRecord

STARTED_AT = datetime(2026, 10, 17, 9, 0, tzinfo=UTC)


def _record(command: str, offset: int) -> CommandRecord:
    return CommandRecord(
        command=command,
        commit="a" * 40,
        started_at=STARTED_AT + timedelta(minutes=offset),
        duration_seconds=12.5 + offset,
        status="passed",
        exit_status=0,
        targets=[TargetTime(target="lint", seconds=3.0)],
    )


def test_appended_records_read_back_equal_and_in_order_and_the_folder_is_created(
    tmp_path: Path,
) -> None:
    path = tmp_path / "state" / "records" / "project-commands.jsonl"
    log: RecordLog[CommandRecord] = JsonLinesRecordLog(path, CommandRecord)
    records = [_record("check", 0), _record("lint", 1), _record("test", 2)]

    assert log.read() == []
    assert not path.parent.exists()
    for record in records:
        log.append(record)

    assert log.read() == records
    assert len(path.read_text(encoding="utf-8").splitlines()) == len(records)


def test_lines_that_do_not_validate_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "project-commands.jsonl"
    valid = [_record("check", 0), _record("lint", 1), _record("test", 2)]
    lines = [valid[0].model_dump_json(), valid[1].model_dump_json(), '{"command":']
    lines += [valid[2].model_dump_json(), "not json"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert JsonLinesRecordLog(path, CommandRecord).read() == valid
