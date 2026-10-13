"""The cost record sidecar file: one JSON object per line, one line per agent run."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import override

from pydantic import ValidationError

from factory.adapters.validation_faults import first_fault
from factory.application.files import CostRecordReader, CostRecordWriter
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CostRecordFormatError

_SEPARATORS = (",", ":")


def _record_of_line(line: str, number: int) -> CostRecord:
    try:
        loaded: object = json.loads(line)
    except json.JSONDecodeError as error:
        raise CostRecordFormatError(number, "not valid JSON") from error
    if not isinstance(loaded, dict):
        raise CostRecordFormatError(number, "not a JSON object")
    try:
        return CostRecord.model_validate(loaded)
    except ValidationError as error:
        raise CostRecordFormatError(number, first_fault(error, "record")) from error


def _check_new_run(record: CostRecord, number: int, seen_runs: set[str]) -> None:
    # A run's line is replaced when it completes, so a second line for it is a fault.
    if record.run in seen_runs:
        raise CostRecordFormatError(number, f"duplicate run: {record.run}")
    seen_runs.add(record.run)


def _line_of_record(record: CostRecord) -> str:
    fields = record.model_dump(mode="json")
    fields["started_at"] = record.started_at.isoformat().removesuffix("+00:00") + "Z"
    fields["cost_usd"] = None if record.cost_usd is None else str(record.cost_usd)
    return json.dumps(fields, separators=_SEPARATORS) + "\n"


class JsonLinesCostRecordReader(CostRecordReader):
    """Reads a cost record file of JSON lines."""

    def __init__(self) -> None:
        """Nothing to prepare; the reader keeps no state."""

    @override
    def parse(self, text: str) -> list[CostRecord]:
        records: list[CostRecord] = []
        seen_runs: set[str] = set()
        # Split on `\n` alone: `splitlines` also breaks at characters a JSON string may hold.
        for number, line in enumerate(text.split("\n"), start=1):
            if not line.strip():
                continue
            record = _record_of_line(line, number)
            _check_new_run(record, number, seen_runs)
            records.append(record)
        return records

    @override
    def read(self, path: Path) -> list[CostRecord]:
        if not path.exists():
            return []
        return self.parse(path.read_text(encoding="utf-8"))


class JsonLinesCostRecordWriter(CostRecordWriter):
    """Writes a cost record file of JSON lines."""

    def __init__(self) -> None:
        """Nothing to prepare; the writer keeps no state."""

    @override
    def render(self, records: Sequence[CostRecord]) -> str:
        seen_runs: set[str] = set()
        for number, record in enumerate(records, start=1):
            _check_new_run(record, number, seen_runs)
        return "".join(_line_of_record(record) for record in records)

    @override
    def write(self, path: Path, records: Sequence[CostRecord]) -> None:
        path.write_text(self.render(records), encoding="utf-8", newline="\n")
