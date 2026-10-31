"""The wiring of the idle shutdown's action: `sudo` by default, the loop's stop with `exit`."""

from collections.abc import Callable
from datetime import timedelta

import pytest

from factory.adapters.power_off import ProcessExit, SystemctlPowerOff
from factory.application.boundaries import Boundaries
from factory.domain.settings import read_settings
from factory.entry.wiring import idle_shutdown_of
from settings_support import BASE


@pytest.mark.parametrize("minutes", [pytest.param(0, id="off"), pytest.param(30, id="thirty")])
def test_without_an_action_the_idle_shutdown_powers_the_machine_off(
    boundaries: Boundaries, minutes: int
) -> None:
    settings = read_settings({**BASE, "FACTORY_IDLE_SHUTDOWN_MINUTES": str(minutes)})

    shutdown = idle_shutdown_of(settings, boundaries)

    assert settings.idle_shutdown_action == "poweroff"
    if minutes == 0:
        assert shutdown is None
        return
    assert shutdown is not None
    assert shutdown.limit == timedelta(minutes=30)
    assert isinstance(shutdown.power, SystemctlPowerOff)


@pytest.mark.parametrize(
    ("minutes", "given", "outcome"),
    [
        pytest.param(30, True, "exit", id="exit-with-a-stop"),
        pytest.param(30, False, "refused", id="exit-without-a-stop"),
        pytest.param(0, True, "off", id="exit-with-the-shutdown-off"),
    ],
)
def test_the_exit_action_stops_the_loop_it_is_given(
    boundaries: Boundaries, minutes: int, outcome: str, *, given: bool
) -> None:
    settings = boundaries.settings.model_copy(
        update={"idle_shutdown_minutes": minutes, "idle_shutdown_action": "exit"}
    )
    calls: list[str] = []
    request_stop: Callable[[], None] | None = (lambda: calls.append("stop")) if given else None

    if outcome == "refused":
        with pytest.raises(
            ValueError, match="^the idle shutdown's exit needs a way to stop the loop$"
        ):
            idle_shutdown_of(settings, boundaries, request_stop)
        return
    shutdown = idle_shutdown_of(settings, boundaries, request_stop)
    if outcome == "off":
        assert shutdown is None
        assert calls == []
        return
    assert shutdown is not None
    assert shutdown.limit == timedelta(minutes=30)
    assert isinstance(shutdown.power, ProcessExit)
    shutdown.power.power_off()
    assert calls == ["stop"]
