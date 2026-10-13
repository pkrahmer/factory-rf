"""The health status file: JSON, replaced atomically, healthy when missing or damaged."""

import os
import tempfile
from pathlib import Path
from typing import override

from pydantic import ValidationError

from factory.application.machine import HealthStatusStore
from factory.domain.stops import HealthStatus


class JsonHealthStatusFile(HealthStatusStore):
    """Keeps the health status as one JSON file."""

    def __init__(self, path: Path) -> None:
        """Keep the status in the file at `path`."""
        self._path = path

    @override
    def read(self) -> HealthStatus:
        # A damaged file reads as healthy: every stop is raised again while its fault lasts.
        try:
            return HealthStatus.model_validate_json(self._path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValidationError):
            return HealthStatus()

    @override
    def write(self, status: HealthStatus) -> None:
        directory = self._path.parent
        directory.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=directory, prefix=f".{self._path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
                file.write(status.model_dump_json())
            # The replace is atomic, so a reader sees the old file or the new one, never half.
            os.replace(temporary, self._path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
