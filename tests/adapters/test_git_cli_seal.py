"""The git wrapper never reaches a repository above a working copy whose git folder is broken."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from factory.domain.git import GitOptions
from git_support import CHECKOUT, run_git, write_files


@pytest.fixture
def headless(tmp_path: Path) -> Path:
    """Return a working copy whose `.git` is an empty folder at `0o755`."""
    directory = tmp_path / CHECKOUT
    folder = directory / ".git"
    folder.mkdir(parents=True)
    folder.chmod(0o755)
    return directory


@pytest.fixture
def repository_above(tmp_path: Path) -> str:
    """Make the working copy's parent a repository whose `main` holds a commit; return it."""
    run_git(tmp_path, "init", "-q", "--initial-branch=main")
    write_files(tmp_path, {"above.txt": "placed above the checkout\n"})
    run_git(tmp_path, "add", "above.txt")
    run_git(tmp_path, "commit", "-q", "-m", "above")
    return run_git(tmp_path, "rev-parse", "HEAD").strip()


def _head_or_none(git: GitCli) -> str | None:
    try:
        return git.resolve("HEAD")
    except GitError:
        return None


@pytest.mark.parametrize(
    "ceiling",
    [
        pytest.param(None, id="no-entry"),
        pytest.param("parent-of-parent", id="parent-of-parent"),
        pytest.param("", id="empty"),
    ],
)
def test_git_never_reaches_a_repository_above_a_working_copy_whose_git_folder_is_broken(
    tmp_path: Path, headless: Path, repository_above: str, ceiling: str | None
) -> None:
    environment: dict[str, str] = {}
    if ceiling is not None:
        value = str(tmp_path.parent) if ceiling == "parent-of-parent" else ceiling
        environment["GIT_CEILING_DIRECTORIES"] = value
    git = GitCli(headless, GitOptions(environment=environment))

    with pytest.raises(GitError):
        git.status()
    assert _head_or_none(git) != repository_above
