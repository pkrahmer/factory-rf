"""The checkout preparer clones a missing checkout and keeps any checkout that holds a `.git`."""

import ast
import inspect
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.scheduler import CheckoutPreparer
from factory.domain.git import GitOptions
from factory.domain.settings import InstanceSettings
from git_support import TEST_IDENTITY, clone
from settings_support import AGENT_HOME
from source_search import SRC, modules

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


def test_an_existing_checkout_is_kept_with_its_files_and_modes(
    remote: Path, directory: Path, git: GitCli
) -> None:
    added = _existing(remote, directory)
    (directory / ".git").chmod(0o755)
    config = directory / ".git" / "config"
    config.chmod(0o664)

    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert added.read_text(encoding="utf-8") == "put there by the test\n"
    assert config.stat().st_mode & 0o777 == 0o664


def _missing(remote: Path, directory: Path, git: GitCli) -> None:
    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert git.resolve("origin/main") is not None


def _group_writable(remote: Path, directory: Path, git: GitCli) -> None:
    added = _existing(remote, directory)
    folder = directory / ".git"
    folder.chmod(0o2775)

    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert folder.stat().st_mode & 0o7777 == 0o2775
    assert added.read_text(encoding="utf-8") == "put there by the test\n"


def _nested(remote: Path, directory: Path, git: GitCli) -> None:
    _existing(remote, directory)
    nested = directory / "sub" / ".git"
    nested.mkdir(parents=True)
    head = nested / "HEAD"
    head.write_text("ref: refs/heads/main\n", encoding="utf-8")

    CheckoutPreparer(git, _settings(remote, directory)).prepare()

    assert head.read_text(encoding="utf-8") == "ref: refs/heads/main\n"


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


def _takes_no_log(_remote: Path, _directory: Path, _git: GitCli) -> None:
    assert "log" not in inspect.signature(CheckoutPreparer.__init__).parameters


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(_takes_no_log, id="no-log-parameter"),
        pytest.param(_missing, id="missing-is-cloned"),
        pytest.param(_group_writable, id="existing-is-kept"),
    ],
)
def test_the_preparer_takes_only_the_git_and_the_settings(
    remote: Path, directory: Path, git: GitCli, case: Callable[[Path, Path, GitCli], None]
) -> None:
    case(remote, directory, git)


def _preparer_class() -> ast.ClassDef:
    tree = modules()["factory.application.scheduler"]
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "CheckoutPreparer"
    )


def _assigns_no_log_attribute() -> None:
    assigned = {
        node.attr
        for node in ast.walk(_preparer_class())
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store)
    }

    assert "_log" not in assigned


def _docstrings_name_no_log() -> None:
    preparer = _preparer_class()
    docstrings = [ast.get_docstring(preparer) or ""] + [
        ast.get_docstring(node) or ""
        for node in preparer.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    ]

    assert all("log" not in docstring.lower() for docstring in docstrings)


def _wiring_passes_no_log() -> None:
    tree = ast.parse((SRC / "entry" / "run.py").read_text(encoding="utf-8"))
    keywords = [
        keyword.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "CheckoutPreparer"
        for keyword in node.keywords
    ]

    assert "log" not in keywords


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(_assigns_no_log_attribute, id="no-log-attribute"),
        pytest.param(_docstrings_name_no_log, id="docstrings"),
        pytest.param(_wiring_passes_no_log, id="run-instance"),
    ],
)
def test_the_preparer_s_source_holds_no_log(case: Callable[[], None]) -> None:
    case()
