"""The evaluation turns what the remote shows into one event, by four tiers in order."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

import pytest

from factory.domain.errors import HostingServiceError
from factory.domain.evaluation import (
    EvaluationInput,
    PullRequestObservation,
    evaluate,
    question_posted,
)
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


def _runnable(*, attempts: int = 0) -> WorkItemState:
    return initial_state("intake").model_copy(update={"attempts": attempts})


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


def _human_comment(comment_id: int) -> PullRequestComment:
    return PullRequestComment(
        id=comment_id,
        author="human",
        body="A remark.",
        created_at=AT,
        by_factory=False,
        key=None,
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


def test_no_work_items_is_idle_at_main_without_a_lookup() -> None:
    lookup = _Lookup()

    event = _evaluate(lookup=lookup)

    assert event.kind == "idle"
    assert event.work_item is None
    assert event.pull_request is None
    assert event.remote_state == MAIN
    assert lookup.calls == []


@pytest.mark.parametrize("before", ["nothing", "waiting"])
@pytest.mark.parametrize("duplicated", ["runnable", "waiting"])
def test_two_work_items_with_one_id_are_a_duplicate_before_anything_else(
    before: str, duplicated: str
) -> None:
    state = _runnable() if duplicated == "runnable" else _at_approval(handed_over=None)
    first = _snapshot(2, state)
    second = _snapshot(2, state, feature_directory="F0001-copy")
    leading = [_snapshot(1, _blocked())] if before == "waiting" else []
    lookup = _Lookup()

    event = _evaluate(*leading, first, second, lookup=lookup)

    assert event.kind == "duplicate"
    assert event.work_item == first
    assert first.path in event.detail
    assert second.path in event.detail
    assert event.detail.index(first.path) < event.detail.index(second.path)
    assert lookup.calls == []


@pytest.mark.parametrize(
    "snapshot",
    [
        _snapshot(3, None),
        _snapshot(3, WorkItemState(stage="nowhere")),
    ],
    ids=["no-state", "unknown-stage"],
)
def test_a_work_item_without_state_or_in_an_unknown_stage_is_a_value_error(
    snapshot: WorkItemSnapshot,
) -> None:
    with pytest.raises(ValueError, match="F0001-S0003"):
        _evaluate(_snapshot(1, _runnable()), snapshot)


@pytest.mark.parametrize("blocked_first", [True, False], ids=["blocked-first", "approval-first"])
def test_only_the_first_waiting_work_item_is_looked_up_once(blocked_first: bool) -> None:
    blocked, approval = _blocked(pull_request=7), _at_approval(pull_request=8)
    first, second = (blocked, approval) if blocked_first else (approval, blocked)
    lookup = _Lookup()

    _evaluate(_snapshot(1, first), _snapshot(2, second), lookup=lookup)

    assert lookup.calls == [first.pull_request]


@pytest.mark.parametrize(
    "state",
    [_blocked(pull_request=None), _at_approval(pull_request=None)],
    ids=["blocked", "approval"],
)
def test_a_waiting_work_item_without_a_pull_request_asks_without_a_lookup(
    state: WorkItemState,
) -> None:
    snapshot = _snapshot(1, state)
    lookup = _Lookup()

    event = _evaluate(snapshot, lookup=lookup)

    assert event.kind == "ask"
    assert event.work_item == snapshot
    assert event.detail == "no pull request"
    assert lookup.calls == []


def test_a_failed_lookup_is_a_pull_request_lookup_event() -> None:
    snapshot = _snapshot(1, _blocked())
    error = HostingServiceError("get_pull_request", "the service is down")

    event = _evaluate(snapshot, _snapshot(2, _runnable()), lookup=_Lookup(error=error))

    assert event.kind == "pull_request_lookup"
    assert event.work_item == snapshot
    assert event.pull_request is None
    assert str(error) in event.detail


@pytest.mark.parametrize("state", ["merged", "closed"])
def test_a_merged_or_closed_pull_request_is_its_own_event(state: PullRequestState) -> None:
    snapshot = _snapshot(1, _at_approval())
    view = _view(state)

    event = _evaluate(snapshot, lookup=_Lookup(view))

    assert event.kind == state
    assert event.work_item == snapshot
    assert event.pull_request == view
    assert event.remote_state == BRANCH_COMMIT


@pytest.mark.parametrize(
    ("state", "comments", "kind"),
    [
        (_at_approval(), [_human_comment(1)], "comment"),
        (_at_approval(handed_over=None), [], "hand_over"),
        (_blocked(), [], "ask"),
    ],
    ids=["comment", "hand_over", "ask"],
)
def test_events_after_a_successful_lookup_carry_the_view(
    state: WorkItemState, comments: list[PullRequestComment], kind: str
) -> None:
    snapshot = _snapshot(1, state)
    view = _view()

    event = _evaluate(snapshot, lookup=_Lookup(view, comments))

    assert event.kind == kind
    assert event.work_item == snapshot
    assert event.pull_request == view


def test_unread_human_comments_are_a_comment_event_with_their_count() -> None:
    snapshot = _snapshot(1, _at_approval(comments_read=[3]))
    comments = [_human_comment(3), _factory_comment(4), _human_comment(5), _human_comment(6)]

    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))

    assert event.kind == "comment"
    assert event.work_item == snapshot
    assert event.detail == "2 new comments"


@pytest.mark.parametrize(
    ("comments", "comments_read"),
    [
        ([_factory_comment(1), _factory_comment(2, kind="stall", n="1")], []),
        ([_human_comment(1), _factory_comment(2), _human_comment(3)], [1, 3]),
    ],
    ids=["only-the-factorys", "all-read"],
)
def test_factory_and_read_comments_are_no_comment_event(
    comments: list[PullRequestComment], comments_read: list[int]
) -> None:
    snapshot = _snapshot(1, _at_approval(comments_read=comments_read))

    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))

    assert event.kind == "idle"


@pytest.mark.parametrize("handed_over", [None, "review"])
@pytest.mark.parametrize("unread", [False, True], ids=["no-comment", "unread-comment"])
def test_an_approval_not_handed_over_is_a_hand_over_before_comments(
    handed_over: str | None, unread: bool
) -> None:
    snapshot = _snapshot(1, _at_approval(handed_over=handed_over))
    comments = [_human_comment(1)] if unread else []

    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))

    assert event.kind == "hand_over"
    assert event.work_item == snapshot


def test_an_approval_handed_over_is_no_hand_over() -> None:
    event = _evaluate(_snapshot(1, _at_approval(handed_over="approval")), lookup=_Lookup())

    assert event.kind == "idle"


@pytest.mark.parametrize(
    "comments",
    [[], [_factory_comment(1, work_item="F0001-S0009")]],
    ids=["no-comment", "keyed-to-another-work-item"],
)
def test_a_blocked_work_item_whose_question_is_not_posted_asks(
    comments: list[PullRequestComment],
) -> None:
    snapshot = _snapshot(1, _blocked())

    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))

    assert event.kind == "ask"
    assert event.work_item == snapshot


@pytest.mark.parametrize(
    "journal",
    [("created", "question"), ("created", "question", "comment")],
    ids=["question-last", "comment-after-question"],
)
def test_a_post_keyed_to_the_latest_question_is_the_posted_question(
    journal: tuple[JournalKind, ...],
) -> None:
    snapshot = _snapshot(1, _blocked(journal=journal))
    comments = [_factory_comment(1, kind="question", n="2")]

    assert question_posted(snapshot, comments)
    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))
    assert event.kind == "idle"


@pytest.mark.parametrize(
    ("state", "comments"),
    [
        (
            _blocked(journal=("created", "question", "result", "question")),
            [_factory_comment(1, kind="question", n="2")],
        ),
        (
            _blocked(blocked="attempts_cap", journal=("created", "question")),
            [_factory_comment(1, kind="question", n="2")],
        ),
        (
            WorkItemState(stage="review", journal=_journal("created", "question")),
            [_factory_comment(1, kind="question", n="1"), _factory_comment(2, n="2")],
        ),
        (
            _blocked(blocked="attempts_cap", journal=("created", "result")),
            [
                _factory_comment(1, kind="attempts_cap", n="1"),
                _factory_comment(2, kind="attempts_cap", n="2"),
            ],
        ),
    ],
    ids=["another-number", "another-kind", "not-blocked", "no-question-record"],
)
def test_question_posted_is_false_without_a_post_for_the_latest_question(
    state: WorkItemState, comments: list[PullRequestComment]
) -> None:
    assert not question_posted(_snapshot(1, state), comments)


def test_a_post_for_an_earlier_question_still_asks() -> None:
    snapshot = _snapshot(1, _blocked(journal=("created", "question", "result", "question")))
    comments = [_factory_comment(1, kind="question", n="2")]

    event = _evaluate(snapshot, lookup=_Lookup(comments=comments))

    assert event.kind == "ask"


@pytest.mark.parametrize("waiting_first", [True, False], ids=["waiting-first", "runnable-first"])
def test_a_waiting_work_item_with_nothing_new_is_idle_and_holds_back_new_work(
    waiting_first: bool,
) -> None:
    waiting_number, runnable_number = (1, 2) if waiting_first else (2, 1)
    waiting = _snapshot(waiting_number, _at_approval())
    runnable = _snapshot(runnable_number, _runnable())
    ordered = sorted([waiting, runnable], key=lambda snapshot: snapshot.id)
    view = _view()

    event = _evaluate(*ordered, lookup=_Lookup(view))

    assert event.kind == "idle"
    assert event.work_item is None
    assert event.pull_request == view
    assert waiting.id in event.detail


@pytest.mark.parametrize(("status", "kind"), [("own", "crash"), ("expired", "expired")])
def test_a_claim_of_this_or_an_expired_instance_comes_before_new_work(
    status: ClaimStatus, kind: str
) -> None:
    claimed = _snapshot(2, _claimed())
    claim_status = _ClaimStatus(status)

    event = _evaluate(
        _snapshot(1, _runnable()),
        claimed,
        _snapshot(3, _claimed()),
        claim_status=claim_status,
    )

    assert event.kind == kind
    assert event.work_item == claimed
    assert claim_status.asked == [claimed.document.state]


def test_a_claim_held_by_another_instance_is_idle_and_holds_back_new_work() -> None:
    claimed = _snapshot(2, _claimed(OTHER_INSTANCE))
    claim_status = _ClaimStatus("held")

    event = _evaluate(
        _snapshot(1, _runnable()),
        claimed,
        _snapshot(3, _runnable()),
        claim_status=claim_status,
    )

    assert event.kind == "idle"
    assert event.work_item is None
    assert claimed.id in event.detail
    assert OTHER_INSTANCE in event.detail
    assert claim_status.asked == [claimed.document.state]


def test_the_first_work_item_with_a_role_runs_and_done_is_skipped() -> None:
    finished = _snapshot(1, WorkItemState(stage="done"))
    runnable = _snapshot(2, _runnable())
    claim_status = _ClaimStatus()

    event = _evaluate(finished, runnable, _snapshot(3, _runnable()), claim_status=claim_status)

    assert event.kind == "run"
    assert event.work_item == runnable
    assert event.remote_state == BRANCH_COMMIT
    assert claim_status.asked == []


@pytest.mark.parametrize(
    ("attempts", "kind", "detail"),
    [(1, "run", None), (2, "ask", "attempts cap")],
)
def test_a_work_item_at_the_attempts_cap_asks_instead_of_running(
    attempts: int, kind: str, detail: str | None
) -> None:
    snapshot = _snapshot(1, _runnable(attempts=attempts))

    event = _evaluate(snapshot)

    assert event.kind == kind
    assert event.work_item == snapshot
    if detail is not None:
        assert event.detail == detail


@pytest.mark.parametrize(
    ("snapshot", "lookup", "status"),
    [
        (_snapshot(1, _at_approval()), _Lookup(), "none"),
        (_snapshot(1, _claimed()), _Lookup(), "held"),
    ],
    ids=["tier-2", "tier-3"],
)
def test_idle_events_of_a_work_item_are_at_main(
    snapshot: WorkItemSnapshot, lookup: _Lookup, status: ClaimStatus
) -> None:
    event = _evaluate(snapshot, lookup=lookup, claim_status=_ClaimStatus(status))

    assert event.kind == "idle"
    assert event.remote_state == MAIN


def _duplicate(branch_commit: str | None) -> list[WorkItemSnapshot]:
    return [
        _snapshot(1, _runnable(), branch_commit=branch_commit),
        _snapshot(1, _runnable(), branch_commit=branch_commit, feature_directory="F0001-copy"),
    ]


@pytest.mark.parametrize(
    ("kind", "build", "status"),
    [
        ("duplicate", _duplicate, "none"),
        ("crash", lambda commit: [_snapshot(1, _claimed(), branch_commit=commit)], "own"),
        ("expired", lambda commit: [_snapshot(1, _claimed(), branch_commit=commit)], "expired"),
        (
            "ask",
            lambda commit: [_snapshot(1, _blocked(pull_request=None), branch_commit=commit)],
            "none",
        ),
        ("ask", lambda commit: [_snapshot(1, _runnable(attempts=2), branch_commit=commit)], "none"),
    ],
    ids=["duplicate", "crash", "expired", "ask-no-pull-request", "ask-attempts-cap"],
)
@pytest.mark.parametrize("branch_commit", [BRANCH_COMMIT, None], ids=["branch", "no-branch"])
def test_work_item_events_are_at_their_branch_else_at_main(
    kind: str,
    build: Callable[[str | None], list[WorkItemSnapshot]],
    status: ClaimStatus,
    branch_commit: str | None,
) -> None:
    snapshots = build(branch_commit)

    event = _evaluate(*snapshots, claim_status=_ClaimStatus(status))

    assert event.kind == kind
    assert event.remote_state == (MAIN if branch_commit is None else branch_commit)
