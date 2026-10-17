"""The git wrapper seals its repository folder, checks the seal and discards the working copy."""

import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError, RepositoryUnsealed
from factory.domain.git import GitOptions
from git_support import CHECKOUT, clone, run_git, write_files

UNSEALED = "seal failed (no exit status): "
OTHER_USER = "belongs to the user"
WRITABLE = "is writable by its group or by others"

Arrange = Callable[[Path, pytest.MonkeyPatch], None]


@pytest.fixture
def directory(tmp_path: Path, remote: Path) -> Path:
    """Return the working copy, a clone of `remote` at `tmp_path / CHECKOUT`."""
    return clone(remote, tmp_path / CHECKOUT)


@pytest.fixture
def other_clone(tmp_path: Path, remote: Path) -> Path:
    """Return a second clone of `remote`, at `tmp_path / "other"`."""
    return clone(remote, tmp_path / "other")


def _modes(root: Path) -> dict[Path, int]:
    """Return the mode of every entry under `root`, symbolic links not followed."""
    modes: dict[Path, int] = {}
    for parent, folders, files in os.walk(root):
        for name in [*folders, *files]:
            path = Path(parent) / name
            modes[path] = path.lstat().st_mode
    return modes


def _git_folder(tmp_path: Path) -> Path:
    return tmp_path / CHECKOUT / ".git"


def _another_user(monkeypatch: pytest.MonkeyPatch) -> None:
    effective = os.geteuid()
    monkeypatch.setattr(os, "geteuid", lambda: effective + 1)


