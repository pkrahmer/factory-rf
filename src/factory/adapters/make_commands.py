"""The project commands of a project whose build is driven by make."""

import os
import re
from datetime import timedelta
from pathlib import Path

from factory.adapters.process import ProcessRequest, run_process
from factory.domain.checks import COMMAND_NAME_PATTERN, OUTPUT_TAIL_LINES, CheckResult, status_of
from factory.domain.errors import ProjectCommandError
from factory.domain.kill_points import KillPoints

_COMMAND_NAME = re.compile(COMMAND_NAME_PATTERN)

# An outer make (the tests run under `make check`) exports these, and an inner make that
# sees them prints "Entering directory" lines that a run on its own would not.
_OUTER_MAKE_VARIABLES = ("MAKELEVEL", "MAKEFLAGS", "MFLAGS")

_MAKE_MESSAGE_PREFIXES = ("make:", "make[")


def _environment() -> dict[str, str]:
    return {name: value for name, value in os.environ.items() if name not in _OUTER_MAKE_VARIABLES}


def _tail(lines: list[str]) -> str:
    return "\n".join(lines[-OUTPUT_TAIL_LINES:])


def _last_line(lines: list[str]) -> str:
    for line in reversed(lines):
        if line.strip() and not line.startswith(_MAKE_MESSAGE_PREFIXES):
            return line
    return ""


class MakeProjectCommands:
    """Runs `make <command>` in the project's directory, where its Makefile is."""

    def __init__(
        self, directory: Path, kill_points: KillPoints | None = None, *, executable: str = "make"
    ) -> None:
        """Run make from `directory`; `kill_points` is accepted for uniform wiring only."""
        self._directory = directory
        self._kill_points = kill_points
        self._executable = executable

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Run `make --no-print-directory <command>` and judge it by its exit status alone."""
        if time_limit <= timedelta(0):
            raise ValueError(f"time_limit must be positive, not {time_limit}")
        if not _COMMAND_NAME.fullmatch(command):
            raise ProjectCommandError(command, f"invalid command name {command!r}")
        request = ProcessRequest(
            argv=[self._executable, "--no-print-directory", command],
            cwd=self._directory,
            env=_environment(),
            time_limit=time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as exc:
            raise ProjectCommandError(command, str(exc)) from exc
        lines = result.stdout.splitlines()
        return CheckResult(
            command=command,
            status=status_of(result.exit_status),
            exit_status=result.exit_status,
            duration=result.duration,
            last_line=_last_line(lines),
            output_tail=_tail(lines),
        )
