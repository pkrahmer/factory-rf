"""The stall reasons, the agent's entry, and the rules that turn a decision into a stage move."""

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, NonNegativeInt

from factory.domain import journal
from factory.domain.agent_runs import QUESTION, AgentRunResult
from factory.domain.identifiers import Name
from factory.domain.journal import JournalKind, NewEntry
from factory.domain.pipeline_definition import PipelineDefinition, StageDefinition
from factory.domain.post_texts import findings_question, round_cap_question
from factory.domain.story_form import FormFinding
from factory.domain.work_item import Blocked, WorkItemState

StallReason = journal.StallReason

_LEFT_OUT_PARAGRAPH = "The factory left out changes outside the write paths: "


def stall_reason_of(result: AgentRunResult) -> StallReason | None:
    """The stall reason of a run that ended early, or `None` for a completed one."""
    if result.end_reason == "completed":
        return None
    return result.end_reason


def agent_entry(
    *, role: str, stage: str, decision: str, text: str, left_out: Sequence[str]
) -> NewEntry | None:
    """The agent's entry, spoken by `role`; `None` when its text is blank without a name prefix.

    One leading `<role>:` or `<stage>:` is removed, since the speaker already names it; the
    `left_out` paths, when there are any, are named in a closing paragraph.
    """
    cleaned = _without_name_prefix(text.strip(), (role, stage)).strip()
    if not cleaned:
        return None
    if left_out:
        cleaned += f"\n\n{_LEFT_OUT_PARAGRAPH}{', '.join(sorted(left_out))}."
    kind: JournalKind = "question" if decision == QUESTION else "result"
    return NewEntry(speaker=role, kind=kind, text=cleaned, on=None)


def _without_name_prefix(text: str, names: Sequence[str]) -> str:
    for name in names:
        prefix = f"{name}:"
        if text.startswith(prefix):
            return text.removeprefix(prefix)
    return text


class StageMove(BaseModel):
    """What a decision does to the work item: the rule that applied, its stage, block and round."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: Literal[1, 2, 3, 4, 6, 7]
    stage: Name
    blocked: Blocked | None
    round: NonNegativeInt
    question: str | None


def decide(
    definition: PipelineDefinition,
    state: WorkItemState,
    decision: str,
    findings: Sequence[FormFinding] = (),
) -> StageMove:
    """The move an agent's `decision` makes from the state's stage, the rules tried in v1's order.

    Raises `ValueError` for a stage outside the definition or a decision outside its `next`.
    """
    stage = _stage_definition(definition, state.stage)
    if decision != QUESTION and decision not in stage.next:
        raise ValueError(f"decision {decision!r} is not allowed at stage {state.stage!r}")
    # A forward decision is next[0]; every other entry of next is a rework, wherever it points.
    forward = stage.next[:1] == [decision]
    if forward and findings:
        return _stay(state, rule=1, blocked="question", question=findings_question(findings))
    if decision == QUESTION:
        return _stay(state, rule=2, blocked="question", question=None)
    if forward:
        return _move(rule=6, stage=decision, rounds=state.round)
    if stage.round_cap is None:
        return _move(rule=7, stage=decision, rounds=state.round)
    rounds = state.round + 1
    if rounds <= stage.round_cap:
        return _move(rule=3, stage=decision, rounds=rounds)
    return StageMove(
        rule=4,
        stage=state.stage,
        blocked="round_cap",
        round=rounds,
        question=round_cap_question(rounds, stage.round_cap),
    )


def _stage_definition(definition: PipelineDefinition, stage: str) -> StageDefinition:
    if stage not in definition.stages:
        raise ValueError(f"stage {stage!r} is not in the pipeline definition")
    return definition.stages[stage]


def _stay(
    state: WorkItemState, *, rule: Literal[1, 2], blocked: Blocked, question: str | None
) -> StageMove:
    return StageMove(
        rule=rule, stage=state.stage, blocked=blocked, round=state.round, question=question
    )


def _move(*, rule: Literal[3, 6, 7], stage: str, rounds: int) -> StageMove:
    return StageMove(rule=rule, stage=stage, blocked=None, round=rounds, question=None)
