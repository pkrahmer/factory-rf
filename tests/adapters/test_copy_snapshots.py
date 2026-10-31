"""The copy snapshots on a real tree: a folder whose base is a copy in a directory of its own."""

import builtins
import errno
import io
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Protocol

import pytest

from factory.adapters.copy_snapshots import CopySnapshots
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.domain.errors import SnapshotError
from factory.domain.git import ChangedPath

MEBIBYTE = 1024 * 1024


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    folder = tmp_path / "work"
    folder.mkdir()
    (folder / "a.txt").write_text("one\n", encoding="utf-8")
    (folder / "a.txt").chmod(0o644)
    (folder / "gone.txt").write_text("x\n", encoding="utf-8")
    (folder / "d").mkdir()
    (folder / "d" / "inner.txt").write_text("inner\n", encoding="utf-8")
    (folder / "link").symlink_to("a.txt")
    return folder


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path / "base"


@pytest.fixture
def snapshots(folder: Path, base: Path) -> CopySnapshots:
    return CopySnapshots(folder, base)


def _tree(folder: Path) -> dict[str, tuple[int, str | bytes]]:
    return {
        path.relative_to(folder).as_posix(): (
            path.lstat().st_mode,
            os.readlink(path) if path.is_symlink() else b"" if path.is_dir() else path.read_bytes(),
        )
        for path in folder.rglob("*")
    }


def _three_files(folder: Path) -> None:
    (folder / "a.txt").write_text("two\n", encoding="utf-8")
    (folder / "b.txt").write_text("new\n", encoding="utf-8")
    (folder / "gone.txt").unlink()


def _directories(folder: Path) -> None:
    (folder / "empty").mkdir()
    (folder / "d").chmod(0o700)


def _mode(folder: Path) -> None:
    (folder / "a.txt").chmod(0o755)


def _retarget(folder: Path) -> None:
    (folder / "link").unlink()
    (folder / "link").symlink_to("gone.txt")


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        pytest.param(
            _three_files,
            [
                ChangedPath(path="a.txt", change="modified"),
                ChangedPath(path="b.txt", change="added"),
                ChangedPath(path="gone.txt", change="deleted"),
            ],
            id="modified-added-deleted",
        ),
        pytest.param(_directories, [], id="directories-only"),
        pytest.param(_mode, [ChangedPath(path="a.txt", change="modified")], id="mode"),
        pytest.param(_retarget, [ChangedPath(path="link", change="modified")], id="link-target"),
    ],
)
def test_changed_paths_lists_the_changed_files_and_links_sorted_by_path(
    snapshots: CopySnapshots,
    folder: Path,
    change: Callable[[Path], None],
    expected: list[ChangedPath],
) -> None:
    snapshots.advance()

    change(folder)

    assert snapshots.changed_paths() == expected


def test_reset_brings_the_tree_back_byte_for_byte_and_keeps_the_folder(
    snapshots: CopySnapshots, folder: Path
) -> None:
    snapshots.advance()
    before = _tree(folder)
    inode = folder.stat().st_ino
    _three_files(folder)
    _directories(folder)
    _mode(folder)
    _retarget(folder)

    snapshots.reset()

    assert folder.stat().st_ino == inode
    assert _tree(folder) == before
    assert (folder / "link").is_symlink()


def _reset(snapshots: CopySnapshots) -> None:
    snapshots.reset()


def _changed_paths(snapshots: CopySnapshots) -> None:
    snapshots.changed_paths()


@pytest.mark.parametrize(
    ("operation", "command"),
    [
        pytest.param(_reset, "reset", id="reset"),
        pytest.param(_changed_paths, "changed_paths", id="changed-paths"),
    ],
)
def test_without_a_base_reset_and_changed_paths_fail_and_leave_the_folder(
    snapshots: CopySnapshots,
    folder: Path,
    base: Path,
    operation: Callable[[CopySnapshots], None],
    command: str,
) -> None:
    before = _tree(folder)

    with pytest.raises(SnapshotError) as raised:
        operation(snapshots)

    assert (raised.value.command, raised.value.detail) == (command, f"no base at {base}")
    assert _tree(folder) == before


def test_advance_without_a_base_makes_the_base(
    snapshots: CopySnapshots, folder: Path, base: Path
) -> None:
    snapshots.advance()

    assert _tree(base) == _tree(folder)
    assert snapshots.changed_paths() == []


class _Readable(Protocol):
    """The part of an open file the comparison may read through."""

    def read(self, size: int | None = -1, /) -> bytes: ...

    def readinto(self, buffer: bytearray | memoryview, /) -> int | None: ...

    def close(self) -> None: ...

    def __iter__(self) -> Iterator[bytes]: ...


