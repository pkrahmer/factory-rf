# SPDX-License-Identifier: Apache-2.0
"""The machine's readings from the user slice's cgroup files and from `/proc/meminfo`."""

from collections.abc import Callable
from pathlib import Path

from factory.watching.application.machine import MachineReadings
from factory.watching.domain.machine import (
    MachineTotals,
    cpu_usage_seconds,
    mem_total_bytes,
    pressure_total_seconds,
)

_MEMORY_PEAK = "memory.peak"
_CPU_STAT = "cpu.stat"
_CPU_PRESSURE = "cpu.pressure"
_MEMORY_PRESSURE = "memory.pressure"


class CgroupMachineReadings(MachineReadings):
    """Reads the files of a cgroup v2 slice folder and a meminfo file; a missing one is `None`."""

    def __init__(self, slice_folder: Path, meminfo: Path) -> None:
        """Read the slice's files in `slice_folder` and the memory total from `meminfo`."""
        self._slice = slice_folder
        self._meminfo = meminfo

    def totals(self) -> MachineTotals:
        """The slice's CPU usage and the `some` totals of its CPU and memory pressure."""
        return MachineTotals(
            cpu_seconds=_parsed(self._slice / _CPU_STAT, cpu_usage_seconds),
            cpu_wait_seconds=_parsed(self._slice / _CPU_PRESSURE, pressure_total_seconds),
            memory_wait_seconds=_parsed(self._slice / _MEMORY_PRESSURE, pressure_total_seconds),
        )

    def memory_peak_bytes(self) -> int | None:
        """The number the slice's `memory.peak` holds."""
        text = _text(self._slice / _MEMORY_PEAK)
        if text is None or not text.strip().isdigit():
            return None
        return int(text)

    def memory_total_bytes(self) -> int | None:
        """`MemTotal` of the meminfo file, in bytes."""
        return _parsed(self._meminfo, mem_total_bytes)


def _parsed[T](path: Path, parse: Callable[[str], T | None]) -> T | None:
    text = _text(path)
    return None if text is None else parse(text)


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
