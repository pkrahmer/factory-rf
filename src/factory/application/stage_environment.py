"""The stage environment: where a stage's agent works and how its result comes back."""

import math
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import override

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.containers import ContainerRuns
from factory.application.snapshots import Snapshots
from factory.application.take import TakeReport, TakeService
from factory.application.undo import UndoService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.checks import last_line
from factory.domain.containers import WORK, WORK_CHECKOUT, WORK_HOME, ContainerResult, Mount
from factory.domain.errors import ContainerError
from factory.domain.git import CommitId

UPSTREAM = "/upstream"
AGENT_FILES = "/etc/factory/claude"
SHELL = "/bin/sh"
SYNC_ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": WORK_HOME}
TIMING_LINE = (
    "stage environment: reset {reset} s, sync {sync} s, advance {advance} s, take {take} s"
)

_SYNC_COMMAND = "sync"

# Every container path comes as an argument and none in the text, so that a run played on
# the host can map them. `--update-head-ok`: git refuses to
# fetch into the checked-out branch, an unborn one too; the checkout and the reset after it
# put the work tree right. The host's branches come in as `origin/<branch>` too, as in a
# clone of the host's repository: the project's commands read `origin/main`. The escaped
# line end keeps the fetch on one line of the script.
_SYNC_SCRIPT = """set -eu
mkdir -p "$1" "$2"
rm -rf "$2/.claude"
cp -R "$4" "$2/.claude"
cd "$1"
if [ ! -e .git ]; then git init -q; fi
git fetch -q --prune --update-head-ok "$3" '+refs/heads/*:refs/heads/*' \
'+refs/heads/*:refs/remotes/origin/*'
git checkout -q -f "$5"
git reset -q --hard "$6"
make sync
"""


class StageEnvironment(ABC):
    """Where a stage's agent works and how its result comes back: one cycle behind one interface."""

    @abstractmethod
    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        """Make the place the agent works in hold `branch` at `commit`, its tools synced.

        `SnapshotError` or `ContainerError` when that cannot be done; the sync's container
        gets `sync_time_limit`.
        """

    @abstractmethod
    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> AgentRunResult:
        """Run `request`'s agent in this environment, through `run` or the boundaries' runtime.

        `run` is called once; whatever it does inside (resumes after a provider limit) happens
        in the same prepared place. Returns the run's result.
        """

    @abstractmethod
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Bring the agent's result into the factory's work tree, as far as the role may write.

        `WorkItemFormatError` naming `work_item_path` when the work item is absent or
        unreadable at the stage-start commit; the work tree is then left untouched.
        """


class InlineEnvironment(StageEnvironment):
    """v1.1's way: the agent in the factory's own checkout; the undo after."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Run in the checkout of `boundaries`."""
        self._boundaries = boundaries

    @override
    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        """Do nothing: the claim already left the checkout on `branch` at `commit`."""

    @override
    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> AgentRunResult:
        """Run the agent in the checkout."""
        return (run or self._boundaries.agent_runtime.run)(request)

    @override
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Undo what the agent changed outside its write paths; what the undo put back is left."""
        undo = UndoService(self._boundaries).undo(stage_start, work_item_path)
        return TakeReport(
            left=sorted({*undo.reverted, *undo.deleted}),
            restored_work_item=undo.restored_work_item,
        )


class ContainerEnvironment(StageEnvironment):
    """v1.2's way: the agent on the dataset in throwaway containers; the take after."""

    def __init__(
        self, boundaries: Boundaries, snapshots: Snapshots, containers: ContainerRuns
    ) -> None:
        """Prepare the dataset of `snapshots` through `containers`; take into the checkout."""
        self._boundaries = boundaries
        self._snapshots = snapshots
        self._containers = containers
        self._reset = timedelta(0)
        self._sync = timedelta(0)
        self._advance = timedelta(0)
        # A stall after the result's take takes again; the stage still logs one line.
        self._timing_due = True

    @override
    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        """Roll the dataset back to its base, sync it in a container, then move the base to it."""
        began = self._now()
        self._snapshots.reset()
        reset_done = self._now()
        self._run_sync(commit, branch, sync_time_limit)
        sync_done = self._now()
        self._snapshots.advance()
        self._reset = reset_done - began
        self._sync = sync_done - reset_done
        self._advance = self._now() - sync_done
        self._timing_due = True

    @override
    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> AgentRunResult:
        """Run the agent on the dataset, which is rolled back before the next stage anyway."""
        return (run or self._boundaries.agent_runtime.run)(request)

    @override
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Take from the dataset's changes what the role may write; log the cycle's timing.

        The timing is logged by the first take after a prepare, or on an object without one.
        """
        began = self._now()
        service = TakeService(self._boundaries, self._snapshots.mount_point)
        report = service.take(stage_start, work_item_path, self._snapshots.changed_paths())
        if self._timing_due:
            self._log_timing(self._now() - began)
            self._timing_due = False
        return report

    def _log_timing(self, take: timedelta) -> None:
        self._boundaries.log.line(
            TIMING_LINE.format(
                reset=_seconds(self._reset),
                sync=_seconds(self._sync),
                advance=_seconds(self._advance),
                take=_seconds(take),
            )
        )

    def _run_sync(self, commit: CommitId, branch: str, time_limit: timedelta) -> None:
        settings = self._boundaries.settings
        result = self._containers.run(
            [
                SHELL,
                "-c",
                _SYNC_SCRIPT,
                "factory-sync",
                WORK_CHECKOUT,
                WORK_HOME,
                UPSTREAM,
                AGENT_FILES,
                branch,
                commit,
            ],
            mounts=[
                Mount(source=self._boundaries.checkout / ".git", target=UPSTREAM, read_only=True),
                Mount(source=settings.agent_home, target=AGENT_FILES, read_only=True),
            ],
            environment=SYNC_ENVIRONMENT,
            time_limit=time_limit,
            working_directory=WORK,
        )
        _check_sync(result, time_limit)

    def _now(self) -> datetime:
        return self._boundaries.clock.now()


def _check_sync(result: ContainerResult, time_limit: timedelta) -> None:
    if result.timed_out:
        seconds = math.ceil(time_limit.total_seconds())
        raise ContainerError(_SYNC_COMMAND, f"no end within {seconds} s")
    if result.exit_status != 0:
        detail = last_line(result.output.splitlines()) or f"exit status {result.exit_status}"
        raise ContainerError(_SYNC_COMMAND, detail)


def _seconds(duration: timedelta) -> str:
    return f"{duration.total_seconds():.1f}"


def stage_environment_of(boundaries: Boundaries) -> StageEnvironment:
    """The container environment when snapshots and containers are set, else the inline one."""
    if boundaries.snapshots is not None and boundaries.containers is not None:
        return ContainerEnvironment(boundaries, boundaries.snapshots, boundaries.containers)
    return InlineEnvironment(boundaries)
