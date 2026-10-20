"""The agent's home, cleared by the fresh-home program run as the agent's user."""

import math
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import override

from factory.adapters.agent_launch import killed_at_limit, launch, line_starting
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.agent_home import AgentHome
from factory.domain.agent_home import FRESH_HOME_PREFIX
from factory.domain.errors import AgentRuntimeError

FRESH_HOME_TIME_LIMIT = timedelta(seconds=60)


class SudoAgentHome(AgentHome):
    """Clears the agent's home by running the fresh-home program as the agent's user."""

    def __init__(
        self,
        home: Path,
        kept: Sequence[str],
        *,
        os_user: str,
        sudo_executable: str,
        program: Sequence[str],
    ) -> None:
        """Clear `home` but the `kept` paths, running `program` as `os_user` through `sudo`."""
        self._home = home
        self._kept = list(kept)
        self._os_user = os_user
        self._sudo_executable = sudo_executable
        self._program = list(program)

    @property
    def home(self) -> Path:
        """The home the program clears."""
        return self._home

    @property
    def kept(self) -> list[str]:
        """The paths, relative to the home, that the program keeps."""
        return list(self._kept)

    @property
    def os_user(self) -> str:
        """The agent's user, whose entries the program removes."""
        return self._os_user

    @property
    def program(self) -> list[str]:
        """The words that start the fresh-home program."""
        return list(self._program)

    @override
    def reset(self) -> None:
        """Run the fresh-home program over the home; `AgentRuntimeError` when it fails."""
        # Read at each call, so that the limit in force is the one used.
        time_limit = FRESH_HOME_TIME_LIMIT
        keeps = [word for path in self._kept for word in ("--keep", path)]
        started = launch(
            [*self._program, "--home", str(self._home), *keeps],
            {},
            os_user=self._os_user,
            sudo_executable=self._sudo_executable,
            time_limit=time_limit,
        )
        # From the root, so the program holds no folder of the checkout open.
        request = ProcessRequest(
            argv=started.argv, cwd=Path("/"), env=started.env, time_limit=started.time_limit
        )
        try:
            result = run_process(request)
        except OSError as exc:
            raise self._fault(exc.strerror or str(exc)) from exc
        if result.exit_status == 0:
            return
        if result.timed_out or killed_at_limit(
            os_user=self._os_user,
            exit_status=result.exit_status,
            duration=result.duration,
            time_limit=time_limit,
        ):
            seconds = math.ceil(time_limit.total_seconds())
            raise self._fault(f"no end within {seconds} s")
        raise self._fault(_failure_line(result))

    def _fault(self, reason: str) -> AgentRuntimeError:
        return AgentRuntimeError(f"cannot reset the agent's home {self._home}: {reason}")


def _failure_line(result: ProcessResult) -> str:
    prefixed = line_starting(result.stderr, FRESH_HOME_PREFIX)
    if prefixed is not None:
        return prefixed
    lines = [line for line in result.stderr.splitlines() if line.strip()]
    if lines:
        return lines[-1]
    return f"exit status {result.exit_status}"
