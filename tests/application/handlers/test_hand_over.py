"""The hand-over handler: the approval's description, the ready flag, the cost table, the record."""

from collections.abc import Callable
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from branch_reading import error_posts
from definition_support import pipeline_definition
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, DispatchOutcome, Handler
from factory.application.handlers.hand_over import HandOverHandler
from factory.application.handlers.recording import commit_subject
from factory.application.stops import StopService
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.events import Event
from factory.domain.git import CommitInfo
from factory.domain.hand_over import hand_over_description
from factory.domain.hosting import PostKey, PullRequestComment, render_post
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.paths import cost_records_path
from factory.domain.post_texts import cost_table_post
from factory.domain.tick_status import TickStatus
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
SIDECAR = cost_records_path(PATH)
REMOTE_STATE = "a" * 40
APPROVAL = "approval"
ORIGINAL_DESCRIPTION = "body"
BODY = (
    "# First story\n\n## Description\n\nBuild it.\n\n## Acceptance criteria\n\n1. One.\n\n"
    "## Journal\n\n1. 2026-10-12 human: created.\n2. tester: wrote the tests.\n"
    "3. coder: built it.\n4. reviewer: one question.\n"
)
BARE_BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
JOURNAL = [
    JournalRecord(number=1, speaker=HUMAN, kind="created"),
    JournalRecord(number=2, speaker="tester", kind="result"),
    JournalRecord(number=3, speaker="coder", kind="result"),
    JournalRecord(number=4, speaker="reviewer", kind="question"),
]
LATEST_RESULT = 3

Publish = Callable[[WorkItemDocument], WorkItemSnapshot]


class Counting(Handler):
    """Counts the events it is handed and passes each to the real handler."""

    def __init__(self, inner: Handler) -> None:
        self.calls = 0
        self._inner = inner

    def handle(self, event: Event) -> None:
        self.calls += 1
        self._inner.handle(event)


def _document(
    pull_request: int | None,
    *,
    stage: str = APPROVAL,
    handed_over: str | None = None,
    journal: list[JournalRecord] | None = None,
    body: str = BODY,
) -> WorkItemDocument:
    state = WorkItemState(
        stage=stage,
        pull_request=pull_request,
        journal=JOURNAL if journal is None else journal,
        round=1,
        attempts=1,
        handed_over=handed_over,
    )
    return WorkItemDocument(state=state, body=body)


def _snapshot(document: WorkItemDocument, branch_commit: str | None) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=branch_commit,
        document=document,
    )


def _event(snapshot: WorkItemSnapshot) -> Event:
    return Event(kind="hand_over", work_item=snapshot, remote_state=REMOTE_STATE)


def _handler(boundaries: Boundaries) -> HandOverHandler:
    return HandOverHandler(boundaries, pipeline_definition(boundaries))


def _records() -> list[CostRecord]:
    return completed_records(WORK_ITEM, 3)


@pytest.fixture
def publish(boundaries: Boundaries, *, human: HumanClone, checkout: GitCli) -> Publish:
    """Return a function that pushes a work item and its cost records and returns its snapshot."""

    def push(document: WorkItemDocument) -> WorkItemSnapshot:
        text = boundaries.work_item_writer.render(document)
        human.push_file(BRANCH, SIDECAR, sidecar_text(_records()))
        human.push_file(BRANCH, PATH, text)
        checkout.fetch()
        return _snapshot(
            boundaries.work_item_reader.parse(text), checkout.resolve(f"origin/{BRANCH}")
        )

    return push


def _remote_state(boundaries: Boundaries, checkout: GitCli) -> WorkItemState:
    checkout.fetch()
    text = checkout.show_file(f"origin/{BRANCH}", PATH)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    return state


def _branch_commits(checkout: GitCli) -> list[CommitInfo]:
    checkout.fetch()
    return checkout.log(f"origin/{BRANCH}", since="origin/main")


def _expected_post(records: list[CostRecord]) -> str:
    return cost_table_post(
        cost_table(bills_by_stage(records)), human="0 questions answered, 0.0 h waited"
    )


def _cost_table_posts(hosting: FakeHostingService, number: int) -> list[PullRequestComment]:
    return [
        post
        for post in hosting.factory_posts(number)
        if post.key is not None and post.key.kind == "cost_table"
    ]


def _cost_key(n: int) -> PostKey:
    return PostKey(work_item=WORK_ITEM, kind="cost_table", n=str(n))


