"""The reject handler: an illegal stage change is put back by a new commit on the branch."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from branch_reading import remote_document
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.reject import RejectHandler
from factory.domain.errors import CannotHandle, HostingServiceError
from factory.domain.events import Event
from factory.domain.git import CommitInfo
from factory.domain.hosting import PostKey, render_post
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, entry_text
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.post_texts import MOVED_BACK_MARKER, correction_note, move_back_entry_text
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import clone, commit_all, remote_commit, run_git, write_files
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = f"work-item/{WORK_ITEM}"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
OTHER_PATH = "src/other.py"
BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")
MOVE_BACK = JournalRecord(
    number=2,
    speaker=FACTORY,
    kind="move_back",
    at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    stage="approval",
)
CLAIM = Claim(
    instance="factory-1",
    stage="approval",
    started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    lease_duration=60,
)


def _text(boundaries: Boundaries, state: WorkItemState, body: str = BODY) -> str:
    return boundaries.work_item_writer.render(WorkItemDocument(state=state, body=body))


def _push(
    boundaries: Boundaries, human: HumanClone, state: WorkItemState, body: str = BODY
) -> None:
    human.push_file(BRANCH, PATH, _text(boundaries, state, body))


def _illegal(
    boundaries: Boundaries,
    human: HumanClone,
    pull_request: int | None,
    claim: Claim | None = None,
) -> None:
    # The opening commit's parent is on origin/main; a legal commit comes before the illegal one.
    journal = [CREATED]
    _push(
        boundaries, human, WorkItemState(stage="tests", pull_request=pull_request, journal=journal)
    )
    _push(
        boundaries, human, WorkItemState(stage="doing", pull_request=pull_request, journal=journal)
    )
    illegal = WorkItemState(
        stage="approval", pull_request=pull_request, claim=claim, journal=journal
    )
    _push(boundaries, human, illegal)


def _event(boundaries: Boundaries, checkout: GitCli, remote: Path) -> Event:
    checkout.fetch()
    text = checkout.show_file(f"origin/{BRANCH}", PATH)
    assert text is not None
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=checkout.resolve(f"origin/{BRANCH}"),
        document=boundaries.work_item_reader.parse(text),
    )
    main = remote_commit(remote, "main")
    assert main is not None
    return Event(kind="reject", work_item=snapshot, remote_state=main)


def _handle(boundaries: Boundaries, event: Event) -> None:
    RejectHandler(boundaries).handle(event)


def _branch_head(remote: Path) -> str:
    head = remote_commit(remote, BRANCH)
    assert head is not None
    return head


def _new_commits(checkout: GitCli, since: str) -> list[CommitInfo]:
    checkout.fetch()
    return checkout.log(f"origin/{BRANCH}", since=since)


def _branch_state(boundaries: Boundaries, checkout: GitCli) -> WorkItemState:
    state = remote_document(boundaries, checkout).state
    assert state is not None
    return state


def _correction_key() -> PostKey:
    return PostKey(work_item=WORK_ITEM, kind="correction", n=str(MOVE_BACK.number))


def _refused_untouched(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    event = _event(boundaries, checkout, remote)
    branch_head = _branch_head(remote)

    with pytest.raises(CannotHandle) as raised:
        _handle(boundaries, event)

    assert raised.value.kind == "reject"
    assert remote_commit(remote, BRANCH) == branch_head
    assert remote_commit(remote, "main") == event.remote_state
    assert hosting.factory_posts(pull_request) == []
    assert hosting.labels(pull_request) == []


def test_an_illegal_stage_change_is_put_back_by_a_new_commit_on_the_branch(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)
    illegal = _branch_head(remote)

    _handle(boundaries, event)

    [commit] = _new_commits(checkout, illegal)
    assert commit.parents == [illegal]
    assert remote_commit(remote, BRANCH) == commit.commit
    assert _branch_state(boundaries, checkout).stage == "doing"


def test_the_correction_commit_subject_says_moved_back(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)
    illegal = _branch_head(remote)

    _handle(boundaries, event)

    [commit] = _new_commits(checkout, illegal)
    assert MOVED_BACK_MARKER in commit.subject


def test_the_correction_appends_one_move_back_entry_by_the_factory(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request)

    _handle(boundaries, _event(boundaries, checkout, remote))

    document = remote_document(boundaries, checkout)
    assert document.state is not None
    assert document.state.journal == [CREATED, MOVE_BACK]
    assert entry_text(document, MOVE_BACK.number) == move_back_entry_text("doing", "approval")
    assert f"{MOVE_BACK.number}. factory: " in document.body


def test_with_a_pull_request_one_correction_note_is_posted_keyed_by_the_new_entry(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, pull_request)

    _handle(boundaries, _event(boundaries, checkout, remote))

    [post] = hosting.factory_posts(pull_request)
    assert post.key == _correction_key()
    assert post.body == render_post(correction_note("doing", "approval"), _correction_key())


def test_without_a_pull_request_nothing_is_posted_and_the_stage_is_still_moved_back(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, None)

    _handle(boundaries, _event(boundaries, checkout, remote))

    assert hosting.factory_posts(pull_request) == []
    state = _branch_state(boundaries, checkout)
    assert state.stage == "doing"
    assert state.journal == [CREATED, MOVE_BACK]


def test_a_claim_held_at_the_illegal_stage_is_cleared(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request, claim=CLAIM)

    _handle(boundaries, _event(boundaries, checkout, remote))

    state = _branch_state(boundaries, checkout)
    assert state.claim is None
    assert state.stage == "doing"


def test_a_kill_before_the_push_leaves_the_branch_and_a_second_run_corrects_once(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)
    illegal = _branch_head(remote)
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill):
        _handle(boundaries, event)

    assert remote_commit(remote, BRANCH) == illegal
    assert remote_commit(remote, "main") == event.remote_state
    assert checkout.status().changes == []
    [note] = hosting.factory_posts(pull_request)
    assert note.key == _correction_key()

    _handle(boundaries, event)

    assert len(_new_commits(checkout, illegal)) == 1
    assert _branch_state(boundaries, checkout).journal == [CREATED, MOVE_BACK]
    assert [post.key for post in hosting.factory_posts(pull_request)] == [_correction_key()]


def test_a_kill_after_the_post_leaves_the_branch_and_a_second_run_posts_no_second_note(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    kill_points: KillPoints,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)
    illegal = _branch_head(remote)
    kill_points.arm(KillPoint.AFTER_POST)

    with pytest.raises(InjectedKill):
        _handle(boundaries, event)

    assert remote_commit(remote, BRANCH) == illegal
    assert len(hosting.factory_posts(pull_request)) == 1

    _handle(boundaries, event)

    assert len(hosting.factory_posts(pull_request)) == 1
    assert len(_new_commits(checkout, illegal)) == 1
    assert _branch_state(boundaries, checkout).journal == [CREATED, MOVE_BACK]


def test_the_main_branch_keeps_its_head(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)

    _handle(boundaries, event)

    assert remote_commit(remote, "main") == event.remote_state


def test_a_merge_commit_is_refused_and_nothing_is_written_or_posted(
    boundaries: Boundaries,
    *,
    tmp_path: Path,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    journal = [CREATED]
    _push(
        boundaries, human, WorkItemState(stage="doing", pull_request=pull_request, journal=journal)
    )
    doing = WorkItemState(stage="doing", pull_request=pull_request, journal=journal)
    _push(boundaries, human, doing, BODY + "\nMore text.\n")
    # A second clone changes the stage beside the body change and merges the two.
    other = clone(remote, tmp_path / "other")
    run_git(other, "checkout", "-q", "-b", "side", f"origin/{BRANCH}~1")
    approval = WorkItemState(stage="approval", pull_request=pull_request, journal=journal)
    write_files(other, {PATH: _text(boundaries, approval)})
    commit_all(other, "move the stage")
    run_git(other, "checkout", "-q", "-B", BRANCH, f"origin/{BRANCH}")
    run_git(other, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    run_git(other, "push", "-q", "origin", BRANCH)

    _refused_untouched(
        boundaries, remote=remote, checkout=checkout, hosting=hosting, pull_request=pull_request
    )


def test_a_commit_that_kept_the_stage_is_refused_and_nothing_is_written_or_posted(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    state = WorkItemState(stage="doing", pull_request=pull_request, journal=[CREATED])
    _push(
        boundaries,
        human,
        WorkItemState(stage="tests", pull_request=pull_request, journal=[CREATED]),
    )
    _push(boundaries, human, state)
    _push(boundaries, human, state, BODY + "\nMore text.\n")

    _refused_untouched(
        boundaries, remote=remote, checkout=checkout, hosting=hosting, pull_request=pull_request
    )


def test_a_parent_without_the_work_item_file_is_refused_and_nothing_is_written_or_posted(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    human.push_file(BRANCH, OTHER_PATH, "VALUE = 1\n")
    state = WorkItemState(stage="approval", pull_request=pull_request, journal=[CREATED])
    _push(boundaries, human, state)

    _refused_untouched(
        boundaries, remote=remote, checkout=checkout, hosting=hosting, pull_request=pull_request
    )


def test_an_illegal_change_followed_by_a_commit_to_another_file_is_moved_back(
    boundaries: Boundaries, *, remote: Path, human: HumanClone, checkout: GitCli, pull_request: int
) -> None:
    _illegal(boundaries, human, pull_request)
    human.push_file(BRANCH, OTHER_PATH, "VALUE = 1\n")
    event = _event(boundaries, checkout, remote)
    later = _branch_head(remote)

    _handle(boundaries, event)

    [commit] = _new_commits(checkout, later)
    assert commit.parents == [later]
    state = _branch_state(boundaries, checkout)
    assert state.stage == "doing"
    assert state.journal == [CREATED, MOVE_BACK]


def test_a_stage_change_that_is_itself_a_correction_is_refused(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, pull_request)
    moved_back = WorkItemState(
        stage="doing", pull_request=pull_request, journal=[CREATED, MOVE_BACK]
    )
    body = BODY + f"2. factory: {move_back_entry_text('doing', 'approval')}\n"
    _push(boundaries, human, moved_back, body)

    _refused_untouched(
        boundaries, remote=remote, checkout=checkout, hosting=hosting, pull_request=pull_request
    )


@pytest.mark.parametrize("with_pull_request", [True, False])
def test_the_stage_label_is_set_again_only_with_a_pull_request(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
    with_pull_request: bool,
) -> None:
    _illegal(boundaries, human, pull_request if with_pull_request else None)
    if not with_pull_request:
        # Any label call would fail the handler.
        hosting.fail_next("set_labels")

    _handle(boundaries, _event(boundaries, checkout, remote))

    expected = ["stage:doing"] if with_pull_request else []
    assert hosting.labels(pull_request) == expected


def test_a_failing_label_call_raises_and_the_correction_stays_on_the_branch(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    _illegal(boundaries, human, pull_request)
    event = _event(boundaries, checkout, remote)
    illegal = _branch_head(remote)
    hosting.fail_next("set_labels")

    with pytest.raises(HostingServiceError):
        _handle(boundaries, event)

    [commit] = _new_commits(checkout, illegal)
    assert commit.parents == [illegal]
    state = _branch_state(boundaries, checkout)
    assert state.stage == "doing"
    assert state.journal == [CREATED, MOVE_BACK]


def test_an_unreadable_parent_is_refused_and_nothing_is_written_or_posted(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    checkout: GitCli,
    hosting: FakeHostingService,
    pull_request: int,
) -> None:
    _push(
        boundaries,
        human,
        WorkItemState(stage="doing", pull_request=pull_request, journal=[CREATED]),
    )
    human.push_file(BRANCH, PATH, "---\nstage: [unclosed\n---\n# First story\n")
    state = WorkItemState(stage="approval", pull_request=pull_request, journal=[CREATED])
    _push(boundaries, human, state)

    _refused_untouched(
        boundaries, remote=remote, checkout=checkout, hosting=hosting, pull_request=pull_request
    )
