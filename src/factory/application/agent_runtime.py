"""The interface through which the factory runs an agent."""

from abc import ABC, abstractmethod

from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult


class AgentRuntime(ABC):
    """Runs one agent to its end and reports how it ended."""

    @abstractmethod
    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the agent of `request` until it ends.

        A run that dies, reaches its time limit or exhausts its budget is a result;
        `AgentRuntimeError` means the runtime could not run it at all.
        """

    @abstractmethod
    def version(self) -> str:
        """The version of the runtime, as it reports it."""


class AgentDefinitionReader(ABC):
    """Tells which agents are installed and reads one into its definition."""

    @abstractmethod
    def names(self) -> list[str]:
        """The names of the installed agents, sorted.

        `AgentDefinitionError` when there is no agents directory; an empty one gives `[]`.
        """

    @abstractmethod
    def read(self, name: str) -> AgentDefinition:
        """The definition of the agent `name`.

        `AgentDefinitionMissing` when no such agent is installed, `AgentDefinitionInvalid`
        when its file does not define an agent.
        """

    @abstractmethod
    def parse(self, name: str, text: str) -> AgentDefinition:
        """The definition of the agent `name` from the text of an agent file.

        `AgentDefinitionMissing` when `name` is not an agent name, `AgentDefinitionInvalid`
        when the text does not define an agent, with the faults of `read`.
        """
