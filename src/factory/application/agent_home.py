"""The agent user's home, cleared of what earlier runs left before every run and command."""

from abc import ABC, abstractmethod


class AgentHome(ABC):
    """The agent user's home, which every agent run and project command starts from fresh."""

    @abstractmethod
    def reset(self) -> None:
        """Remove what earlier runs left in the home, the kept paths aside.

        `AgentRuntimeError` when the home cannot be cleared.
        """
