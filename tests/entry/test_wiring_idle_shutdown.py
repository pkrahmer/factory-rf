"""The wiring of the idle shutdown: off at zero, else on the instance's clock, log and `sudo`."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.power_off import SystemctlPowerOff
from factory.application.boundaries import Boundaries
from factory.entry.wiring import idle_shutdown_of
from power_support import IDLE


def _calls(record: Path) -> list[str]:
    return record.read_text(encoding="utf-8").splitlines() if record.exists() else []


@pytest.mark.parametrize("minutes", [pytest.param(0, id="off"), pytest.param(30, id="thirty")])
def test_the_idle_shutdown_is_wired_from_the_settings(
    boundaries: Boundaries,
    clock: ManualClock,
    sudo_stand_in: Path,
    tmp_path: Path,
    minutes: int,
) -> None:
    settings = boundaries.settings.model_copy(update={"idle_shutdown_minutes": minutes})

    shutdown = idle_shutdown_of(settings, boundaries)

    assert _calls(sudo_stand_in) == []
    if minutes == 0:
        assert shutdown is None
        return
    assert shutdown is not None
    assert shutdown.limit == timedelta(minutes=30)
    assert isinstance(shutdown.power, SystemctlPowerOff)
    clock.advance(timedelta(minutes=30))
    shutdown.observe(IDLE)
    assert _calls(sudo_stand_in) == ["-n /usr/bin/systemctl poweroff"]
    log = (tmp_path / "state" / "factory.log").read_text(encoding="utf-8")
    assert "idle shutdown: " in log
