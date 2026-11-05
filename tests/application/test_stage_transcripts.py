"""A stage keeps its run's transcript in the transcript folder, or writes a line and goes on."""

import gzip
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_containers import FakeContainerRuns
from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.agents.domain.agent_runs import AgentRunResult
from factory.agents.domain.provider_limits import ProviderLimit
from factory.application.boundaries import Boundaries
from factory.shared.adapters.clock import ManualClock, ManualWaiter
from factory.watching.adapters.transcript_files import FileTranscriptStore
from factory.watching.domain.transcripts import Transcript
from human_clone import HumanClone
from stage_run_support import WORK_ITEM, open_story, pushed_cost_records, run_stage
from transcript_support import sha256_of

SESSION = "ses_a"
SECONDS = timedelta(seconds=5)
LIMITED = AgentRunResult(end_reason="provider_limit", duration=SECONDS, session=SESSION)
COMPLETED = AgentRunResult(
    end_reason="completed",
    decision="doing",
    entry="tests written.",
    duration=SECONDS,
    session=SESSION,
)
WITHOUT_SESSION = COMPLETED.model_copy(update={"session": None})
FIRST = Transcript(extension="jsonl", content=b'{"part": "before the resume"}\n')
SECOND = Transcript(extension="jsonl", content=b'{"part": "after the resume"}\n')
LATER = Transcript(extension="jsonl", content=b'{"part": "the later run"}\n')
NOT_KEPT = "transcript: not kept for "


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """The transcript folder, outside the workspace, the checkout, the state and the home."""
    return tmp_path / "transcripts"


def _with_transcripts(boundaries: Boundaries, tmp_path: Path, folder: Path) -> Boundaries:
    settings = boundaries.settings.model_copy(
        update={"workspace": tmp_path / "workspace", "transcript_dir": folder}
    )
    return replace(boundaries, settings=settings, transcripts=FileTranscriptStore(folder))


@pytest.fixture
def transcribed(boundaries: Boundaries, tmp_path: Path, folder: Path) -> Boundaries:
    """The boundaries with a transcript folder and the dataset's workspace in their settings."""
    return _with_transcripts(boundaries, tmp_path, folder)


def _log_text(boundaries: Boundaries) -> str:
    log_file = boundaries.settings.state_directory / "factory.log"
    return log_file.read_text(encoding="utf-8") if log_file.exists() else ""


def _files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.rglob("*") if path.is_file()) if folder.exists() else []


def _limited_settings(boundaries: Boundaries, agent_home: Path) -> Boundaries:
    minute = timedelta(minutes=1)
    settings = boundaries.settings.model_copy(
        update={
            "provider_limit": ProviderLimit(cooldown=minute, ceiling=minute),
            "agent_home": agent_home,
        }
    )
    return replace(boundaries, settings=settings)


def test_without_a_transcript_folder_a_stage_runs_as_before_and_keeps_nothing(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    tmp_path: Path,
) -> None:
    assert boundaries.transcripts is None
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=COMPLETED, transcript=FIRST))

    report = run_stage(boundaries)

    assert report.stall is None
    assert report.next_stage == "doing"
    assert all(record.transcript is None for record in pushed_cost_records(boundaries, remote))
    assert "transcript:" not in _log_text(boundaries)
    assert boundaries.stop_records.read() == []
    assert [path for path in _files(tmp_path) if path.name.endswith(".gz")] == []


def test_a_completed_run_leaves_its_transcript_that_its_record_names(
    transcribed: Boundaries,
    *,
    folder: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(transcribed, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=COMPLETED, transcript=FIRST))

    run_stage(transcribed)

    [record] = pushed_cost_records(transcribed, remote)
    expected = f"{WORK_ITEM}/{record.run}.jsonl.gz"
    assert _files(folder) == [folder / expected]
    written = folder / expected
    assert written.stat().st_mode & 0o777 == 0o600
    assert gzip.decompress(written.read_bytes()) == FIRST.content
    assert record.transcript is not None
    assert record.transcript.path == expected
    assert record.transcript.sha256 == sha256_of(written)


