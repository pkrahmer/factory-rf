"""The interface through which the factory reaches a project's build."""

from datetime import timedelta
from typing import Protocol

from factory.domain.checks import CheckResult


class ProjectCommands(Protocol):
    """The project's named commands, such as `check`, `lint` and `test`."""

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `command` until it ends or reaches `time_limit`.

        A red or timed-out command is a result; `ProjectCommandError` means it could not start.
        """
        ...
