"""The closed handler: a close before the approval moves the story back to the backlog."""

from collections.abc import Callable
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from definition_support import pipeline_definition
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.costs import BillService
from factory.application.handlers.closed import ClosedHandler
from factory.domain.errors import PushFailed
from factory.domain.events import Event
from factory.domain.git import ChangedPath
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit, run_git
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
FEATURE = "factory/features/F0001-example"
BACKLOG = f"{FEATURE}/backlog"
IN_PROGRESS = f"{FEATURE}/in-progress"
BACKLOG_PATH = f"{BACKLOG}/F0001-S0001-first.md"
PATH = f"{IN_PROGRESS}/F0001-S0001-first.md"
SIDECAR = f"{IN_PROGRESS}/F0001-S0001-first.costs.jsonl"
BACKLOG_SIDECAR = f"{BACKLOG}/F0001-S0001-first.costs.jsonl"
BRANCH_BODY = "# First story\n\nRewritten by the factory on the branch.\n"
SUBJECT = f"work item {WORK_ITEM}: closed before the approval, back in the backlog"

Close = Callable[[str], WorkItemSnapshot]


def _event(snapshot: WorkItemSnapshot, remote: Path) -> Event:
    main = remote_commit(remote, "main")
    assert main is not None
    return Event(kind="closed", work_item=snapshot, remote_state=main)


def _handle(boundaries: Boundaries, event: Event) -> None:
    ClosedHandler(boundaries, pipeline_definition(boundaries)).handle(event)


@pytest.fixture
def close(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> Close:
    """Return a function that starts the story, works on its branch at `stage` and closes it."""

    def run(stage: str) -> WorkItemSnapshot:
        human.start(BACKLOG_PATH)
        created = JournalRecord(number=1, speaker=HUMAN, kind="created")
        state = WorkItemState(stage=stage, pull_request=pull_request, journal=[created])
        text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BRANCH_BODY))
        human.push_file(BRANCH, PATH, text)
        human.push_file(BRANCH, SIDECAR, sidecar_text(completed_records(WORK_ITEM, 2)))
        hosting.close_by_human(pull_request)
        checkout.fetch()
        return WorkItemSnapshot(
            id=WORK_ITEM,
            path=PATH,
            folder="in-progress",
            branch=BRANCH,
            branch_commit=checkout.resolve(f"origin/{BRANCH}"),
            document=boundaries.work_item_reader.parse(text),
        )

    return run


def test_a_story_closed_at_doing_is_moved_back_under_backlog_on_main(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    event = _event(snapshot, remote)

    _handle(boundaries, event)

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert checkout.list_files("origin/main", IN_PROGRESS) == []
    [commit] = checkout.log("origin/main", since=event.remote_state)
    assert commit.subject == SUBJECT


def test_the_discarded_story_keeps_the_text_main_held_whatever_the_branch_held(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    before = checkout.show_file("origin/main", PATH)
    assert before is not None

    _handle(boundaries, _event(snapshot, remote))

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) == before


@pytest.mark.parametrize("stage", ["intake", "tests", "review", "docs", "smoke-test"])
def test_a_story_closed_at_any_stage_before_the_approval_is_discarded_the_same_way(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close, stage: str
) -> None:
    snapshot = close(stage)
    before = checkout.show_file("origin/main", PATH)

    _handle(boundaries, _event(snapshot, remote))

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) == before
    assert checkout.show_file("origin/main", PATH) is None
    assert remote_commit(remote, BRANCH) is None


def test_the_discard_commit_moves_only_that_story(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    event = _event(snapshot, remote)

    _handle(boundaries, event)

    checkout.fetch()
    checkout.reset_to("origin/main")
    assert checkout.changed_paths(event.remote_state) == [
        ChangedPath(path=BACKLOG_PATH, change="added"),
        ChangedPath(path=PATH, change="deleted"),
    ]


def test_after_the_discard_the_branch_is_gone_from_the_remote_and_the_checkout(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    checkout.checkout(BRANCH, start_point=f"origin/{BRANCH}")

    _handle(boundaries, _event(snapshot, remote))

    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"refs/heads/{BRANCH}") is None
    assert checkout.resolve(f"origin/{BRANCH}") is None


def test_a_story_started_again_after_a_discard_has_an_empty_bill(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")

    _handle(boundaries, _event(snapshot, remote))
    human.start(BACKLOG_PATH)
    checkout.fetch()

    assert checkout.show_file("origin/main", SIDECAR) is None
    assert checkout.show_file("origin/main", BACKLOG_SIDECAR) is None
    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"origin/{BRANCH}") is None
    result = BillService(boundaries.git, boundaries.cost_reader).for_work_item(WORK_ITEM)
    assert result is not None
    assert result.total.runs == 0


def test_a_story_whose_branch_is_already_gone_is_discarded_without_an_error(
    boundaries: Boundaries, *, tmp_path: Path, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    run_git(tmp_path / "human", "push", "-q", "origin", "--delete", BRANCH)

    _handle(boundaries, _event(snapshot, remote))

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert remote_commit(remote, BRANCH) is None


def test_a_kill_before_the_push_changes_nothing_and_a_second_run_discards_once(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    kill_points: KillPoints,
    close: Close,
) -> None:
    snapshot = close("doing")
    event = _event(snapshot, remote)
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _handle(boundaries, event)

    assert remote_commit(remote, "main") == event.remote_state
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit

    _handle(boundaries, event)

    checkout.fetch()
    [commit] = checkout.log("origin/main", since=event.remote_state)
    assert commit.subject == SUBJECT
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert remote_commit(remote, BRANCH) is None


def test_a_kill_after_the_move_is_pushed_leaves_the_branch_on_the_remote(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    kill_points: KillPoints,
    close: Close,
) -> None:
    snapshot = close("doing")
    kill_points.arm(KillPoint.AFTER_PUSH)

    with pytest.raises(InjectedKill):
        _handle(boundaries, _event(snapshot, remote))

    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_main_moved_since_the_checkout_rejects_the_discard_and_keeps_the_branch(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, close: Close
) -> None:
    snapshot = close("doing")
    event = _event(snapshot, remote)
    human.push_file("main", "notes.md", "The human pushed this.\n")
    moved = remote_commit(remote, "main")

    with pytest.raises(PushFailed) as raised:
        _handle(boundaries, event)

    assert raised.value.outcome == "rejected"
    assert remote_commit(remote, "main") == moved
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_discard_posts_nothing_and_leaves_the_pull_request_closed(
    boundaries: Boundaries,
    *,
    remote: Path,
    hosting: FakeHostingService,
    close: Close,
    pull_request: int,
) -> None:
    snapshot = close("doing")

    _handle(boundaries, _event(snapshot, remote))

    assert hosting.factory_posts(pull_request) == []
    assert hosting.get_pull_request(pull_request).state == "closed"


def test_a_refused_branch_deletion_fails_after_the_move_is_pushed(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, close: Close
) -> None:
    snapshot = close("doing")
    run_git(remote, "config", "receive.denyDeletes", "true")

    with pytest.raises(PushFailed) as raised:
        _handle(boundaries, _event(snapshot, remote))

    assert raised.value.branch == BRANCH
    assert raised.value.outcome == "rejected"
    checkout.fetch()
    assert checkout.show_file("origin/main", BACKLOG_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
