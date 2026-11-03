"""In a job, a machine stop that stands for ten minutes ends the loop and `factory-run` with 1."""

import threading
from datetime import timedelta
from pathlib import Path
from typing import Literal, override

import pytest

import factory.entry.run as run_module
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick, TickOutcome
from factory.domain.settings import STATE_VARIABLE, InstanceSettings
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.entry.run import main, run_instance
from factory.entry.wiring import health_store
from power_support import IDLE

DETAIL = "tool:uv: uv is not on the PATH"
MACHINE_STOP = ("machine", "preflight_failed")
REPOSITORY_STOP = ("repository", "main_branch_failing")
IDLE_EXIT_LINE = "idle shutdown: idle for 30 minutes, ending the factory's process"

# What a step does to the machine's stops: raise one at the step's time, lift it, or leave it.
Action = Literal["raise", "lift", "stand", "idle"]
# (minutes and seconds after the loop starts at which a tick runs, what it does)
Step = tuple[int, int, Action]


def _line(reason: str) -> str:
    return (
        "machine stop: standing for 10 minutes in a job, ending the factory's process: "
        f"{reason}: {DETAIL}"
    )


class _StopTick(Tick):
    """Moves the clock to each step's time and raises, lifts or keeps one stop there."""

    def __init__(
        self,
        clock: ManualClock,
        state_directory: Path,
        stop: tuple[str, str],
        steps: list[Step],
    ) -> None:
        self._clock = clock
        self._start = clock.now()
        self._health = health_store(state_directory)
        self._scope, self._reason = stop
        self._steps = list(steps)
        self.runs = 0

    @property
    def exhausted(self) -> bool:
        """True once every step has run."""
        return not self._steps

    @override
    def run(self) -> TickOutcome:
        minutes, seconds, action = self._steps.pop(0)
        self.runs += 1
        self._clock.advance(
            self._start + timedelta(minutes=minutes, seconds=seconds) - self._clock.now()
        )
        stopped = TickOutcome.model_validate({"stopped": self._reason})
        if action == "raise":
            stop = RepositoryStop.model_validate(
                {
                    "scope": self._scope,
                    "reason": self._reason,
                    "detail": DETAIL,
                    "at": self._clock.now(),
                }
            )
            self._health.write(self._health.read().with_stop(stop))
            return stopped
        if action == "lift":
            status = self._health.read()
            self._health.write(
                HealthStatus(stops=[each for each in status.stops if each.reason != self._reason])
            )
            return IDLE
        if action == "stand":
            return stopped
        return IDLE


class _Outcome:
    """What one run of `main` left: its status, the tick, the loop's stop events and the log."""

    def __init__(self, status: int, tick: _StopTick, stops: list[threading.Event], log: str):
        self.status = status
        self.tick = tick
        self.stops = stops
        self.log = log


@pytest.fixture
def run_main(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    tmp_path: Path,
) -> "_RunMain":
    """Return a call that runs `main` over scripted ticks with the given idle shutdown."""
    return _RunMain(
        instance_settings,
        hosting,
        clock=clock,
        monkeypatch=monkeypatch,
        environment=environment,
        tmp_path=tmp_path,
    )


