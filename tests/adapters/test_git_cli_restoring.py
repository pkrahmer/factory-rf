"""The git wrapper's restoring operations: reset, revert of paths and move."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from git_support import CHECKOUT, commit_all, head_of, run_git, write_files


def _status(directory: Path) -> str:
    return run_git(directory, "status", "--porcelain", "--untracked-files=all")


def _tracked(directory: Path) -> list[str]:
    return run_git(directory, "ls-files").splitlines()


def _base(directory: Path) -> str:
    write_files(directory, {"a.txt": "a base\n", "b.txt": "b base\n", "c.txt": "c base\n"})
    return commit_all(directory, "base")


def test_reset_to_discards_tracked_changes_and_moves_the_branch(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    write_files(directory, {"a.txt": "a later\n"})
    commit_all(directory, "later")
    write_files(directory, {"a.txt": "a staged\n", "b.txt": "b unstaged\n"})
    run_git(directory, "add", "a.txt")

    checkout.reset_to(base)

    assert head_of(directory) == base
    assert run_git(directory, "rev-parse", "--abbrev-ref", "HEAD").strip() == "main"
    assert (directory / "a.txt").read_text(encoding="utf-8") == "a base\n"
    assert (directory / "b.txt").read_text(encoding="utf-8") == "b base\n"
    assert _status(directory) == ""


def test_reset_to_removes_untracked_files_and_directories_and_keeps_ignored(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {".gitignore": "kept.log\n"})
    base = commit_all(directory, "ignore")
    write_files(
        directory,
        {"junk.txt": "junk\n", "junkdir/inner/file.txt": "junk\n", "kept.log": "kept\n"},
    )

    checkout.reset_to(base)

    assert not (directory / "junk.txt").exists()
    assert not (directory / "junkdir").exists()
    assert (directory / "kept.log").read_text(encoding="utf-8") == "kept\n"


def test_reset_to_an_unknown_ref_raises_and_changes_nothing(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    write_files(directory, {"a.txt": "a edited\n"})

    with pytest.raises(GitError):
        checkout.reset_to("nope")

    assert head_of(directory) == base
    assert (directory / "a.txt").read_text(encoding="utf-8") == "a edited\n"


def test_revert_paths_restores_edited_and_deleted_files_in_work_tree_and_index(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    write_files(directory, {"a.txt": "a later\n"})
    commit_all(directory, "later")
    write_files(directory, {"a.txt": "a edited\n"})
    run_git(directory, "add", "a.txt")
    (directory / "b.txt").unlink()

    checkout.revert_paths(base, ["a.txt", "b.txt"])

    assert (directory / "a.txt").read_text(encoding="utf-8") == "a base\n"
    assert (directory / "b.txt").read_text(encoding="utf-8") == "b base\n"
    assert run_git(directory, "diff", "--name-only", base, "--", "a.txt", "b.txt") == ""
    assert run_git(directory, "diff", "--cached", "--name-only", base, "--", "a.txt", "b.txt") == ""


def test_revert_paths_deletes_paths_missing_at_the_commit_and_skips_unknown_ones(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    write_files(directory, {"added.txt": "added\n"})
    commit_all(directory, "added")
    write_files(directory, {"staged.txt": "staged\n", "untracked.txt": "untracked\n"})
    run_git(directory, "add", "staged.txt")
    paths = ["added.txt", "staged.txt", "untracked.txt", "nowhere.txt"]

    checkout.revert_paths(base, paths)

    for path in paths:
        assert not (directory / path).exists(), path
        assert path not in _tracked(directory), path


def test_revert_paths_leaves_other_paths_alone(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    write_files(
        directory,
        {"a.txt": "a edited\n", "b.txt": "b staged\n", "c.txt": "c edited\n", "new.txt": "new\n"},
    )
    run_git(directory, "add", "b.txt")
    before = _status(directory)

    checkout.revert_paths(base, ["a.txt"])

    assert (directory / "b.txt").read_text(encoding="utf-8") == "b staged\n"
    assert (directory / "c.txt").read_text(encoding="utf-8") == "c edited\n"
    assert (directory / "new.txt").read_text(encoding="utf-8") == "new\n"
    assert [line for line in _status(directory).splitlines() if "a.txt" not in line] == [
        line for line in before.splitlines() if "a.txt" not in line
    ]


@pytest.mark.parametrize("unsafe", ["../x", "a/../../x", "absolute"])
def test_revert_paths_refuses_unsafe_paths_before_changing_any(
    tmp_path: Path, checkout: GitCli, unsafe: str
) -> None:
    directory = tmp_path / CHECKOUT
    base = _base(directory)
    if unsafe == "absolute":
        unsafe = str(directory / "b.txt")
    write_files(directory, {"a.txt": "a edited\n", "b.txt": "b edited\n"})

    with pytest.raises(ValueError, match=r".+"):
        checkout.revert_paths(base, ["a.txt", unsafe])

    assert (directory / "a.txt").read_text(encoding="utf-8") == "a edited\n"
    assert (directory / "b.txt").read_text(encoding="utf-8") == "b edited\n"


def test_revert_paths_accepts_a_path_in_a_subdirectory(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {"docs/a.txt": "docs base\n"})
    base = commit_all(directory, "docs")
    write_files(directory, {"docs/a.txt": "docs edited\n"})

    checkout.revert_paths(base, ["docs/a.txt"])

    assert (directory / "docs" / "a.txt").read_text(encoding="utf-8") == "docs base\n"


def test_revert_paths_from_an_unknown_commit_raises(tmp_path: Path, checkout: GitCli) -> None:
    _base(tmp_path / CHECKOUT)

    with pytest.raises(GitError):
        checkout.revert_paths("nope", ["a.txt"])


def test_move_creates_folders_and_stages_a_rename(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    _base(directory)

    checkout.move("a.txt", "docs/new/a.txt")

    assert not (directory / "a.txt").exists()
    assert (directory / "docs" / "new" / "a.txt").read_text(encoding="utf-8") == "a base\n"
    assert _status(directory).splitlines() == ["R  a.txt -> docs/new/a.txt"]


@pytest.mark.parametrize(
    ("source", "destination"),
    [("untracked.txt", "moved.txt"), ("a.txt", "b.txt")],
    ids=["untracked-source", "existing-destination"],
)
def test_move_refuses_an_untracked_source_or_an_existing_destination(
    tmp_path: Path, checkout: GitCli, source: str, destination: str
) -> None:
    directory = tmp_path / CHECKOUT
    _base(directory)
    write_files(directory, {"untracked.txt": "untracked\n"})

    with pytest.raises(GitError):
        checkout.move(source, destination)

    assert (directory / "a.txt").read_text(encoding="utf-8") == "a base\n"
    assert (directory / "b.txt").read_text(encoding="utf-8") == "b base\n"


@pytest.mark.parametrize("destination", ["../x.txt", "absolute"])
def test_move_refuses_an_unsafe_destination_before_creating_any_folder(
    tmp_path: Path, checkout: GitCli, destination: str
) -> None:
    directory = tmp_path / CHECKOUT
    _base(directory)
    if destination == "absolute":
        destination = str(tmp_path / "outside" / "x.txt")
    outside_before = sorted(path.name for path in tmp_path.iterdir())

    with pytest.raises(ValueError, match=r".+"):
        checkout.move("a.txt", destination)

    assert sorted(path.name for path in tmp_path.iterdir()) == outside_before
    assert (directory / "a.txt").read_text(encoding="utf-8") == "a base\n"


@pytest.mark.parametrize("source", ["../x.txt", "absolute"])
def test_move_refuses_an_unsafe_source_and_changes_nothing(
    tmp_path: Path, checkout: GitCli, source: str
) -> None:
    directory = tmp_path / CHECKOUT
    _base(directory)
    outside = tmp_path / "outside"
    outside.mkdir()
    write_files(outside, {"x.txt": "outside\n"})
    write_files(tmp_path, {"x.txt": "outside\n"})
    if source == "absolute":
        source = str(outside / "x.txt")
    status_before = _status(directory)
    outside_before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    with pytest.raises(ValueError, match=r".+"):
        checkout.move(source, "b.txt")

    assert _status(directory) == status_before
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == outside_before
    assert (directory / "b.txt").read_text(encoding="utf-8") == "b base\n"
