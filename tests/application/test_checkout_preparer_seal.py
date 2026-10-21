"""The checkout preparer seals the checkout's git folder and clones again one it cannot trust."""

import os
import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.machine import FactoryLog
from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter
from factory.application.stops import StopService
from factory.domain.git import GitOptions
from factory.domain.settings import InstanceSettings
from git_support import TEST_IDENTITY, clone

UNSEALED = "seal failed (no exit status): "
KEPT = "added-by-test.txt"


class RecordingLog(FactoryLog):
    """Keeps the lines written to it."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)


@pytest.fixture
def directory(tmp_path: Path) -> Path:
    """Return the instance's checkout folder, `tmp_path / "instance"`; nothing is created."""
    return tmp_path / "instance"


@pytest.fixture
def git(directory: Path) -> GitCli:
    """Return the factory's git on the instance's checkout."""
    return GitCli(directory, GitOptions(identity=TEST_IDENTITY))


def _settings(remote: Path, directory: Path) -> InstanceSettings:
    return InstanceSettings(repository_url=str(remote), instance="one", checkout=directory)


def _existing(remote: Path, directory: Path) -> Path:
    """Clone `remote` into `directory`, put a file in its work tree; return that file."""
    clone(remote, directory)
    added = directory / KEPT
    added.write_text("put there by the test\n", encoding="utf-8")
    return added


def _closed(folder: Path) -> bool:
    return folder.is_dir() and not folder.is_symlink() and not folder.stat().st_mode & 0o022


@pytest.mark.usefixtures("group_umask")
def test_a_missing_checkout_is_cloned_and_sealed(
    remote: Path, directory: Path, git: GitCli
) -> None:
    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert _closed(directory / ".git")
    assert git.resolve("origin/main") is not None


def test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line(
    remote: Path, directory: Path, git: GitCli
) -> None:
    added = _existing(remote, directory)
    (directory / ".git").chmod(0o755)
    config = directory / ".git" / "config"
    config.chmod(0o664)
    log = RecordingLog()

    CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert added.read_text(encoding="utf-8") == "put there by the test\n"
    assert config.stat().st_mode & 0o777 == 0o644
    assert log.lines == []


def _group_writable(_remote: Path, folder: Path) -> str:
    folder.chmod(0o2775)
    return f"{folder} is writable by its group or by others"


def _link_elsewhere(remote: Path, folder: Path) -> str:
    elsewhere = clone(remote, folder.parent.parent / "elsewhere")
    shutil.rmtree(folder)
    folder.symlink_to(elsewhere / ".git", target_is_directory=True)
    return f"{folder} is a symbolic link"


@pytest.mark.parametrize(
    ("arrange", "logged"),
    [
        pytest.param(_group_writable, True, id="group-writable"),
        pytest.param(_link_elsewhere, True, id="symbolic-link"),
        pytest.param(_group_writable, False, id="group-writable-without-log"),
    ],
)
def test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again(
    remote: Path,
    directory: Path,
    git: GitCli,
    arrange: Callable[[Path, Path], str],
    logged: bool,
) -> None:
    added = _existing(remote, directory)
    detail = arrange(remote, directory / ".git")
    log = RecordingLog()
    settings = _settings(remote, directory)
    preparer = (
        CheckoutPreparer(git, settings, log=log) if logged else CheckoutPreparer(git, settings)
    )

    preparer.prepare()

    assert not added.exists()
    assert git.resolve("origin/main") is not None
    assert _closed(directory / ".git")
    assert log.lines == ([f"cloning the checkout again: {UNSEALED}{detail}"] if logged else [])


@pytest.mark.skipif(os.geteuid() == 0, reason="root removes files in unwritable directories")
def test_a_checkout_that_cannot_be_discarded_is_the_repository_unavailable_stop(
    boundaries: Boundaries, remote: Path, directory: Path, git: GitCli
) -> None:
    _existing(remote, directory)
    (directory / ".git").chmod(0o2775)
    locked = directory / "locked"
    locked.mkdir()
    (locked / "file.txt").write_text("cannot be removed\n", encoding="utf-8")
    locked.chmod(0o555)
    instance = replace(boundaries, git=git, log=RecordingLog(), checkout=directory)
    waiter = RepositoryWaiter(
        CheckoutPreparer(git, _settings(remote, directory), log=instance.log),
        instance,
        StopService(instance),
    )
    try:
        prepared = waiter.prepare()
    finally:
        locked.chmod(0o755)

    assert prepared is False
    stops = [
        stop for stop in instance.health.read().stops if stop.reason == "repository_unavailable"
    ]
    assert len(stops) == 1
    assert stops[0].detail.startswith("cannot prepare the checkout: discard failed")
