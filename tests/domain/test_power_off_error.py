"""The text of the error a refused or failed power-off raises."""

from factory.domain.errors import PowerOffError


def test_the_power_off_error_says_the_power_off_failed() -> None:
    assert str(PowerOffError("x")) == "power off failed: x"
