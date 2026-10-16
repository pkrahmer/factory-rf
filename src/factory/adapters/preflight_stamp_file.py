"""The preflight stamp file: JSON, replaced atomically, no stamp when missing or damaged."""

from pathlib import Path
from typing import override

from pydantic import ValidationError

from factory.adapters.atomic_file import replace_text
from factory.application.preflight import PreflightStampStore
from factory.domain.preflight import PreflightStamp


class JsonPreflightStampFile(PreflightStampStore):
    """Keeps the preflight stamp as one JSON file."""

    def __init__(self, path: Path) -> None:
        """Keep the stamp in the file at `path`."""
        self._path = path

    @override
    def read(self) -> PreflightStamp | None:
        # The stamp is a cache: a damaged file only costs one more run of the preflight.
        try:
            return PreflightStamp.model_validate_json(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValidationError):
            return None

    @override
    def write(self, stamp: PreflightStamp) -> None:
        replace_text(self._path, stamp.model_dump_json())