def _missing(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.rmtree(_git_folder(tmp_path))


def _link_to_other_clone(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.rmtree(_git_folder(tmp_path))
    _git_folder(tmp_path).symlink_to(tmp_path / "other" / ".git", target_is_directory=True)


def _a_file(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
    shutil.rmtree(_git_folder(tmp_path))
    _git_folder(tmp_path).write_text("gitdir: elsewhere\n", encoding="utf-8")


def _another_users_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    writable = _git_folder(tmp_path) / "agent-file"
    writable.write_text("agent\n", encoding="utf-8")
    writable.chmod(0o666)
    _another_users_closed_folder(tmp_path, monkeypatch)


def _another_users_closed_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git_folder(tmp_path).chmod(0o755)
    _another_user(monkeypatch)


def _folder_mode(mode: int) -> Arrange:
    def arrange(tmp_path: Path, _monkeypatch: pytest.MonkeyPatch) -> None:
        _git_folder(tmp_path).chmod(mode)

    return arrange


def _entry(name: str, mode: int) -> Callable[[Path], Path]:
    def arrange(directory: Path) -> Path:
        path = directory / ".git" / name
        if name.endswith("folder"):
            path.mkdir()
        elif name.endswith("file"):
            path.write_text("entry\n", encoding="utf-8")
        path.chmod(mode)
        return path

    return arrange


def _link_to_an_open_file_outside(directory: Path) -> Path:
    outside = directory.parent / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    outside.chmod(0o666)
    (directory / ".git" / "agent-link").symlink_to(outside)
    return outside


@pytest.mark.parametrize(
    ("arrange", "expected"),
    [
        pytest.param(_entry(".", 0o2775), 0o2755, id="git-folder"),
        pytest.param(_entry("agent-folder", 0o777), 0o755, id="folder-inside"),
        pytest.param(_entry("agent-file", 0o666), 0o644, id="file-inside"),
        pytest.param(_entry("closed-file", 0o640), 0o640, id="closed-file-inside"),
        pytest.param(_link_to_an_open_file_outside, 0o666, id="link-inside"),
    ],
)
def test_seal_takes_the_group_and_others_write_bits_and_keeps_every_other_bit(
    directory: Path, arrange: Callable[[Path], Path], expected: int
) -> None:
    path = arrange(directory)

    GitCli(directory).seal()

    assert path.stat().st_mode & 0o7777 == expected
    assert [link.name for link in (directory / ".git").iterdir() if link.is_symlink()] == (
        ["agent-link"] if path.name == "outside.txt" else []
    )


@pytest.mark.usefixtures("other_clone")
@pytest.mark.parametrize(
    ("arrange", "detail"),
    [
        pytest.param(_missing, "does not exist", id="missing"),
        pytest.param(_link_to_other_clone, "is a symbolic link", id="symbolic-link"),
        pytest.param(_a_file, "is not a directory", id="file"),
        pytest.param(_another_users_folder, OTHER_USER, id="another-user"),
    ],
)
def test_seal_refuses_a_git_folder_that_is_not_the_factorys_and_changes_nothing(
    tmp_path: Path,
    directory: Path,
    monkeypatch: pytest.MonkeyPatch,
    arrange: Arrange,
    detail: str,
) -> None:
    arrange(tmp_path, monkeypatch)
    before = _modes(tmp_path)

    with pytest.raises(RepositoryUnsealed, match=re.escape(f"{directory / '.git'} {detail}")):
        GitCli(directory).seal()

    assert _modes(tmp_path) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root lists folders without the read bit")
def test_seal_refuses_a_folder_inside_that_it_cannot_list_and_names_it(directory: Path) -> None:
    hidden = directory / ".git" / "agent-folder"
    hidden.mkdir()
    (hidden / "inside.txt").write_text("inside\n", encoding="utf-8")
    hidden.chmod(0o300)
    try:
        with pytest.raises(RepositoryUnsealed) as raised:
            GitCli(directory).seal()
    finally:
        hidden.chmod(0o755)

    assert str(hidden) in str(raised.value)


@pytest.mark.usefixtures("other_clone")
@pytest.mark.parametrize(
    ("arrange", "detail"),
    [
        pytest.param(_folder_mode(0o2750), None, id="2750"),
        pytest.param(_folder_mode(0o750), None, id="750"),
        pytest.param(_folder_mode(0o2770), WRITABLE, id="2770"),
        pytest.param(_folder_mode(0o757), WRITABLE, id="757"),
        pytest.param(_link_to_other_clone, "is a symbolic link", id="symbolic-link"),
        pytest.param(_a_file, "is not a directory", id="file"),
        pytest.param(_missing, "does not exist", id="missing"),
        pytest.param(_another_users_closed_folder, OTHER_USER, id="another-user"),
    ],
)
def test_check_seal_passes_only_a_closed_git_folder_of_the_factorys_user_and_changes_nothing(
    tmp_path: Path,
    directory: Path,
    monkeypatch: pytest.MonkeyPatch,
    arrange: Arrange,
    detail: str | None,
) -> None:
    arrange(tmp_path, monkeypatch)
    before = _modes(tmp_path)

    if detail is None:
        GitCli(directory).check_seal()
    else:
        with pytest.raises(RepositoryUnsealed, match=re.escape(f"{directory / '.git'} {detail}")):
            GitCli(directory).check_seal()

    assert _modes(tmp_path) == before


def test_check_seal_names_a_group_writable_folder_in_its_message(directory: Path) -> None:
    folder = directory / ".git"
    folder.chmod(0o2770)

    with pytest.raises(RepositoryUnsealed) as raised:
        GitCli(directory).check_seal()

    assert str(raised.value) == f"{UNSEALED}{folder} {WRITABLE}"


@pytest.fixture
def headless(tmp_path: Path) -> Path:
    """Return a working copy whose `.git` is an empty folder at `0o755`."""
    directory = tmp_path / CHECKOUT
    folder = directory / ".git"
    folder.mkdir(parents=True)
    folder.chmod(0o755)
    return directory


@pytest.mark.parametrize("operation", ["seal", "check_seal"])
def test_a_git_folder_without_head_is_refused_and_changes_nothing(
    tmp_path: Path, headless: Path, operation: str
) -> None:
    before = _modes(tmp_path)

    with pytest.raises(
        RepositoryUnsealed, match=re.escape(f"{headless / '.git'} holds no HEAD file")
    ):
        getattr(GitCli(headless), operation)()

    assert _modes(tmp_path) == before


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


@pytest.mark.parametrize("cloned", [pytest.param(True, id="clone"), pytest.param(False, id="none")])
def test_discard_removes_the_working_copy_and_a_missing_one_is_no_error(
    tmp_path: Path, remote: Path, cloned: bool
) -> None:
    directory = tmp_path / CHECKOUT
    if cloned:
        clone(remote, directory)

    GitCli(directory).discard()

    assert not directory.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root removes files in unwritable directories")
def test_discard_that_cannot_remove_a_file_is_a_git_error(directory: Path) -> None:
    locked = directory / "locked"
    locked.mkdir()
    (locked / "file.txt").write_text("cannot be removed\n", encoding="utf-8")
    locked.chmod(0o555)
    try:
        with pytest.raises(GitError, match="discard"):
            GitCli(directory).discard()
    finally:
        locked.chmod(0o755)