class _RunMain:
    def __init__(
        self,
        settings: InstanceSettings,
        hosting: FakeHostingService,
        *,
        clock: ManualClock,
        monkeypatch: pytest.MonkeyPatch,
        environment: dict[str, str],
        tmp_path: Path,
    ) -> None:
        self._settings = settings
        self._hosting = hosting
        self._clock = clock
        self._monkeypatch = monkeypatch
        self._environment = environment
        self._tmp_path = tmp_path

    def __call__(
        self, minutes: int, action: str, steps: list[Step], stop: tuple[str, str] = MACHINE_STOP
    ) -> _Outcome:
        state_directory = self._settings.state_directory
        tick = _StopTick(self._clock, state_directory, stop, steps)

        def build(_boundaries: Boundaries, _settings: InstanceSettings) -> Tick:
            return tick

        self._monkeypatch.setattr(run_module, "build_tick", build)
        stops: list[threading.Event] = []

        def runner(given: InstanceSettings) -> None:
            settings = self._settings.model_copy(
                update={
                    "idle_shutdown_minutes": given.idle_shutdown_minutes,
                    "idle_shutdown_action": given.idle_shutdown_action,
                }
            )
            event = threading.Event()
            stops.append(event)
            run_instance(
                settings,
                sleep=lambda _seconds: None,
                # The script's end stops the loop too, so that a missed stop cannot run forever.
                should_stop=lambda: event.is_set() or tick.exhausted,
                hosting=self._hosting,
                request_stop=event.set,
            )

        status = main(
            {
                **self._environment,
                STATE_VARIABLE: str(state_directory),
                "FACTORY_IDLE_SHUTDOWN_MINUTES": str(minutes),
                "FACTORY_IDLE_SHUTDOWN_ACTION": action,
            },
            runner=runner,
            state_directory=self._tmp_path,
            clock=self._clock,
        )
        log = (state_directory / "factory.log").read_text(encoding="utf-8")
        return _Outcome(status, tick, stops, log)


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one(
    run_main: _RunMain,
) -> None:
    outcome = run_main(
        30,
        "exit",
        [(0, 0, "raise"), (5, 0, "stand"), (9, 0, "stand"), (10, 0, "stand"), (11, 0, "stand")],
    )

    assert outcome.status == 1
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 4
    assert not outcome.tick.exhausted
    assert outcome.log.count(_line("preflight_failed")) == 1


@pytest.mark.usefixtures("on_the_manual_clock")
@pytest.mark.parametrize(
    ("steps", "ends"),
    [
        pytest.param([(0, 0, "raise"), (9, 59, "stand")], False, id="9-minutes-59-seconds"),
        pytest.param([(0, 0, "raise"), (10, 0, "stand"), (10, 30, "stand")], True, id="10-minutes"),
    ],
)
def test_a_machine_stop_ends_the_loop_from_ten_minutes_on(
    run_main: _RunMain, *, steps: list[Step], ends: bool
) -> None:
    outcome = run_main(30, "exit", steps)

    assert [stop.is_set() for stop in outcome.stops] == [ends]
    assert outcome.tick.runs == 2
    assert outcome.tick.exhausted is not ends
    assert (_line("preflight_failed") in outcome.log) is ends
    assert outcome.status == (1 if ends else 0)


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_lifted_machine_stop_ends_nothing_and_a_new_one_counts_from_its_own_time(
    run_main: _RunMain,
) -> None:
    outcome = run_main(
        30,
        "exit",
        [
            (0, 0, "raise"),
            (5, 0, "lift"),
            (8, 0, "raise"),
            (10, 0, "stand"),
            (17, 59, "stand"),
            (18, 0, "stand"),
            (19, 0, "stand"),
        ],
    )

    assert outcome.status == 1
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 6
    assert not outcome.tick.exhausted
    assert outcome.log.count(_line("preflight_failed")) == 1


@pytest.mark.usefixtures("on_the_manual_clock")
@pytest.mark.parametrize(
    ("minutes", "action", "stop"),
    [
        pytest.param(30, "poweroff", MACHINE_STOP, id="poweroff"),
        pytest.param(0, "exit", MACHINE_STOP, id="idle-shutdown-off"),
        pytest.param(30, "exit", REPOSITORY_STOP, id="repository-stop"),
    ],
)
def test_a_standing_stop_ends_nothing_where_the_rule_does_not_hold(
    run_main: _RunMain, *, minutes: int, action: str, stop: tuple[str, str]
) -> None:
    outcome = run_main(
        minutes,
        action,
        [(0, 0, "raise"), (10, 0, "stand"), (20, 0, "stand"), (31, 0, "stand")],
        stop,
    )

    assert outcome.status == 0
    assert [each.is_set() for each in outcome.stops] == [False]
    assert outcome.tick.runs == 4
    assert outcome.tick.exhausted
    assert "machine stop: standing for 10 minutes" not in outcome.log


@pytest.mark.usefixtures("on_the_manual_clock")
def test_the_idle_exit_without_a_stop_still_ends_the_loop_with_status_zero(
    run_main: _RunMain,
) -> None:
    outcome = run_main(
        30, "exit", [(10, 0, "idle"), (20, 0, "idle"), (30, 0, "idle"), (31, 0, "idle")]
    )

    assert outcome.status == 0
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 3
    assert not outcome.tick.exhausted
    assert IDLE_EXIT_LINE in outcome.log
    assert "machine stop: standing for 10 minutes" not in outcome.log
