"""The health status file: JSON, replaced atomically, healthy when missing or damaged."""

from pathlib import Path
from typing import override

from pydantic import ValidationError

from factory.adapters.atomic_file import replace_text
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
        replace_text(self._path, status.model_dump_json())
