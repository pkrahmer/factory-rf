"""The request, the completed result and the recording run that the tests of agent runs share."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult

COMPLETED = AgentRunResult(
    end_reason="completed", decision="question", entry="done", duration=timedelta(seconds=5)
)


def run_request(checkout: Path) -> AgentRunRequest:
    """A coder's run request whose working directory is `checkout`."""
    agent = AgentDefinition(
        name="coder",
        model="sonnet",
        tools=["Read"],
        budget_usd=Decimal("1.00"),
        instructions="Write the code.",
    )
    return AgentRunRequest(
        agent=agent,
        prompt="Do the stage.",
        allowed_decisions=["question"],
        time_limit=timedelta(minutes=5),
        working_directory=checkout,
    )


class RecordingRun:
    """A run of the test: records each request and returns the completed result."""

    def __init__(self) -> None:
        """Start with no request."""
        self.requests: list[AgentRunRequest] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Record `request`."""
        self.requests.append(request)
        return COMPLETED
