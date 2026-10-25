"""The agent-run DTOs: definition, request, result and their rules."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import get_args

import pytest
from pydantic import ValidationError

from factory.domain.agent_runs import (
    QUESTION,
    AgentDefinition,
    AgentRunRequest,
    AgentRunResult,
    EndReason,
    GuardSettings,
    TokenCounts,
)

ROOT = Path("/work/project")
OTHER_REASONS = ["no_result", "time_limit", "budget", "died"]


def _agent(name: str = "coder", budget_usd: Decimal = Decimal("3")) -> AgentDefinition:
    return AgentDefinition(
        name=name, model="sonnet", tools=["Read"], budget_usd=budget_usd, instructions="Code."
    )


def _request(
    allowed_decisions: list[str] | None = None,
    time_limit: timedelta = timedelta(minutes=5),
    working_directory: Path = ROOT,
) -> AgentRunRequest:
    return AgentRunRequest(
        agent=_agent(),
        prompt="Stage: doing",
        allowed_decisions=["doing", QUESTION] if allowed_decisions is None else allowed_decisions,
        time_limit=time_limit,
        working_directory=working_directory,
    )


def test_question_and_the_six_end_reasons() -> None:
    assert QUESTION == "question"
    reasons = get_args(EndReason)
    assert len(reasons) == 6
    assert set(reasons) == {
        "completed",
        "no_result",
        "time_limit",
        "budget",
        "died",
        "provider_limit",
    }


@pytest.mark.parametrize(
    ("budget", "accepted"),
    [(Decimal("0.01"), True), (Decimal("0"), False), (Decimal("-1"), False)],
)
def test_agent_budget_must_be_positive(budget: Decimal, accepted: bool) -> None:
    if accepted:
        assert _agent(budget_usd=budget).budget_usd == budget
    else:
        with pytest.raises(ValidationError):
            _agent(budget_usd=budget)


def test_agent_name_must_be_a_name() -> None:
    with pytest.raises(ValidationError):
        _agent(name="Coder")


def test_minimal_request_has_empty_defaults_not_shared() -> None:
    first = _request()
    second = _request()

    assert first.environment == {}
    assert first.os_user is None
    assert first.environment is not second.environment


@pytest.mark.parametrize("decisions", [[], ["doing"]])
def test_allowed_decisions_without_question_are_rejected(decisions: list[str]) -> None:
    with pytest.raises(ValidationError) as caught:
        _request(allowed_decisions=decisions)
    assert "question" in str(caught.value)


def test_allowed_decisions_with_question_are_accepted() -> None:
    assert _request(allowed_decisions=["doing", "question"]).allowed_decisions == [
        "doing",
        "question",
    ]


def test_allowed_decisions_with_a_repeat_are_rejected() -> None:
    with pytest.raises(ValidationError):
        _request(allowed_decisions=["doing", "doing", "question"])


@pytest.mark.parametrize(
    ("limit", "accepted"), [(timedelta(0), False), (timedelta(seconds=1), True)]
)
def test_time_limit_must_be_positive(limit: timedelta, accepted: bool) -> None:
    if accepted:
        assert _request(time_limit=limit).time_limit == limit
    else:
        with pytest.raises(ValidationError):
            _request(time_limit=limit)


def test_working_directory_must_be_absolute() -> None:
    assert _request(working_directory=ROOT).working_directory == ROOT
    with pytest.raises(ValidationError):
        _request(working_directory=Path("relative/dir"))


def test_guard_root_must_be_absolute_and_paths_are_kept() -> None:
    guard = GuardSettings(root=ROOT, write_paths=["tests/", "src/"], protected_paths=["factory/"])

    assert guard.root == ROOT
    assert guard.write_paths == ["tests/", "src/"]
    assert guard.protected_paths == ["factory/"]
    with pytest.raises(ValidationError):
        GuardSettings(root=Path("relative"), write_paths=[], protected_paths=[])


@pytest.mark.parametrize("field", ["input", "output", "cache_read", "cache_creation"])
def test_token_counts_reject_negative_counts(field: str) -> None:
    counts = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}
    assert getattr(TokenCounts.model_validate(counts), field) == 0
    with pytest.raises(ValidationError):
        TokenCounts.model_validate(counts | {field: -1})


def test_token_counts_default_cache_counts_to_zero() -> None:
    counts = TokenCounts(input=10, output=20)

    assert counts.cache_read == 0
    assert counts.cache_creation == 0


def test_completed_result_needs_decision_and_entry() -> None:
    duration = timedelta(seconds=5)
    with pytest.raises(ValidationError):
        AgentRunResult(end_reason="completed", entry="Done.", duration=duration)
    with pytest.raises(ValidationError):
        AgentRunResult(end_reason="completed", decision="doing", duration=duration)
    result = AgentRunResult(
        end_reason="completed", decision="doing", entry="Done.", duration=duration
    )
    assert (result.decision, result.entry) == ("doing", "Done.")


@pytest.mark.parametrize("reason", OTHER_REASONS)
def test_other_end_reasons_carry_no_decision_or_entry(reason: EndReason) -> None:
    duration = timedelta(seconds=5)
    with pytest.raises(ValidationError):
        AgentRunResult(end_reason=reason, decision="doing", duration=duration)
    with pytest.raises(ValidationError):
        AgentRunResult(end_reason=reason, entry="Done.", duration=duration)
    assert AgentRunResult(end_reason=reason, duration=duration).end_reason == reason


@pytest.mark.parametrize("reason", ["completed", *OTHER_REASONS])
def test_unreported_measures_are_none_and_ok_only_when_completed(reason: EndReason) -> None:
    completed = reason == "completed"
    result = AgentRunResult(
        end_reason=reason,
        decision="doing" if completed else None,
        entry="Done." if completed else None,
        duration=timedelta(seconds=5),
    )

    assert result.turns is None
    assert result.tokens is None
    assert result.cost_usd is None
    assert result.ok is completed
