"""The job start script's check of the transcript folder it is given."""

import os
from pathlib import Path

import pytest

from vm_support import run_job_start

SETTING = "FACTORY_TRANSCRIPT_DIR"


@pytest.mark.parametrize(
    "folder",
    [
        pytest.param("writable", id="writable"),
        pytest.param(None, id="unset"),
    ],
)
def test_a_writable_or_unset_transcript_folder_starts_the_factory_as_before(
    tmp_path: Path, folder: str | None
) -> None:
    transcripts = tmp_path / "transcripts"
    inputs: dict[str, str | None] = {SETTING: None}
    if folder is not None:
        transcripts.mkdir()
        inputs[SETTING] = str(transcripts)

    run = run_job_start(tmp_path, inputs)

    assert run.result.exit_status == 0, run.result.stderr
    assert "cannot be written" not in run.result.stderr
    assert len(run.named("factory-run")) == 1
    if folder is not None:
        assert list(transcripts.iterdir()) == []


@pytest.mark.parametrize(
    "folder",
    [
        pytest.param("missing", id="missing"),
        pytest.param(
            "read-only",
            id="read-only",
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root writes every folder"),
        ),
    ],
)
def test_a_transcript_folder_that_cannot_be_written_ends_the_start(
    tmp_path: Path, folder: str
) -> None:
    transcripts = tmp_path / "transcripts"
    if folder == "read-only":
        transcripts.mkdir()
        transcripts.chmod(0o500)

    run = run_job_start(tmp_path, {SETTING: str(transcripts)})

    assert run.result.exit_status != 0
    assert f"transcript folder {transcripts} cannot be written" in run.result.stderr
    assert run.named("factory-run") == []
