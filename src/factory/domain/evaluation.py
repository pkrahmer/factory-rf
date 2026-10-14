"""The evaluation: what the remote shows, judged in four tiers, becomes one event."""

from collections.abc import Callable, Sequence

from pydantic import BaseModel, ConfigDict

from factory.domain.errors import HostingServiceError
from factory.domain.events import Event, EventKind
from factory.domain.git import CommitId
from factory.domain.hosting import PullRequestComment, PullRequestView
from factory.domain.lease import ClaimStatus
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemSnapshot, WorkItemState


class PullRequestObservation(BaseModel):
    """What the one pull request lookup returns: the view and, while open, its comments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    view: PullRequestView
    comments: list[PullRequestComment]


class EvaluationInput(BaseModel):
    """The facts one evaluation judges: the definition, the work items in id order, main's head."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: PipelineDefinition
    snapshots: list[WorkItemSnapshot]
    main_commit: CommitId


PullRequestLookup = Callable[[int], PullRequestObservation]
ClaimStatusOf = Callable[[WorkItemState], ClaimStatus]
_Pairs = Sequence[tuple[WorkItemSnapshot, WorkItemState]]

_CLAIM_EVENTS: dict[ClaimStatus, EventKind] = {"own": "crash", "expired": "expired"}


def waiting(state: WorkItemState, definition: PipelineDefinition) -> bool:
    """Whether the work item waits for the human: it is blocked or at an approval stage."""
    return state.blocked is not None or definition.stages[state.stage].approval


def question_posted(snapshot: WorkItemSnapshot, comments: Sequence[PullRequestComment]) -> bool:
    """Whether a factory post answers the latest question record of the blocked work item."""
    state = snapshot.document.state
    if state is None or state.blocked is None:
        return False
    questions = [record.number for record in state.journal if record.kind == "question"]
    if not questions:
        return False
    latest = str(questions[-1])
    return any(
        comment.by_factory
        and comment.key is not None
        and comment.key.work_item == snapshot.id
        and comment.key.kind == state.blocked
        and comment.key.n == latest
        for comment in comments
    )


def evaluate(
    facts: EvaluationInput, lookup: PullRequestLookup, claim_status: ClaimStatusOf
) -> Event:
    """The first event of the four tiers: integrity, the human, the agent at work, new work.

    Raises `ValueError` for a work item with no state or in a stage the definition lacks.
    """
    duplicate = _duplicate(facts)
    if duplicate is not None:
        return duplicate
    states = [_validated_state(snapshot, facts.definition) for snapshot in facts.snapshots]
    pairs = list(zip(facts.snapshots, states, strict=True))
    return (
        _human_signal(facts, pairs, lookup)
        or _agent_at_work(facts, pairs, claim_status)
        or _new_work(facts, pairs)
        or Event(kind="idle", work_item=None, remote_state=facts.main_commit)
    )


def _duplicate(facts: EvaluationInput) -> Event | None:
    first_of: dict[str, WorkItemSnapshot] = {}
    for snapshot in facts.snapshots:
        first = first_of.setdefault(snapshot.id, snapshot)
        if first is not snapshot:
            detail = f"{snapshot.id} at {first.path} and {snapshot.path}"
            return _event("duplicate", first, facts.main_commit, detail=detail)
    return None


def _validated_state(snapshot: WorkItemSnapshot, definition: PipelineDefinition) -> WorkItemState:
    state = snapshot.document.state
    if state is None:
        raise ValueError(f"work item {snapshot.id} has no state")
    if state.stage not in definition.stages:
        raise ValueError(
            f"work item {snapshot.id}: stage {state.stage} is not in the pipeline definition"
        )
    return state


def _human_signal(facts: EvaluationInput, pairs: _Pairs, lookup: PullRequestLookup) -> Event | None:
    # Only the first waiting work item is looked up, so an idle tick costs at most one lookup.
    for snapshot, state in pairs:
        if waiting(state, facts.definition):
            return _signal_of(facts, snapshot, state, lookup)
    return None


def _signal_of(
    facts: EvaluationInput,
    snapshot: WorkItemSnapshot,
    state: WorkItemState,
    lookup: PullRequestLookup,
) -> Event:
    main = facts.main_commit
    if state.pull_request is None:
        return _event("ask", snapshot, main, detail="no pull request")
    try:
        observation = lookup(state.pull_request)
    except HostingServiceError as error:
        return _event("pull_request_lookup", snapshot, main, detail=str(error))
    view = observation.view
    kind, detail = _signal_of_observation(facts.definition, snapshot, state, observation)
    if kind is None:
        return Event(
            kind="idle",
            work_item=None,
            pull_request=view,
            remote_state=main,
            detail=f"{snapshot.id} waits for the human",
        )
    return _event(kind, snapshot, main, pull_request=view, detail=detail)


def _signal_of_observation(
    definition: PipelineDefinition,
    snapshot: WorkItemSnapshot,
    state: WorkItemState,
    observation: PullRequestObservation,
) -> tuple[EventKind | None, str]:
    if observation.view.state == "merged":
        return "merged", ""
    if observation.view.state == "closed":
        return "closed", ""
    if definition.stages[state.stage].approval and state.handed_over != state.stage:
        return "hand_over", ""
    new_comments = [
        comment
        for comment in observation.comments
        if not comment.by_factory and comment.id not in state.comments_read
    ]
    if new_comments:
        return "comment", f"{len(new_comments)} new comments"
    if state.blocked is not None and not question_posted(snapshot, observation.comments):
        return "ask", ""
    return None, ""


def _agent_at_work(
    facts: EvaluationInput, pairs: _Pairs, claim_status: ClaimStatusOf
) -> Event | None:
    claimed = next(
        ((snapshot, state) for snapshot, state in pairs if state.claim is not None), None
    )
    if claimed is None:
        return None
    snapshot, state = claimed
    status = claim_status(state)
    if status == "held" and state.claim is not None:
        detail = f"{snapshot.id} is held by {state.claim.instance}"
        return Event(kind="idle", work_item=None, remote_state=facts.main_commit, detail=detail)
    kind = _CLAIM_EVENTS.get(status)
    return None if kind is None else _event(kind, snapshot, facts.main_commit)


def _new_work(facts: EvaluationInput, pairs: _Pairs) -> Event | None:
    definition = facts.definition
    for snapshot, state in pairs:
        if definition.stages[state.stage].role is None or waiting(state, definition):
            continue
        if state.attempts >= definition.attempts_cap:
            return _event("ask", snapshot, facts.main_commit, detail="attempts cap")
        return _event("run", snapshot, facts.main_commit)
    return None


def _event(
    kind: EventKind,
    snapshot: WorkItemSnapshot,
    main_commit: CommitId,
    *,
    pull_request: PullRequestView | None = None,
    detail: str = "",
) -> Event:
    remote_state = main_commit if snapshot.branch_commit is None else snapshot.branch_commit
    return Event(
        kind=kind,
        work_item=snapshot,
        pull_request=pull_request,
        remote_state=remote_state,
        detail=detail,
    )
