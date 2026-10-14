"""The stall reasons and the mapping from an agent run's end reason to one."""

from typing import Literal

from factory.domain.agent_runs import AgentRunResult

StallReason = Literal[
    "died",
    "time_limit",
    "budget",
    "no_result",
    "decision_not_allowed",
    "left_branch",
    "form_invalid",
    "check_red",
    "merge_conflict",
]


def stall_reason_of(result: AgentRunResult) -> StallReason | None:
    """The stall reason of a run that ended early, or `None` for a completed one."""
    if result.end_reason == "completed":
        return None
    return result.end_reason
