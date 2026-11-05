"""Transcript lines of tool calls, in Claude Code's session form and in opencode's stream form."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from factory.watching.domain.transcripts import Transcript

STARTED = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
CALL_SPACING = timedelta(seconds=10)
SESSION = "ses_a"


def _default_input() -> dict[str, object]:
    return {"command": "ls"}


@dataclass(frozen=True)
class Call:
    """One tool call: its tool, whether it failed, its seconds (`None`: no times), its answer."""

    tool: str
    failed: bool = False
    seconds: float | None = 1.5
    answered: bool = True
    tool_input: Mapping[str, object] = field(default_factory=_default_input)
    output: str = "done"


def _line(event: Mapping[str, object]) -> str:
    return json.dumps(event)


def _stamp(at: datetime) -> str:
    return at.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _claude_line(kind: str, content: object, at: datetime | None) -> str:
    event: dict[str, object] = {"type": kind, "message": {"role": kind, "content": content}}
    if at is not None:
        event["timestamp"] = _stamp(at)
    return _line(event)


def claude_lines(calls: list[Call]) -> list[str]:
    """A session transcript: the prompt, then each call's `tool_use` line and its `tool_result`."""
    lines = [_claude_line("user", "Write the tests.", STARTED)]
    for number, call in enumerate(calls):
        called_at = STARTED + CALL_SPACING * (number + 1)
        timed = call.seconds is not None
        use: dict[str, object] = {
            "type": "tool_use",
            "id": f"toolu_{number:02d}",
            "name": call.tool,
            "input": dict(call.tool_input),
        }
        lines.append(_claude_line("assistant", [use], called_at if timed else None))
        if call.answered:
            answered_at = called_at + timedelta(seconds=call.seconds or 0)
            result = {
                "type": "tool_result",
                "tool_use_id": f"toolu_{number:02d}",
                "content": call.output,
                "is_error": call.failed,
            }
            lines.append(_claude_line("user", [result], answered_at if timed else None))
    return lines


def opencode_lines(calls: list[Call]) -> list[str]:
    """An event stream: a step's start, then one `tool_use` event per call."""
    started_ms = int(STARTED.timestamp() * 1000)
    lines = [
        _line(
            {
                "type": "step_start",
                "timestamp": started_ms,
                "sessionID": SESSION,
                "part": {"type": "step-start"},
            }
        )
    ]
    for number, call in enumerate(calls):
        called_ms = started_ms + 10_000 * (number + 1)
        state: dict[str, object] = {
            "status": "error" if call.failed else "completed",
            "input": dict(call.tool_input),
        }
        if call.failed:
            state["error"] = call.output
        else:
            state["output"] = call.output
        if call.seconds is not None:
            state["time"] = {"start": called_ms, "end": called_ms + round(call.seconds * 1000)}
        lines.append(
            _line(
                {
                    "type": "tool_use",
                    "timestamp": called_ms,
                    "sessionID": SESSION,
                    "part": {"type": "tool", "tool": call.tool, "state": state},
                }
            )
        )
    return lines


def transcript_of(lines: list[str]) -> Transcript:
    """The transcript that holds `lines`, one per line."""
    return Transcript(extension="jsonl", content="".join(f"{line}\n" for line in lines).encode())
