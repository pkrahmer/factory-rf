"""The disk record: the instance's folders measured, kept in the records and the factory log."""

from collections.abc import Callable
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.machine import DiskSpace
from factory.domain.disk import DiskOccasion, DiskRecord, DiskUse, disk_line
from factory.domain.settings import InstanceSettings


class DiskRecorder:
    """Measures the instance's folders and keeps the measure in the records and the factory log."""

    def __init__(self, boundaries: Boundaries) -> None:
        self._boundaries = boundaries

    def record(self, occasion: DiskOccasion) -> DiskRecord | None:
        """Measure, append and log one record.

        None when the boundaries have no disk, no disk records or no settings.
        """
        disk = self._boundaries.disk
        records = self._boundaries.disk_records
        settings = self._boundaries.settings
        if disk is None or records is None or settings is None:
            return None
        record = DiskRecord(
            at=self._boundaries.clock.now(),
            occasion=occasion,
            folders=[_measure(disk, folder) for folder in _folders(settings)],
        )
        log = self._boundaries.log
        log.line(disk_line(record))
        try:
            records.append(record)
        except OSError as error:
            # The record is a watch on the disk: a full disk must not stop the instance.
            log.line(f"cannot write the disk record: {error}")
        return record

    def last(self) -> DiskRecord | None:
        """The latest record in the records, whatever its occasion.

        None without a record or without a record log.
        """
        records = self._boundaries.disk_records
        if records is None:
            return None
        written = records.read()
        return written[-1] if written else None


def _folders(settings: InstanceSettings) -> list[Path]:
    folders = [settings.checkout.parent, settings.state_directory]
    if settings.temporary_directory is not None:
        folders.append(settings.temporary_directory)
    return folders


def _measure(disk: DiskSpace, folder: Path) -> DiskUse:
    return DiskUse(
        path=str(folder),
        free_bytes=_bytes_or_unknown(disk.free_bytes, folder),
        used_bytes=_bytes_or_unknown(disk.used_bytes, folder),
    )


def _bytes_or_unknown(measure: Callable[[Path], int], folder: Path) -> int | None:
    try:
        return measure(folder)
    except OSError:
        return None
