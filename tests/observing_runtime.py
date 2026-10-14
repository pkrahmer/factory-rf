"""An agent runtime that records what the remote and the hosting fake hold when a run starts."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.agent_runtime import AgentRuntime
from factory.application.git import Git
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.hosting import PullRequestView
from git_support import remote_commit


class Observation(BaseModel):
    """What the outside world held at the moment `run` was called."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    remote_head: str | None
    checkout_head: str | None
    pull_requests: list[PullRequestView]


class ObservingRuntime(AgentRuntime):
    """Records an observation of `branch` on `remote` and of `hosting`, then delegates."""

    def __init__(
        self,
        delegate: FakeAgentRuntime,
        *,
        remote: Path,
        branch: str,
        hosting: FakeHostingService,
        checkout: Git,
    ) -> None:
        """Observe `branch` on the bare `remote`, `hosting` and `checkout`; run on `delegate`."""
        self._delegate = delegate
        self._remote = remote
        self._branch = branch
        self._hosting = hosting
        self._checkout = checkout
        self._observations: list[Observation] = []

    def observations(self) -> list[Observation]:
        """One observation per call of `run`, in order."""
        return list(self._observations)

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Observe, then let the delegate play the request."""
        self._observations.append(
            Observation(
                remote_head=remote_commit(self._remote, self._branch),
                checkout_head=self._checkout.status().head,
                pull_requests=self._hosting.pull_requests(),
            )
        )
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()
