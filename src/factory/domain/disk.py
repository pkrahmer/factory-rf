"""The low-disk fault, the disk record of the instance's folders, and their lines in gigabytes."""

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, NonNegativeInt

from factory.domain.settings import MIN_FREE_SPACE_VARIABLE
from factory.domain.times import UtcDatetime

GIGABYTE = 10**9


def gigabytes(byte_count: int) -> str:
    """`byte_count` in gigabytes of 10**9 bytes, rounded down to one decimal: `3.2`."""
    tenths = byte_count * 10 // GIGABYTE
    return f"{tenths // 10}.{tenths % 10}"


def disk_low_detail(free: Mapping[Path, int], minimum_gb: int) -> str | None:
    """The fault of the paths with less than `minimum_gb` GB free; None if all have enough."""
    faults = [
        f"{path} has {gigabytes(byte_count)} GB free, "
        f"less than the {minimum_gb} GB {MIN_FREE_SPACE_VARIABLE} asks for"
        for path, byte_count in free.items()
        if byte_count < minimum_gb * GIGABYTE
    ]
    return "; ".join(faults) if faults else None


DiskOccasion = Literal["start", "acceptance"]


class DiskUse(BaseModel):
    """One folder: its path, the bytes free on its file system and the bytes under it.

    None is a value that could not be read.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    free_bytes: NonNegativeInt | None
    used_bytes: NonNegativeInt | None


class DiskRecord(BaseModel):
    """The folders' use at one moment, and why it was taken."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    at: UtcDatetime
    occasion: DiskOccasion
    folders: list[DiskUse]


def disk_line(record: DiskRecord) -> str:
    """`disk <occasion>: <path> <free> free, <used> used; ...`, each value in GB or `unknown`."""
    folders = "; ".join(
        f"{use.path} {_amount(use.free_bytes)} free, {_amount(use.used_bytes)} used"
        for use in record.folders
    )
    return f"disk {record.occasion}: {folders}"


def _amount(byte_count: int | None) -> str:
    return "unknown" if byte_count is None else f"{gigabytes(byte_count)} GB"
