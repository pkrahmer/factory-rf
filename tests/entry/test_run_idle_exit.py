"""The idle shutdown's exit ends the instance's loop, and `factory-run` with status 0."""

import os
import threading
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

import factory.entry.run as run_module
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.hosting import HostingService
from factory.application.tick import Tick, TickOutcome
from factory.domain.settings import InstanceSettings
from factory.entry.run import main, run_instance, run_until_stopped
from factory.entry.wiring import machine_log
from power_support import IDLE, OTHER
from stage_run_support import INSTANCE
from wiring_support import with_dataset

LINE = "idle shutdown: idle for 1 minutes, powering the machine off"
EXIT_LINE = "idle shutdown: idle for 1 minutes, ending the factory's process"

# (minutes and seconds after the loop starts at which a tick runs, its outcome)
Step = tuple[int, int, TickOutcome]


class _ScriptedTick(Tick):
    """Moves the clock to each step's time and returns its outcome, one step per run."""

    def __init__(self, clock: ManualClock, steps: list[Step]) -> None:
        self._clock = clock
        self._start = clock.now()
        self._steps = list(steps)
        self.runs = 0

    @property
    def exhausted(self) -> bool:
        """True once every step has run."""
        return not self._steps

    @override
    def run(self) -> TickOutcome:
        minutes, seconds, outcome = self._steps.pop(0)
        self.runs += 1
        self._clock.advance(
            self._start + timedelta(minutes=minutes, seconds=seconds) - self._clock.now()
        )
        return outcome


@pytest.fixture
def instance_settings(tmp_path: Path, remote: Path, agent_home: Path) -> InstanceSettings:
    """Return settings on `remote`, the idle shutdown at one minute, everything in `tmp_path`."""
    token = tmp_path / "hosting-token"
    token.write_text("example-value\n", encoding="utf-8")
    state = tmp_path / "instance-state"
    state.mkdir()
    return with_dataset(
        InstanceSettings(
            repository_url=str(remote),
            instance=INSTANCE,
            checkout=tmp_path / "instance-checkout",
            state_directory=state,
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
            token_file=token,
            idle_shutdown_minutes=1,
        ),
        tmp_path,
    )


@pytest.fixture
def on_the_manual_clock(clock: ManualClock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Give the boundaries `run_instance` builds the test's clock and a log on it."""
    original = run_module.build_boundaries

    def built(
        settings: InstanceSettings, token: str, *, hosting: HostingService | None = None
    ) -> Boundaries:
        boundaries = original(settings, token, hosting=hosting)
        return replace(boundaries, clock=clock, log=machine_log(settings.state_directory, clock))

    monkeypatch.setattr(run_module, "build_boundaries", built)


def _scripted(
    clock: ManualClock, steps: list[Step], monkeypatch: pytest.MonkeyPatch
) -> _ScriptedTick:
    tick = _ScriptedTick(clock, steps)

    def build(_boundaries: Boundaries, _settings: InstanceSettings) -> Tick:
        return tick

    monkeypatch.setattr(run_module, "build_tick", build)
    return tick


def _run(
    settings: InstanceSettings, tick: _ScriptedTick, hosting: FakeHostingService
) -> threading.Event:
    stop = threading.Event()
    sleeps: list[float] = []
    run_instance(
        settings,
        sleep=sleeps.append,
        # The script's end stops the loop too, so that a missed stop cannot run forever.
        should_stop=lambda: stop.is_set() or tick.exhausted,
        hosting=hosting,
        request_stop=stop.set,
    )
    return stop


def _log(settings: InstanceSettings) -> str:
    return (settings.state_directory / "factory.log").read_text(encoding="utf-8")


@pytest.mark.usefixtures("on_the_manual_clock")
@pytest.mark.parametrize(
    ("steps", "runs"),
    [
        pytest.param(
            [(0, 30, IDLE), (0, 59, IDLE), (1, 0, IDLE), (1, 30, IDLE)],
            3,
            id="stops-at-the-limit",
        ),
        pytest.param(
            [
                (0, 30, IDLE),
                (0, 45, OTHER),
                (1, 0, IDLE),
                (1, 44, IDLE),
                (1, 45, IDLE),
                (2, 0, IDLE),
            ],
            5,
            id="another-event-starts-the-stretch-again",
        ),
    ],
)
def test_the_idle_exit_stops_the_loop_after_the_tick_that_ends_the_stretch(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    steps: list[Step],
    runs: int,
) -> None:
    settings = instance_settings.model_copy(update={"idle_shutdown_action": "exit"})
    tick = _scripted(clock, steps, monkeypatch)

    stop = _run(settings, tick, hosting)

    assert stop.is_set()
    assert tick.runs == runs
    assert not tick.exhausted
    assert _log(settings).count(EXIT_LINE) == 1


@pytest.mark.usefixtures("on_the_manual_clock")
def test_main_returns_zero_after_the_idle_exit_ends_the_loop(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    tmp_path: Path,
) -> None:
    tick = _scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)
    stops: list[threading.Event] = []

    def runner(given: InstanceSettings) -> None:
        settings = instance_settings.model_copy(
            update={
                "idle_shutdown_minutes": given.idle_shutdown_minutes,
                "idle_shutdown_action": given.idle_shutdown_action,
            }
        )
        stops.append(_run(settings, tick, hosting))

    status = main(
        {
            **environment,
            "FACTORY_IDLE_SHUTDOWN_MINUTES": "1",
            "FACTORY_IDLE_SHUTDOWN_ACTION": "exit",
        },
        runner=runner,
        state_directory=tmp_path,
        clock=clock,
    )

    assert status == 0
    assert [stop.is_set() for stop in stops] == [True]
    assert tick.runs == 1


