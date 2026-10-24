"""The interface through which the factory reaches a project's build, and its recorder."""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import override

from factory.application.files import RecordLog
from factory.application.git import Git
from factory.application.machine import Clock, FactoryLog
from factory.domain.checks import CheckResult
from factory.domain.command_records import CommandRecord
from factory.domain.errors import GitError
from factory.domain.git import CommitId


class ProjectCommands(ABC):
    """The project's named commands, such as `check`, `lint` and `test`."""

    @abstractmethod
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `command` until it ends or reaches `time_limit`.

        A red or timed-out command is a result; `ProjectCommandError` means it could not start.
        """


class RecordingProjectCommands(ProjectCommands):
    """Runs the project commands of another implementation and records every run."""

    def __init__(
        self,
        inner: ProjectCommands,
        git: Git,
        records: RecordLog[CommandRecord],
        clock: Clock,
        log: FactoryLog,
    ) -> None:
        self._inner = inner
        self._git = git
        self._records = records
        self._clock = clock
        self._log = log

    @property
    def inner(self) -> ProjectCommands:
        """The implementation whose runs this one records."""
        return self._inner

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        commit = self._head()
        started_at = self._clock.now()
        result = self._inner.run(command, time_limit=time_limit)
        record = CommandRecord(
            command=command,
            commit=commit,
            started_at=started_at,
            duration_seconds=result.duration.total_seconds(),
            status=result.status,
            exit_status=result.exit_status,
            targets=result.targets,
        )
        try:
            self._records.append(record)
        except OSError as error:
            # The record is telemetry: losing it must never lose the command's result.
            self._log.line(f"cannot write the record of {command}: {error}")
        return result

    def _head(self) -> CommitId | None:
        try:
            return self._git.resolve("HEAD")
        except GitError:
            return None
