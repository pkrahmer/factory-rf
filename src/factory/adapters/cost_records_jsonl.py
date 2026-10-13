"""The cost record sidecar file: one JSON object per line, one line per agent run."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import override

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from factory.application.files import CostRecordReader, CostRecordWriter
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CostRecordFormatError

_SEPARATORS = (",", ":")
# The rank of each kind of validation fault; the lowest is reported.
_UNKNOWN_KEY, _MISSING_KEY, _INVALID_VALUE, _INVALID_RECORD = range(4)


def _key_path(location: tuple[int | str, ...]) -> str:
    return ".".join(str(part) for part in location)


def _rank(error: ErrorDetails) -> int:
    if error["type"] == "extra_forbidden":
        return _UNKNOWN_KEY
    if error["type"] == "missing":
        return _MISSING_KEY
    if error["loc"]:
        return _INVALID_VALUE
    return _INVALID_RECORD


def _fault(error: ErrorDetails) -> str:
    path = _key_path(error["loc"])
    rank = _rank(error)
    if rank == _UNKNOWN_KEY:
        return f"unknown key: {path}"
    if rank == _MISSING_KEY:
        return f"missing key: {path}"
    if rank == _INVALID_VALUE:
        return f"invalid {path}: {error['msg']}"
    return f"invalid record: {error['msg']}"


def _first_fault(validation_error: ValidationError) -> str:
    # `min` keeps the first of equal rank, and pydantic lists errors in the order of the fields.
    return _fault(min(validation_error.errors(), key=_rank))


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
        raise CostRecordFormatError(number, _first_fault(error)) from error


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
            if record.run in seen_runs:
                raise CostRecordFormatError(number, f"duplicate run: {record.run}")
            seen_runs.add(record.run)
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
            if record.run in seen_runs:
                raise CostRecordFormatError(number, f"duplicate run: {record.run}")
            seen_runs.add(record.run)
        return "".join(_line_of_record(record) for record in records)

    @override
    def write(self, path: Path, records: Sequence[CostRecord]) -> None:
        path.write_text(self.render(records), encoding="utf-8", newline="\n")
