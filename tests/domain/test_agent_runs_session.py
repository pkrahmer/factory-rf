"""A run's session, the wait a provider's limit names, and a request that resumes a session."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    resumed_result,
)

RESULT: type[BaseModel] = AgentRunResult
REQUEST: type[BaseModel] = AgentRunRequest
MINUTE = timedelta(seconds=60)


@pytest.mark.parametrize(
    ("end_reason", "limit_wait", "refusal"),
    [
        pytest.param("provider_limit", timedelta(seconds=420), None, id="limit-with-wait"),
        pytest.param(
            "died",
            timedelta(seconds=420),
            "a run that ended by died has no limit_wait",
            id="died-with-wait",
        ),
        pytest.param("provider_limit", timedelta(0), "", id="zero-wait"),
    ],
)
def test_a_limit_wait_is_positive_and_only_on_a_provider_limit(
    end_reason: str, limit_wait: timedelta, refusal: str | None
) -> None:
    fields = {"end_reason": end_reason, "duration": MINUTE, "limit_wait": limit_wait}

    if refusal is None:
        result = RESULT(**fields)
        assert isinstance(result, AgentRunResult)
        assert result.limit_wait == limit_wait
        return
    with pytest.raises(ValidationError) as raised:
        RESULT(**fields)
    assert refusal in str(raised.value)


@pytest.mark.parametrize(
    ("resume_session", "accepted"),
    [
        pytest.param("ses_a", True, id="named"),
        pytest.param("", False, id="empty"),
        pytest.param("  ", False, id="blank"),
    ],
)
def test_a_session_to_resume_is_not_blank(
    tmp_path: Path, resume_session: str, *, accepted: bool
) -> None:
    fields: dict[str, object] = {
        "agent": AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        "prompt": "Stage: doing",
        "allowed_decisions": ["doing", "question"],
        "time_limit": MINUTE,
        "working_directory": tmp_path,
        "resume_session": resume_session,
    }

    if accepted:
        request = REQUEST(**fields)
        assert isinstance(request, AgentRunRequest)
        assert request.resume_session == resume_session
        return
    with pytest.raises(ValidationError):
        REQUEST(**fields)


Ended = tuple[str | None, timedelta | None]


def _ended(ended: Ended) -> AgentRunResult:
    session, limit_wait = ended
    end_reason: EndReason = "provider_limit" if limit_wait is not None else "budget"
    return AgentRunResult(
        end_reason=end_reason, duration=MINUTE, session=session, limit_wait=limit_wait
    )


@pytest.mark.parametrize(
    ("first", "second", "session", "limit_wait"),
    [
        pytest.param(
            ("ses_a", None),
            ("ses_b", timedelta(seconds=420)),
            "ses_b",
            timedelta(seconds=420),
            id="second-has-both",
        ),
        pytest.param(("ses_a", None), (None, None), "ses_a", None, id="second-has-no-session"),
        pytest.param(
            ("ses_a", timedelta(seconds=60)),
            (None, None),
            "ses_a",
            None,
            id="first-wait-not-kept",
        ),
    ],
)
def test_a_resumed_result_takes_the_second_session_else_the_first_and_the_second_wait(
    first: Ended,
    second: Ended,
    session: str | None,
    limit_wait: timedelta | None,
) -> None:
    result = resumed_result(_ended(first), _ended(second))

    assert result.session == session
    assert result.limit_wait == limit_wait
