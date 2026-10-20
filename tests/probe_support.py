"""The agent environment, the completed run and the opencode texts shared by the probe tests."""

from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult

ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": "/home/agent", "LANG": "C.UTF-8"}
COMPLETED = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)


def opencode_died(user: str) -> str:
    """Return the detail of a died probe under opencode, run as `user`."""
    return f"the probe run ended died; run opencode run by hand as {user} to see why"


def opencode_sso_hint(user: str) -> str:
    """Return the hint appended when the opencode agent runs as `user` get no API key."""
    return (
        f"; the agent runs get no API key: log in once as {user} with the opencode build's own "
        "login, or put a key in the file FACTORY_API_LOGIN_FILE names"
    )
