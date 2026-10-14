"""The texts the factory writes on the hosting service."""

from factory.domain.decisions import StallReason
from factory.domain.identifiers import WorkItemId


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
    """The note posted on the pull request after a stall; it promises a retry only below the cap."""
    cause = stall_cause(reason, detail)
    if attempts < attempts_cap:
        follow_up = "Retrying on the next tick."
    else:
        follow_up = "The attempts cap is reached; the factory asks you next."
    return f"Stalled (attempt {attempts} of {attempts_cap}): {cause}. {follow_up}"
