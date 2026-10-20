"""Sealed runs: the checkout's git folder is sealed before every run and checked after it."""

from collections.abc import Callable
from datetime import timedelta
from typing import override

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.application.machine import FactoryLog
from factory.application.project_commands import ProjectCommands
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.checks import CheckResult


class SealedRun(BaseModel):
    """A sealed run's result and the nested repositories removed after it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    result: AgentRunResult
    nested_repositories: list[str]


def run_sealed(
    boundaries: Boundaries,
    request: AgentRunRequest,
    *,
    run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
) -> SealedRun:
    """Seal the git folder, run the agent, check the seal, remove nested and ignored paths.

    `run` runs the agent in place of the boundaries' runtime, when it is given.

    No run starts when the seal fails. `RepositoryUnsealed` from the check or the removal after
    the run wins over an error of the run, which becomes its context. A failed check searches
    nothing: the checkout is cloned again before any git command.
    """
    git = boundaries.git
    run_agent = boundaries.agent_runtime.run if run is None else run
    git.seal()
    try:
        result = run_agent(request)
    # An agent run may have swapped the git folder or made a repository even when it failed;
    # no git command may follow before both are dealt with.
    finally:
        git.check_seal()
        nested = git.remove_nested_repositories()
    # Only after a returned run: a raised one leaves its ignored paths to the next restore.
    git.remove_ignored()
    return SealedRun(result=result, nested_repositories=nested)


class SealedProjectCommands(ProjectCommands):
    """Runs another implementation's project commands with the checkout's git folder sealed."""

    def __init__(self, inner: ProjectCommands, git: Git, log: FactoryLog) -> None:
        self._inner = inner
        self._git = git
        self._log = log

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Seal the git folder, run `command`, check the seal and remove nested repositories.

        `RepositoryUnsealed` from the seal or its check wins over an error of the command,
        which becomes its context; a failed check removes nothing.
        """
        self._git.seal()
        try:
            return self._inner.run(command, time_limit=time_limit)
        # A command runs code an agent wrote, which may have swapped the git folder or made a
        # repository even when the command failed.
        finally:
            self._git.check_seal()
            nested = self._git.remove_nested_repositories()
            if nested:
                self._log.line(f"removed nested repositories after {command}: {', '.join(nested)}")
