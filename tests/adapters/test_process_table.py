"""The process table read from folders of a fake `/proc`, and the identity of the own process."""

import os
import pwd
from pathlib import Path

import pytest

from factory.adapters.process import own_identity, read_process_table
from factory.domain.sessions import ProcessEntry

_VALID = "{pid} (x) S 1 {pid} {pid} 0\n"


def _entry(pid: int, *, ended: bool = False) -> ProcessEntry:
    return ProcessEntry(pid=pid, session=pid, ended=ended, uid=os.getuid())


@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        pytest.param({"7": "7 (x y) S 1 7 7 0\n"}, [_entry(7)], id="running"),
        pytest.param({"8": "8 (x) Z 1 8 8 0\n"}, [_entry(8, ended=True)], id="zombie"),
        pytest.param({"self": _VALID.format(pid=1)}, [], id="self"),
        pytest.param({"12a": _VALID.format(pid=12)}, [], id="not-digits"),
        pytest.param({"12": None}, [], id="no-stat"),
        pytest.param(
            {name: _VALID.format(pid=name) for name in ("10", "2", "33")},
            [_entry(2), _entry(10), _entry(33)],
            id="sorted",
        ),
        pytest.param({"5": "5 x S 1 5 5 0\n"}, None, id="unreadable-stat"),
    ],
)
def test_process_table_is_read_from_the_folders(
    tmp_path: Path, folders: dict[str, str | None], expected: list[ProcessEntry] | None
) -> None:
    for name, stat in folders.items():
        (tmp_path / name).mkdir()
        if stat is not None:
            (tmp_path / name / "stat").write_text(stat, encoding="utf-8")

    if expected is None:
        with pytest.raises(ValueError):  # noqa: PT011  # pydantic's ValidationError is one
            read_process_table(tmp_path)
    else:
        assert read_process_table(tmp_path) == expected


def test_missing_process_table_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_process_table(tmp_path / "missing")


def test_own_identity_is_the_running_process() -> None:
    identity = own_identity()

    assert identity.uid == os.getuid()
    assert identity.user == pwd.getpwuid(os.getuid()).pw_name
    assert identity.pid == os.getpid()
