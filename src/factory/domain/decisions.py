"""The stall reasons, the mapping from an agent run's end reason to one, and the agent's entry."""

from collections.abc import Sequence
from typing import Literal

from factory.domain.agent_runs import QUESTION, AgentRunResult
from factory.domain.journal import JournalKind, NewEntry

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

_UNDONE_PARAGRAPH = "The factory undid changes outside the write paths: "


def stall_reason_of(result: AgentRunResult) -> StallReason | None:
    """The stall reason of a run that ended early, or `None` for a completed one."""
    if result.end_reason == "completed":
        return None
    return result.end_reason


def agent_entry(
    *, role: str, stage: str, decision: str, text: str, undone: Sequence[str]
) -> NewEntry | None:
    """The agent's entry, spoken by `role`; `None` when its text is blank without a name prefix.

    One leading `<role>:` or `<stage>:` is removed, since the speaker already names it; the
    `undone` paths, when there are any, are named in a closing paragraph.
    """
    cleaned = _without_name_prefix(text.strip(), (role, stage)).strip()
    if not cleaned:
        return None
    if undone:
        cleaned += f"\n\n{_UNDONE_PARAGRAPH}{', '.join(sorted(undone))}."
    kind: JournalKind = "question" if decision == QUESTION else "result"
    return NewEntry(speaker=role, kind=kind, text=cleaned, on=None)


def _without_name_prefix(text: str, names: Sequence[str]) -> str:
    for name in names:
        prefix = f"{name}:"
        if text.startswith(prefix):
            return text.removeprefix(prefix)
    return text
