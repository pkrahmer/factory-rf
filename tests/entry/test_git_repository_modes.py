"""The factory's git writes `.git` closed to the group and leaves the work tree to it."""

import os
import stat
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.domain.paths import PIPELINE_DEFINITION_FILE
from factory.entry.wiring import git_environment
from git_support import CHECKOUT, TEST_IDENTITY

pytestmark = pytest.mark.usefixtures("group_umask")


@pytest.fixture
def cloned(tmp_path: Path, remote: Path, group_umask: None) -> GitCli:
    """Return the factory's git on a clone of `remote` made under the umask `0002`."""
    del group_umask  # requested for its umask alone, so that it is set before the clone
    git = GitCli(
        tmp_path / CHECKOUT, GitOptions(identity=TEST_IDENTITY, environment=git_environment())
    )
    git.clone(str(remote))
    return git


def _entries(folder: Path) -> list[Path]:
    """Return `folder` and everything under it, symbolic links left out."""
    found = [folder]
    for parent, folders, files in os.walk(folder):
        found.extend(Path(parent) / name for name in [*folders, *files])
    return [path for path in found if not path.is_symlink()]


@pytest.mark.usefixtures("cloned")
@pytest.mark.parametrize(
    ("name", "bits", "expected"),
    [
        pytest.param(".git", 0o070, 0o050, id="git-folder-group-reads"),
        pytest.param(".git/config", 0o7777, 0o640, id="git-config"),
        pytest.param(PIPELINE_DEFINITION_FILE, 0o020, 0o020, id="work-tree-file"),
        pytest.param(
            str(Path(PIPELINE_DEFINITION_FILE).parent), 0o020, 0o020, id="work-tree-folder"
        ),
    ],
)
def test_a_clone_closes_the_git_folder_to_the_group_and_leaves_the_work_tree_writable(
    tmp_path: Path, name: str, bits: int, expected: int
) -> None:
    mode = stat.S_IMODE((tmp_path / CHECKOUT / name).lstat().st_mode)

    assert mode & bits == expected


def test_after_git_work_and_a_seal_nothing_in_the_git_folder_is_writable_but_by_its_owner(
    tmp_path: Path, cloned: GitCli
) -> None:
    cloned.fetch()
    cloned.checkout("work", start_point="origin/main")
    (tmp_path / CHECKOUT / "new.txt").write_text("new\n", encoding="utf-8")
    cloned.commit("add a file")
    cloned.reset_to("HEAD")

    cloned.seal()

    entries = _entries(tmp_path / CHECKOUT / ".git")
    assert [path for path in entries if path.lstat().st_mode & 0o022] == []
    folders = [path for path in entries if path.is_dir()]
    assert [path for path in folders if path.stat().st_mode & 0o050 != 0o050] == []
    assert [path for path in entries if path.is_file() and not path.stat().st_mode & 0o040] == []
