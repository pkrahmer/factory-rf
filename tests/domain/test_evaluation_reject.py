"""The evaluation rejects an illegal stage change, after the one pull request lookup."""

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from factory.domain.errors import HostingServiceError
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.events import Event
from factory.domain.hosting import PullRequestComment, PullRequestState, PullRequestView
from factory.domain.journal import JournalRecord
from factory.domain.lease import ClaimStatus
from factory.domain.move_rule import IllegalChange, StageChange
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import (
    Claim,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)

MAIN = "a" * 40
MERGE_COMMIT = "c" * 40
PULL_REQUEST = 7
AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)

DEFINITION = PipelineDefinition(
    contract="1.0",
    stages={
        "intake": StageDefinition(role="intake", next=["review"]),
        "review": StageDefinition(role="reviewer", next=["approval", "intake"]),
        "approval": StageDefinition(approval=True, next=["done", "review"]),
        "done": StageDefinition(),
    },
    roles={
        "intake": RoleDefinition(write_paths=["{work_item}"]),
        "reviewer": RoleDefinition(write_paths=["{work_item}"]),
    },
    attempts_cap=2,
)

# intake may only move to review; skipping it to approval is what the illegal changes show.
JUMP = StageChange(from_stage="intake", to_stage="approval")
JUMP_DETAIL = "stage changed from intake to approval, which the pipeline definition does not allow"


def _id(number: int) -> str:
    return f"F0001-S{number:04d}"


def _commit(number: int) -> str:
    return str(number) * 40


def _snapshot(
    number: int, state: WorkItemState, *, feature_directory: str = "F0001-demo"
) -> WorkItemSnapshot:
    work_item = _id(number)
    return WorkItemSnapshot(
        id=work_item,
        path=f"factory/features/{feature_directory}/in-progress/{work_item}-x.md",
        folder="in-progress",
        branch=f"work-item/{work_item}",
        branch_commit=_commit(number),
        document=WorkItemDocument(state=state, body="# T\n"),
    )


def _illegal(number: int, change: StageChange = JUMP) -> IllegalChange:
    return IllegalChange(work_item=_id(number), change=change)


def _at_approval(*, handed_over: str | None = "approval") -> WorkItemState:
    return WorkItemState(stage="approval", pull_request=PULL_REQUEST, handed_over=handed_over)


def _blocked() -> WorkItemState:
    return WorkItemState(
        stage="review",
        blocked="question",
        pull_request=PULL_REQUEST,
        journal=[
            JournalRecord(number=1, speaker="human", kind="created"),
            JournalRecord(number=2, speaker="factory", kind="question"),
        ],
    )


def _runnable() -> WorkItemState:
    return initial_state("intake")


def _claimed() -> WorkItemState:
    claim = Claim(instance="factory-2", stage="intake", started_at=AT, lease_duration=60)
    return initial_state("intake").model_copy(update={"claim": claim})


def _finished() -> WorkItemState:
    # At done: no role, no wait, no claim, so it gives no event of its own.
    return WorkItemState(stage="done")


def _view(state: PullRequestState) -> PullRequestView:
    return PullRequestView(
        number=PULL_REQUEST,
        branch="work-item/F0001-S0001",
        title="t",
        state=state,
        draft=False,
        merge_commit=MERGE_COMMIT if state == "merged" else None,
        url=f"https://example.test/{PULL_REQUEST}",
    )


def _human_comment() -> PullRequestComment:
    return PullRequestComment(
        id=1,
        author="human",
        body="A remark.",
        created_at=AT,
        by_factory=False,
        key=None,
    )


class _Lookup:
    """A pull request lookup that records its calls and answers with one observation."""

    def __init__(
        self,
        state: PullRequestState = "open",
        comments: Sequence[PullRequestComment] = (),
        error: HostingServiceError | None = None,
    ) -> None:
        self.calls: list[int] = []
        self._view = _view(state)
        self._comments = list(comments) if state == "open" else []
        self._error = error

    def __call__(self, number: int) -> PullRequestObservation:
        self.calls.append(number)
        if self._error is not None:
            raise self._error
        return PullRequestObservation(view=self._view, comments=self._comments)


def _evaluate(
    snapshots: Sequence[WorkItemSnapshot],
    illegal_changes: Sequence[IllegalChange],
    *,
    lookup: _Lookup | None = None,
    claim_status: ClaimStatus = "none",
) -> Event:
    facts = EvaluationInput(
        definition=DEFINITION,
        snapshots=list(snapshots),
        main_commit=MAIN,
        illegal_changes=list(illegal_changes),
    )
    return evaluate(facts, _Lookup() if lookup is None else lookup, lambda _state: claim_status)


