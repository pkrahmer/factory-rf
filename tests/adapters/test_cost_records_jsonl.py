"""The cost record sidecar file: one JSON line per run, its reader, writer and faults."""

import json
from abc import ABC
from pathlib import Path

import pytest

from cost_records_support import (
    COMPLETED_LINE,
    REQUIRED,
    STARTED_AT,
    STARTED_LINE,
    _completed,
    _started,
)
from factory.adapters.cost_records_jsonl import (
    JsonLinesCostRecordReader,
    JsonLinesCostRecordWriter,
)
from factory.application.files import CostRecordReader, CostRecordWriter
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CostRecordFormatError

COMPLETED: dict[str, object] = {
    **REQUIRED,
    "status": "completed",
    "duration_seconds": 41.0,
    "end_reason": "completed",
}


def _timed_out(run: str = "c" * 32) -> CostRecord:
    return CostRecord(
        run=run,
        work_item="F0002-S0007",
        stage="tests",
        role="tester",
        attempt=1,
        status="completed",
        started_at=STARTED_AT,
        duration_seconds=2400.0,
        end_reason="time_limit",
    )


def _line(fields: dict[str, object]) -> str:
    return json.dumps(fields, separators=(",", ":"))


def _without(fields: dict[str, object], key: str) -> dict[str, object]:
    return {name: value for name, value in fields.items() if name != key}


def _error_of_parse(text: str) -> CostRecordFormatError:
    with pytest.raises(CostRecordFormatError) as caught:
        JsonLinesCostRecordReader().parse(text)
    return caught.value


def test_render_writes_the_lines_of_the_format() -> None:
    text = JsonLinesCostRecordWriter().render([_completed(), _started()])

    assert text == COMPLETED_LINE + STARTED_LINE


def test_render_keeps_the_order_with_one_line_per_record() -> None:
    records = [_timed_out(), _started(), _completed()]

    lines = JsonLinesCostRecordWriter().render(records).splitlines(keepends=True)

    assert [json.loads(line)["run"] for line in lines] == ["c" * 32, "b" * 32, "a" * 32]
    assert all(line.endswith("\n") for line in lines)


def test_render_of_no_records_is_empty() -> None:
    assert JsonLinesCostRecordWriter().render([]) == ""


def test_render_refuses_a_run_twice() -> None:
    with pytest.raises(CostRecordFormatError) as caught:
        JsonLinesCostRecordWriter().render([_completed("a" * 32), _started("a" * 32)])

    assert caught.value.line == 2
    assert caught.value.fault == "duplicate run: " + "a" * 32


def test_parse_of_render_gives_the_records_back_with_unknowns_and_digits() -> None:
    records = [_started(), _completed(), _timed_out()]

    back = JsonLinesCostRecordReader().parse(JsonLinesCostRecordWriter().render(records))

    assert back == records
    assert str(back[1].cost_usd) == "0.3450"
    assert back[2].turns is None
    assert back[2].tokens is None
    assert back[2].cost_usd is None


def test_parse_ignores_blank_lines() -> None:
    text = "\n   \n" + COMPLETED_LINE + "\t\n" + STARTED_LINE + "\n"

    assert JsonLinesCostRecordReader().parse(text) == [_completed(), _started()]


def test_parse_counts_blank_lines_in_the_line_number() -> None:
    error = _error_of_parse("\n  \n{not json}\n")

    assert error.line == 3
    assert error.fault == "not valid JSON"


def test_parse_of_the_required_keys_leaves_the_rest_unknown() -> None:
    started, completed = JsonLinesCostRecordReader().parse(
        _line(REQUIRED) + "\n" + _line({**COMPLETED, "run": "c" * 32}) + "\n"
    )

    assert started.status == "started"
    assert started.duration_seconds is None
    assert started.end_reason is None
    assert started.turns is None
    assert started.tokens is None
    assert started.cost_usd is None
    assert started.image is None
    assert completed.duration_seconds == 41.0
    assert completed.end_reason == "completed"
    assert completed.turns is None
    assert completed.tokens is None
    assert completed.cost_usd is None
    assert completed.image is None


@pytest.mark.parametrize(
    ("line", "fault"),
    [
        ("{not json}", "not valid JSON"),
        (_line({**COMPLETED, "duration_seconds": float("inf")}), "not valid JSON"),
        ("[1, 2]", "not a JSON object"),
        (_line({**REQUIRED, "extra": 1}), "unknown key: extra"),
        (
            _line({**COMPLETED, "tokens": {"input": 1, "output": 1, "extra": 1}}),
            "unknown key: tokens.extra",
        ),
        (_line(_without(REQUIRED, "run")), "missing key: run"),
        (_line({**COMPLETED, "tokens": {"input": 1}}), "missing key: tokens.output"),
    ],
    ids=[
        "not-json",
        "infinite-duration",
        "list",
        "extra-key",
        "extra-token-key",
        "no-run",
        "no-output-tokens",
    ],
)
def test_parse_names_a_broken_line_and_its_fault(line: str, fault: str) -> None:
    error = _error_of_parse(STARTED_LINE + line + "\n")

    assert error.line == 2
    assert error.fault == fault


