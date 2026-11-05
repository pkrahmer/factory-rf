"""A tick that follows a script on the manual clock, and runs of the loop and `main` over it."""

import threading
from collections.abc import Callable, Mapping
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

import factory.entry.run as run_module
from factory.entry.run import main, run_instance
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.tick import Tick, TickOutcome
from factory.shared.adapters.clock import ManualClock
from factory.shared.domain.settings import InstanceSettings

# (minutes and seconds after the loop starts at which a tick runs, its outcome)
Step = tuple[int, int, TickOutcome]


class ScriptedTick[A](Tick):
    """Moves the clock to each step's time and plays its action, one step per run."""

    def __init__(
        self,
        clock: ManualClock,
        steps: list[tuple[int, int, A]],
        play: Callable[[A], TickOutcome],
    ) -> None:
        self._clock = clock
        self._start = clock.now()
        self._steps = list(steps)
        self._play = play
        self.runs = 0

    @property
    def exhausted(self) -> bool:
        """True once every step has run."""
        return not self._steps

    @override
    def run(self, *, fetched: bool = False) -> TickOutcome:
        minutes, seconds, action = self._steps.pop(0)
        self.runs += 1
        self._clock.advance(
            self._start + timedelta(minutes=minutes, seconds=seconds) - self._clock.now()
        )
        return self._play(action)


def installed[T: Tick](tick: T, monkeypatch: pytest.MonkeyPatch) -> T:
    """Make `run_instance` build `tick` as its one tick."""

    def build(_boundaries: Boundaries, _settings: InstanceSettings) -> Tick:
        return tick

    monkeypatch.setattr(run_module, "build_tick", build)
    return tick


def scripted(
    clock: ManualClock, steps: list[Step], monkeypatch: pytest.MonkeyPatch
) -> ScriptedTick[TickOutcome]:
    """Install a tick that returns each step's outcome at the step's time."""
    return installed(ScriptedTick(clock, steps, lambda outcome: outcome), monkeypatch)


def run_loop[A](
    settings: InstanceSettings,
    tick: ScriptedTick[A],
    hosting: FakeHostingService,
    *,
    sleep: Callable[[float], None] | None = None,
    stop: threading.Event | None = None,
) -> threading.Event:
    """Run the instance's loop over `tick`; return the event its `request_stop` sets."""
    stop = threading.Event() if stop is None else stop
    sleeps: list[float] = []
    run_instance(
        settings,
        sleep=sleeps.append if sleep is None else sleep,
        # The script's end stops the loop too, so that a missed stop cannot run forever.
        should_stop=lambda: stop.is_set() or tick.exhausted,
        hosting=hosting,
        request_stop=stop.set,
    )
    return stop


class MainRun:
    """What one run of `main` left: its status and the stop event of each loop it ran."""

    def __init__(self, status: int, stops: list[threading.Event]) -> None:
        self.status = status
        self.stops = stops


def run_main[A](
    settings: InstanceSettings,
    tick: ScriptedTick[A],
    hosting: FakeHostingService,
    *,
    variables: Mapping[str, str],
    state_directory: Path,
    clock: ManualClock,
    sleep: Callable[[float], None] | None = None,
) -> MainRun:
    """Run `main` on `variables` with a runner that loops `settings` over `tick`.

    The runner takes the idle shutdown's minutes and action from the settings `main` read.
    """
    stops: list[threading.Event] = []

    def runner(given: InstanceSettings) -> None:
        looped = settings.model_copy(
            update={
                "idle_shutdown_minutes": given.idle_shutdown_minutes,
                "idle_shutdown_action": given.idle_shutdown_action,
            }
        )
        # Kept before the loop runs: a loop that ends by raising returns no event.
        stop = threading.Event()
        stops.append(stop)
        run_loop(looped, tick, hosting, sleep=sleep, stop=stop)

    status = main(variables, runner=runner, state_directory=state_directory, clock=clock)
    return MainRun(status, stops)
