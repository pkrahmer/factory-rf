"""The project commands of a project whose build is driven by make."""

import os
import re
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

from factory.adapters.agent_launch import SHELL_EXECUTABLE, Launch
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
from factory.domain.containers import WORK_CHECKOUT, bundle_mounts
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


class MakeProjectCommands(ProjectCommands):
    """Runs `make <command>` in the project's directory, where its Makefile is."""

    def __init__(
        self,
        directory: Path,
        kill_points: KillPoints | None = None,
        *,
        executable: str = "make",
    ) -> None:
        """Run make from `directory`, as the factory's own user.

        `kill_points` is accepted for uniform wiring only.
        """
        self._directory = directory
        self._kill_points = kill_points
        self._executable = executable

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `make --no-print-directory <command>` and judge its result by its exit status."""
        _check_call(command, time_limit)
        argv = [self._executable, "--no-print-directory", command]
        started = Launch(argv=argv, env=_without_outer_make(os.environ), time_limit=time_limit)
        result = self._start(command, started, self._directory)
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
        self,
        snapshots: Snapshots,
        containers: ContainerRuns,
        git: Git,
        *,
        checkout: Path,
        extra_environment: Mapping[str, str] = {},
        ca_bundle: Path | None = None,
    ) -> None:
        """Reset the dataset of `snapshots`, copy in what differs from `HEAD` in `checkout`.

        The check's container gets `extra_environment` below its own and `ca_bundle` mounted
        read-only at its own path.
        """
        self._snapshots = snapshots
        # The check's own names win: its `PATH` and home never come from the host.
        self._environment = {**extra_environment, **CHECK_ENVIRONMENT}
        self._mounts = bundle_mounts(ca_bundle)
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
                mounts=self._mounts,
                environment=self._environment,
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
