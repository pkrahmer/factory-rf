"""In a job, a machine stop that stands for ten minutes ends the loop and `factory-run` with 1."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Literal

import pytest

from factory.application.tick import TickOutcome
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.entry.wiring import health_store
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.adapters.clock import ManualClock
from factory.shared.domain.settings import STATE_VARIABLE, InstanceSettings
from power_support import IDLE
from scripted_tick_support import MainRun, ScriptedTick, installed, run_main

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


def _played(
    clock: ManualClock, state_directory: Path, stop: tuple[str, str]
) -> Callable[[Action], TickOutcome]:
    """Return the play of a step: raise, lift or keep one stop in the health status."""
    health = health_store(state_directory)
    scope, reason = stop
    stopped = TickOutcome.model_validate({"stopped": reason})

    def play(action: Action) -> TickOutcome:
        if action == "raise":
            raised = RepositoryStop.model_validate(
                {"scope": scope, "reason": reason, "detail": DETAIL, "at": clock.now()}
            )
            health.write(health.read().with_stop(raised))
            return stopped
        if action == "lift":
            status = health.read()
            health.write(
                HealthStatus(stops=[each for each in status.stops if each.reason != reason])
            )
            return IDLE
        if action == "stand":
            return stopped
        return IDLE

    return play


class _Outcome:
    """What one run of `main` left: its status, the tick, the loop's stop events and the log."""

    def __init__(self, run: MainRun, tick: ScriptedTick[Action], log: str) -> None:
        self.status = run.status
        self.tick = tick
        self.stops = run.stops
        self.log = log


def _variables(
    environment: dict[str, str], state_directory: Path, minutes: int, action: str
) -> dict[str, str]:
    return {
        **environment,
        STATE_VARIABLE: str(state_directory),
        "FACTORY_IDLE_SHUTDOWN_MINUTES": str(minutes),
        "FACTORY_IDLE_SHUTDOWN_ACTION": action,
    }


def _log(state_directory: Path) -> str:
    return (state_directory / "factory.log").read_text(encoding="utf-8")


@pytest.fixture
def run_stops(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    tmp_path: Path,
) -> "_RunStops":
    """Return a call that runs `main` over scripted ticks with the given idle shutdown."""
    return _RunStops(
        instance_settings,
        hosting,
        clock=clock,
        monkeypatch=monkeypatch,
        environment=environment,
        tmp_path=tmp_path,
    )


class _RunStops:
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
        tick = installed(
            ScriptedTick(self._clock, steps, _played(self._clock, state_directory, stop)),
            self._monkeypatch,
        )
        run = run_main(
            self._settings,
            tick,
            self._hosting,
            variables=_variables(self._environment, state_directory, minutes, action),
            state_directory=self._tmp_path,
            clock=self._clock,
        )
        return _Outcome(run, tick, _log(state_directory))


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one(
    run_stops: _RunStops,
) -> None:
    outcome = run_stops(
        30,
        "exit",
        [(0, 0, "raise"), (5, 0, "stand"), (9, 0, "stand"), (10, 0, "stand"), (11, 0, "stand")],
    )

    assert outcome.status == 1
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 4
    assert not outcome.tick.exhausted
    assert outcome.log.count(_line("preflight_failed")) == 1
    assert outcome.log.splitlines()[-1].endswith(_line("preflight_failed"))


@pytest.mark.usefixtures("on_the_manual_clock")
@pytest.mark.parametrize(
    ("steps", "ends"),
    [
        pytest.param([(0, 0, "raise"), (9, 59, "stand")], False, id="9-minutes-59-seconds"),
        pytest.param([(0, 0, "raise"), (10, 0, "stand"), (10, 30, "stand")], True, id="10-minutes"),
    ],
)
def test_a_machine_stop_ends_the_loop_from_ten_minutes_on(
    run_stops: _RunStops, *, steps: list[Step], ends: bool
) -> None:
    outcome = run_stops(30, "exit", steps)

    assert [stop.is_set() for stop in outcome.stops] == [ends]
    assert outcome.tick.runs == 2
    assert outcome.tick.exhausted is not ends
    assert (_line("preflight_failed") in outcome.log) is ends
    assert outcome.status == (1 if ends else 0)


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_lifted_machine_stop_ends_nothing_and_a_new_one_counts_from_its_own_time(
    run_stops: _RunStops,
) -> None:
    outcome = run_stops(
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
    run_stops: _RunStops, *, minutes: int, action: str, stop: tuple[str, str]
) -> None:
    outcome = run_stops(
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
    run_stops: _RunStops,
) -> None:
    outcome = run_stops(
        30, "exit", [(10, 0, "idle"), (20, 0, "idle"), (30, 0, "idle"), (31, 0, "idle")]
    )

    assert outcome.status == 0
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 3
    assert not outcome.tick.exhausted
    assert IDLE_EXIT_LINE in outcome.log
    assert "machine stop: standing for 10 minutes" not in outcome.log


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_machine_stop_raised_again_on_every_tick_counts_from_its_first_raise(
    run_stops: _RunStops,
) -> None:
    outcome = run_stops(
        30,
        "exit",
        [(0, 0, "raise"), (5, 0, "raise"), (9, 0, "raise"), (10, 0, "raise"), (11, 0, "raise")],
    )

    assert outcome.status == 1
    assert [stop.is_set() for stop in outcome.stops] == [True]
    assert outcome.tick.runs == 4
    assert not outcome.tick.exhausted
    assert outcome.log.count(_line("preflight_failed")) == 1


class _AdvancingSleep:
    """Moves the clock by each pause and keeps the times at which the loop paused."""

    def __init__(self, clock: ManualClock, bound: timedelta) -> None:
        self._clock = clock
        self._end = clock.now() + bound
        self.paused_at: list[timedelta] = []
        self._start = clock.now()

    def __call__(self, seconds: float) -> None:
        self.paused_at.append(self._clock.now() - self._start)
        # A missed stop would otherwise pause on for ever.
        if self._clock.now() > self._end:
            raise AssertionError("the loop ran past its bound")
        self._clock.advance(timedelta(seconds=seconds))


@pytest.mark.usefixtures("on_the_manual_clock")
def test_a_machine_stop_ends_the_loop_after_iterations_that_ran_no_tick(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    tmp_path: Path,
) -> None:
    # A repository that does not exist leaves `prepare` without a tick on every iteration.
    settings = instance_settings.model_copy(
        update={"repository_url": str(tmp_path / "no-such-remote")}
    )
    state_directory = settings.state_directory
    health = health_store(state_directory)
    stop = RepositoryStop.model_validate(
        {"scope": "machine", "reason": "preflight_failed", "detail": DETAIL, "at": clock.now()}
    )
    health.write(HealthStatus(stops=[stop]))
    start = clock.now()
    tick = installed(ScriptedTick(clock, [(0, 0, IDLE)], lambda outcome: outcome), monkeypatch)
    sleep = _AdvancingSleep(clock, timedelta(minutes=30))

    run = run_main(
        settings,
        tick,
        hosting,
        variables=_variables(environment, state_directory, 30, "exit"),
        state_directory=tmp_path,
        clock=clock,
        sleep=sleep,
    )

    assert run.status == 1
    assert [each.is_set() for each in run.stops] == [True]
    assert tick.runs == 0
    assert sleep.paused_at
    assert all(paused < timedelta(minutes=10) for paused in sleep.paused_at)
    assert clock.now() - start >= timedelta(minutes=10)
    log = _log(state_directory)
    assert log.count(_line("preflight_failed")) == 1
    assert log.splitlines()[-1].endswith(_line("preflight_failed"))
