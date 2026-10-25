"""The project commands of a project whose build is driven by make."""

import os
import re
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.agent_launch import (
    SHELL_EXECUTABLE,
    SUDO_PREFIX,
    Launch,
    killed_at_limit,
    launch,
)
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.containers import ContainerRuns
from factory.application.git import Git
from factory.application.project_commands import ProjectCommands
from factory.application.snapshots import Snapshots
from factory.application.stage_environment import SYNC_ENVIRONMENT
from factory.application.take import MOUNTED_CHECKOUT, copy_changed
from factory.domain.checks import (
    COMMAND_NAME_PATTERN,
    OUTPUT_TAIL_LINES,
    CheckResult,
    last_line,
    status_of,
    target_times,
)
from factory.domain.containers import WORK_CHECKOUT
from factory.domain.errors import ContainerError, ProjectCommandError, SnapshotError
from factory.domain.kill_points import KillPoints

_COMMAND_NAME = re.compile(COMMAND_NAME_PATTERN)

# A check sees the same system and home as the sync before the agent.
CHECK_ENVIRONMENT = dict(SYNC_ENVIRONMENT)

# The command's name is an argument, never part of the script, so the shell never parses it.
_CHECK_SCRIPT = '"$1" sync && "$1" --no-print-directory "$2"'
_CHECK_SCRIPT_NAME = "factory-check"

# An outer make (the tests run under `make check`) exports these, and an inner make that
# sees them prints "Entering directory" lines that a run on its own would not.
_OUTER_MAKE_VARIABLES = ("MAKELEVEL", "MAKEFLAGS", "MFLAGS")


def _without_outer_make(environment: Mapping[str, str]) -> dict[str, str]:
    return {name: value for name, value in environment.items() if name not in _OUTER_MAKE_VARIABLES}


def _tail(lines: list[str]) -> str:
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


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
        """Run `make --no-print-directory <command>` and judge its result.

        Without a user the run is judged by its exit status alone. With a user it runs
        through `sudo` as that user: a kill at the limit is a `time_limit` result, and a
        refusal by `sudo` raises `ProjectCommandError`.
        """
        _check_call(command, time_limit)
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
        if refusal is not None:
            raise ProjectCommandError(command, refusal)
        if killed:
            return _check_result(command, result.model_copy(update={"exit_status": None}))
        return _check_result(command, result)

    @staticmethod
    def _start(command: str, started: Launch, cwd: Path) -> ProcessResult:
        request = ProcessRequest(
            argv=started.argv,
            cwd=cwd,
            env=started.env,
            time_limit=started.time_limit,
            merge_stderr=True,
        )
        try:
            return run_process(request)
        except OSError as exc:
            raise ProjectCommandError(command, str(exc)) from exc


class ContainerMakeCommands(ProjectCommands):
    """Runs `make sync && make <command>` in a check container on the base with the taken files."""

    def __init__(
        self, snapshots: Snapshots, containers: ContainerRuns, git: Git, *, checkout: Path
    ) -> None:
        """Reset the dataset of `snapshots`, copy in what differs from `HEAD` in `checkout`."""
        self._snapshots = snapshots
        self._containers = containers
        self._git = git
        self._checkout = checkout

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `command` after `sync` in a container on the base with the host's changes.

        A fault of the reset or of the container raises `ProjectCommandError`; a `GitError`
        or a `ValueError` of the copy propagates as it is.
        """
        _check_call(command, time_limit)
        try:
            self._snapshots.reset()
        except SnapshotError as exc:
            raise ProjectCommandError(command, str(exc)) from exc
        # What differs from `HEAD` is what the take brought; nothing is remembered between them.
        copy_changed(
            self._checkout,
            self._snapshots.mount_point / MOUNTED_CHECKOUT,
            self._git.changed_paths("HEAD"),
        )
        try:
            result = self._containers.run(
                [SHELL_EXECUTABLE, "-c", _CHECK_SCRIPT, _CHECK_SCRIPT_NAME, "make", command],
                mounts=[],
                environment=CHECK_ENVIRONMENT,
                time_limit=time_limit,
                working_directory=WORK_CHECKOUT,
            )
        except ContainerError as exc:
            raise ProjectCommandError(command, str(exc)) from exc
        return _read_result(command, result.exit_status, result.output, result.duration)


def _check_call(command: str, time_limit: timedelta) -> None:
    if time_limit <= timedelta(0):
        raise ValueError(f"time_limit must be positive, not {time_limit}")
    if not _COMMAND_NAME.fullmatch(command):
        raise ProjectCommandError(command, f"invalid command name {command!r}")


def _refusal(user: CommandUser, result: ProcessResult) -> str | None:
    if result.exit_status in (0, None):
        return None
    line = _refusal_line(result.stdout.splitlines())
    if line is None:
        return None
    return f"{user.sudo_executable} refused the command: {line}"


def _check_result(command: str, result: ProcessResult) -> CheckResult:
    return _read_result(command, result.exit_status, result.stdout, result.duration)


def _read_result(
    command: str, exit_status: int | None, output: str, duration: timedelta
) -> CheckResult:
    lines = output.splitlines()
    return CheckResult(
        command=command,
        status=status_of(exit_status),
        exit_status=exit_status,
        duration=duration,
        last_line=last_line(lines),
        output_tail=_tail(lines),
        targets=target_times(output),
    )
