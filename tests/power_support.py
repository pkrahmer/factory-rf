"""A power switch that counts its calls, and the tick outcomes the idle shutdown tells apart."""

from typing import override

from factory.application.machine import PowerOff
from factory.application.tick import TickOutcome
from factory.domain.errors import PowerOffError
from factory.domain.events import Event

STATE = "a" * 40
IDLE = TickOutcome(event=Event(kind="idle", work_item=None, remote_state=STATE), dispatch="handled")
WAITS = TickOutcome(
    event=Event(
        kind="idle",
        work_item=None,
        remote_state=STATE,
        detail="F0001-S0001 waits for the human",
    ),
    dispatch="handled",
)
OTHER = TickOutcome(
    event=Event(kind="acceptance_due", work_item=None, feature="F0001", remote_state=STATE),
    dispatch="handled",
)
STOPPED = TickOutcome(stopped="main_branch_failing")
IDLE_ERROR = TickOutcome(
    event=Event(kind="idle", work_item=None, remote_state=STATE), dispatch="error"
)


class CountingPower(PowerOff):
    """Counts the calls to `power_off`; raises `error` on each when it is given."""

    def __init__(self, error: PowerOffError | None = None) -> None:
        self.calls = 0
        self._error = error

    @override
    def power_off(self) -> None:
        self.calls += 1
        if self._error is not None:
            raise self._error
