# SPDX-License-Identifier: Apache-2.0
"""The machine's readings in text: build warnings, sizes in GB, cgroup totals and the memory."""

import math
import re

from pydantic import BaseModel, ConfigDict

_WARNING = re.compile(r"warn", re.IGNORECASE)
# A slim base lacks the manual pages, and apt warns once for each link it cannot make.
_APT_ALTERNATIVES = re.compile(r"update-alternatives: warning:", re.IGNORECASE)
_BYTES_PER_GIGABYTE = 10**9
_MICROSECONDS_PER_SECOND = 1_000_000
_BYTES_PER_KILOBYTE = 1024


class MachineTotals(BaseModel):
    """The kernel's running totals of the user's containers, in seconds; `None` when unread."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cpu_seconds: float | None
    cpu_wait_seconds: float | None
    memory_wait_seconds: float | None


def count_warnings(output: str) -> int:
    """The lines of a build's output that warn, apt's `update-alternatives` warnings left out."""
    return sum(
        1
        for line in output.splitlines()
        if _WARNING.search(line) and not _APT_ALTERNATIVES.search(line)
    )


def gigabytes(size: int) -> str:
    """`size` bytes in GB of 10^9 bytes, with two decimals."""
    return f"{size / _BYTES_PER_GIGABYTE:.2f}"


def pressure_total_seconds(text: str) -> float | None:
    """The `total` of the `some` line of a pressure file, in seconds; `None` when unreadable."""
    for line in text.splitlines():
        words = line.split()
        if words[:1] == ["some"]:
            fields = dict(word.partition("=")[::2] for word in words[1:])
            return _microseconds(fields.get("total"))
    return None


def cpu_usage_seconds(text: str) -> float | None:
    """The `usage_usec` of a `cpu.stat` file, in seconds; `None` when unreadable."""
    return _microseconds(_keyed_value(text, "usage_usec"))


def mem_total_bytes(meminfo: str) -> int | None:
    """`MemTotal` of `/proc/meminfo`, given in kB, in bytes; `None` when unreadable."""
    value = _keyed_value(meminfo, "MemTotal:")
    if value is None or not value.isdigit():
        return None
    return int(value) * _BYTES_PER_KILOBYTE


def machine_differences(start: MachineTotals | None, end: MachineTotals) -> MachineTotals:
    """The totals a run added: `end` minus `start`, each `None` where either reading is."""
    if start is None:
        return MachineTotals(cpu_seconds=None, cpu_wait_seconds=None, memory_wait_seconds=None)
    return MachineTotals(
        cpu_seconds=_difference(start.cpu_seconds, end.cpu_seconds),
        cpu_wait_seconds=_difference(start.cpu_wait_seconds, end.cpu_wait_seconds),
        memory_wait_seconds=_difference(start.memory_wait_seconds, end.memory_wait_seconds),
    )


def _keyed_value(text: str, key: str) -> str | None:
    for line in text.splitlines():
        words = line.split()
        if words[:1] == [key] and len(words) > 1:
            return words[1]
    return None


def _microseconds(value: str | None) -> float | None:
    if value is None or not value.isdigit():
        return None
    return int(value) / _MICROSECONDS_PER_SECOND


def _difference(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    difference = end - start
    # A total that went back means the cgroup began again; the run's share is unknown.
    if difference < 0 or not math.isfinite(difference):
        return None
    return difference
