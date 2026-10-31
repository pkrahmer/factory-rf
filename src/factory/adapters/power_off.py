"""The machine's power, switched off through `sudo` and `systemctl`, or the loop's stop."""

from collections.abc import Callable
from datetime import timedelta

from factory.adapters.process import run_or_raise
from factory.application.machine import PowerOff
from factory.domain.errors import PowerOffError

# The one command the machine's `sudoers` line allows the factory.
POWER_OFF_COMMAND = ("-n", "/usr/bin/systemctl", "poweroff")
POWER_OFF_TIME_LIMIT = timedelta(minutes=1)


class SystemctlPowerOff(PowerOff):
    """Powers the machine off with `sudo -n /usr/bin/systemctl poweroff`."""

    def __init__(
        self, sudo_executable: str = "sudo", *, time_limit: timedelta = POWER_OFF_TIME_LIMIT
    ) -> None:
        """Run the command through `sudo_executable`, ending it at `time_limit`."""
        self._sudo_executable = sudo_executable
        self._time_limit = time_limit

    def power_off(self) -> None:
        """Run the command; raise `PowerOffError` when it cannot start, fails or does not end."""
        try:
            run_or_raise(
                [self._sudo_executable, *POWER_OFF_COMMAND],
                time_limit=self._time_limit,
                fault=PowerOffError,
            )
        except PowerOffError as error:
            if isinstance(error.__cause__, OSError):
                detail = f"cannot start {self._sudo_executable}: {error.detail}"
                raise PowerOffError(detail) from error.__cause__
            raise


class ProcessExit(PowerOff):
    """Ends the factory's own process instead of the machine, by asking its loop to stop."""

    def __init__(self, request_stop: Callable[[], None]) -> None:
        """Stop the loop through `request_stop`."""
        self._request_stop = request_stop

    def power_off(self) -> None:
        """Ask the loop to stop; it ends after the tick in progress."""
        self._request_stop()
