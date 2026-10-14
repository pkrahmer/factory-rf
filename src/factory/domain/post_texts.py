"""The texts the factory writes on the hosting service."""

# Postponed annotations let this module name StallReason while decisions imports these texts.
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from factory.domain.identifiers import WorkItemId

if TYPE_CHECKING:
    from factory.domain.decisions import StallReason
    from factory.domain.story_form import FormFinding


def opened_for_stop_description(work_item: WorkItemId) -> str:
    """The description of a draft pull request the factory opened to report a stop."""
    return (
        f"The factory opened this draft pull request to report a stop on {work_item}."
        " The stop is the comment below."
    )


_STALL_SENTENCES: dict[StallReason, str] = {
    "died": "the agent run died without a result",
    "time_limit": "the agent run reached its time limit",
    "budget": "the agent run spent its budget, and the resume too",
    "no_result": "the agent gave no valid decision and entry",
    "decision_not_allowed": "the agent's decision is not an allowed one",
    "left_branch": "the agent left the work item's branch",
    "form_invalid": "the work item's form broke during the stage",
    "check_red": "a check is red after the stage",
    "merge_conflict": "merging the main branch conflicts and the merge was aborted",
}


def stall_cause(reason: StallReason, detail: str = "") -> str:
    """The sentence that names why a stage stalled, followed by `detail` when there is one."""
    sentence = _STALL_SENTENCES[reason]
    if not detail:
        return sentence
    return f"{sentence}: {detail}"


def stall_note(reason: StallReason, attempts: int, attempts_cap: int, *, detail: str = "") -> str:
    """The note posted on the pull request after a stall; it promises a retry only below the cap.

    A multi-line `detail` gives its first line to the sentence and the rest to a fenced block.
    """
    first_line, *rest = detail.rstrip("\n").split("\n")
    if attempts < attempts_cap:
        follow_up = "Retrying on the next tick."
    else:
        follow_up = "The attempts cap is reached; the factory asks you next."
    sentence = (
        f"Stalled (attempt {attempts} of {attempts_cap}): "
        f"{stall_cause(reason, first_line)}. {follow_up}"
    )
    if not rest:
        return sentence
    return "\n".join([sentence, "", *_text_block(rest)])


def _text_block(lines: list[str]) -> list[str]:
    # GitHub renders a comment as Markdown; the fence keeps a check's output as it was printed.
    longest_run = max((len(run) for run in re.findall("`+", "\n".join(lines))), default=0)
    fence = "`" * max(3, longest_run + 1)
    return [f"{fence}text", *lines, fence]


def round_cap_question(rounds: int, cap: int) -> str:
    """The question asked when a rework would send the work item back more often than its cap."""
    return (
        f"This work item has now been sent back {rounds} times, more than {cap}."
        " What should happen? Answer with a comment;"
        " close the pull request to discard the work item."
    )


def findings_question(findings: Sequence[FormFinding]) -> str:
    """The question asked when a forward decision leaves the form with findings."""
    numbered = " ".join(
        f"{number}. {finding.message}" for number, finding in enumerate(findings, start=1)
    )
    return (
        f"The work item's form has findings, so the stage cannot move forward: {numbered}."
        " What should happen? Answer with a comment; the stage then runs again."
        " Close the pull request to discard the work item."
    )
