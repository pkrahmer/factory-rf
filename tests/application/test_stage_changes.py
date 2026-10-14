"""The last stage change of a work item: its newest commit beyond origin/main on its branch."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.work_items import RemoteWorkItems
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.move_rule import StageChange
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemSnapshot, WorkItemState
from git_support import clone, commit_all, run_git, write_files
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
BODY = "# First story\n"
CLAIM = Claim(
    instance="factory-1",
    stage="tests",
    started_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC),
    lease_duration=60,
)


def _journal(*kinds: JournalKind) -> list[JournalRecord]:
    return [
        JournalRecord(number=number, speaker="factory", kind=kind)
        for number, kind in enumerate(kinds, start=1)
    ]


def _text(state: WorkItemState, body: str = BODY) -> str:
    return FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body=body))


def _open(human: HumanClone, state: WorkItemState) -> None:
    # The branch's first commit opens it from origin/main; only the commits after it can change.
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, PATH, _text(state))


def _last_change(boundaries: Boundaries, *, path: str = PATH) -> StageChange | None:
    git = boundaries.git
    git.fetch()
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=path,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=git.resolve(f"origin/{BRANCH}"),
        document=WorkItemDocument(state=WorkItemState(stage="intake"), body=BODY),
    )
    return RemoteWorkItems(git, FrontmatterWorkItemReader()).last_stage_change(snapshot)


def test_a_commit_that_changed_the_stage_is_the_last_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    _open(human, WorkItemState(stage="intake"))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="tests")))

    change = _last_change(boundaries)

    assert change == StageChange(from_stage="intake", to_stage="tests", correction=False)


def test_only_the_newest_commit_that_touched_the_file_counts(
    boundaries: Boundaries, human: HumanClone
) -> None:
    _open(human, WorkItemState(stage="intake"))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="tests")))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="doing")))
    human.push_file(BRANCH, "src/other.py", "VALUE = 1\n")

    change = _last_change(boundaries)

    assert change == StageChange(from_stage="tests", to_stage="doing")


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            WorkItemState(stage="tests"),
            WorkItemState(stage="tests", journal=_journal("started")),
        ),
        (
            WorkItemState(stage="tests"),
            WorkItemState(stage="tests", attempts=1, claim=CLAIM),
        ),
        (WorkItemState(stage="tests"), WorkItemState(stage="tests")),
    ],
    ids=["journal", "claim", "body"],
)
def test_a_commit_that_kept_the_stage_is_no_stage_change(
    boundaries: Boundaries, human: HumanClone, before: WorkItemState, after: WorkItemState
) -> None:
    _open(human, WorkItemState(stage="intake"))
    human.push_file(BRANCH, PATH, _text(before))
    human.push_file(BRANCH, PATH, _text(after, body=BODY + "\nMore text.\n"))

    assert _last_change(boundaries) is None


def test_a_merge_commit_is_no_stage_change(
    boundaries: Boundaries, human: HumanClone, remote: Path, tmp_path: Path
) -> None:
    _open(human, WorkItemState(stage="intake"))
    # One clone changes another key on the branch, a second clone changes the stage beside it.
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="intake", pull_request=3)))
    other = clone(remote, tmp_path / "other")
    run_git(other, "checkout", "-q", "-b", "side", f"origin/{BRANCH}~1")
    write_files(other, {PATH: _text(WorkItemState(stage="tests"))})
    commit_all(other, "move the stage")
    run_git(other, "checkout", "-q", "-B", BRANCH, f"origin/{BRANCH}")
    run_git(other, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    run_git(other, "push", "-q", "origin", BRANCH)
    merged = run_git(other, "show", f"HEAD:{PATH}")
    assert "stage: tests" in merged
    assert "pull_request: 3" in merged

    assert _last_change(boundaries) is None


def test_a_snapshot_without_a_branch_has_no_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    git = boundaries.git
    git.fetch()
    snapshot = WorkItemSnapshot(
        id=WORK_ITEM,
        path=PATH,
        folder="in-progress",
        branch=BRANCH,
        branch_commit=None,
        document=WorkItemDocument(state=WorkItemState(stage="intake"), body=BODY),
    )

    change = RemoteWorkItems(git, FrontmatterWorkItemReader()).last_stage_change(snapshot)

    assert change is None


def test_a_branch_whose_commits_beyond_main_left_the_file_alone_has_no_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.push_file("main", BACKLOG_PATH, _text(WorkItemState(stage="review")))
    human.start(BACKLOG_PATH)
    human.push_file(BRANCH, "src/other.py", "VALUE = 1\n")

    assert _last_change(boundaries) is None


def test_a_file_the_newest_commit_added_has_no_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.push_file(BRANCH, "src/other.py", "VALUE = 1\n")
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="tests")))

    assert _last_change(boundaries) is None


def test_a_previous_version_that_cannot_be_parsed_has_no_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    _open(human, WorkItemState(stage="intake"))
    human.push_file(BRANCH, PATH, "---\nstage: [unclosed\n---\n# First story\n")
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="approval")))

    assert _last_change(boundaries) is None


def test_a_file_the_newest_commit_deleted_has_no_stage_change(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    _open(human, WorkItemState(stage="intake"))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="tests")))
    directory = tmp_path / "human"
    run_git(directory, "rm", "-q", PATH)
    run_git(directory, "commit", "-q", "-m", "delete the work item")
    run_git(directory, "push", "-q", "origin", BRANCH)

    assert _last_change(boundaries) is None


@pytest.mark.parametrize(("kind", "correction"), [("move_back", True), ("result", False)])
def test_a_stage_change_that_appends_a_move_back_is_a_correction(
    boundaries: Boundaries, human: HumanClone, kind: JournalKind, correction: bool
) -> None:
    _open(human, WorkItemState(stage="intake", journal=_journal("started")))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="review", journal=_journal("started"))))
    after = WorkItemState(stage="intake", journal=_journal("started", kind))
    human.push_file(BRANCH, PATH, _text(after))

    change = _last_change(boundaries)

    assert change == StageChange(from_stage="review", to_stage="intake", correction=correction)


def test_a_stage_change_that_keeps_the_journals_length_is_no_correction(
    boundaries: Boundaries, human: HumanClone
) -> None:
    journal = _journal("started", "move_back")
    _open(human, WorkItemState(stage="intake", journal=journal))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="review", journal=journal)))
    human.push_file(BRANCH, PATH, _text(WorkItemState(stage="intake", journal=journal)))

    change = _last_change(boundaries)

    assert change == StageChange(from_stage="review", to_stage="intake", correction=False)


def test_the_opening_commit_of_a_started_story_is_no_stage_change(
    boundaries: Boundaries, human: HumanClone
) -> None:
    human.push_file("main", BACKLOG_PATH, _text(WorkItemState(stage="review")))
    _open(human, WorkItemState(stage="intake"))

    assert _last_change(boundaries) is None