class _ScriptBoundEvent(threading.Event):
    """An event whose `wait` returns at once, and fails once the script has run out."""

    def __init__(self, tick: _ScriptedTick) -> None:
        super().__init__()
        self._tick = tick

    @override
    def wait(self, timeout: float | None = None) -> bool:
        # A missed stop would otherwise loop on the spent script for ever.
        if self._tick.exhausted:
            raise AssertionError("the loop ran past the end of the script")
        return self.is_set()


@pytest.mark.usefixtures("on_the_manual_clock", "restored_signals")
def test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = instance_settings.model_copy(update={"idle_shutdown_action": "exit"})
    tick = _scripted(
        clock, [(0, 30, IDLE), (0, 59, IDLE), (1, 0, IDLE), (1, 30, IDLE)], monkeypatch
    )
    stop = _ScriptBoundEvent(tick)

    run_until_stopped(settings, stop, hosting=hosting)

    assert stop.is_set()
    assert tick.runs == 3
    assert not tick.exhausted
    assert _log(settings).count(EXIT_LINE) == 1


@pytest.fixture
def refusing_sudo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a `sudo` stand-in first on `PATH` that refuses with exit status 1."""
    folder = tmp_path / "refusing-sudo"
    folder.mkdir()
    sudo = folder / "sudo"
    sudo.write_text(
        "#!/bin/sh\necho 'sudo: a password is required' >&2\nexit 1\n", encoding="utf-8"
    )
    sudo.chmod(0o755)
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ.get('PATH', '')}")


@pytest.mark.usefixtures("on_the_manual_clock", "refusing_sudo")
def test_a_refused_power_off_does_not_stop_the_loop(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = instance_settings.model_copy(update={"idle_shutdown_action": "poweroff"})
    tick = _scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)

    stop = _run(settings, tick, hosting)

    assert not stop.is_set()
    assert tick.runs == 2
    log = _log(settings)
    assert LINE in log
    assert "the factory runs on" in log


@pytest.mark.usefixtures("on_the_manual_clock", "refusing_sudo")
@pytest.mark.parametrize(
    ("action", "line"),
    [
        pytest.param("exit", EXIT_LINE, id="exit"),
        pytest.param("poweroff", LINE, id="poweroff"),
    ],
)
def test_the_idle_line_says_what_the_action_does(
    instance_settings: InstanceSettings,
    hosting: FakeHostingService,
    clock: ManualClock,
    *,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    line: str,
) -> None:
    settings = instance_settings.model_copy(update={"idle_shutdown_action": action})
    tick = _scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)

    _run(settings, tick, hosting)

    idle_lines = [each for each in _log(settings).splitlines() if "idle shutdown: idle" in each]
    assert len(idle_lines) == 1
    assert idle_lines[0].endswith(line)
