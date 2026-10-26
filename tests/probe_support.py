"""The agent environment, the probe run results and the opencode texts shared by the probe tests."""

from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult, EndReason, Login

ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin", "HOME": "/home/agent", "LANG": "C.UTF-8"}
COMPLETED = AgentRunResult(
    end_reason="completed", decision="question", entry="probe", duration=timedelta(seconds=5)
)


def probe_result(reason: EndReason, login: Login | None) -> AgentRunResult:
    """Return the probe run's result that ended for `reason`, handed `login`."""
    duration = timedelta(seconds=5)
    if reason == "completed":
        return AgentRunResult(
            end_reason=reason, duration=duration, decision="question", entry="probe", login=login
        )
    return AgentRunResult(end_reason=reason, duration=duration, login=login)


def opencode_died(user: str) -> str:
    """Return the detail of a died probe under opencode, run as `user`."""
    return f"the probe run ended died; run opencode run by hand as {user} to see why"


def opencode_sso_hint() -> str:
    """Return the hint appended when the opencode agent runs get no API key."""
    return "; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names"