def test_the_hand_over_sets_the_description_and_marks_the_pull_request_ready(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    commits = _branch_commits(checkout)

    _handler(boundaries).handle(_event(snapshot))

    expected = hand_over_description(snapshot.document, commits)
    assert hosting.description(pull_request) == expected
    assert not hosting.get_pull_request(pull_request).draft


@pytest.mark.parametrize(
    ("journal", "body", "n"),
    [
        (JOURNAL, BODY, LATEST_RESULT),
        ([JournalRecord(number=1, speaker=HUMAN, kind="created")], BARE_BODY, 0),
    ],
    ids=["latest-result", "no-result"],
)
def test_the_hand_over_posts_the_cost_table_of_the_branch_records_keyed_by_the_latest_result(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    journal: list[JournalRecord],
    body: str,
    n: int,
) -> None:
    snapshot = publish(_document(pull_request, journal=journal, body=body))
    local = boundaries.checkout / SIDECAR
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(sidecar_text(completed_records(WORK_ITEM, 1)), encoding="utf-8")

    _handler(boundaries).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    assert post.key == _cost_key(n)
    assert post.body == render_post(_expected_post(_records()), _cost_key(n))


def test_the_hand_over_then_records_handed_over_in_one_commit_and_changes_nothing_else(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    before = _remote_state(boundaries, checkout)

    _handler(boundaries).handle(_event(snapshot))

    checkout.fetch()
    [commit] = checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit)
    assert commit.subject == commit_subject(WORK_ITEM, f"handed over at {APPROVAL}")
    after = _remote_state(boundaries, checkout)
    assert after.handed_over == APPROVAL
    assert after.model_copy(update={"handed_over": None}) == before


def test_a_failing_post_raises_after_the_description_and_before_any_record(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    commits = _branch_commits(checkout)
    hosting.fail_next("post_comment")

    with pytest.raises(HostingServiceError):
        _handler(boundaries).handle(_event(snapshot))

    assert hosting.description(pull_request) == hand_over_description(snapshot.document, commits)
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
    assert _remote_state(boundaries, checkout).handed_over is None


def test_after_a_failing_post_the_next_handling_completes_with_one_cost_table_post(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    hosting.fail_next("post_comment")
    with pytest.raises(HostingServiceError):
        _handler(boundaries).handle(_event(snapshot))

    _handler(boundaries).handle(_event(snapshot))

    assert _remote_state(boundaries, checkout).handed_over == APPROVAL
    assert len(_cost_table_posts(hosting, pull_request)) == 1


def test_a_kill_after_the_post_leaves_one_post_and_the_next_handling_records_without_another(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    kill_points.arm(KillPoint.AFTER_POST)
    with pytest.raises(InjectedKill):
        _handler(boundaries).handle(_event(snapshot))

    assert len(_cost_table_posts(hosting, pull_request)) == 1
    assert _remote_state(boundaries, checkout).handed_over is None

    _handler(boundaries).handle(_event(snapshot))

    assert _remote_state(boundaries, checkout).handed_over == APPROVAL
    assert len(_cost_table_posts(hosting, pull_request)) == 1


def test_a_work_item_already_handed_over_at_its_stage_is_handled_without_any_effect(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, handed_over=APPROVAL))

    _handler(boundaries).handle(_event(snapshot))

    assert hosting.description(pull_request) == ORIGINAL_DESCRIPTION
    assert hosting.get_pull_request(pull_request).draft
    assert hosting.factory_posts(pull_request) == []
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_work_item_at_a_stage_that_is_not_an_approval_cannot_be_handed_over(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request, stage="smoke-test"))

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "hand_over"
    assert hosting.description(pull_request) == ORIGINAL_DESCRIPTION
    assert hosting.get_pull_request(pull_request).draft
    assert hosting.factory_posts(pull_request) == []
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_work_item_without_a_pull_request_cannot_be_handed_over(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    remote: Path,
    pull_request: int,
) -> None:
    snapshot = _snapshot(_document(None), None)

    with pytest.raises(CannotHandle) as raised:
        _handler(boundaries).handle(_event(snapshot))

    assert raised.value.kind == "hand_over"
    assert hosting.description(pull_request) == ORIGINAL_DESCRIPTION
    assert hosting.get_pull_request(pull_request).draft
    assert hosting.factory_posts(pull_request) == []
    assert remote_commit(remote, BRANCH) is None


def test_a_hand_over_that_always_fails_is_tried_three_times_and_reported_once(
    boundaries: Boundaries,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_document(pull_request))
    hosting.fail_next("set_description", times=10)
    handler = Counting(_handler(boundaries))
    dispatcher = Dispatcher({"hand_over": handler}, TickStatus(), StopService(boundaries))
    event = _event(snapshot)

    outcomes: list[DispatchOutcome] = [dispatcher.dispatch(event), dispatcher.dispatch(event)]
    assert error_posts(hosting, pull_request) == []
    outcomes.append(dispatcher.dispatch(event))
    assert len(error_posts(hosting, pull_request)) == 1
    outcomes.append(dispatcher.dispatch(event))

    assert outcomes == ["error", "error", "reported", "capped"]
    assert handler.calls == 3
    assert len(error_posts(hosting, pull_request)) == 1
