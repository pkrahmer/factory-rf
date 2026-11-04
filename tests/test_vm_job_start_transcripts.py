"""The job start script's check of the transcript folder it is given."""

import os
from pathlib import Path

import pytest

from vm_support import run_job_start

SETTING = "FACTORY_TRANSCRIPT_DIR"


@pytest.mark.parametrize(
    ("folder", "starts"),
    [
        pytest.param("writable", True, id="writable"),
        pytest.param(None, True, id="unset"),
        pytest.param("missing", False, id="missing"),
        pytest.param(
            "read-only",
            False,
            id="read-only",
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root writes every folder"),
        ),
    ],
)
def test_the_factory_starts_only_with_a_writable_or_unset_transcript_folder(
    tmp_path: Path, folder: str | None, starts: bool
) -> None:
    transcripts = tmp_path / "transcripts"
    inputs: dict[str, str | None] = {SETTING: None}
    if folder is not None:
        inputs[SETTING] = str(transcripts)
    if folder in ("writable", "read-only"):
        transcripts.mkdir()
    if folder == "read-only":
        transcripts.chmod(0o500)

    run = run_job_start(tmp_path, inputs)

    if starts:
        assert run.result.exit_status == 0, run.result.stderr
        assert "cannot be written" not in run.result.stderr
        assert len(run.named("factory-run")) == 1
        if folder is not None:
            assert list(transcripts.iterdir()) == []
    else:
        assert run.result.exit_status != 0
        assert f"transcript folder {transcripts} cannot be written" in run.result.stderr
        assert run.named("factory-run") == []
