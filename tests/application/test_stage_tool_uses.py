"""A stage's completed cost record sums up its run's tool calls, without a call's content."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.transcript_files import FileTranscriptStore
from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import ToolUse
from factory.domain.transcripts import Transcript
from human_clone import HumanClone
from stage_run_support import open_story, pushed_cost_records, pushed_cost_text, run_stage
from tool_use_support import Call, claude_lines, transcript_of

SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
COMPLETED = AgentRunResult(
    end_reason="completed",
    decision="doing",
    entry="tests written.",
    duration=timedelta(seconds=5),
    session=SESSION,
)
KEY = "sk-ant-api03-" + "a" * 40
PATH_IN_INPUT = "/work/checkout/src/secret_plans/launch.py"
COMMAND = "grep -rn launch-codes /etc"


class ClaudeReadingRuntime(FakeAgentRuntime):
    """The fake runtime, reading tool calls from its transcripts as Claude Code's wrapper does."""

    def __init__(self, claude: ClaudeCodeRuntime) -> None:
        """Play scripted runs; read tool calls through `claude`."""
        super().__init__()
        self._claude = claude

    def tool_uses(self, transcript: Transcript) -> list[ToolUse] | None:
        """What Claude Code's wrapper reads of `transcript`."""
        return self._claude.tool_uses(transcript)


@pytest.fixture
def runtime(tmp_path: Path) -> ClaudeReadingRuntime:
    """A fake runtime that reads tool calls as Claude Code's wrapper does."""
    return ClaudeReadingRuntime(ClaudeCodeRuntime("claude", tmp_path / "claude-state"))


def _staged(
    boundaries: Boundaries, runtime: FakeAgentRuntime, tmp_path: Path, *, folder: bool
) -> Boundaries:
    update: dict[str, object] = {"workspace": tmp_path / "workspace"}
    staged = replace(boundaries, agent_runtime=runtime)
    if folder:
        update["transcript_dir"] = tmp_path / "transcripts"
        staged = replace(staged, transcripts=FileTranscriptStore(tmp_path / "transcripts"))
    return replace(staged, settings=boundaries.settings.model_copy(update=update))


@pytest.mark.parametrize(
    ("calls", "folder", "expected"),
    [
        pytest.param(
            [Call("Read", seconds=0.5), Call("Bash", failed=True, seconds=2.0)],
            False,
            [
                ToolUse(tool="Bash", calls=1, failed=1, seconds=2.0),
                ToolUse(tool="Read", calls=1, failed=0, seconds=0.5),
            ],
            id="without-a-transcript-folder",
        ),
        pytest.param(
            [Call("Read", seconds=0.5), Call("Bash", failed=True, seconds=2.0)],
            True,
            [
                ToolUse(tool="Bash", calls=1, failed=1, seconds=2.0),
                ToolUse(tool="Read", calls=1, failed=0, seconds=0.5),
            ],
            id="with-a-transcript-folder",
        ),
        pytest.param([], False, [], id="no-tool-call"),
    ],
)
def test_a_completed_run_s_record_carries_its_tool_calls(  # noqa: PLR0913 - the fixtures a stage needs
    boundaries: Boundaries,
    runtime: ClaudeReadingRuntime,
    *,
    human: HumanClone,
    agent_home: Path,
    remote: Path,
    tmp_path: Path,
    calls: list[Call],
    folder: bool,
    expected: list[ToolUse],
) -> None:
    staged = _staged(boundaries, runtime, tmp_path, folder=folder)
    open_story(staged, human, agent_home)
    runtime.queue(ScriptedRun(result=COMPLETED, transcript=transcript_of(claude_lines(calls))))

    run_stage(staged)

    [record] = pushed_cost_records(staged, remote)
    assert record.tools == expected


@pytest.mark.parametrize(
    ("tool_input", "secret"),
    [
        pytest.param({"file_path": PATH_IN_INPUT}, PATH_IN_INPUT, id="path"),
        pytest.param({"command": COMMAND}, COMMAND, id="command"),
        pytest.param({"command": f"export KEY={KEY}"}, KEY, id="key"),
    ],
)
def test_a_record_s_tools_hold_no_text_of_a_call_s_input_or_output(  # noqa: PLR0913 - the fixtures a stage needs
    boundaries: Boundaries,
    runtime: ClaudeReadingRuntime,
    *,
    human: HumanClone,
    agent_home: Path,
    remote: Path,
    tmp_path: Path,
    tool_input: dict[str, object],
    secret: str,
) -> None:
    staged = _staged(boundaries, runtime, tmp_path, folder=False)
    open_story(staged, human, agent_home)
    calls = [Call("Bash", tool_input=tool_input, output=f"echoed {secret}")]
    runtime.queue(ScriptedRun(result=COMPLETED, transcript=transcript_of(claude_lines(calls))))

    run_stage(staged)

    [record] = pushed_cost_records(staged, remote)
    assert record.tools == [ToolUse(tool="Bash", calls=1, failed=0, seconds=1.5)]
    assert secret not in pushed_cost_text(staged, remote)


@pytest.mark.parametrize(
    "transcript",
    [
        pytest.param(Transcript(extension="jsonl", content=b"not a JSON line\n"), id="unreadable"),
        pytest.param(None, id="no-transcript"),
    ],
)
def test_tool_calls_that_cannot_be_read_leave_tools_none_and_the_run_goes_on(  # noqa: PLR0913 - the fixtures a stage needs
    boundaries: Boundaries,
    runtime: ClaudeReadingRuntime,
    *,
    human: HumanClone,
    agent_home: Path,
    remote: Path,
    tmp_path: Path,
    transcript: Transcript | None,
) -> None:
    staged = _staged(boundaries, runtime, tmp_path, folder=False)
    open_story(staged, human, agent_home)
    runtime.queue(ScriptedRun(result=COMPLETED, transcript=transcript))

    report = run_stage(staged)

    assert report.stall is None
    assert report.next_stage == "doing"
    [record] = pushed_cost_records(staged, remote)
    assert record.status == "completed"
    assert record.tools is None
