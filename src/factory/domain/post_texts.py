"""The texts the factory writes on the hosting service."""

# Postponed annotations let this module name StallReason while decisions imports these texts.
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from factory.domain.bills import Bill, cost_line
from factory.domain.git import CommitId
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
    "provider_limit": "the provider's spend limit lasted past the waiting ceiling",
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
        " What should happen? Answer with a comment, which starts the count of rounds over;"
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


def error_report_text(event_key: str, error: str, remote_state: CommitId, cap: int) -> str:
    """The report posted when one event failed `cap` times on one remote state."""
    return (
        f"The factory failed {cap} times on `{event_key}` and has stopped retrying it."
        f" Last error: {error}. A new commit on the work item's branch"
        f" (now at {remote_state[:12]}) makes the factory try again."
    )


def attempts_cap_question(stage: str, attempts: int, last_stall: str) -> str:
    """The question asked when a work item has stalled as often as its attempts allow."""
    return (
        f"Stage {stage} stalled {attempts} times. The last time: {last_stall}\n"
        "\n"
        "Comment anything to retry: the attempts go back to 0 and the stage runs again."
        " Close the pull request to discard the story instead: it goes back to the backlog"
        " as you wrote it, and its branch and bill are deleted."
    )


def crash_cap_question(stage: str, crashes: int, crash_cap: int) -> str:
    """The question asked when a stage has crashed as often as the crash cap allows."""
    return (
        f"Stage {stage} crashed {crashes} times, which is the crash cap of {crash_cap}."
        " The factory has not rerun it. Write a comment here and the stage reruns with the"
        " crash counter reset to 0 (your comment is copied into the journal). Close the pull"
        " request to discard the story instead: it goes back to the backlog as you wrote it,"
        " and its branch and bill are deleted."
    )


def expiry_note(crashes: int, crash_cap: int) -> str:
    """The note posted after an expired lease; it promises a retry only below the crash cap."""
    if crashes < crash_cap:
        follow_up = "Retrying."
    else:
        follow_up = "The factory does not rerun it and asks you instead."
    return (
        "The run that held this stage ended without finishing:"
        f" its lease expired (crash {crashes} of {crash_cap}). {follow_up}"
    )


def cost_table_post(table: str, human: str | None = None) -> str:
    """The post that shows the human the cost table at the approval, and their line under it."""
    post = f"Cost of this work item so far\n\n{table}"
    if human is None:
        return post
    return f"{post}\n\nHuman: {human}"


def done_entry_text(bill: Bill) -> str:
    """The journal text of a merged work item's archive, with its bill."""
    return f"done (pull request merged); cost: {cost_line(bill)}"


CLOSE_ENTRY_TEXT = "closed the pull request."
SEND_BACK_QUESTION = (
    "What should happen? 1. Comment what should change; the story is reworked with exactly that. "
    "2. Close the pull request again to discard the story: it goes back to the backlog "
    "as you wrote it, and its branch is deleted. 3. If closing was a mistake: "
    "mark the pull request ready for review and merge it, which accepts the story as it is."
)


def send_back_entry_text(target: str, round_number: int) -> str:
    """The journal text of a send-back to `target` in round `round_number`."""
    return f"sent back to {target}, round {round_number}."


def send_back_question(round_number: int, cap: int | None, has_reason: bool) -> str | None:
    """The question a send-back asks, or None when the close says enough.

    Past the cap the cap question wins, whether a reason was given or not.
    """
    if cap is not None and round_number > cap:
        return (
            f"This story has now been sent back {round_number} times, more than {cap}. "
            + SEND_BACK_QUESTION
        )
    if not has_reason:
        return "The pull request was closed without a comment. " + SEND_BACK_QUESTION
    return None


MOVED_BACK_MARKER = "moved back"


def move_back_entry_text(old: str, new: str) -> str:
    """The journal text of an illegal stage change from `old` to `new` that was put back."""
    return f"illegal stage change {old} -> {new}, {MOVED_BACK_MARKER}."


def correction_note(old: str, new: str) -> str:
    """The note posted on the pull request when an illegal stage change was put back."""
    return (
        f"The stage was changed from {old} to {new}, which factory/pipeline.yml does not allow;"
        f" it is back at {old}."
    )
