"""The machine's power, switched off through `sudo` and `systemctl`."""

from datetime import timedelta
from pathlib import Path

from factory.adapters.printed_output import failure_detail, no_end_detail
from factory.adapters.process import ProcessRequest, run_process
from factory.application.machine import PowerOff
from factory.domain.errors import PowerOffError

# The one command the machine's `sudoers` line allows the factory.
POWER_OFF_COMMAND = ("-n", "/usr/bin/systemctl", "poweroff")
POWER_OFF_TIME_LIMIT = timedelta(minutes=1)

_ROOT = Path("/")


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
        request = ProcessRequest(
            argv=[self._sudo_executable, *POWER_OFF_COMMAND],
            cwd=_ROOT,
            env=None,
            time_limit=self._time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as error:
            raise PowerOffError(f"cannot start {self._sudo_executable}: {error}") from error
        if result.timed_out:
            raise PowerOffError(no_end_detail(self._time_limit))
        if result.exit_status != 0:
            raise PowerOffError(failure_detail(result.stdout, result.exit_status))
