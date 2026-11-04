"""A fake of the machine-readings interface, told what each reading answers."""

from factory.application.machine import MachineReadings
from factory.domain.machine import MachineTotals

UNREAD = MachineTotals(cpu_seconds=None, cpu_wait_seconds=None, memory_wait_seconds=None)


class FakeMachineReadings(MachineReadings):
    """Answers the totals, the memory peak and the memory total it was given."""

    def __init__(
        self,
        totals: MachineTotals = UNREAD,
        memory_peak_bytes: int | None = None,
        memory_total_bytes: int | None = None,
    ) -> None:
        self._totals = totals
        self._peak = memory_peak_bytes
        self._total = memory_total_bytes

    def totals(self) -> MachineTotals:
        return self._totals

    def memory_peak_bytes(self) -> int | None:
        return self._peak

    def memory_total_bytes(self) -> int | None:
        return self._total
