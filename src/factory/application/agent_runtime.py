"""The interface through which the factory runs an agent."""

from typing import Protocol

from factory.domain.agent_runs import AgentRunRequest, AgentRunResult


class AgentRuntime(Protocol):
    """Runs one agent to its end and reports how it ended."""

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` until it ends.

        A run that dies, reaches its time limit or exhausts its budget is a result;
        `AgentRuntimeError` means the runtime could not run it at all.
        """
        ...

    def version(self) -> str:
        """The version of the runtime, as it reports it."""
        ...
