"""The checkout preparer clones a missing checkout and keeps any checkout that holds a `.git`."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.scheduler import CheckoutPreparer
from factory.domain.git import GitOptions
from factory.domain.settings import InstanceSettings
from git_support import TEST_IDENTITY, clone
from recording_log import RecordingLog
from settings_support import AGENT_HOME

KEPT = "added-by-test.txt"
PREPARE_DOCSTRING = "Clone when the checkout holds no `.git`; keep any checkout that does."


@pytest.fixture
def directory(tmp_path: Path) -> Path:
    """Return the instance's checkout folder, `tmp_path / "instance"`; nothing is created."""
    return tmp_path / "instance"


@pytest.fixture
def git(directory: Path) -> GitCli:
    """Return the factory's git on the instance's checkout."""
    return GitCli(directory, GitOptions(identity=TEST_IDENTITY))


def _settings(remote: Path, directory: Path) -> InstanceSettings:
    return InstanceSettings(
        repository_url=str(remote), instance="one", agent_home=AGENT_HOME, checkout=directory
    )


def _existing(remote: Path, directory: Path) -> Path:
    """Clone `remote` into `directory`, put a file in its work tree; return that file."""
    clone(remote, directory)
    added = directory / KEPT
    added.write_text("put there by the test\n", encoding="utf-8")
    return added


def test_a_missing_checkout_is_cloned(remote: Path, directory: Path, git: GitCli) -> None:
    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert git.resolve("origin/main") is not None


def test_an_existing_checkout_is_kept_without_a_log_line(
    remote: Path, directory: Path, git: GitCli
) -> None:
    added = _existing(remote, directory)
    (directory / ".git").chmod(0o755)
    config = directory / ".git" / "config"
    config.chmod(0o664)
    log = RecordingLog()

    CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert added.read_text(encoding="utf-8") == "put there by the test\n"
    assert config.stat().st_mode & 0o777 == 0o664
    assert log.lines == []


def _missing(remote: Path, directory: Path, git: GitCli) -> None:
    log = RecordingLog()

    CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert git.resolve("origin/main") is not None
    assert log.lines == []


def _group_writable(remote: Path, directory: Path, git: GitCli) -> None:
    added = _existing(remote, directory)
    folder = directory / ".git"
    folder.chmod(0o2775)
    log = RecordingLog()

    CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert folder.stat().st_mode & 0o7777 == 0o2775
    assert added.read_text(encoding="utf-8") == "put there by the test\n"
    assert log.lines == []


def _nested(remote: Path, directory: Path, git: GitCli) -> None:
    _existing(remote, directory)
    nested = directory / "sub" / ".git"
    nested.mkdir(parents=True)
    head = nested / "HEAD"
    head.write_text("ref: refs/heads/main\n", encoding="utf-8")
    log = RecordingLog()

    CheckoutPreparer(git, _settings(remote, directory), log=log).prepare()

    assert head.read_text(encoding="utf-8") == "ref: refs/heads/main\n"
    assert log.lines == []


def _docstring(_remote: Path, _directory: Path, _git: GitCli) -> None:
    assert CheckoutPreparer.prepare.__doc__ == PREPARE_DOCSTRING


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(_missing, id="missing-is-cloned"),
        pytest.param(_group_writable, id="group-writable-git-is-kept"),
        pytest.param(_nested, id="nested-repository-is-left"),
        pytest.param(_docstring, id="docstring"),
    ],
)
def test_the_preparer_clones_only_a_missing_checkout_and_checks_none(
    remote: Path, directory: Path, git: GitCli, case: Callable[[Path, Path, GitCli], None]
) -> None:
    case(remote, directory, git)
