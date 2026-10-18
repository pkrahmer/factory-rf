"""A stop record is one raised or cleared event of a stop, kept as one JSON line."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.stops import StopRecord, parse_stop_records, stop_records_text

AT = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
FIRST = StopRecord(event="raised", scope="repository", reason="fetch_failed", at=AT)
SECOND = StopRecord(
    event="cleared", scope="machine", reason="disk_low", at=AT.replace(minute=5), instance="self"
)
UNKNOWN_REASON = (
    '{"event":"raised","scope":"repository","reason":"bogus",'
    '"at":"2026-10-18T10:00:00Z","instance":null}\n'
)


def _line(record: StopRecord) -> str:
    return record.model_dump_json() + "\n"


@pytest.mark.parametrize(
    ("fields", "accepted"),
    [
        pytest.param({"scope": "machine", "reason": "disk_low"}, True, id="machine-disk-low"),
        pytest.param(
            {"scope": "machine", "reason": "preflight_failed"}, True, id="machine-preflight"
        ),
        pytest.param({"scope": "repository", "reason": "fetch_failed"}, True, id="repository"),
        pytest.param({"scope": "repository", "reason": "disk_low"}, False, id="disk-low-repo"),
        pytest.param({"scope": "machine", "reason": "fetch_failed"}, False, id="fetch-machine"),
        pytest.param(
            {"event": "paused", "scope": "repository", "reason": "fetch_failed"},
            False,
            id="unknown-event",
        ),
    ],
)
def test_a_stop_record_accepts_a_known_event_and_the_scope_of_its_reason(
    fields: dict[str, object], accepted: bool
) -> None:
    model: type[BaseModel] = StopRecord
    values: dict[str, object] = {"event": "raised", "at": AT, **fields}

    if accepted:
        record = model(**values)
        assert isinstance(record, StopRecord)
        assert (record.scope, record.reason) == (fields["scope"], fields["reason"])
    else:
        with pytest.raises(ValidationError):
            model(**values)


@pytest.mark.parametrize(
    ("records", "expected"),
    [
        pytest.param(
            [
                StopRecord(
                    event="raised", scope="machine", reason="disk_low", at=AT, instance="self"
                )
            ],
            '{"event":"raised","scope":"machine","reason":"disk_low",'
            '"at":"2026-10-18T10:00:00Z","instance":"self"}\n',
            id="one-record",
        ),
        pytest.param([], "", id="no-records"),
    ],
)
def test_the_records_text_is_one_json_line_per_record_in_field_order(
    records: list[StopRecord], expected: str
) -> None:
    assert stop_records_text(records) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(_line(FIRST) + _line(SECOND), [FIRST, SECOND], id="two-records"),
        pytest.param(
            _line(FIRST) + "\n" + "not json\n" + UNKNOWN_REASON + _line(SECOND),
            [FIRST, SECOND],
            id="invalid-lines-between",
        ),
        pytest.param("", [], id="empty"),
    ],
)
def test_parsing_keeps_the_records_that_validate_in_order(
    text: str, expected: list[StopRecord]
) -> None:
    assert parse_stop_records(text) == expected
