"""The acceptance's hand-over: its description, the ready flag, the cost table, the record."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.acceptance import AcceptanceHandOver, AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import commit_subject
from factory.domain.acceptance import AcceptanceState, acceptance_description
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.cost_records import CostRecord
from factory.domain.errors import CannotHandle, HostingServiceError, PushFailed
from factory.domain.events import Event, EventKind
from factory.domain.hosting import PostKey, PullRequestComment
from factory.domain.journal import FACTORY, JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit, run_git
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
ARCHIVED = ["F0002-S0001", "F0002-S0002"]
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
SIDECAR = cost_records_path(REPORT)
ROLE = "acceptance-reviewer"
APPROVAL = "approval"
ORIGINAL_DESCRIPTION = "body"
REMOTE_STATE = "a" * 40
STORY = "F0001-S0001"
STORY_PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
BODY = (
    "# Acceptance of Todo service\n\n## Recommendation\n\naccepted with stories\n\n"
    "## Proposed stories\n\n- one story\n\n## Journal\n\n1. factory: started.\n"
    "2. acceptance-reviewer: accepted with stories; 1 story proposed\n"
)
BARE_BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: started.\n"
STARTED = JournalRecord(number=1, speaker=FACTORY, kind="started")
JOURNAL = [STARTED, JournalRecord(number=2, speaker=ROLE, kind="result")]
LATEST_RESULT = 2

Publish = Callable[[WorkItemDocument], WorkItemSnapshot]


@pytest.fixture
def opened(boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone) -> str:
    """Push the due feature `F0002-todo`, open its acceptance and return the branch."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    return AcceptanceService(boundaries, definition).open("F0002").branch


@pytest.fixture
def pull_request(hosting: FakeHostingService, opened: str) -> int:
    """Return the number of the acceptance's open draft pull request."""
    view = hosting.create_pull_request(opened, f"{ACCEPTANCE}: acceptance", "body", draft=True)
    return view.number


@pytest.fixture
def publish(boundaries: Boundaries, *, human: HumanClone, checkout: GitCli, opened: str) -> Publish:
    """Return a function that pushes the report and its cost records and returns its snapshot."""

    def push(document: WorkItemDocument) -> WorkItemSnapshot:
        text = boundaries.work_item_writer.render(document)
        human.push_file(opened, SIDECAR, sidecar_text(_records()))
        human.push_file(opened, REPORT, text)
        checkout.fetch()
        return WorkItemSnapshot(
            id=ACCEPTANCE,
            path=REPORT,
            folder="in-progress",
            branch=opened,
            branch_commit=checkout.resolve(f"origin/{opened}"),
            document=boundaries.work_item_reader.parse(text),
        )

    return push


def _records() -> list[CostRecord]:
    return completed_records(ACCEPTANCE, 3)


def _report(
    pull_request: int | None,
    *,
    stage: str = APPROVAL,
    handed_over: str | None = None,
    journal: list[JournalRecord] | None = None,
    body: str = BODY,
) -> WorkItemDocument:
    state = AcceptanceState(
        stage=stage,
        stories=ARCHIVED,
        pull_request=pull_request,
        handed_over=handed_over,
        journal=JOURNAL if journal is None else journal,
    )
    return WorkItemDocument(state=state, body=body)


def _event(snapshot: WorkItemSnapshot, kind: EventKind = "hand_over") -> Event:
    return Event(kind=kind, work_item=snapshot, remote_state=REMOTE_STATE)


def _story_event() -> Event:
    state = WorkItemState(stage=APPROVAL, pull_request=1)
    snapshot = WorkItemSnapshot(
        id=STORY,
        path=STORY_PATH,
        folder="in-progress",
        branch=f"work-item/{STORY}",
        branch_commit=None,
        document=WorkItemDocument(state=state, body="# First story\n"),
    )
    return _event(snapshot)


def _remote_state(boundaries: Boundaries, checkout: GitCli) -> WorkItemState:
    checkout.fetch()
    text = checkout.show_file(f"origin/{BRANCH}", REPORT)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    return state


def _cost_table_posts(hosting: FakeHostingService, number: int) -> list[PullRequestComment]:
    return [
        post
        for post in hosting.factory_posts(number)
        if post.key is not None and post.key.kind == "cost_table"
    ]


def _assert_untouched(
    hosting: FakeHostingService, number: int, remote: Path, branch_commit: str | None
) -> None:
    assert hosting.description(number) == ORIGINAL_DESCRIPTION
    assert hosting.get_pull_request(number).draft
    assert hosting.factory_posts(number) == []
    assert remote_commit(remote, BRANCH) == branch_commit


def test_the_hand_over_sets_the_acceptance_description_and_marks_the_pull_request_ready(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request))

    AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert hosting.description(pull_request) == acceptance_description(snapshot.document, ROLE)
    assert not hosting.get_pull_request(pull_request).draft


@pytest.mark.parametrize(
    ("journal", "body", "n"),
    [(JOURNAL, BODY, LATEST_RESULT), ([STARTED], BARE_BODY, 0)],
    ids=["latest-result", "no-result"],
)
def test_the_hand_over_posts_the_cost_table_once_keyed_by_the_latest_result(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    publish: Publish,
    pull_request: int,
    journal: list[JournalRecord],
    body: str,
    n: int,
) -> None:
    snapshot = publish(_report(pull_request, journal=journal, body=body))

    AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    [post] = hosting.factory_posts(pull_request)
    assert post.key == PostKey(work_item=ACCEPTANCE, kind="cost_table", n=str(n))
    assert cost_table(bills_by_stage(_records())) in post.body