def test_a_run_resumed_within_itself_keeps_one_file_with_the_content_after_the_resume(
    transcribed: Boundaries,
    *,
    folder: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    open_story(transcribed, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=LIMITED, transcript=FIRST))
    agent_runtime.queue(ScriptedRun(result=COMPLETED, transcript=SECOND))

    run_stage(replace(transcribed, waiter=ManualWaiter(clock)))

    [record] = pushed_cost_records(transcribed, remote)
    written = folder / WORK_ITEM / f"{record.run}.jsonl.gz"
    assert _files(folder) == [written]
    assert gzip.decompress(written.read_bytes()) == SECOND.content
    assert record.transcript is not None
    assert record.transcript.sha256 == sha256_of(written)


@pytest.mark.parametrize(
    ("result", "transcript", "folder_is_a_file"),
    [
        pytest.param(WITHOUT_SESSION, FIRST, False, id="missing-session"),
        pytest.param(COMPLETED, None, False, id="missing-transcript"),
        pytest.param(COMPLETED, FIRST, True, id="folder-not-writable"),
    ],
)
def test_a_transcript_not_kept_writes_its_line_and_leaves_the_run_unchanged(
    transcribed: Boundaries,
    *,
    result: AgentRunResult,
    transcript: Transcript | None,
    folder_is_a_file: bool,
    folder: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    if folder_is_a_file:
        folder.write_text("a file where the folder should be", encoding="utf-8")
    open_story(transcribed, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=result, transcript=transcript))

    report = run_stage(transcribed)

    assert report.stall is None
    assert report.next_stage == "doing"
    [record] = pushed_cost_records(transcribed, remote)
    assert record.status == "completed"
    assert record.transcript is None
    assert f"{NOT_KEPT}{record.run}: " in _log_text(transcribed)


@pytest.mark.parametrize(
    "later_transcript",
    [
        pytest.param(LATER, id="kept"),
        pytest.param(None, id="not-kept"),
    ],
)
def test_a_later_run_of_an_earlier_session_names_its_own_file_or_none(
    transcribed: Boundaries,
    *,
    later_transcript: Transcript | None,
    folder: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    clock: ManualClock,
) -> None:
    open_story(transcribed, human, agent_home)
    limited = _limited_settings(replace(transcribed, waiter=ManualWaiter(clock)), agent_home)
    agent_runtime.queue(ScriptedRun(result=LIMITED, transcript=FIRST))
    agent_runtime.queue(ScriptedRun(result=LIMITED, transcript=FIRST))
    assert run_stage(limited).stall is not None
    agent_runtime.queue(ScriptedRun(result=COMPLETED, transcript=later_transcript))

    run_stage(limited)

    earlier, later = pushed_cost_records(transcribed, remote)[-2:]
    assert earlier.run != later.run
    assert earlier.transcript is not None
    assert earlier.transcript.sha256 == sha256_of(folder / earlier.transcript.path)
    if later_transcript is None:
        assert later.transcript is None
        assert f"{NOT_KEPT}{later.run}: " in _log_text(transcribed)
    else:
        assert later.transcript is not None
        assert later.transcript.path == f"{WORK_ITEM}/{later.run}.jsonl.gz"
        written = folder / later.transcript.path
        assert gzip.decompress(written.read_bytes()) == later_transcript.content
        assert later.transcript.sha256 == sha256_of(written)


def test_no_container_and_no_prompt_names_the_transcript_folder(
    transcribed: Boundaries,
    *,
    folder: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    open_story(transcribed, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=COMPLETED, transcript=FIRST))

    run_stage(transcribed)

    containers = transcribed.containers
    assert isinstance(containers, FakeContainerRuns)
    assert containers.calls
    named = str(folder)
    for call in containers.calls:
        assert all(named not in str(mount.source) for mount in call.mounts)
    assert all(named not in request.prompt for request in agent_runtime.requests())
