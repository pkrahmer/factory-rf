"""The cleanup deletes the remote branch of a story that is back in the backlog or done."""

from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.recovery import delete_stale_branches
from factory.domain.identifiers import branch_name
from git_support import CHECKOUT, remote_commit, run_git
from human_clone import HumanClone

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
SECOND_ITEM = "F0001-S0002"
SECOND_BRANCH = branch_name(SECOND_ITEM)
FEATURE = "factory/features/F0001-example"
BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0001-first.md"
IN_PROGRESS_PATH = f"{FEATURE}/in-progress/F0001-S0001-first.md"
SECOND_BACKLOG_PATH = f"{FEATURE}/backlog/F0001-S0002-second.md"
SECOND_DONE_PATH = f"{FEATURE}/done/F0001-S0002-second.md"


def _log_lines(tmp_path: Path) -> list[str]:
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _push_branch(human: HumanClone, checkout: GitCli, branch: str) -> None:
    human.push_file(branch, "marker.txt", "x\n")
    checkout.fetch()


def test_the_branch_of_a_story_back_in_the_backlog_is_deleted(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    _push_branch(human, checkout, BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == [BRANCH]
    assert checkout.resolve(f"origin/{BRANCH}") is None
    assert remote_commit(remote, BRANCH) is None


def test_the_branch_of_a_story_in_progress_stays(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    human.start(BACKLOG_PATH)
    _push_branch(human, checkout, BRANCH)
    before = remote_commit(remote, BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == []
    assert before is not None
    assert remote_commit(remote, BRANCH) == before


@pytest.mark.parametrize("branch", ["main", "scratch", "work-item/not-an-id"])
def test_a_branch_no_work_item_owns_stays(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, human: HumanClone, branch: str
) -> None:
    _push_branch(human, checkout, branch)
    before = remote_commit(remote, branch)

    deleted = delete_stale_branches(boundaries)

    assert deleted == []
    assert before is not None
    assert remote_commit(remote, branch) == before


def test_a_backlog_story_without_a_branch_changes_nothing(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, tmp_path: Path
) -> None:
    main_before = remote_commit(remote, "main")
    branches_before = checkout.remote_branches()

    deleted = delete_stale_branches(boundaries)

    assert deleted == []
    assert _log_lines(tmp_path) == []
    assert remote_commit(remote, "main") == main_before
    checkout.fetch()
    assert checkout.remote_branches() == branches_before


def test_a_story_moved_back_in_the_work_tree_only_keeps_its_branch(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    tmp_path: Path,
) -> None:
    human.start(BACKLOG_PATH)
    _push_branch(human, checkout, BRANCH)
    checkout.reset_to("origin/main")
    directory = tmp_path / CHECKOUT
    (directory / BACKLOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    (directory / IN_PROGRESS_PATH).rename(directory / BACKLOG_PATH)
    before = remote_commit(remote, BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == []
    assert before is not None
    assert remote_commit(remote, BRANCH) == before


@pytest.mark.parametrize("folder", ["backlog", "done"])
def test_an_id_with_a_story_file_in_progress_as_well_keeps_its_branch(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    folder: str,
) -> None:
    human.push_file("main", f"{FEATURE}/{folder}/F0001-S0002-second.md", "# T\n")
    human.push_file("main", f"{FEATURE}/in-progress/F0001-S0002-other.md", "# T\n")
    _push_branch(human, checkout, SECOND_BRANCH)
    before = remote_commit(remote, SECOND_BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == []
    assert before is not None
    assert remote_commit(remote, SECOND_BRANCH) == before


def test_two_stale_branches_are_deleted_in_the_order_of_their_names(
    boundaries: Boundaries, *, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    human.push_file("main", SECOND_BACKLOG_PATH, "# Second story\n")
    human.push_file(SECOND_BRANCH, "marker.txt", "x\n")
    _push_branch(human, checkout, BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == [BRANCH, SECOND_BRANCH]
    assert remote_commit(remote, BRANCH) is None
    assert remote_commit(remote, SECOND_BRANCH) is None


def test_a_deleted_branch_is_named_in_one_log_line(
    boundaries: Boundaries, *, checkout: GitCli, human: HumanClone, tmp_path: Path
) -> None:
    _push_branch(human, checkout, BRANCH)

    delete_stale_branches(boundaries)

    expected = f"deleted stale branch {BRANCH}: its story is back in the backlog"
    assert len([line for line in _log_lines(tmp_path) if line.endswith(expected)]) == 1


def test_a_refused_deletion_is_logged_and_tried_again_on_the_next_call(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    tmp_path: Path,
) -> None:
    _push_branch(human, checkout, BRANCH)
    before = remote_commit(remote, BRANCH)
    run_git(remote, "config", "receive.denyDeletes", "true")

    refused = delete_stale_branches(boundaries)

    assert refused == []
    assert before is not None
    assert remote_commit(remote, BRANCH) == before
    expected = f"could not delete stale branch {BRANCH}: rejected"
    assert any(line.endswith(expected) for line in _log_lines(tmp_path))

    run_git(remote, "config", "--unset", "receive.denyDeletes")

    deleted = delete_stale_branches(boundaries)

    assert deleted == [BRANCH]
    assert remote_commit(remote, BRANCH) is None


def test_the_cleanup_leaves_the_pull_request_the_hosting_service_and_the_checkout(
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    human: HumanClone,
    hosting: FakeHostingService,
) -> None:
    _push_branch(human, checkout, BRANCH)
    number = hosting.create_pull_request(BRANCH, f"{WORK_ITEM}: first", "body", draft=True).number
    hosting.close_by_human(number)
    status = checkout.status()
    main_head = checkout.resolve("refs/heads/main")

    deleted = delete_stale_branches(boundaries)

    assert deleted == [BRANCH]
    assert hosting.get_pull_request(number).state == "closed"
    assert all(hosting.factory_posts(pull.number) == [] for pull in hosting.pull_requests())
    assert checkout.status().branch == status.branch
    assert checkout.resolve("refs/heads/main") == main_head


def test_the_branch_of_a_done_story_is_deleted(
    boundaries: Boundaries,
    *,
    remote: Path,
    checkout: GitCli,
    human: HumanClone,
    tmp_path: Path,
) -> None:
    human.push_file("main", SECOND_DONE_PATH, "# T\n")
    _push_branch(human, checkout, SECOND_BRANCH)

    deleted = delete_stale_branches(boundaries)

    assert deleted == [SECOND_BRANCH]
    assert remote_commit(remote, SECOND_BRANCH) is None
    expected = f"deleted stale branch {SECOND_BRANCH}: its story is done"
    assert len([line for line in _log_lines(tmp_path) if line.endswith(expected)]) == 1