class _CountingFile:
    """A file whose reads note the number of bytes each one returned."""

    def __init__(self, inner: _Readable, reads: list[int]) -> None:
        self._inner = inner
        self._reads = reads

    def read(self, size: int | None = -1) -> bytes:
        data = self._inner.read(size)
        self._reads.append(len(data))
        return data

    def readinto(self, buffer: bytearray | memoryview) -> int | None:
        count = self._inner.readinto(buffer)
        self._reads.append(count or 0)
        return count

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)

    def __enter__(self) -> "_CountingFile":
        return self

    def __exit__(self, *_exception: object) -> None:
        self._inner.close()

    def __iter__(self) -> Iterator[bytes]:
        for line in self._inner:
            self._reads.append(len(line))
            yield line


def _count_reads(monkeypatch: pytest.MonkeyPatch, root: Path) -> list[int]:
    """Note the size of every read of a file under `root`, through any of Python's readers."""
    reads: list[int] = []
    original_open: Callable[..., _Readable] = builtins.open
    original_os_open: Callable[..., int] = os.open
    original_os_read = os.read
    descriptors: set[int] = set()

    def counting_open(file: object, *args: object, **kwargs: object) -> object:
        opened = original_open(file, *args, **kwargs)
        if isinstance(file, str | os.PathLike) and Path(os.fspath(file)).is_relative_to(root):
            return _CountingFile(opened, reads)
        return opened

    def counting_os_open(path: object, *args: object, **kwargs: object) -> int:
        descriptor = original_os_open(path, *args, **kwargs)
        if isinstance(path, str | os.PathLike) and Path(os.fspath(path)).is_relative_to(root):
            descriptors.add(descriptor)
        return descriptor

    def counting_os_read(descriptor: int, size: int) -> bytes:
        data = original_os_read(descriptor, size)
        if descriptor in descriptors:
            reads.append(len(data))
        return data

    monkeypatch.setattr(builtins, "open", counting_open)
    monkeypatch.setattr(io, "open", counting_open)
    monkeypatch.setattr(os, "open", counting_os_open)
    monkeypatch.setattr(os, "read", counting_os_read)
    return reads


def test_a_large_file_is_compared_in_chunks_of_at_most_a_mebibyte(
    snapshots: CopySnapshots, folder: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = bytes(3 * MEBIBYTE)
    (folder / "large.bin").write_bytes(content)
    snapshots.advance()
    (folder / "large.bin").write_bytes(content[:-1] + b"\x01")
    reads = _count_reads(monkeypatch, tmp_path)

    changes = snapshots.changed_paths()

    monkeypatch.undo()
    assert changes == [ChangedPath(path="large.bin", change="modified")]
    assert reads
    assert max(reads) <= MEBIBYTE


def _file_base(tmp_path: Path) -> Path:
    base = tmp_path / "base-file"
    base.write_text("not a directory\n", encoding="utf-8")
    return base


def _base_under_a_file(tmp_path: Path) -> Path:
    parent = tmp_path / "parent-file"
    parent.write_text("not a directory\n", encoding="utf-8")
    return parent / "base"


def _reset_on(snapshots: CopySnapshots) -> None:
    snapshots.reset()


def _advance_on(snapshots: CopySnapshots) -> None:
    snapshots.advance()


@pytest.mark.parametrize(
    ("make_base", "operation", "command"),
    [
        pytest.param(_file_base, _reset_on, "reset", id="reset-on-a-file"),
        pytest.param(_base_under_a_file, _advance_on, "advance", id="advance-under-a-file"),
    ],
)
def test_an_operating_system_fault_of_the_copy_is_a_snapshot_error_naming_the_operation(
    tmp_path: Path,
    folder: Path,
    make_base: Callable[[Path], Path],
    operation: Callable[[CopySnapshots], None],
    command: str,
) -> None:
    snapshots = CopySnapshots(folder, make_base(tmp_path))

    with pytest.raises(SnapshotError) as raised:
        operation(snapshots)

    assert raised.value.command == command
    assert raised.value.detail


def test_an_operating_system_fault_after_the_base_is_found_is_a_reset_error_with_its_message(
    tmp_path: Path, base: Path
) -> None:
    base.mkdir()
    folder_file = tmp_path / "work-file"
    folder_file.write_text("not a directory\n", encoding="utf-8")
    snapshots = CopySnapshots(folder_file, base)

    with pytest.raises(SnapshotError) as raised:
        snapshots.reset()

    assert raised.value.command == "reset"
    assert raised.value.detail != f"no base at {base}"
    assert os.strerror(errno.ENOTDIR) in raised.value.detail


def test_the_fake_snapshots_are_copy_snapshots() -> None:
    assert issubclass(FakeSnapshots, CopySnapshots)