def test_the_first_illegal_change_in_snapshot_order_is_rejected_at_its_branch() -> None:
    first = _snapshot(1, _runnable())
    second = _snapshot(2, _runnable())
    other_jump = StageChange(from_stage="review", to_stage="done")

    event = _evaluate([first, second], [_illegal(2, other_jump), _illegal(1)])

    assert event.kind == "reject"
    assert event.work_item == first
    assert event.remote_state == _commit(1)
    assert event.detail == JUMP_DETAIL


def test_no_illegal_change_is_no_reject() -> None:
    event = _evaluate([_snapshot(1, _runnable())], [])

    assert event.kind == "run"


@pytest.mark.parametrize(
    ("snapshot", "commented", "claim_status", "kind"),
    [
        (_snapshot(1, _at_approval()), True, "none", "comment"),
        (_snapshot(1, _blocked()), False, "none", "ask"),
        (_snapshot(1, _at_approval(handed_over=None)), False, "none", "hand_over"),
        (_snapshot(1, _claimed()), False, "own", "crash"),
        (_snapshot(1, _claimed()), False, "expired", "expired"),
        (_snapshot(1, _runnable()), False, "none", "run"),
        (_snapshot(1, _finished()), False, "none", "idle"),
    ],
    ids=["comment", "ask", "hand_over", "crash", "expired", "run", "idle"],
)
def test_reject_comes_before_every_later_event(
    snapshot: WorkItemSnapshot, commented: bool, claim_status: ClaimStatus, kind: str
) -> None:
    changed = _snapshot(9, _finished())
    comments = [_human_comment()] if commented else []

    without = _evaluate(
        [snapshot, changed], [], lookup=_Lookup(comments=comments), claim_status=claim_status
    )
    with_change = _evaluate(
        [snapshot, changed],
        [_illegal(9)],
        lookup=_Lookup(comments=comments),
        claim_status=claim_status,
    )

    assert without.kind == kind
    assert with_change.kind == "reject"
    assert with_change.work_item == changed


def test_a_duplicate_comes_before_reject() -> None:
    first = _snapshot(9, _runnable())
    second = _snapshot(9, _runnable(), feature_directory="F0001-copy")

    event = _evaluate([first, second], [_illegal(9)])

    assert event.kind == "duplicate"


@pytest.mark.parametrize(("state", "kind"), [("merged", "merged"), ("open", "reject")])
def test_the_waiting_work_items_change_is_skipped_only_when_its_pull_request_is_merged(
    state: PullRequestState, kind: str
) -> None:
    waiting = _snapshot(1, _at_approval())
    lookup = _Lookup(state)

    event = _evaluate([waiting], [_illegal(1)], lookup=lookup)

    assert event.kind == kind
    assert event.work_item == waiting
    assert lookup.calls == [PULL_REQUEST]


@pytest.mark.parametrize("own_change", [True, False], ids=["both-changed", "other-changed"])
def test_another_work_items_change_is_rejected_beside_a_merged_pull_request(
    own_change: bool,
) -> None:
    waiting = _snapshot(1, _at_approval())
    other = _snapshot(2, _runnable())
    changes = [_illegal(1), _illegal(2)] if own_change else [_illegal(2)]
    lookup = _Lookup("merged")

    event = _evaluate([waiting, other], changes, lookup=lookup)

    assert event.kind == "reject"
    assert event.work_item == other
    assert lookup.calls == [PULL_REQUEST]


@pytest.mark.parametrize("changed", [1, 2], ids=["waiting-changed", "other-changed"])
def test_a_failed_lookup_skips_no_illegal_change(changed: int) -> None:
    waiting = _snapshot(1, _at_approval())
    other = _snapshot(2, _runnable())
    lookup = _Lookup(error=HostingServiceError("get_pull_request", "the service is down"))

    event = _evaluate([waiting, other], [_illegal(changed)], lookup=lookup)

    assert event.kind == "reject"
    assert event.work_item == (waiting if changed == 1 else other)
    assert lookup.calls == [PULL_REQUEST]


def test_no_lookup_when_no_work_item_waits() -> None:
    lookup = _Lookup("merged")

    event = _evaluate([_snapshot(1, _runnable())], [_illegal(1)], lookup=lookup)

    assert event.kind == "reject"
    assert lookup.calls == []


def test_evaluation_input_has_no_illegal_changes_by_default() -> None:
    facts = EvaluationInput(definition=DEFINITION, snapshots=[], main_commit=MAIN)

    assert facts.illegal_changes == []
