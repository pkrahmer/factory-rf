"""The git wrapper refuses option-like values and runs git in the C locale."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.domain.kill_points import KillPoint, KillPoints
from git_support import CHECKOUT, remote_commit, run_git, write_executable, write_files
from human_clone import HumanClone

BRANCH = "work-item/F0001-S0001"


def _recording_executable(tmp_path: Path) -> tuple[Path, Path]:
    calls = tmp_path / "calls"
    body = (
        f"import sys\nwith open({str(calls)!r}, 'a') as f:\n    f.write(' '.join(sys.argv) + '\\n')"
    )
    return write_executable(tmp_path, body), calls


def _remote_refs(remote: Path) -> str:
    return run_git(remote, "for-each-ref", "--format=%(objectname) %(refname)")


def _branch_and_head(directory: Path) -> tuple[str, str]:
    branch = run_git(directory, "rev-parse", "--abbrev-ref", "HEAD").strip()
    return branch, run_git(directory, "rev-parse", "HEAD").strip()


def test_push_of_an_option_like_branch_is_refused_before_anything_runs(
    tmp_path: Path, remote: Path, checkout: GitCli, human: HumanClone, kill_points: KillPoints
) -> None:
    human.push_file("main", "human.txt", "human\n")
    human_tip = remote_commit(remote, "main")
    write_files(tmp_path / CHECKOUT, {"factory.txt": "factory\n"})
    checkout.commit("diverged")

    with pytest.raises(ValueError):
        checkout.push("--force")

    assert remote_commit(remote, "main") == human_tip
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 0


def test_delete_remote_branch_of_an_option_like_name_is_refused(
    remote: Path, checkout: GitCli
) -> None:
    before = _remote_refs(remote)

    with pytest.raises(ValueError):
        checkout.delete_remote_branch("--all")

    assert _remote_refs(remote) == before


def test_clone_of_an_option_like_url_is_refused(tmp_path: Path) -> None:
    directory = tmp_path / "parent" / "clone"

    with pytest.raises(ValueError):
        GitCli(directory).clone("--upload-pack=x")

    assert not directory.exists()


@pytest.mark.parametrize(("branch", "start_point"), [("--detach", None), ("x", "--orphan")])
def test_checkout_of_an_option_like_branch_or_start_point_is_refused(
    tmp_path: Path, checkout: GitCli, branch: str, start_point: str | None
) -> None:
    before = _branch_and_head(tmp_path / CHECKOUT)

    with pytest.raises(ValueError):
        checkout.checkout(branch, start_point=start_point)

    assert _branch_and_head(tmp_path / CHECKOUT) == before


def test_delete_branch_of_an_option_like_name_is_refused(checkout: GitCli) -> None:
    with pytest.raises(ValueError):
        checkout.delete_branch("-D")


@pytest.mark.parametrize(
    "operation",
    [
        lambda cli: cli.resolve("-x"),
        lambda cli: cli.show_file("-x", "README.md"),
        lambda cli: cli.list_files("-x", "factory"),
        lambda cli: cli.is_ancestor("-x", "main"),
        lambda cli: cli.is_ancestor("main", "-x"),
        lambda cli: cli.log("-x"),
        lambda cli: cli.log("main", since="-x"),
        lambda cli: cli.changed_paths("-x"),
        lambda cli: cli.merge("-x"),
        lambda cli: cli.reset_to("-x"),
        lambda cli: cli.revert_paths("-x", ["README.md"]),
    ],
)
def test_option_like_ref_is_refused_without_starting_git(
    tmp_path: Path, operation: Callable[[GitCli], object]
) -> None:
    executable, calls = _recording_executable(tmp_path)
    cli = GitCli(tmp_path, GitOptions(executable=str(executable)))

    with pytest.raises(ValueError):
        operation(cli)

    assert not calls.exists()


def test_push_of_a_new_branch_with_hyphens_in_its_name_is_pushed(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    checkout.checkout(BRANCH, start_point="origin/main")
    write_files(tmp_path / CHECKOUT, {"work.txt": "work\n"})
    commit = checkout.commit("work")

    assert checkout.push(BRANCH) == "pushed"
    assert remote_commit(remote, BRANCH) == commit


@pytest.mark.parametrize(
    ("in_process", "in_options"), [(False, False), (True, False), (False, True), (True, True)]
)
def test_git_runs_in_the_c_locale_whatever_the_environment_says(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, in_process: bool, in_options: bool
) -> None:
    seen = tmp_path / "locale"
    body = (
        f"import os\nwith open({str(seen)!r}, 'w') as f:\n    f.write(os.environ.get('LC_ALL', ''))"
    )
    executable = write_executable(tmp_path, body)
    if in_process:
        monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    else:
        monkeypatch.delenv("LC_ALL", raising=False)
    environment = {"LC_ALL": "de_DE.UTF-8"} if in_options else {}
    cli = GitCli(tmp_path, GitOptions(executable=str(executable), environment=environment))

    cli.fetch()

    assert seen.read_text(encoding="utf-8") == "C"


def test_push_of_a_forcing_refspec_is_refused_before_anything_runs(
    tmp_path: Path, remote: Path, checkout: GitCli, human: HumanClone, kill_points: KillPoints
) -> None:
    human.push_file("main", "human.txt", "human\n")
    human_tip = remote_commit(remote, "main")
    write_files(tmp_path / CHECKOUT, {"factory.txt": "factory\n"})
    checkout.commit("diverged")

    with pytest.raises(ValueError):
        checkout.push("+main")

    assert remote_commit(remote, "main") == human_tip
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 0


def test_push_of_a_deleting_refspec_is_refused_and_the_remote_branch_stays(
    remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    human.push_file("keep", "keep.txt", "keep\n")
    keep_tip = remote_commit(remote, "keep")

    with pytest.raises(ValueError):
        checkout.push(":keep")

    assert keep_tip is not None
    assert remote_commit(remote, "keep") == keep_tip


def test_push_of_a_refspec_naming_another_ref_is_refused_and_creates_nothing(
    remote: Path, checkout: GitCli
) -> None:
    with pytest.raises(ValueError):
        checkout.push("HEAD:refs/heads/other")

    assert remote_commit(remote, "other") is None


@pytest.mark.parametrize("branch", ["+main", "main:x"])
def test_delete_remote_branch_of_a_refspec_is_refused(
    remote: Path, checkout: GitCli, branch: str
) -> None:
    before = _remote_refs(remote)

    with pytest.raises(ValueError):
        checkout.delete_remote_branch(branch)

    assert _remote_refs(remote) == before


def test_push_of_a_new_branch_with_a_plus_inside_its_name_is_pushed(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    checkout.checkout("a+b", start_point="origin/main")
    write_files(tmp_path / CHECKOUT, {"work.txt": "work\n"})
    commit = checkout.commit("work")

    assert checkout.push("a+b") == "pushed"
    assert remote_commit(remote, "a+b") == commit


@pytest.mark.parametrize("branch", ["+x", "x:y"])
def test_delete_branch_of_a_refspec_like_name_is_not_refused_and_changes_nothing(
    tmp_path: Path, checkout: GitCli, branch: str
) -> None:
    before = run_git(tmp_path / CHECKOUT, "for-each-ref", "--format=%(objectname) %(refname)")

    checkout.delete_branch(branch)

    assert (
        run_git(tmp_path / CHECKOUT, "for-each-ref", "--format=%(objectname) %(refname)") == before
    )


def test_push_of_a_negative_refspec_is_refused_before_anything_runs(
    remote: Path, checkout: GitCli, kill_points: KillPoints
) -> None:
    main_tip = remote_commit(remote, "main")

    with pytest.raises(ValueError):
        checkout.push("^main")

    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 0
    assert remote_commit(remote, "main") == main_tip


@pytest.mark.parametrize("branch", ["HEAD", "@"])
def test_push_of_the_checked_out_branch_by_alias_is_refused_and_creates_nothing(
    remote: Path, checkout: GitCli, branch: str
) -> None:
    before = _remote_refs(remote)

    with pytest.raises(ValueError):
        checkout.push(branch)

    assert _remote_refs(remote) == before
