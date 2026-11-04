"""The transcript folder on disk: files written owner-only, and copies past their days removed."""

import hashlib
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory.adapters.transcript_files import FileTranscriptStore

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
DAYS = 3
RELATIVE = f"F0001-S0001/{'a' * 32}.jsonl.gz"


def test_a_written_transcript_is_owner_only_and_its_sha256_returned(tmp_path: Path) -> None:
    data = b"\x1f\x8b compressed bytes"

    sha256 = FileTranscriptStore(tmp_path).write(RELATIVE, data)

    written = tmp_path / RELATIVE
    assert written.read_bytes() == data
    assert stat.S_IMODE(written.stat().st_mode) == 0o600
    assert sha256 == hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize(
    ("age", "removed"),
    [
        pytest.param(timedelta(days=DAYS, seconds=1), True, id="older-than-the-days"),
        pytest.param(timedelta(days=DAYS), False, id="exactly-the-days"),
        pytest.param(timedelta(days=DAYS, seconds=-1), False, id="newer-than-the-days"),
    ],
)
def test_only_files_strictly_older_than_the_days_are_removed(
    tmp_path: Path, age: timedelta, removed: bool
) -> None:
    store = FileTranscriptStore(tmp_path)
    store.write(RELATIVE, b"transcript")
    stamp = (NOW - age).timestamp()
    os.utime(tmp_path / RELATIVE, (stamp, stamp))

    count = store.remove_older_than(DAYS, NOW)

    assert count == (1 if removed else 0)
    assert (tmp_path / RELATIVE).exists() is not removed
