"""The idle shutdown's exit ends the instance's loop, and `factory-run` with status 0."""

import os
import threading
from pathlib import Path
from typing import override

import pytest

from factory.application.tick import TickOutcome
from factory.entry.run import run_until_stopped
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.adapters.clock import ManualClock
from factory.shared.domain.settings import InstanceSettings
from power_support import IDLE, OTHER
from scripted_tick_support import ScriptedTick, Step, run_loop, run_main, scripted

LINE = "idle shutdown: idle for 1 minutes, powering the machine off"
EXIT_LINE = "idle shutdown: idle for 1 minutes, ending the factory's process"


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
    tick = scripted(clock, steps, monkeypatch)

    stop = run_loop(settings, tick, hosting)

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
    tick = scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)

    run = run_main(
        instance_settings,
        tick,
        hosting,
        variables={
            **environment,
            "FACTORY_IDLE_SHUTDOWN_MINUTES": "1",
            "FACTORY_IDLE_SHUTDOWN_ACTION": "exit",
        },
        state_directory=tmp_path,
        clock=clock,
    )

    assert run.status == 0
    assert [stop.is_set() for stop in run.stops] == [True]
    assert tick.runs == 1


class _ScriptBoundEvent(threading.Event):
    """An event whose `wait` returns at once, and fails once the script has run out."""

    def __init__(self, tick: ScriptedTick[TickOutcome]) -> None:
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
    tick = scripted(clock, [(0, 30, IDLE), (0, 59, IDLE), (1, 0, IDLE), (1, 30, IDLE)], monkeypatch)
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
    tick = scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)

    stop = run_loop(settings, tick, hosting)

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
    tick = scripted(clock, [(1, 0, IDLE), (1, 30, IDLE)], monkeypatch)

    run_loop(settings, tick, hosting)

    idle_lines = [each for each in _log(settings).splitlines() if "idle shutdown: idle" in each]
    assert len(idle_lines) == 1
    assert idle_lines[0].endswith(line)
