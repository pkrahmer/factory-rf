"""The git wrapper removes every repository nested below its working copy's root."""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import RepositoryUnsealed
from git_support import CHECKOUT, clone, run_git
from root_support import AS_ROOT

# Folders the tests close; the fixture opens them again so that nothing is left unreadable.
CLOSED = ("closed", "locked")

Arrange = Callable[[Path], None]


@pytest.fixture
def directory(tmp_path: Path, remote: Path) -> Iterator[Path]:
    """Return the working copy, a clone of `remote`; reopen the closed folders afterwards."""
    checkout = clone(remote, tmp_path / CHECKOUT)
    yield checkout
    for name in CLOSED:
        if os.path.lexists(checkout / name):
            (checkout / name).chmod(0o755)


def _init(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    run_git(folder, "init", "-q")


def _snapshot(root: Path) -> list[str]:
    """Every entry under `root`, relative and `/`-separated; symbolic links not followed."""
    entries: list[str] = []
    for parent, folders, files in os.walk(root):
        for name in [*folders, *files]:
            entries.append((Path(parent) / name).relative_to(root).as_posix())
    return sorted(entries)


def _nothing(_checkout: Path) -> None:
    pass


def _repository_with_a_file(checkout: Path) -> None:
    _init(checkout / "notes" / "sub")
    (checkout / "notes" / "sub" / "a.txt").write_text("a\n", encoding="utf-8")


def _gitdir_file(checkout: Path) -> None:
    (checkout / "other").mkdir()
    elsewhere = checkout.parent / "elsewhere"
    (checkout / "other" / ".git").write_text(f"gitdir: {elsewhere}\n", encoding="utf-8")


def _link_outside(checkout: Path) -> None:
    target = checkout.parent / "link-target"
    target.mkdir()
    (target / "file.txt").write_text("outside\n", encoding="utf-8")
    (checkout / "link").mkdir()
    (checkout / "link" / ".git").symlink_to(target, target_is_directory=True)


def _two_levels(checkout: Path) -> None:
    _init(checkout / "a")
    _init(checkout / "a" / "b")


def _lookalikes(checkout: Path) -> None:
    (checkout / ".github").mkdir()
    (checkout / ".github" / "workflow.yml").write_text("on: push\n", encoding="utf-8")
    (checkout / "x.git").write_text("not a repository\n", encoding="utf-8")
    (checkout / "sub.git").mkdir()


def _in_venv(checkout: Path) -> None:
    _init(checkout / ".venv" / "lib" / "x")


def _link_to_a_repository_beside(checkout: Path) -> None:
    _init(checkout.parent / "outside")
    (checkout / "mirror").symlink_to(checkout.parent / "outside", target_is_directory=True)


def _link_to_the_root(checkout: Path) -> None:
    (checkout / "self").symlink_to(checkout, target_is_directory=True)


def _link_to_the_parent(checkout: Path) -> None:
    (checkout / "deep").mkdir()
    (checkout / "deep" / "up").symlink_to(checkout.parent, target_is_directory=True)


def _git_inside_the_roots_git(checkout: Path) -> None:
    (checkout / ".git" / "extra" / ".git").mkdir(parents=True)


def _git_inside_a_found_git(checkout: Path) -> None:
    _init(checkout / "notes")
    (checkout / "notes" / ".git" / "modules" / "m" / ".git").mkdir(parents=True)


def _repository_in_a_dot_folder(checkout: Path) -> None:
    _init(checkout / "a")
    _init(checkout / "a" / ".cache")


def _closed_folder(checkout: Path) -> None:
    _init(checkout / "closed" / "inner")
    (checkout / "closed").chmod(0o000)


@pytest.mark.parametrize(
    ("arrange", "expected"),
    [
        pytest.param(_nothing, [], id="nothing-nested"),
        pytest.param(_repository_with_a_file, ["notes/sub/.git"], id="repository"),
        pytest.param(_gitdir_file, ["other/.git"], id="gitdir-file"),
        pytest.param(_link_outside, ["link/.git"], id="link-outside"),
        pytest.param(_two_levels, ["a/.git", "a/b/.git"], id="two-levels"),
        pytest.param(_lookalikes, [], id="lookalikes"),
        pytest.param(_in_venv, [".venv/lib/x/.git"], id="venv"),
        pytest.param(_link_to_a_repository_beside, [], id="link-to-repository-beside"),
        pytest.param(_link_to_the_root, [], id="link-to-root"),
        pytest.param(_link_to_the_parent, [], id="link-to-parent"),
        pytest.param(_git_inside_the_roots_git, [], id="git-inside-roots-git"),
        pytest.param(_git_inside_a_found_git, ["notes/.git"], id="git-inside-found-git"),
        pytest.param(
            _repository_in_a_dot_folder, ["a/.cache/.git", "a/.git"], id="sorted-dot-folder"
        ),
        pytest.param(_closed_folder, [], id="closed-folder", marks=AS_ROOT),
    ],
)
def test_remove_nested_repositories_removes_and_reports_each_nested_git_entry(
    tmp_path: Path, directory: Path, arrange: Arrange, expected: list[str]
) -> None:
    head = run_git(directory, "rev-parse", "HEAD").strip()
    arrange(directory)
    before = _snapshot(tmp_path)
    gone = [f"{CHECKOUT}/{path}" for path in expected]

    removed = GitCli(directory).remove_nested_repositories()

    assert removed == expected
    assert _snapshot(tmp_path) == [
        entry
        for entry in before
        if not any(entry == path or entry.startswith(f"{path}/") for path in gone)
    ]
    assert (directory / ".git").is_dir()
    assert GitCli(directory).resolve("HEAD") == head


@AS_ROOT
def test_a_nested_repository_that_cannot_be_removed_raises_repository_unsealed(
    directory: Path,
) -> None:
    _init(directory / "locked")
    (directory / "locked").chmod(0o555)

    with pytest.raises(RepositoryUnsealed) as raised:
        GitCli(directory).remove_nested_repositories()

    assert str(directory / "locked" / ".git") in str(raised.value)
