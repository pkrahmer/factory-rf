"""The result of a resumed run: the second call's answer, both calls' refusals and measures."""

from datetime import timedelta
from decimal import Decimal

import pytest

from factory.domain.agent_runs import (
    AgentRunResult,
    PermissionDenial,
    TokenCounts,
    resumed_result,
)

FIRST_DENIAL = PermissionDenial(tool="Write", detail="first refusal", path="/work/first.py")
SECOND_DENIAL = PermissionDenial(tool="Bash", detail="second refusal")
LATER_DENIAL = PermissionDenial(tool="Edit", detail="later refusal", path="/work/later.py")


def _seconds(value: float) -> timedelta:
    return timedelta(seconds=value)


FULL_FIRST = AgentRunResult(
    end_reason="completed",
    decision="question",
    entry="First.",
    duration=_seconds(10),
    model_duration=_seconds(8),
    turns=3,
    tokens=TokenCounts(input=100, output=20, cache_read=5, cache_creation=1),
    cost_usd=Decimal("1.00"),
    permission_denials=[FIRST_DENIAL],
    login="subscription",
)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        pytest.param(
            FULL_FIRST,
            AgentRunResult(
                end_reason="completed",
                decision="doing",
                entry="Second.",
                duration=_seconds(4),
                model_duration=_seconds(3),
                turns=1,
                tokens=TokenCounts(input=10, output=2, cache_read=3, cache_creation=4),
                cost_usd=Decimal("0.25"),
                permission_denials=[SECOND_DENIAL, LATER_DENIAL],
                login="api_key",
            ),
            AgentRunResult(
                end_reason="completed",
                decision="doing",
                entry="Second.",
                duration=_seconds(14),
                model_duration=_seconds(11),
                turns=4,
                tokens=TokenCounts(input=110, output=22, cache_read=8, cache_creation=5),
                cost_usd=Decimal("1.25"),
                permission_denials=[FIRST_DENIAL, SECOND_DENIAL, LATER_DENIAL],
                login="api_key",
            ),
            id="every-measure-summed",
        ),
        pytest.param(
            AgentRunResult(
                end_reason="budget",
                duration=_seconds(10),
                model_duration=_seconds(8),
                turns=None,
                tokens=TokenCounts(input=100, output=20),
                cost_usd=None,
            ),
            AgentRunResult(
                end_reason="completed",
                decision="doing",
                entry="Second.",
                duration=_seconds(4),
                model_duration=None,
                turns=2,
                tokens=None,
                cost_usd=Decimal("0.25"),
            ),
            AgentRunResult(
                end_reason="completed",
                decision="doing",
                entry="Second.",
                duration=_seconds(14),
                model_duration=_seconds(8),
                turns=2,
                tokens=TokenCounts(input=100, output=20),
                cost_usd=Decimal("0.25"),
            ),
            id="measure-of-one-call",
        ),
        pytest.param(
            AgentRunResult(end_reason="budget", duration=_seconds(10)),
            AgentRunResult(
                end_reason="completed", decision="doing", entry="Second.", duration=_seconds(4)
            ),
            AgentRunResult(
                end_reason="completed", decision="doing", entry="Second.", duration=_seconds(14)
            ),
            id="measure-of-neither-call",
        ),
        pytest.param(
            FULL_FIRST,
            AgentRunResult(
                end_reason="time_limit",
                duration=_seconds(30),
                turns=1,
                permission_denials=[SECOND_DENIAL],
            ),
            AgentRunResult(
                end_reason="time_limit",
                duration=_seconds(40),
                turns=1,
                permission_denials=[FIRST_DENIAL, SECOND_DENIAL],
            ),
            id="second-ended-by-time-limit",
        ),
    ],
)
def test_resumed_result_takes_the_second_answer_and_adds_up_both_calls(
    first: AgentRunResult, second: AgentRunResult, expected: AgentRunResult
) -> None:
    assert resumed_result(first, second) == expected
