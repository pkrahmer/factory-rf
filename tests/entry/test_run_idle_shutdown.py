"""The scheduler's tick hands every tick's outcome to the idle shutdown."""

from datetime import timedelta
from typing import override

from factory.adapters.clock import ManualClock
from factory.application.idle_shutdown import IdleShutdown
from factory.application.tick import Tick, TickOutcome
from factory.entry.run import activity_tick
from power_support import IDLE, OTHER, CountingPower
from recording_log import RecordingLog


class _ScriptedTick(Tick):
    """Returns its outcomes one per run, in order."""

    def __init__(self, outcomes: list[TickOutcome]) -> None:
        self._outcomes = list(outcomes)

    @override
    def run(self) -> TickOutcome:
        return self._outcomes.pop(0)


class _RecordingShutdown(IdleShutdown):
    """Keeps the outcomes it observes."""

    def __init__(self, clock: ManualClock) -> None:
        super().__init__(timedelta(minutes=30), clock, CountingPower(), RecordingLog())
        self.observed: list[TickOutcome] = []

    @override
    def observe(self, outcome: TickOutcome) -> None:
        self.observed.append(outcome)


def test_the_activity_tick_hands_each_outcome_to_the_idle_shutdown(clock: ManualClock) -> None:
    idle = _RecordingShutdown(clock)
    serve = activity_tick(_ScriptedTick([IDLE, OTHER]), idle)

    first = serve()
    second = serve()

    assert (first, second) == (False, True)
    assert idle.observed == [IDLE, OTHER]