def test_the_hand_over_records_handed_over_in_one_commit_of_the_report_only(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    remote: Path,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request))

    AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    checkout.fetch()
    [commit] = checkout.log(f"origin/{BRANCH}", since=snapshot.branch_commit)
    assert commit.subject == commit_subject(ACCEPTANCE, f"handed over at {APPROVAL}")
    assert _remote_state(boundaries, checkout).handed_over == APPROVAL
    changed = run_git(remote, "diff-tree", "--no-commit-id", "--name-only", "-r", BRANCH)
    assert changed.splitlines() == [REPORT]


def test_a_failing_description_raises_and_posts_and_records_nothing(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request))
    hosting.fail_next("set_description")

    with pytest.raises(HostingServiceError):
        AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert hosting.factory_posts(pull_request) == []
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_after_a_failing_ready_flag_the_next_handling_completes_with_one_cost_table_post(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request))
    hosting.fail_next("set_draft")
    with pytest.raises(HostingServiceError):
        AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert len(_cost_table_posts(hosting, pull_request)) == 1
    assert _remote_state(boundaries, checkout).handed_over == APPROVAL


def test_after_a_kill_before_the_push_the_next_handling_records_with_one_cost_table_post(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    checkout: GitCli,
    kill_points: KillPoints,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request))
    kill_points.arm(KillPoint.BEFORE_PUSH)
    with pytest.raises(InjectedKill):
        AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert len(_cost_table_posts(hosting, pull_request)) == 1
    assert _remote_state(boundaries, checkout).handed_over == APPROVAL


def test_a_report_handed_over_on_its_branch_is_handled_without_effect_despite_a_stale_snapshot(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    pushed = publish(_report(pull_request, handed_over=APPROVAL))
    stale = pushed.model_copy(update={"document": _report(pull_request)})

    AcceptanceHandOver(boundaries, definition).handle(_event(stale))

    _assert_untouched(hosting, pull_request, remote, pushed.branch_commit)


def test_a_report_without_a_pull_request_cannot_be_handed_over(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(None))

    with pytest.raises(CannotHandle) as raised:
        AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert (raised.value.kind, raised.value.reason) == (
        "hand_over",
        f"work item {ACCEPTANCE} has no pull request",
    )
    _assert_untouched(hosting, pull_request, remote, snapshot.branch_commit)


def test_a_report_at_a_stage_that_is_not_an_approval_cannot_be_handed_over(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
) -> None:
    snapshot = publish(_report(pull_request, stage="acceptance"))

    with pytest.raises(CannotHandle) as raised:
        AcceptanceHandOver(boundaries, definition).handle(_event(snapshot))

    assert (raised.value.kind, raised.value.reason) == (
        "hand_over",
        "stage acceptance is not an approval",
    )
    _assert_untouched(hosting, pull_request, remote, snapshot.branch_commit)


@pytest.mark.parametrize(
    ("story", "kind", "reason"),
    [(False, "merged", "not a hand_over event"), (True, "hand_over", "not an acceptance")],
    ids=["another-kind", "a-story"],
)
def test_an_event_that_is_not_an_acceptance_hand_over_cannot_be_handled(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
    story: bool,
    kind: EventKind,
    reason: str,
) -> None:
    snapshot = publish(_report(pull_request))
    event = _story_event() if story else _event(snapshot, kind)

    with pytest.raises(CannotHandle) as raised:
        AcceptanceHandOver(boundaries, definition).handle(event)

    assert (raised.value.kind, raised.value.reason) == (kind, reason)
    _assert_untouched(hosting, pull_request, remote, snapshot.branch_commit)


@pytest.mark.parametrize(
    ("story", "reason"),
    [(False, "no acceptance stage"), (True, "not an acceptance")],
    ids=["an-acceptance", "a-story"],
)
def test_without_an_acceptance_stage_the_handler_is_built_and_refuses_every_hand_over(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    hosting: FakeHostingService,
    remote: Path,
    publish: Publish,
    pull_request: int,
    story: bool,
    reason: str,
) -> None:
    snapshot = publish(_report(pull_request))
    without = definition.model_copy(update={"acceptance_stage": None})
    handler = AcceptanceHandOver(boundaries, without)

    with pytest.raises(CannotHandle) as raised:
        handler.handle(_story_event() if story else _event(snapshot))

    assert (raised.value.kind, raised.value.reason) == ("hand_over", reason)
    _assert_untouched(hosting, pull_request, remote, snapshot.branch_commit)


class RacingHosting(FakeHostingService):
    """Lets the human push a change to the branch just before the description is set."""

    def __init__(self, kill_points: KillPoints, human: HumanClone) -> None:
        super().__init__(kill_points)
        self._human = human

    def set_description(self, number: int, body: str) -> None:
        self._human.push_file(BRANCH, f"{TODO}/notes.md", "The human was here.\n")
        super().set_description(number, body)


def test_a_push_that_is_not_pushed_raises_and_leaves_handed_over_unset(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    kill_points: KillPoints,
    human: HumanClone,
    checkout: GitCli,
    publish: Publish,
) -> None:
    racing = RacingHosting(kill_points, human)
    view = racing.create_pull_request(BRANCH, f"{ACCEPTANCE}: acceptance", "body", draft=True)
    snapshot = publish(_report(view.number))

    with pytest.raises(PushFailed):
        AcceptanceHandOver(replace(boundaries, hosting=racing), definition).handle(_event(snapshot))

    assert _remote_state(boundaries, checkout).handed_over is None
