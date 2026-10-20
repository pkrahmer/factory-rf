"""An append-only file of records, one JSON object per line."""

from pathlib import Path
from typing import override

from pydantic import BaseModel, ValidationError

from factory.application.files import RecordLog


class JsonLinesRecordLog[R: BaseModel](RecordLog[R]):
    """The records of one model in a JSON Lines file at a path."""

    def __init__(self, path: Path, model: type[R]) -> None:
        self._path = path
        self._model = model

    @override
    def append(self, record: R) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # One write per record, so concurrent appends never interleave inside a line.
        with self._path.open("a", encoding="utf-8") as file:
            file.write(record.model_dump_json() + "\n")

    @override
    def read(self) -> list[R]:
        if not self._path.exists():
            return []
        # Split the bytes at the line feed alone: `str.splitlines` would also cut a record
        # at U+2028, U+2029 or U+0085 inside its text.
        lines = self._path.read_bytes().split(b"\n")
        return [record for line in lines if (record := self._parse(line)) is not None]

    def _parse(self, line: bytes) -> R | None:
        try:
            text = line.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            # A kill during a write can cut the last line inside a multibyte character.
            return None
        if not text.strip():
            return None
        try:
            return self._model.model_validate_json(text)
        except ValidationError:
            # A kill during a write can tear the last line; the others still count.
            return None
