"""The work tree's id: the tree a commit would record now, less the paths left out."""

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from factory.domain.git import GitOptions
from git_support import CHECKOUT, TEST_IDENTITY, run_git, write_files

IdPair = tuple[str, str]


def _head_tree(directory: Path) -> str:
    return run_git(directory, "rev-parse", "HEAD^{tree}").strip()


def _clean(git: GitCli, directory: Path) -> IdPair:
    return git.work_tree_id(), _head_tree(directory)


def _changed(git: GitCli, directory: Path) -> IdPair:
    write_files(directory, {"tracked.txt": "one\n", "gone.txt": "gone\n"})
    git.commit("base")
    write_files(directory, {"tracked.txt": "two\n", "notes/new.txt": "new\n"})
    (directory / "gone.txt").unlink()
    expected = git.work_tree_id()
    git.commit("changes")
    return expected, _head_tree(directory)


def _ignored(git: GitCli, directory: Path) -> IdPair:
    write_files(directory, {".gitignore": "*.log\n"})
    without = git.work_tree_id()
    write_files(directory, {"build.log": "noise\n"})
    return git.work_tree_id(), without


def _tracked_ignored(git: GitCli, directory: Path) -> IdPair:
    write_files(directory, {"kept.log": "one\n"})
    git.commit("kept")
    write_files(directory, {".gitignore": "*.log\n"})
    git.commit("ignore")
    write_files(directory, {"kept.log": "two\n"})
    expected = git.work_tree_id()
    git.commit("edit")
    return expected, _head_tree(directory)


def _no_commit(git: GitCli, directory: Path) -> IdPair:
    del git
    fresh = directory.parent / "fresh"
    fresh.mkdir()
    run_git(fresh, "init", "-q", "--initial-branch=main")
    write_files(fresh, {"a.txt": "a\n", "b/c.txt": "c\n"})
    git_fresh = GitCli(fresh, GitOptions(identity=TEST_IDENTITY))
    expected = git_fresh.work_tree_id()
    git_fresh.commit("first")
    return expected, _head_tree(fresh)


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(_clean, id="clean"),
        pytest.param(_changed, id="edited-untracked-deleted"),
        pytest.param(_ignored, id="ignored-file"),
        pytest.param(_tracked_ignored, id="tracked-ignored-file"),
        pytest.param(_no_commit, id="no-commit"),
    ],
)
def test_the_work_tree_id_is_the_tree_a_commit_records(
    tmp_path: Path, checkout: GitCli, row: Callable[[GitCli, Path], IdPair]
) -> None:
    actual, expected = row(checkout, tmp_path / CHECKOUT)

    assert actual == expected


DOCS_TREE = {
    "src/a.py": "a\n",
    "docs/guide.md": "guide\n",
    "docs/sub/deep.md": "deep\n",
    "docsx/a.md": "x\n",
    "docs/:x.md": "colon\n",
    "docs/a*b.md": "star\n",
}
ROOT_TREE = {"a*b.md": "star\n", "aXb.md": "x\n", ":x.md": "colon\n", "x.md": "plain\n"}


def _docs_removed(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    left_out = git.work_tree_id(["docs/*"])
    shutil.rmtree(directory / "docs")
    return left_out, git.work_tree_id(), True


def _deep_edit_left_out(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    before = git.work_tree_id(["docs/*"])
    write_files(directory, {"docs/sub/deep.md": "edited\n"})
    return before, git.work_tree_id(["docs/*"]), True


def _deep_edit_whole(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    before = git.work_tree_id()
    write_files(directory, {"docs/sub/deep.md": "edited\n"})
    return before, git.work_tree_id(), False


def _sibling_edit(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    before = git.work_tree_id(["docs/*"])
    write_files(directory, {"docsx/a.md": "edited\n"})
    return before, git.work_tree_id(["docs/*"]), False


def _other_case(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    del directory
    return git.work_tree_id(["Docs/*"]), git.work_tree_id(), True


def _everything(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    empty = run_git(directory, "hash-object", "-t", "tree", "/dev/null").strip()
    return git.work_tree_id(["*"]), empty, True


def _literal_names(git: GitCli, directory: Path) -> tuple[str, str, bool]:
    write_files(directory, ROOT_TREE)
    left_out = git.work_tree_id(["a[*]b.md", ":x.md"])
    (directory / "a*b.md").unlink()
    (directory / ":x.md").unlink()
    return left_out, git.work_tree_id(), True


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(_docs_removed, id="docs-left-out-is-docs-removed"),
        pytest.param(_deep_edit_left_out, id="deep-edit-left-out-unchanged"),
        pytest.param(_deep_edit_whole, id="deep-edit-whole-changed"),
        pytest.param(_sibling_edit, id="docsx-edit-changed"),
        pytest.param(_other_case, id="case-differs"),
        pytest.param(_everything, id="star-is-empty-tree"),
        pytest.param(_literal_names, id="literal-names"),
    ],
)
def test_the_left_out_paths_are_not_in_the_work_tree_id(
    tmp_path: Path,
    checkout: GitCli,
    row: Callable[[GitCli, Path], tuple[str, str, bool]],
) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, DOCS_TREE)
    checkout.commit("tree")

    first, second, equal = row(checkout, directory)

    assert (first == second) is equal


def _changes_kept(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {"staged.txt": "staged\n", "factory/story-form.md": "unstaged\n"})
    run_git(directory, "add", "staged.txt")
    write_files(directory, {"untracked.txt": "untracked\n"})
    index = directory / ".git" / "index"
    before = (checkout.status(), checkout.resolve("HEAD"), index.read_bytes())

    checkout.work_tree_id(["docs/*"])

    assert (checkout.status(), checkout.resolve("HEAD"), index.read_bytes()) == before


def _not_a_repository(tmp_path: Path, checkout: GitCli) -> None:
    del checkout
    plain = tmp_path / "plain"
    plain.mkdir()
    write_files(plain, {"a.txt": "a\n"})

    with pytest.raises(GitError):
        GitCli(plain, GitOptions(identity=TEST_IDENTITY)).work_tree_id()


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(_changes_kept, id="checkout-unchanged"),
        pytest.param(_not_a_repository, id="not-a-repository"),
    ],
)
def test_the_work_tree_id_changes_nothing_and_leaves_no_temporary_file(
    tmp_path: Path,
    checkout: GitCli,
    monkeypatch: pytest.MonkeyPatch,
    row: Callable[[Path, GitCli], None],
) -> None:
    temporary = tmp_path / "tmp"
    temporary.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temporary))

    row(tmp_path, checkout)

    assert list(temporary.iterdir()) == []
