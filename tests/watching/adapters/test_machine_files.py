"""The machine's readings from the user slice's cgroup files and from `/proc/meminfo`."""

from pathlib import Path

import pytest

from factory.watching.adapters.machine_files import CgroupMachineReadings
from factory.watching.domain.machine import MachineTotals

CPU_STAT = "usage_usec 123500000\nuser_usec 100000000\nsystem_usec 23500000\n"
CPU_PRESSURE = (
    "some avg10=0.00 avg60=0.00 avg300=0.00 total=2500000\n"
    "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
)
MEMORY_PRESSURE = (
    "some avg10=0.00 avg60=0.00 avg300=0.00 total=750000\n"
    "full avg10=0.00 avg60=0.00 avg300=0.00 total=500000\n"
)
MEMINFO = "MemTotal:       15625000 kB\nMemFree:         2000000 kB\n"
FILES = {
    "memory.peak": "8100000000\n",
    "cpu.stat": CPU_STAT,
    "cpu.pressure": CPU_PRESSURE,
    "memory.pressure": MEMORY_PRESSURE,
}


@pytest.fixture
def readings(tmp_path: Path) -> CgroupMachineReadings:
    """Readings on a slice folder that holds every file, and on a meminfo beside it."""
    slice_folder = tmp_path / "user-1000.slice"
    slice_folder.mkdir()
    for name, text in FILES.items():
        (slice_folder / name).write_text(text, encoding="utf-8")
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(MEMINFO, encoding="utf-8")
    return CgroupMachineReadings(slice_folder, meminfo)


def test_the_memory_peak_is_what_the_slice_s_file_holds(
    readings: CgroupMachineReadings, tmp_path: Path
) -> None:
    assert readings.memory_peak_bytes() == 8_100_000_000
    (tmp_path / "user-1000.slice" / "memory.peak").write_text("8200000000\n", encoding="utf-8")

    assert readings.memory_peak_bytes() == 8_200_000_000


def test_the_memory_total_is_mem_total_of_meminfo_in_bytes(
    readings: CgroupMachineReadings,
) -> None:
    assert readings.memory_total_bytes() == 15_625_000 * 1024


def test_the_totals_are_the_cpu_usage_and_the_some_lines_in_seconds(
    readings: CgroupMachineReadings,
) -> None:
    assert readings.totals() == MachineTotals(
        cpu_seconds=123.5, cpu_wait_seconds=2.5, memory_wait_seconds=0.75
    )


def test_a_missing_file_gives_none(tmp_path: Path) -> None:
    missing = CgroupMachineReadings(tmp_path / "no-such.slice", tmp_path / "no-meminfo")

    assert missing.memory_peak_bytes() is None
    assert missing.memory_total_bytes() is None
    assert missing.totals() == MachineTotals(
        cpu_seconds=None, cpu_wait_seconds=None, memory_wait_seconds=None
    )
