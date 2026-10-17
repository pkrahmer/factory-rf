"""The free space of a file system and the bytes a folder takes, read with the standard library."""

import os
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.disk_space import ShutilDiskSpace


def test_the_free_bytes_are_positive_and_within_the_total_or_missing_raises(
    tmp_path: Path,
) -> None:
    free = ShutilDiskSpace().free_bytes(tmp_path)

    assert 0 < free <= shutil.disk_usage(tmp_path).total
    with pytest.raises(FileNotFoundError):
        ShutilDiskSpace().free_bytes(tmp_path / "missing")


def _plain(folder: Path, _outside: Path) -> Path:
    return folder


def _link_to_file(folder: Path, outside: Path) -> Path:
    (outside / "big").write_bytes(b"x" * 100)
    (folder / "link").symlink_to(outside / "big")
    return folder


def _link_to_folder(folder: Path, outside: Path) -> Path:
    (outside / "big").write_bytes(b"x" * 100)
    (folder / "link").symlink_to(outside, target_is_directory=True)
    return folder


def _named_pipe(folder: Path, _outside: Path) -> Path:
    os.mkfifo(folder / "pipe")
    return folder


def _missing(folder: Path, _outside: Path) -> Path:
    return folder / "missing"


@pytest.mark.parametrize(
    ("measured", "expected"),
    [(_plain, 15), (_link_to_file, 15), (_link_to_folder, 15), (_named_pipe, 15), (_missing, 0)],
    ids=["files", "link-to-file", "link-to-folder", "named-pipe", "missing"],
)
def test_the_used_bytes_add_the_regular_files_only(
    tmp_path: Path, measured: Callable[[Path, Path], Path], expected: int
) -> None:
    folder = tmp_path / "folder"
    (folder / "sub").mkdir(parents=True)
    (folder / "three").write_bytes(b"x" * 3)
    (folder / "five").write_bytes(b"x" * 5)
    (folder / "sub" / "seven").write_bytes(b"x" * 7)
    outside = tmp_path / "outside"
    outside.mkdir()

    assert ShutilDiskSpace().used_bytes(measured(folder, outside)) == expected
