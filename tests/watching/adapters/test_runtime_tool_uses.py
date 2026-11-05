"""Each runtime's wrapper sums up the tool calls of the transcript it read of a run."""

import json
from pathlib import Path

import pytest

from claude_stand_in import Step
from factory.agents.adapters.claude_runtime import ClaudeCodeRuntime
from factory.watching.domain.cost_records import ToolUse
from opencode_stand_in import (
    SESSION,
    opencode_request,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
    tool_use,
)
from tool_use_support import Call, claude_lines

CLAUDE_SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
LINE_LIKE_CHARACTERS = "first\u2028second\u0085third"


def _unescaped(line: str) -> str:
    """The same JSON line with every character written raw, as Node and Bun write it."""
    return json.dumps(json.loads(line), ensure_ascii=False)


@pytest.mark.parametrize(
    ("calls", "expected"),
    [
        pytest.param(
            [Call("Read", seconds=0.5), Call("Bash", failed=True, seconds=2.0)],
            [
                ToolUse(tool="Bash", calls=1, failed=1, seconds=2.0),
                ToolUse(tool="Read", calls=1, failed=0, seconds=0.5),
            ],
            id="tool-calls",
        ),
        pytest.param(
            [
                Call(
                    "Read",
                    seconds=0.5,
                    tool_input={"file_path": LINE_LIKE_CHARACTERS},
                    output=LINE_LIKE_CHARACTERS,
                )
            ],
            [ToolUse(tool="Read", calls=1, failed=0, seconds=0.5)],
            id="raw-line-separators-in-input-and-output",
        ),
        pytest.param([], [], id="no-tool-call"),
    ],
)
def test_claude_code_sums_up_the_tool_calls_of_its_session_transcript(
    tmp_path: Path, *, calls: list[Call], expected: list[ToolUse]
) -> None:
    home = tmp_path / "home"
    folder = home / ".claude" / "projects" / "-work-checkout"
    folder.mkdir(parents=True)
    lines = [_unescaped(line) for line in claude_lines(calls)]
    (folder / f"{CLAUDE_SESSION}.jsonl").write_text("".join(f"{line}\n" for line in lines))
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state")
    transcript = runtime.read_transcript(home, CLAUDE_SESSION)
    assert transcript is not None

    assert runtime.tool_uses(transcript) == expected


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        pytest.param(
            [
                tool_use(1600, tool="read", status="completed", error=None, start=1100, end=1600),
                tool_use(1850, tool="bash", error="exit 1", start=1600, end=1850),
                tool_use(2100, tool="bash", status="completed", error=None, start=1850, end=2100),
            ],
            [
                ToolUse(tool="bash", calls=2, failed=1, seconds=0.5),
                ToolUse(tool="read", calls=1, failed=0, seconds=0.5),
            ],
            id="tool-calls",
        ),
        pytest.param(
            [
                tool_use(
                    1600,
                    tool="read",
                    tool_input={"filePath": LINE_LIKE_CHARACTERS},
                    error=LINE_LIKE_CHARACTERS,
                    start=1100,
                    end=1600,
                )
            ],
            [ToolUse(tool="read", calls=1, failed=1, seconds=0.5)],
            id="raw-line-separators-in-input-and-output",
        ),
        pytest.param([], [], id="no-tool-call"),
    ],
)
def test_opencode_sums_up_the_tool_calls_of_its_run_s_stream(
    tmp_path: Path, *, events: list[str], expected: list[ToolUse]
) -> None:
    raw_events = [_unescaped(event) for event in events]
    printed = stdout(step_start(1000), *raw_events, text(result_text(), 2150), step_finish(2200))
    runtime = stand_in_runtime(tmp_path, [Step(stdout=printed)])
    assert runtime.run(opencode_request(tmp_path / "work")).end_reason == "completed"
    transcript = runtime.read_transcript(tmp_path / "home", SESSION)
    assert transcript is not None

    assert runtime.tool_uses(transcript) == expected
