"""The stall reasons and how an agent run's end reason maps to one."""

from datetime import timedelta

import pytest

from factory.domain.agent_runs import AgentRunResult, EndReason
from factory.domain.decisions import stall_reason_of


@pytest.mark.parametrize("end_reason", ["died", "time_limit", "budget", "no_result"])
def test_a_run_that_did_not_complete_maps_to_the_stall_reason_of_its_name(
    end_reason: EndReason,
) -> None:
    result = AgentRunResult(end_reason=end_reason, duration=timedelta(minutes=3))

    assert stall_reason_of(result) == end_reason


def test_a_completed_run_is_no_stall() -> None:
    result = AgentRunResult(
        end_reason="completed", decision="doing", entry="done.", duration=timedelta(minutes=1)
    )

    assert stall_reason_of(result) is None
