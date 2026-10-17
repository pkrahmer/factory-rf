"""Sealed agent runs: the checkout's git folder is sealed before every run and checked after it."""

from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult


def run_sealed(boundaries: Boundaries, request: AgentRunRequest) -> AgentRunResult:
    """Seal the git folder, run the agent, then check the seal.

    No run starts when the seal fails. `RepositoryUnsealed` from the check after the run wins
    over an error of the run, which becomes its context.
    """
    boundaries.git.seal()
    try:
        return boundaries.agent_runtime.run(request)
    # An agent run may have swapped the git folder even when it failed; no git command may follow.
    finally:
        boundaries.git.check_seal()
