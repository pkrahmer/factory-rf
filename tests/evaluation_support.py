"""Shared inputs of the evaluation's tests: a pipeline definition, snapshots, lookups, claims."""

from collections.abc import Sequence
from datetime import UTC, datetime

from factory.domain.errors import HostingServiceError
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.events import Event
from factory.domain.hosting import (
    PostKey,
    PostKind,
    PullRequestComment,
    PullRequestState,
    PullRequestView,
)
from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.lease import ClaimStatus
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import (
    Blocked,
    Claim,
    WorkItemDocument,
    WorkItemSnapshot,
    WorkItemState,
    initial_state,
)

MAIN = "a" * 40
BRANCH_COMMIT = "b" * 40
MERGE_COMMIT = "c" * 40
PULL_REQUEST = 7
OTHER_INSTANCE = "factory-2"
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


def _id(number: int) -> str:
    return f"F0001-S{number:04d}"


def _snapshot(
    number: int,
    state: WorkItemState | None,
    *,
    branch_commit: str | None = BRANCH_COMMIT,
    feature_directory: str = "F0001-demo",
) -> WorkItemSnapshot:
    work_item = _id(number)
    return WorkItemSnapshot(
        id=work_item,
        path=f"factory/features/{feature_directory}/in-progress/{work_item}-x.md",
        folder="in-progress",
        branch=f"work-item/{work_item}",
        branch_commit=branch_commit,
        document=WorkItemDocument(state=state, body="# T\n"),
    )


def _journal(*kinds: JournalKind) -> list[JournalRecord]:
    return [
        JournalRecord(number=number, speaker="factory" if kind != "created" else "human", kind=kind)
        for number, kind in enumerate(kinds, start=1)
    ]


def _blocked(
    *,
    pull_request: int | None = PULL_REQUEST,
    blocked: Blocked = "question",
    journal: Sequence[JournalKind] = ("created", "question"),
    comments_read: Sequence[int] = (),
) -> WorkItemState:
    return WorkItemState(
        stage="review",
        blocked=blocked,
        pull_request=pull_request,
        journal=_journal(*journal),
        comments_read=list(comments_read),
    )


def _at_approval(
    *,
    pull_request: int | None = PULL_REQUEST,
    handed_over: str | None = "approval",
    comments_read: Sequence[int] = (),
) -> WorkItemState:
    return WorkItemState(
        stage="approval",
        pull_request=pull_request,
        handed_over=handed_over,
        comments_read=list(comments_read),
    )


def _claimed(instance: str = OTHER_INSTANCE) -> WorkItemState:
    claim = Claim(instance=instance, stage="intake", started_at=AT, lease_duration=60)
    return initial_state("intake").model_copy(update={"claim": claim})


def _view(state: PullRequestState = "open", number: int = PULL_REQUEST) -> PullRequestView:
    return PullRequestView(
        number=number,
        branch="work-item/F0001-S0001",
        title="t",
        state=state,
        draft=False,
        merge_commit=MERGE_COMMIT if state == "merged" else None,
        url=f"https://example.test/{number}",
    )


def _factory_comment(
    comment_id: int, *, work_item: str = "F0001-S0001", kind: PostKind = "question", n: str = "2"
) -> PullRequestComment:
    return PullRequestComment(
        id=comment_id,
        author="factory",
        body="A post.",
        created_at=AT,
        by_factory=True,
        key=PostKey(work_item=work_item, kind=kind, n=n),
    )


class _Lookup:
    """A pull request lookup that records its calls and answers with one observation."""

    def __init__(
        self,
        view: PullRequestView | None = None,
        comments: Sequence[PullRequestComment] = (),
        error: HostingServiceError | None = None,
    ) -> None:
        self.calls: list[int] = []
        self._view = _view() if view is None else view
        self._comments = list(comments) if self._view.state == "open" else []
        self._error = error

    def __call__(self, number: int) -> PullRequestObservation:
        self.calls.append(number)
        if self._error is not None:
            raise self._error
        return PullRequestObservation(view=self._view, comments=self._comments)


class _ClaimStatus:
    """A claim status that records the states it is asked about and gives one answer."""

    def __init__(self, status: ClaimStatus = "none") -> None:
        self.asked: list[WorkItemState] = []
        self._status = status

    def __call__(self, state: WorkItemState) -> ClaimStatus:
        self.asked.append(state)
        return self._status


def _facts(*snapshots: WorkItemSnapshot) -> EvaluationInput:
    return EvaluationInput(definition=DEFINITION, snapshots=list(snapshots), main_commit=MAIN)


def _evaluate(
    *snapshots: WorkItemSnapshot,
    lookup: _Lookup | None = None,
    claim_status: _ClaimStatus | None = None,
) -> Event:
    return evaluate(
        _facts(*snapshots),
        _Lookup() if lookup is None else lookup,
        _ClaimStatus() if claim_status is None else claim_status,
    )
