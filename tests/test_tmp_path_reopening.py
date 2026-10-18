"""Reopening a test's tmp_path: the helper on its own, and the autouse fixture in a child pytest."""

import os
import shutil
import stat
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.process import ProcessRequest, run_process
from tmp_path_support import reopen

TESTS = Path(__file__).parent

INNER_TESTS = """\
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def closing(tmp_path: Path) -> Iterator[Path]:
    yield tmp_path
    late = tmp_path / "late"
    late.mkdir()
    late.chmod(0o000)


def test_closes_its_tmp_path(tmp_path: Path) -> None:
    git = tmp_path / "checkout" / ".git"
    (git / "objects").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\\n", encoding="utf-8")
    git.chmod(0o020)
    closed = tmp_path / "closed"
    (closed / "inner").mkdir(parents=True)
    closed.chmod(0o000)


def test_closes_in_a_fixture(closing: Path) -> None:
    assert closing.is_dir()


def test_uses_no_tmp_path() -> None:
    assert True
"""


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def _sealed_git_folder(tree: Path) -> None:
    git = tree / "checkout" / ".git"
    git.mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git / "HEAD").chmod(0o644)
    (tree / "checkout").chmod(0o755)
    git.chmod(0o020)
    tree.chmod(0o755)


def _folder_with_file(folder_mode: int) -> Callable[[Path], None]:
    def arrange(tree: Path) -> None:
        folder = tree / "folder"
        folder.mkdir(parents=True)
        (folder / "file").write_text("text\n", encoding="utf-8")
        (folder / "file").chmod(0o644)
        folder.chmod(folder_mode)
        tree.chmod(0o755)

    return arrange


def _no_write(tree: Path) -> None:
    folder = tree / "folder"
    (folder / "sub").mkdir(parents=True)
    (folder / "file").write_text("text\n", encoding="utf-8")
    (folder / "file").chmod(0o444)
    (folder / "sub").chmod(0o555)
    folder.chmod(0o555)
    tree.chmod(0o755)


def _closed_inside_closed(tree: Path) -> None:
    inner = tree / "outer" / "inner"
    inner.mkdir(parents=True)
    (inner / "file").write_text("text\n", encoding="utf-8")
    (inner / "file").chmod(0o000)
    inner.chmod(0o000)
    (tree / "outer").chmod(0o000)
    tree.chmod(0o755)


def _closed_root(tree: Path) -> None:
    tree.mkdir()
    (tree / "file").write_text("text\n", encoding="utf-8")
    (tree / "file").chmod(0o644)
    tree.chmod(0o000)


def _open_with_setgid(tree: Path) -> None:
    git = tree / ".git"
    git.mkdir(parents=True)
    (git / "config").write_text("[core]\n", encoding="utf-8")
    (git / "config").chmod(0o664)
    git.chmod(0o2775)
    tree.chmod(0o755)


@pytest.mark.parametrize(
    ("arrange", "expected"),
    [
        pytest.param(
            _sealed_git_folder,
            {".": 0o755, "checkout": 0o755, "checkout/.git": 0o720, "checkout/.git/HEAD": 0o644},
            id="sealed-git-folder",
        ),
        pytest.param(
            _folder_with_file(0o600),
            {"folder": 0o700, "folder/file": 0o644, ".": 0o755},
            id="no-search",
        ),
        pytest.param(
            _folder_with_file(0o300),
            {"folder": 0o700, "folder/file": 0o644, ".": 0o755},
            id="no-read",
        ),
        pytest.param(
            _no_write,
            {"folder": 0o755, "folder/file": 0o644, "folder/sub": 0o755, ".": 0o755},
            id="no-write",
        ),
        pytest.param(
            _closed_inside_closed,
            {"outer": 0o700, "outer/inner": 0o700, "outer/inner/file": 0o600, ".": 0o755},
            id="closed-inside-closed",
        ),
        pytest.param(_closed_root, {".": 0o700, "file": 0o644}, id="closed-root"),
        pytest.param(
            _open_with_setgid,
            {".git": 0o2775, ".git/config": 0o664, ".": 0o755},
            id="open-with-setgid",
        ),
    ],
)
def test_reopen_gives_the_owner_back_every_folder_and_entry_and_keeps_every_other_bit(
    tmp_path: Path, arrange: Callable[[Path], None], expected: dict[str, int]
) -> None:
    tree = tmp_path / "tree"
    arrange(tree)

    reopen(tree)

    assert {name: _mode(tree / name) for name in expected} == expected
    shutil.rmtree(tree)
    assert not tree.exists()


