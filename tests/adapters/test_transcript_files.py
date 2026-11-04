"""The transcript folder on disk: files written owner-only."""

import hashlib
import stat
from pathlib import Path

from factory.adapters.transcript_files import FileTranscriptStore

RELATIVE = f"F0001-S0001/{'a' * 32}.jsonl.gz"


def test_a_written_transcript_is_owner_only_and_its_sha256_returned(tmp_path: Path) -> None:
    data = b"\x1f\x8b compressed bytes"

    sha256 = FileTranscriptStore(tmp_path).write(RELATIVE, data)

    written = tmp_path / RELATIVE
    assert written.read_bytes() == data
    assert stat.S_IMODE(written.stat().st_mode) == 0o600
    assert sha256 == hashlib.sha256(data).hexdigest()
