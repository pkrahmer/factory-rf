"""The prompt of a stage's agent and the decisions it may end with, composed from fixed lines."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, NonNegativeInt, PositiveInt

from factory.domain.agent_runs import QUESTION
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.story_form import FormFinding

TESTER_ROLE = "tester"
CODER_ROLE = "coder"
END_LINE = (
    "End with your decision and your journal entry; "
    "the factory commits, pushes and moves the work item."
)


class PromptFacts(BaseModel):
    """What the prompt tells the agent: the work item, its stage, its decisions and its mode."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    path: str
    stage: Name
    allowed_decisions: list[str]
    branch: str
    pull_request: PositiveInt
    round: NonNegativeInt
    test_change_entry: PositiveInt | None = None
    findings: list[FormFinding] | None = None


def allowed_decisions(next_stages: Sequence[str]) -> list[str]:
    """The stages of `next_stages` in their order, then `QUESTION`, which every stage allows."""
    return [*next_stages, QUESTION]


def _mode_line(entry: int) -> str:
    return f"Mode: a test change the human approved; the coder's journal entry {entry} names it."


def _format_check_line(findings: Sequence[FormFinding]) -> str:
    if not findings:
        return "Format check: passed"
    items = " ".join(
        f"{number}. {finding.message}" for number, finding in enumerate(findings, start=1)
    )
    return f"Format check found: {items}"


def compose_prompt(facts: PromptFacts) -> str:
    """The prompt's lines in their fixed order, joined by newlines, without a trailing one."""
    lines = [
        f"Work item: {facts.path}",
        f"Id: {facts.work_item}",
        f"Stage: {facts.stage}",
        f"Allowed decisions: {', '.join(facts.allowed_decisions)}",
        f"Branch: {facts.branch}",
        f"Pull request: {facts.pull_request}",
        f"Round: {facts.round}",
    ]
    if facts.test_change_entry is not None:
        lines.append(_mode_line(facts.test_change_entry))
    if facts.findings is not None:
        lines.append(_format_check_line(facts.findings))
    lines.append(END_LINE)
    return "\n".join(lines)
