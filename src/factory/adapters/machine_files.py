"""The machine's readings from the user slice's cgroup files and from `/proc/meminfo`."""

from pathlib import Path

from factory.application.machine import MachineReadings
from factory.domain.machine import (
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
        cpu = _text(self._slice / _CPU_STAT)
        cpu_pressure = _text(self._slice / _CPU_PRESSURE)
        memory_pressure = _text(self._slice / _MEMORY_PRESSURE)
        return MachineTotals(
            cpu_seconds=None if cpu is None else cpu_usage_seconds(cpu),
            cpu_wait_seconds=None if cpu_pressure is None else pressure_total_seconds(cpu_pressure),
            memory_wait_seconds=None
            if memory_pressure is None
            else pressure_total_seconds(memory_pressure),
        )

    def memory_peak_bytes(self) -> int | None:
        """The number the slice's `memory.peak` holds."""
        text = _text(self._slice / _MEMORY_PEAK)
        if text is None or not text.strip().isdigit():
            return None
        return int(text)

    def memory_total_bytes(self) -> int | None:
        """`MemTotal` of the meminfo file, in bytes."""
        text = _text(self._meminfo)
        return None if text is None else mem_total_bytes(text)


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
