"""The request and the completed result that the tests of sealed agent runs share."""

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


def leave(checkout: Path) -> None:
    """Change nothing in `checkout`: the step of a run that leaves its git folder alone."""
    del checkout
