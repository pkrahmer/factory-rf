"""The project commands of a project whose build is driven by make."""

import os
import re
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.agent_launch import (
    LEFTOVERS_FAULT,
    SUDO_PREFIX,
    Launch,
    killed_at_limit,
    launch,
    leftovers_fault,
    leftovers_launch,
)
from factory.adapters.process import ProcessRequest, ProcessResult, own_identity, run_process
from factory.application.project_commands import ProjectCommands
from factory.domain.checks import (
    COMMAND_NAME_PATTERN,
    OUTPUT_TAIL_LINES,
    CheckResult,
    status_of,
    target_times,
)
from factory.domain.errors import ProjectCommandError
from factory.domain.kill_points import KillPoints

_COMMAND_NAME = re.compile(COMMAND_NAME_PATTERN)

# An outer make (the tests run under `make check`) exports these, and an inner make that
# sees them prints "Entering directory" lines that a run on its own would not.
_OUTER_MAKE_VARIABLES = ("MAKELEVEL", "MAKEFLAGS", "MFLAGS")

_MAKE_MESSAGE_PREFIXES = ("make:", "make[")


def _without_outer_make(environment: Mapping[str, str]) -> dict[str, str]:
    return {name: value for name, value in environment.items() if name not in _OUTER_MAKE_VARIABLES}


def _tail(lines: list[str]) -> str:
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


def _last_line(lines: list[str]) -> str:
    for line in reversed(lines):
        if line.strip() and not line.startswith(_MAKE_MESSAGE_PREFIXES):
            return line
    return ""


def _refusal_line(lines: list[str]) -> str | None:
    # Only `sudo` printed: the command itself never ran.
    printed = [line for line in lines if line.strip()]
    if not printed or not all(line.startswith(SUDO_PREFIX) for line in printed):
        return None
    return printed[-1]


class CommandUser(BaseModel):
    """The operating-system user a project command runs as, how to become it, its environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    os_user: str
    sudo_executable: str
    environment: dict[str, str]
    leftovers: list[str] | None = None


class MakeProjectCommands(ProjectCommands):
    """Runs `make <command>` in the project's directory, where its Makefile is."""

    def __init__(
        self,
        directory: Path,
        kill_points: KillPoints | None = None,
        *,
        executable: str = "make",
        user: CommandUser | None = None,
    ) -> None:
        """Run make from `directory`, as `user` when one is set.

        `kill_points` is accepted for uniform wiring only.
        """
        self._directory = directory
        self._kill_points = kill_points
        self._executable = executable
        self._user = user

    @property
    def user(self) -> CommandUser | None:
        """The user the commands run as, or `None` for the factory's own."""
        return self._user

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `make --no-print-directory <command>` and judge it by its exit status alone."""
        if time_limit <= timedelta(0):
            raise ValueError(f"time_limit must be positive, not {time_limit}")
        if not _COMMAND_NAME.fullmatch(command):
            raise ProjectCommandError(command, f"invalid command name {command!r}")
        argv = [self._executable, "--no-print-directory", command]
        if self._user is None:
            return self._run_as_own_user(command, argv, time_limit)
        return self._run_as(self._user, command, argv, time_limit)

    def _run_as_own_user(self, command: str, argv: list[str], time_limit: timedelta) -> CheckResult:
        started = Launch(argv=argv, env=_without_outer_make(os.environ), time_limit=time_limit)
        result = self._start(command, started, self._directory)
        return _check_result(command, result)

    def _run_as(
        self, user: CommandUser, command: str, argv: list[str], time_limit: timedelta
    ) -> CheckResult:
        started = launch(
            argv,
            _without_outer_make(user.environment),
            os_user=user.os_user,
            sudo_executable=user.sudo_executable,
            time_limit=time_limit,
        )
        result = self._start(command, started, self._directory)
        killed = killed_at_limit(
            os_user=user.os_user,
            exit_status=result.exit_status,
            duration=result.duration,
            time_limit=time_limit,
        )
        # A `sudo:` warning before a kill at the limit is no refusal.
        refusal = None if killed else _refusal(user, result)
        leftovers_error = self._end_leftovers(user, command)
        if refusal is not None:
            raise ProjectCommandError(command, refusal)
        if leftovers_error is not None:
            raise ProjectCommandError(command, leftovers_error)
        if killed:
            return _check_result(command, result.model_copy(update={"exit_status": None}))
        return _check_result(command, result)

    def _end_leftovers(self, user: CommandUser, command: str) -> str | None:
        # Never for the factory's own user: the program would end the factory itself.
        if user.leftovers is None or user.os_user == own_identity().user:
            return None
        started = leftovers_launch(
            user.leftovers, os_user=user.os_user, sudo_executable=user.sudo_executable
        )
        try:
            # From the root, so the program holds no folder of the project open.
            result = self._start(command, started, Path("/"), merge_stderr=False)
        except ProjectCommandError as exc:
            return f"{LEFTOVERS_FAULT} {exc.detail}"
        return leftovers_fault(
            exit_status=result.exit_status, timed_out=result.timed_out, stderr=result.stderr
        )

    @staticmethod
    def _start(
        command: str, started: Launch, cwd: Path, *, merge_stderr: bool = True
    ) -> ProcessResult:
        request = ProcessRequest(
            argv=started.argv,
            cwd=cwd,
            env=started.env,
            time_limit=started.time_limit,
            merge_stderr=merge_stderr,
        )
        try:
            return run_process(request)
        except OSError as exc:
            raise ProjectCommandError(command, str(exc)) from exc


def _refusal(user: CommandUser, result: ProcessResult) -> str | None:
    if result.exit_status in (0, None):
        return None
    line = _refusal_line(result.stdout.splitlines())
    if line is None:
        return None
    return f"{user.sudo_executable} refused the command: {line}"


def _check_result(command: str, result: ProcessResult) -> CheckResult:
    lines = result.stdout.splitlines()
    return CheckResult(
        command=command,
        status=status_of(result.exit_status),
        exit_status=result.exit_status,
        duration=result.duration,
        last_line=_last_line(lines),
        output_tail=_tail(lines),
        targets=target_times(result.stdout),
    )
