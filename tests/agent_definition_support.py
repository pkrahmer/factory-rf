"""The completed run of the tick's agent definition tests."""

from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult

COMPLETED = AgentRunResult(
    end_reason="completed", decision="tests", entry="checked.", duration=timedelta(minutes=1)
)