@pytest.mark.parametrize(
    ("fields", "prefix"),
    [
        ({**REQUIRED, "status": "done"}, "invalid status"),
        ({**COMPLETED, "turns": -1}, "invalid turns"),
        ({**COMPLETED, "tokens": {"input": -1, "output": 1}}, "invalid tokens.input"),
        ({**COMPLETED, "cost_usd": 0.34}, "invalid cost_usd"),
        ({**COMPLETED, "cost_usd": True}, "invalid cost_usd"),
        ({**COMPLETED, "cost_usd": "abc"}, "invalid cost_usd"),
        ({**COMPLETED, "cost_usd": "-0.01"}, "invalid cost_usd"),
        ({**REQUIRED, "cost_usd": "0.1"}, "invalid record:"),
    ],
    ids=[
        "status",
        "turns",
        "tokens-input",
        "cost-number",
        "cost-boolean",
        "cost-text",
        "cost-negative",
        "started-with-cost",
    ],
)
def test_parse_names_a_bad_value_and_its_key(fields: dict[str, object], prefix: str) -> None:
    error = _error_of_parse(STARTED_LINE + _line(fields) + "\n")

    assert error.line == 2
    assert error.fault.startswith(prefix)


@pytest.mark.parametrize(
    ("fields", "prefix"),
    [
        ({**_without(REQUIRED, "run"), "extra": 1}, "unknown key: extra"),
        ({**_without(COMPLETED, "run"), "turns": -1}, "missing key: run"),
        ({**REQUIRED, "turns": -1, "cost_usd": "0.1"}, "invalid turns"),
    ],
    ids=["unknown-before-missing", "missing-before-invalid", "invalid-before-record"],
)
def test_parse_reports_the_first_fault_of_a_line(fields: dict[str, object], prefix: str) -> None:
    assert _error_of_parse(_line(fields) + "\n").fault.startswith(prefix)


def test_parse_reports_the_first_broken_line() -> None:
    error = _error_of_parse(STARTED_LINE + "{not json}\n" + "[1]\n")

    assert error.line == 2
    assert error.fault == "not valid JSON"


def test_parse_refuses_a_run_twice() -> None:
    error = _error_of_parse(COMPLETED_LINE + STARTED_LINE + _line(REQUIRED) + "\n")

    assert error.line == 3
    assert error.fault == "duplicate run: " + "b" * 32


def test_read_of_a_missing_file_is_no_records(tmp_path: Path) -> None:
    assert JsonLinesCostRecordReader().read(tmp_path / "missing.jsonl") == []


def test_read_parses_a_file(tmp_path: Path) -> None:
    path = tmp_path / "costs.jsonl"
    path.write_text(COMPLETED_LINE + STARTED_LINE, encoding="utf-8")

    assert JsonLinesCostRecordReader().read(path) == [_completed(), _started()]


def test_read_names_the_broken_line_of_a_file(tmp_path: Path) -> None:
    path = tmp_path / "costs.jsonl"
    path.write_text(COMPLETED_LINE + "\n{not json}\n", encoding="utf-8")

    with pytest.raises(CostRecordFormatError) as caught:
        JsonLinesCostRecordReader().read(path)

    assert caught.value.line == 3


def test_write_leaves_the_rendered_text_and_reads_back(tmp_path: Path) -> None:
    path = tmp_path / "costs.jsonl"
    records = [_completed(), _started()]

    JsonLinesCostRecordWriter().write(path, records)

    assert path.read_bytes() == JsonLinesCostRecordWriter().render(records).encode("utf-8")
    assert JsonLinesCostRecordReader().read(path) == records


def test_write_replaces_the_old_content_whole(tmp_path: Path) -> None:
    path = tmp_path / "costs.jsonl"
    path.write_text(COMPLETED_LINE + STARTED_LINE + _line(COMPLETED) + "\n", encoding="utf-8")

    JsonLinesCostRecordWriter().write(path, [_started()])

    assert path.read_bytes() == STARTED_LINE.encode("utf-8")


def test_write_of_no_records_leaves_an_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "costs.jsonl"
    path.write_text(STARTED_LINE, encoding="utf-8")

    JsonLinesCostRecordWriter().write(path, [])

    assert path.read_bytes() == b""


def test_reader_and_writer_implement_abstract_interfaces() -> None:
    assert issubclass(CostRecordReader, ABC)
    assert issubclass(CostRecordWriter, ABC)
    assert CostRecordReader.__abstractmethods__ == {"parse", "read"}
    assert CostRecordWriter.__abstractmethods__ == {"render", "write"}
    assert issubclass(JsonLinesCostRecordReader, CostRecordReader)
    assert issubclass(JsonLinesCostRecordWriter, CostRecordWriter)
