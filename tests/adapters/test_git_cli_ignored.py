"""The git wrapper's removal of every untracked path the ignore rules match."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from git_support import CHECKOUT, CLEAN_IGNORED, commit_all, head_of, run_git, write_files
from root_support import AS_ROOT

GITIGNORE = ".venv/\n__pycache__/\n*.pyc\n.mypy_cache/\nmutants/\n"
MODULE = "x = 1\n"
STANDIN = "standin\n"
TARGET = "outside target\n"

Setup = Callable[[Path, Path], None]


@pytest.fixture
def directory(tmp_path: Path, checkout: GitCli) -> Path:
    """The checkout with a commit holding the `.gitignore` and `src/mod.py`."""
    del checkout
    root = tmp_path / CHECKOUT
    write_files(root, {".gitignore": GITIGNORE, "src/mod.py": MODULE})
    commit_all(root, "ignore rules")
    return root


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    """A folder outside the repository holding the file `target.txt`."""
    folder = tmp_path / "outside"
    write_files(folder, {"target.txt": TARGET})
    return folder


def _status(directory: Path) -> str:
    return run_git(directory, "status", "--porcelain")


def _files(directory: Path) -> list[str]:
    return sorted(
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.relative_to(directory).parts[0] != ".git"
    )


def _writes(files: dict[str, str]) -> Setup:
    def setup(directory: Path, outside: Path) -> None:
        del outside
        write_files(directory, files)

    return setup


def _excluded(directory: Path, outside: Path) -> None:
    del outside
    (directory / ".git" / "info" / "exclude").write_text("scratch.log\n", encoding="utf-8")
    write_files(directory, {"scratch.log": STANDIN})


def _nested_repository(directory: Path, outside: Path) -> None:
    del outside
    nested = directory / ".venv" / "src" / "dep"
    write_files(nested, {"setup.py": STANDIN})
    run_git(nested, "init", "-q")


def _file_link(directory: Path, outside: Path) -> None:
    (directory / "src" / "stray.pyc").symlink_to(outside / "target.txt")


def _folder_link(directory: Path, outside: Path) -> None:
    (directory / ".mypy_cache").symlink_to(outside, target_is_directory=True)


@pytest.mark.parametrize(
    ("setup", "gone"),
    [
        pytest.param(
            _writes({".venv/lib/python3.12/site-packages/standin.pth": STANDIN}),
            ".venv",
            id="venv",
        ),
        pytest.param(
            _writes({"src/pkg/__pycache__/mod.cpython-312.pyc": STANDIN}),
            "src/pkg/__pycache__",
            id="pycache-folder",
        ),
        pytest.param(_writes({"src/stray.pyc": STANDIN}), "src/stray.pyc", id="pattern"),
        pytest.param(
            _writes({".mypy_cache/3.12/standin.json": STANDIN}), ".mypy_cache", id="mypy-cache"
        ),
        pytest.param(_writes({"mutants/src/mod.py": STANDIN}), "mutants", id="mutants"),
        pytest.param(
            _writes({"tests/hidden/.gitignore": "*\n", "tests/hidden/conftest.py": STANDIN}),
            "tests/hidden",
            id="nested-gitignore-hides-itself",
        ),
        pytest.param(
            _writes({"src/.gitignore": "secret.py\n", "src/secret.py": STANDIN}),
            "src/secret.py",
            id="nested-gitignore",
        ),
        pytest.param(_excluded, "scratch.log", id="info-exclude"),
        pytest.param(_nested_repository, ".venv", id="nested-repository"),
        pytest.param(_file_link, "src/stray.pyc", id="link-as-link"),
    ],
)
def test_remove_ignored_removes_every_untracked_path_the_rules_match(
    checkout: GitCli, directory: Path, outside: Path, *, setup: Setup, gone: str
) -> None:
    setup(directory, outside)

    checkout.remove_ignored()

    assert not (directory / gone).is_symlink()
    assert not (directory / gone).exists()
    assert (outside / "target.txt").read_text(encoding="utf-8") == TARGET


@pytest.mark.parametrize(
    ("setup", "kept", "text", "link"),
    [
        pytest.param(
            _writes({"src/mod.py": "x = 2\n"}), "src/mod.py", "x = 2\n", None, id="tracked-edit"
        ),
        pytest.param(_writes({}), ".gitignore", GITIGNORE, None, id="tracked-gitignore"),
        pytest.param(
            _writes({"src/pkg/new.py": "y = 2\n"}), "src/pkg/new.py", "y = 2\n", None, id="new"
        ),
        pytest.param(
            _writes({"src/.gitignore": "secret.py\n"}),
            "src/.gitignore",
            "secret.py\n",
            None,
            id="new-gitignore",
        ),
        pytest.param(
            _folder_link, ".mypy_cache/target.txt", TARGET, ".mypy_cache", id="unmatched-link"
        ),
    ],
)
def test_remove_ignored_keeps_tracked_and_unmatched_paths(
    checkout: GitCli,
    directory: Path,
    outside: Path,
    *,
    setup: Setup,
    kept: str,
    text: str,
    link: str | None,
) -> None:
    setup(directory, outside)
    head = head_of(directory)
    status = _status(directory)

    checkout.remove_ignored()

    assert (directory / kept).read_text(encoding="utf-8") == text
    if link is not None:
        assert (directory / link).is_symlink()
        assert (outside / "target.txt").read_text(encoding="utf-8") == TARGET
    assert _status(directory) == status
    assert head_of(directory) == head


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(0o555, id="unwritable", marks=AS_ROOT),
        pytest.param(0o755, id="writable"),
        pytest.param(None, id="nothing-ignored"),
    ],
)
def test_remove_ignored_raises_git_error_for_a_path_it_cannot_remove(
    checkout: GitCli, directory: Path, mode: int | None
) -> None:
    locked = directory / ".venv" / "locked"
    if mode is not None:
        write_files(locked, {"file.txt": STANDIN})
        locked.chmod(mode)
    files = _files(directory)
    status = _status(directory)

    try:
        if mode == 0o555:
            with pytest.raises(GitError) as raised:
                checkout.remove_ignored()
            assert raised.value.command == CLEAN_IGNORED
            assert raised.value.exit_status == 1
        else:
            checkout.remove_ignored()
    finally:
        if locked.exists():
            locked.chmod(0o755)

    if mode == 0o755:
        assert not locked.exists()
    if mode is None:
        assert _files(directory) == files
        assert _status(directory) == status
