"""The keeper of transcripts: each run's transcript compressed under its run id, or a log line."""

import gzip
from pathlib import Path

import pytest

from factory.watching.adapters.transcript_files import FileTranscriptStore
from factory.watching.application.transcripts import TranscriptKeeper
from factory.watching.domain.transcripts import Transcript
from support.recording_log import RecordingLog
from support.transcript_support import sha256_of

WORK_ITEM = "F0001-S0001"
RUN = "a" * 32
LATER_RUN = "c" * 32


@pytest.fixture
def log() -> RecordingLog:
    return RecordingLog()


def test_a_kept_transcript_is_a_gzip_file_under_its_run_id_that_its_ref_names(
    tmp_path: Path, log: RecordingLog
) -> None:
    transcript = Transcript(extension="jsonl", content=b'{"type": "user"}\n')

    ref = TranscriptKeeper(FileTranscriptStore(tmp_path), log).keep(WORK_ITEM, RUN, transcript)

    assert ref is not None
    assert ref.path == f"{WORK_ITEM}/{RUN}.jsonl.gz"
    written = tmp_path / ref.path
    assert gzip.decompress(written.read_bytes()) == transcript.content
    assert ref.sha256 == sha256_of(written)
    assert [path.name for path in tmp_path.rglob("*") if path.is_file()] == [f"{RUN}.jsonl.gz"]
    assert log.lines == []


def test_a_run_kept_again_replaces_its_file_and_a_later_run_keeps_its_own(
    tmp_path: Path, log: RecordingLog
) -> None:
    keeper = TranscriptKeeper(FileTranscriptStore(tmp_path), log)
    keeper.keep(WORK_ITEM, RUN, Transcript(extension="jsonl", content=b"before the resume\n"))

    resumed = keeper.keep(
        WORK_ITEM, RUN, Transcript(extension="jsonl", content=b"after the resume\n")
    )
    later = keeper.keep(
        WORK_ITEM, LATER_RUN, Transcript(extension="jsonl", content=b"the later run\n")
    )

    assert resumed is not None
    assert later is not None
    assert later.path == f"{WORK_ITEM}/{LATER_RUN}.jsonl.gz"
    assert sorted(path.name for path in (tmp_path / WORK_ITEM).iterdir()) == [
        f"{RUN}.jsonl.gz",
        f"{LATER_RUN}.jsonl.gz",
    ]
    assert gzip.decompress((tmp_path / resumed.path).read_bytes()) == b"after the resume\n"
    assert resumed.sha256 == sha256_of(tmp_path / resumed.path)
    assert later.sha256 == sha256_of(tmp_path / later.path)


def test_a_folder_that_cannot_be_written_logs_the_line_and_keeps_nothing(
    tmp_path: Path, log: RecordingLog
) -> None:
    not_a_folder = tmp_path / "transcripts"
    not_a_folder.write_text("a file where the folder should be", encoding="utf-8")
    keeper = TranscriptKeeper(FileTranscriptStore(not_a_folder), log)

    ref = keeper.keep(WORK_ITEM, RUN, Transcript(extension="jsonl", content=b"lost\n"))

    assert ref is None
    assert len(log.lines) == 1
    assert log.lines[0].startswith(f"transcript: not kept for {RUN}: ")
