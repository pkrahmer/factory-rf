"""A record log that cannot be written, for the paths that survive a full or broken disk."""

from typing import override

from pydantic import BaseModel

from factory.application.files import RecordLog


class UnwritableRecordLog[R: BaseModel](RecordLog[R]):
    """Raises the `OSError` it was given on every `append`; reads as empty."""

    def __init__(self, error: OSError) -> None:
        self._error = error

    @override
    def append(self, record: R) -> None:
        raise self._error

    @override
    def read(self) -> list[R]:
        return []
