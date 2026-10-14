"""The merged handler: a merged story is archived on main with its bill, then its branch goes."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bill_support import completed_records, sidecar_text
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.merged import MergedHandler
from factory.domain.bills import bill
from factory.domain.cost_records import CostRecord
from factory.domain.errors import PushFailed
from factory.domain.events import Event
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry, entry_text
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import remote_commit, run_git
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
IN_PROGRESS = f"{FEATURE}/in-progress"
PATH = f"{IN_PROGRESS}/F0001-S0001-first.md"
SIDECAR = f"{IN_PROGRESS}/F0001-S0001-first.costs.jsonl"
DONE_PATH = f"{FEATURE}/done/F0001-S0001-first.md"
DONE_SIDECAR = f"{FEATURE}/done/F0001-S0001-first.costs.jsonl"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
SUBJECT = f"work item {WORK_ITEM}: merged, archived"
RESULT = NewEntry(speaker="coder", kind="result", text="implemented.")

Merge = Callable[[WorkItemState, list[CostRecord] | None], WorkItemSnapshot]


def _state(stage: str, pull_request: int) -> WorkItemState:
    created = JournalRecord(number=1, speaker=HUMAN, kind="created")
    return WorkItemState(stage=stage, pull_request=pull_request, journal=[created])


def _event(snapshot: WorkItemSnapshot, remote: Path) -> Event:
    main = remote_commit(remote, "main")
    assert main is not None
    return Event(kind="merged", work_item=snapshot, remote_state=main)


def _archived(boundaries: Boundaries, checkout: GitCli) -> WorkItemDocument:
    checkout.fetch()
    text = checkout.show_file("origin/main", DONE_PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def _archived_state(boundaries: Boundaries, checkout: GitCli) -> WorkItemState:
    state = _archived(boundaries, checkout).state
    assert state is not None
    return state


@pytest.fixture
def merge(boundaries: Boundaries, *, human: HumanClone, checkout: GitCli) -> Merge:
    """Return a function that starts the story, pushes it to its branch and merges it into main."""

    def run(state: WorkItemState, records: list[CostRecord] | None) -> WorkItemSnapshot:
        human.start(BACKLOG_PATH)
        text = boundaries.work_item_writer.render(WorkItemDocument(state=state, body=BODY))
        human.push_file(BRANCH, PATH, text)
        if records is not None:
            human.push_file(BRANCH, SIDECAR, sidecar_text(records))
        human.merge(BRANCH, "merge")
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


def test_the_merged_story_is_moved_under_done_on_main(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    snapshot = merge(_state("doing", pull_request), None)
    event = _event(snapshot, remote)

    MergedHandler(boundaries).handle(event)

    checkout.fetch()
    assert checkout.show_file("origin/main", DONE_PATH) is not None
    assert checkout.show_file("origin/main", PATH) is None
    assert checkout.list_files("origin/main", IN_PROGRESS) == []
    [commit] = checkout.log("origin/main", since=event.remote_state)
    assert commit.subject == SUBJECT


def test_the_archived_state_is_done_unblocked_and_unclaimed_and_keeps_the_rest(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    created = WorkItemDocument(state=_state("doing", pull_request), body=BODY)
    appended = append_entry(created, RESULT).state
    assert appended is not None
    claim = Claim(
        instance="night",
        stage="doing",
        started_at=datetime(2026, 10, 12, 11, 0, tzinfo=UTC),
        lease_duration=60,
    )
    state = appended.model_copy(
        update={
            "blocked": "question",
            "round": 2,
            "attempts": 1,
            "crashes": 1,
            "comments_read": [3, 5],
            "handed_over": "night",
            "claim": claim,
        }
    )
    snapshot = merge(state, None)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    done = JournalRecord(number=3, speaker=FACTORY, kind="done")
    expected = state.model_copy(
        update={
            "stage": "done",
            "blocked": None,
            "claim": None,
            "journal": [*state.journal, done],
        }
    )
    assert _archived_state(boundaries, checkout) == expected


@pytest.mark.parametrize("stage", ["tests", "doing", "approval"])
def test_a_story_is_archived_the_same_way_at_whatever_stage_it_was_merged(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    merge: Merge,
    pull_request: int,
    stage: str,
) -> None:
    state = _state(stage, pull_request)
    snapshot = merge(state, None)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    done = JournalRecord(number=2, speaker=FACTORY, kind="done")
    expected = state.model_copy(update={"stage": "done", "journal": [*state.journal, done]})
    assert _archived_state(boundaries, checkout) == expected
    assert checkout.show_file("origin/main", PATH) is None


def test_the_archive_appends_one_done_entry_of_the_factory_with_the_bill(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    records = completed_records(WORK_ITEM, 2)
    snapshot = merge(_state("approval", pull_request), records)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    archived = _archived(boundaries, checkout)
    assert archived.state is not None
    assert archived.state.journal[-1] == JournalRecord(number=2, speaker=FACTORY, kind="done")
    assert len(archived.state.journal) == 2
    assert entry_text(archived, 2) == done_entry_text(bill(records))


def test_the_bill_counts_every_record_whatever_its_end_and_known_cost(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    first, second, third = completed_records(WORK_ITEM, 3)
    records = [
        first,
        second.model_copy(update={"end_reason": "died"}),
        third.model_copy(update={"cost_usd": None}),
    ]
    snapshot = merge(_state("approval", pull_request), records)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert entry_text(_archived(boundaries, checkout), 2) == done_entry_text(bill(records))


def test_the_cost_records_move_beside_the_archived_story(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    records = completed_records(WORK_ITEM, 2)
    snapshot = merge(_state("approval", pull_request), records)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    checkout.fetch()
    assert checkout.show_file("origin/main", DONE_SIDECAR) == sidecar_text(records)
    assert checkout.show_file("origin/main", SIDECAR) is None
    assert checkout.list_files("origin/main", IN_PROGRESS) == []


def test_a_story_without_cost_records_is_archived_with_an_empty_bill(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    snapshot = merge(_state("approval", pull_request), None)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert entry_text(_archived(boundaries, checkout), 2) == done_entry_text(bill([]))


def test_after_the_archive_the_branch_is_gone_from_the_remote_and_the_checkout(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    checkout.checkout(BRANCH, start_point=f"origin/{BRANCH}")

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert remote_commit(remote, BRANCH) is None
    assert checkout.resolve(f"refs/heads/{BRANCH}") is None
    assert checkout.resolve(f"origin/{BRANCH}") is None


def test_a_story_whose_branch_is_already_gone_is_archived_without_an_error(
    boundaries: Boundaries,
    *,
    tmp_path: Path,
    remote: Path,
    checkout: GitCli,
    merge: Merge,
    pull_request: int,
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    run_git(tmp_path / "human", "push", "-q", "origin", "--delete", BRANCH)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert _archived_state(boundaries, checkout).stage == "done"
    assert remote_commit(remote, BRANCH) is None


def test_a_kill_before_the_push_changes_nothing_and_a_second_run_archives_once(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    kill_points: KillPoints,
    merge: Merge,
    pull_request: int,
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    event = _event(snapshot, remote)
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        MergedHandler(boundaries).handle(event)

    assert remote_commit(remote, "main") == event.remote_state
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit

    MergedHandler(boundaries).handle(event)

    state = _archived_state(boundaries, checkout)
    assert [record.kind for record in state.journal] == ["created", "done"]
    [commit] = checkout.log("origin/main", since=event.remote_state)
    assert commit.subject == SUBJECT
    assert remote_commit(remote, BRANCH) is None


def test_a_kill_after_the_archive_is_pushed_leaves_the_branch_on_the_remote(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    kill_points: KillPoints,
    merge: Merge,
    pull_request: int,
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    kill_points.arm(KillPoint.AFTER_PUSH)

    with pytest.raises(InjectedKill):
        MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert _archived_state(boundaries, checkout).stage == "done"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_main_moved_since_the_checkout_rejects_the_archive_and_keeps_the_branch(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    merge: Merge,
    pull_request: int,
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    event = _event(snapshot, remote)
    human.push_file("main", "notes.md", "The human pushed this.\n")
    moved = remote_commit(remote, "main")

    with pytest.raises(PushFailed) as raised:
        MergedHandler(boundaries).handle(event)

    assert raised.value.outcome == "rejected"
    assert remote_commit(remote, "main") == moved
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit


def test_a_merge_posts_nothing_on_the_pull_request(
    boundaries: Boundaries,
    *,
    remote: Path,
    hosting: FakeHostingService,
    merge: Merge,
    pull_request: int,
) -> None:
    snapshot = merge(_state("approval", pull_request), None)

    MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert hosting.factory_posts(pull_request) == []


def test_a_refused_branch_deletion_fails_after_the_archive_is_pushed(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, merge: Merge, pull_request: int
) -> None:
    snapshot = merge(_state("approval", pull_request), None)
    run_git(remote, "config", "receive.denyDeletes", "true")

    with pytest.raises(PushFailed) as raised:
        MergedHandler(boundaries).handle(_event(snapshot, remote))

    assert raised.value.branch == BRANCH
    assert raised.value.outcome == "rejected"
    assert _archived_state(boundaries, checkout).stage == "done"
    assert remote_commit(remote, BRANCH) == snapshot.branch_commit
