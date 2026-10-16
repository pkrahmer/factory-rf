"""The preflight item `token-file`: the token file exists, is the factory's, and only its."""

import os
from pathlib import Path

import pytest

from factory.application.preflight import token_file_item


@pytest.fixture
def token(tmp_path: Path) -> Path:
    """Return a token file in `tmp_path` holding a value."""
    path = tmp_path / "hosting-token"
    path.write_text("example-value\n", encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("mode", "passed"),
    [
        (0o600, True),
        (0o400, True),
        (0o640, False),
        (0o604, False),
        (0o644, False),
        (0o660, False),
    ],
    ids=oct,
)
def test_the_token_file_passes_only_without_a_bit_for_group_or_others(
    token: Path, *, mode: int, passed: bool
) -> None:
    token.chmod(mode)

    item = token_file_item(token, uid=os.getuid(), stat=os.stat)

    assert item.name == "token-file"
    assert item.passed is passed
    if not passed:
        assert str(token) in item.detail


@pytest.mark.parametrize("fault", ["other-owner", "missing", "no-path"])
def test_the_token_file_fails_naming_the_path_for_an_owner_a_missing_file_or_no_path(
    tmp_path: Path, token: Path, fault: str
) -> None:
    token.chmod(0o600)
    uid = os.getuid() + 1 if fault == "other-owner" else os.getuid()
    path = {"other-owner": token, "missing": tmp_path / "absent", "no-path": None}[fault]

    item = token_file_item(path, uid=uid, stat=os.stat)

    assert item.name == "token-file"
    assert not item.passed
    assert str(path) in item.detail


def test_the_token_file_is_read_only_through_stat(tmp_path: Path) -> None:
    absent = tmp_path / "absent"
    uid = os.getuid()

    def stat(path: Path) -> os.stat_result:
        assert path == absent
        return os.stat_result((0o100600, 1, 1, 1, uid, uid, 14, 0, 0, 0))

    item = token_file_item(absent, uid=uid, stat=stat)

    assert item.passed
