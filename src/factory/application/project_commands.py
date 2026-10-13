"""The interface through which the factory reaches a project's build."""

from abc import ABC, abstractmethod
from datetime import timedelta

from factory.domain.checks import CheckResult


class ProjectCommands(ABC):
    """The project's named commands, such as `check`, `lint` and `test`."""

    @abstractmethod
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `command` until it ends or reaches `time_limit`.

        A red or timed-out command is a result; `ProjectCommandError` means it could not start.
        """
