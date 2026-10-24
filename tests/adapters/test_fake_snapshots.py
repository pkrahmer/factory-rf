"""The fake snapshots: a folder whose base is a copy beside it."""

import os
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.fake_snapshots import FakeSnapshots
from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    folder = tmp_path / "work"
    folder.mkdir()
    (folder / "a.txt").write_text("one\n", encoding="utf-8")
    (folder / "a.txt").chmod(0o644)
    (folder / "gone.txt").write_text("x\n", encoding="utf-8")
    return folder


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path / "base"


@pytest.fixture
def snapshots(folder: Path, base: Path) -> FakeSnapshots:
    return FakeSnapshots(folder, base)


def _change(folder: Path) -> None:
    (folder / "b").mkdir()
    (folder / "b" / "new.txt").write_text("n\n", encoding="utf-8")
    (folder / "a.txt").write_text("two\n", encoding="utf-8")
    (folder / "gone.txt").unlink()
    (folder / "empty").mkdir()


def _tree(folder: Path) -> dict[str, tuple[int, str | bytes]]:
    return {
        path.relative_to(folder).as_posix(): (
            path.lstat().st_mode,
            os.readlink(path) if path.is_symlink() else b"" if path.is_dir() else path.read_bytes(),
        )
        for path in folder.rglob("*")
    }


def test_the_mount_point_is_the_folder_given(snapshots: FakeSnapshots, folder: Path) -> None:
    assert snapshots.mount_point == folder


def test_changed_paths_lists_added_modified_and_deleted_files_by_path(
    snapshots: FakeSnapshots, folder: Path
) -> None:
    snapshots.advance()
    assert snapshots.changed_paths() == []

    _change(folder)

    assert snapshots.changed_paths() == [
        ChangedPath(path="a.txt", change="modified"),
        ChangedPath(path="b/new.txt", change="added"),
        ChangedPath(path="gone.txt", change="deleted"),
    ]


def _chmod(folder: Path) -> None:
    (folder / "a.txt").chmod(0o755)


def _retarget(folder: Path) -> None:
    (folder / "old-link").unlink()
    (folder / "old-link").symlink_to("gone.txt")


def _new_link(folder: Path) -> None:
    (folder / "new-link").symlink_to("a.txt")


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        pytest.param(_chmod, ChangedPath(path="a.txt", change="modified"), id="mode"),
        pytest.param(_retarget, ChangedPath(path="old-link", change="modified"), id="link-target"),
        pytest.param(_new_link, ChangedPath(path="new-link", change="added"), id="new-link"),
    ],
)
def test_a_mode_or_a_link_change_is_listed(
    snapshots: FakeSnapshots,
    folder: Path,
    change: Callable[[Path], None],
    expected: ChangedPath,
) -> None:
    (folder / "old-link").symlink_to("a.txt")
    snapshots.advance()

    change(folder)

    assert snapshots.changed_paths() == [expected]


def test_reset_puts_the_folder_back_to_the_base(snapshots: FakeSnapshots, folder: Path) -> None:
    (folder / "link").symlink_to("a.txt")
    snapshots.advance()
    _change(folder)
    (folder / "a.txt").chmod(0o755)
    (folder / "link").unlink()

    snapshots.reset()

    assert folder.is_dir()
    assert (folder / "a.txt").read_bytes() == b"one\n"
    assert (folder / "a.txt").stat().st_mode & 0o777 == 0o644
    assert not (folder / "b" / "new.txt").exists()
    assert not (folder / "empty").exists()
    assert (folder / "gone.txt").read_bytes() == b"x\n"
    assert (folder / "link").is_symlink()
    assert os.readlink(folder / "link") == "a.txt"
    assert snapshots.changed_paths() == []


def _reset(snapshots: FakeSnapshots) -> None:
    snapshots.reset()


def _changed_paths(snapshots: FakeSnapshots) -> None:
    snapshots.changed_paths()


@pytest.mark.parametrize(
    ("operation", "command"),
    [
        pytest.param(_reset, "reset", id="reset"),
        pytest.param(_changed_paths, "changed_paths", id="changed-paths"),
    ],
)
def test_without_a_base_the_operation_fails_and_leaves_the_folder(
    snapshots: FakeSnapshots,
    folder: Path,
    base: Path,
    operation: Callable[[FakeSnapshots], None],
    command: str,
) -> None:
    before = _tree(folder)

    with pytest.raises(SnapshotError) as raised:
        operation(snapshots)

    assert raised.value.command == command
    assert raised.value.detail == f"no base at {base}"
    assert _tree(folder) == before


def _modify(folder: Path) -> None:
    (folder / "a.txt").write_text("two\n", encoding="utf-8")


def _delete(folder: Path) -> None:
    (folder / "gone.txt").unlink()


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(_modify, id="modified-file"),
        pytest.param(_delete, id="deleted-file"),
    ],
)
def test_a_second_advance_replaces_the_base(
    snapshots: FakeSnapshots, folder: Path, change: Callable[[Path], None]
) -> None:
    snapshots.advance()
    change(folder)
    after = _tree(folder)

    snapshots.advance()

    assert snapshots.changed_paths() == []
    snapshots.reset()
    assert _tree(folder) == after