def _folder_target(tmp_path: Path) -> tuple[Path, int]:
    target = tmp_path / "outside"
    target.mkdir()
    target.chmod(0o500)
    return target, 0o500


def _file_target(tmp_path: Path) -> tuple[Path, int]:
    target = tmp_path / "outside.txt"
    target.write_text("text\n", encoding="utf-8")
    target.chmod(0o400)
    return target, 0o400


def _missing_target(tmp_path: Path) -> tuple[Path, int | None]:
    return tmp_path / "missing", None


@pytest.mark.parametrize(
    "make_target",
    [
        pytest.param(_folder_target, id="link-to-a-folder"),
        pytest.param(_file_target, id="link-to-a-file"),
        pytest.param(_missing_target, id="dangling"),
    ],
)
def test_reopen_leaves_a_symbolic_link_and_its_target_as_they_are(
    tmp_path: Path, make_target: Callable[[Path], tuple[Path, int | None]]
) -> None:
    target, target_mode = make_target(tmp_path)
    tree = tmp_path / "tree"
    tree.mkdir()
    tree.chmod(0o755)
    link = tree / "link"
    link.symlink_to(target)
    text = os.readlink(link)

    reopen(tree)

    assert link.is_symlink()
    assert os.readlink(link) == text
    if target_mode is None:
        assert not os.path.lexists(target)
    else:
        assert _mode(target) == target_mode


def test_reopen_of_a_missing_root_changes_nothing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    missing = tmp_path / "missing"

    reopen(missing)

    assert not os.path.lexists(missing)
    assert sorted(tmp_path.iterdir()) == before


@pytest.mark.parametrize(
    ("plugin", "expected"),
    [
        pytest.param(["-p", "conftest"], (0o720, 0o700, 0o700), id="with-conftest"),
        pytest.param([], (0o020, 0o000, 0o000), id="without-conftest"),
    ],
)
def test_a_test_that_closes_folders_in_its_tmp_path_leaves_them_open_after_its_teardown(
    tmp_path: Path, plugin: list[str], expected: tuple[int, int, int]
) -> None:
    inner = tmp_path / "inner"
    inner.mkdir()
    ini = "[pytest]\ntmp_path_retention_policy = all\n"
    (inner / "pytest.ini").write_text(ini, encoding="utf-8")
    (inner / "test_inner.py").write_text(INNER_TESTS, encoding="utf-8")
    base = tmp_path / "base"
    env = {name: value for name, value in os.environ.items() if not name.startswith("PYTEST_")}
    env["PYTHONPATH"] = str(TESTS)

    result = run_process(
        ProcessRequest(
            argv=[
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-c",
                str(inner / "pytest.ini"),
                "--rootdir",
                str(inner),
                "--basetemp",
                str(base),
                *plugin,
                str(inner / "test_inner.py"),
            ],
            cwd=inner,
            env=env,
            time_limit=timedelta(seconds=120),
        )
    )

    assert result.exit_status == 0, result.stdout + result.stderr
    assert "3 passed" in result.stdout
    assert not (base / "test_uses_no_tmp_path0").exists()
    left = base / "test_closes_its_tmp_path0"
    late = base / "test_closes_in_a_fixture0" / "late"
    assert (_mode(left / "checkout" / ".git"), _mode(left / "closed"), _mode(late)) == expected
    if plugin:
        shutil.rmtree(base)
        assert not base.exists()
