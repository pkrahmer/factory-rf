"""The idle shutdown's exit: the power switch that asks the factory's own loop to stop."""

from factory.adapters.power_off import ProcessExit


def test_each_power_off_requests_the_stop_once() -> None:
    calls: list[str] = []
    power = ProcessExit(lambda: calls.append("stop"))

    power.power_off()
    assert calls == ["stop"]
    power.power_off()
    assert calls == ["stop", "stop"]
