"""The preflight item `token-file`: the token file exists in a folder that is the factory's."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from factory.application.preflight import token_file_item


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    """Return a folder of mode `0700` in `tmp_path`, made writable again for the cleanup."""
    path = tmp_path / "secrets"
    path.mkdir()
    path.chmod(0o700)
    yield path
    path.chmod(0o700)


@pytest.fixture
def token(folder: Path) -> Path:
    """Return a token file of mode `0600` in `folder` holding a value."""
    path = folder / "hosting-token"
    path.write_text("example-value\n", encoding="utf-8")
    path.chmod(0o600)
    return path


@pytest.mark.parametrize(
    ("mode", "passed"),
    [
        (0o700, True),
        (0o500, True),
        (0o740, False),
        (0o720, False),
        (0o710, False),
        (0o704, False),
        (0o702, False),
        (0o701, False),
    ],
    ids=lambda value: oct(value) if isinstance(value, int) and value > 1 else str(value),
)
def test_the_folder_passes_only_without_a_bit_for_group_or_others(
    folder: Path, token: Path, *, mode: int, passed: bool
) -> None:
    folder.chmod(mode)

    item = token_file_item(token, uid=os.getuid(), stat=os.stat)

    assert item.name == "token-file"
    assert item.passed is passed
    if not passed:
        assert item.detail == f"{token}: the folder {folder} has mode {mode:04o}; make it 0700"


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o666, 0o777], ids=oct)
def test_the_token_files_own_mode_does_not_count(token: Path, mode: int) -> None:
    token.chmod(mode)

    item = token_file_item(token, uid=os.getuid(), stat=os.stat)

    assert item.name == "token-file"
    assert item.passed


def test_a_folder_of_another_owner_fails(folder: Path, token: Path) -> None:
    uid = os.getuid() + 1

    item = token_file_item(token, uid=uid, stat=os.stat)

    assert item.name == "token-file"
    assert not item.passed
    assert item.detail == (
        f"{token}: the folder {folder} belongs to uid {os.getuid()}, not to {uid}"
    )


@pytest.mark.parametrize("set_path", [False, True], ids=["no-path", "missing"])
def test_no_path_or_a_missing_token_file_fails(folder: Path, *, set_path: bool) -> None:
    path = folder / "hosting-token" if set_path else None
    fault = "the token file does not exist" if set_path else "no token file is set"

    item = token_file_item(path, uid=os.getuid(), stat=os.stat)

    assert item.name == "token-file"
    assert not item.passed
    assert item.detail == f"{path}: {fault}"


@pytest.mark.parametrize(
    ("folder_mode", "token_exists", "uid_offset", "fault"),
    [
        pytest.param(
            0o750,
            False,
            0,
            "the folder {folder} has mode 0750; make it 0700",
            id="mode-before-missing-file",
        ),
        pytest.param(
            0o750,
            True,
            1,
            "the folder {folder} belongs to uid {owner}, not to {uid}",
            id="owner-before-mode",
        ),
        pytest.param(None, False, 0, "the token file does not exist", id="missing-folder"),
    ],
)
def test_the_first_fault_found_is_the_detail(
    tmp_path: Path,
    *,
    folder_mode: int | None,
    token_exists: bool,
    uid_offset: int,
    fault: str,
) -> None:
    folder = tmp_path / "secrets"
    token = folder / "hosting-token"
    if folder_mode is not None:
        folder.mkdir()
        if token_exists:
            token.write_text("example-value\n", encoding="utf-8")
            token.chmod(0o600)
        folder.chmod(folder_mode)
    uid = os.getuid() + uid_offset

    item = token_file_item(token, uid=uid, stat=os.stat)

    assert item.name == "token-file"
    assert not item.passed
    expected = fault.format(folder=folder, owner=os.getuid(), uid=uid)
    assert item.detail == f"{token}: {expected}"


def test_the_item_reads_only_through_stat(tmp_path: Path) -> None:
    absent = tmp_path / "secrets" / "hosting-token"
    uid = os.getuid()
    answers = {
        absent.parent: os.stat_result((0o040700, 1, 1, 1, uid, uid, 0, 0, 0, 0)),
        absent: os.stat_result((0o100000, 1, 1, 1, uid + 1, uid + 1, 14, 0, 0, 0)),
    }
    asked: list[Path] = []

    def stat(path: Path) -> os.stat_result:
        asked.append(path)
        return answers[path]

    item = token_file_item(absent, uid=uid, stat=stat)

    assert item.passed
    assert asked == [absent.parent, absent]
