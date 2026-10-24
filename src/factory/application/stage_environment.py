"""The stage environment: where a stage's agent works and how its result comes back."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import timedelta
from typing import override

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.sealed_runs import SealedRun, run_sealed
from factory.application.take import TakeReport
from factory.application.undo import UndoService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.git import CommitId


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
    ) -> SealedRun:
        """Run `request`'s agent in this environment, through `run` or the boundaries' runtime.

        `run` is called once; whatever it does inside (resumes after a provider limit) happens
        in the same prepared place. The result and the nested repositories removed after it.
        """

    @abstractmethod
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Bring the agent's result into the factory's work tree, as far as the role may write.

        `WorkItemFormatError` naming `work_item_path` when the work item is absent or
        unreadable at the stage-start commit; the work tree is then left untouched.
        """


class InlineEnvironment(StageEnvironment):
    """v1.1's way: the agent in the factory's own checkout, sealed around; the undo after."""

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
    ) -> SealedRun:
        """Run the agent in the checkout with its git folder sealed around the run."""
        return run_sealed(self._boundaries, request, run=run)

    @override
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Undo what the agent changed outside its write paths; what the undo put back is left."""
        undo = UndoService(self._boundaries).undo(stage_start, work_item_path)
        return TakeReport(
            left=sorted({*undo.reverted, *undo.deleted}),
            restored_work_item=undo.restored_work_item,
        )


def stage_environment_of(boundaries: Boundaries) -> StageEnvironment:
    """The environment the boundaries describe: for now always the inline one."""
    return InlineEnvironment(boundaries)
