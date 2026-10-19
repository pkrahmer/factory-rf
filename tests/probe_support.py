"""The agent environment and the completed run shared by the tests of the agent-run probe."""

from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult

ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": "/home/agent", "LANG": "C.UTF-8"}
COMPLETED = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)
