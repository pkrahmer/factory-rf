"""The low-disk fault: free bytes in gigabytes and the paths with too little room."""

from collections.abc import Mapping
from pathlib import Path

from factory.domain.settings import MIN_FREE_SPACE_VARIABLE

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
