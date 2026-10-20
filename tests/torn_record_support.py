"""Known-result records and the torn lines a kill during an append leaves behind."""

from datetime import UTC, datetime

from factory.domain.known_results import ResultKey, ResultRecord

KEY = ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None)


def result_record(last_line: str) -> ResultRecord:
    """A passed record under `KEY` with the given `last_line`."""
    return ResultRecord(
        key=KEY,
        at=datetime(2026, 10, 20, tzinfo=UTC),
        status="passed",
        last_line=last_line,
        duration_seconds=1.0,
    )


def line_of(record: ResultRecord) -> bytes:
    """The record's JSON text as UTF-8, without a line feed."""
    return record.model_dump_json().encode("utf-8")


def torn_inside(record: ResultRecord, character: str, kept: int) -> bytes:
    """The record's line up to `character`, of whose UTF-8 bytes only the first `kept` remain."""
    line = line_of(record)
    return line[: line.index(character.encode("utf-8")) + kept]
