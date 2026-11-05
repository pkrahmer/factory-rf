"""A run's tool calls summed up per tool from its runtime's transcript, without their content."""

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

from factory.watching.domain.cost_records import TOOL_NAME_PATTERN, ToolUse

OTHER_TOOL = "other"


class _Unreadable(Exception):
    """A transcript line that is no JSON object, or a call field of the wrong shape."""


@dataclass(frozen=True)
class _Call:
    tool: str
    failed: bool
    seconds: float | None


def claude_tool_uses(lines: list[str]) -> list[ToolUse] | None:
    """The tool calls of a Claude Code session transcript, one entry per tool, sorted by name.

    A call is a `tool_use` item of an `assistant` line, failed when its `tool_result` on a
    `user` line has `is_error`, timed by the `timestamp`s of the two lines. Lines of any other
    type replay the conversation without its times and are not read; of two lines with the
    same id, the first counts. `None` when a line cannot be read; `[]` for no call.
    """
    try:
        events = _objects(lines)
        uses: dict[str, tuple[str, datetime | None]] = {}
        results: dict[str, tuple[bool, datetime | None]] = {}
        for event in events:
            at = _timestamp(event)
            line_type = event.get("type")
            for item in _content_items(event):
                kind = item.get("type")
                if kind == "tool_use" and line_type == "assistant":
                    uses.setdefault(_text(item, "id"), (_text(item, "name"), at))
                elif kind == "tool_result" and line_type == "user":
                    results.setdefault(
                        _text(item, "tool_use_id"), (item.get("is_error") is True, at)
                    )
    except _Unreadable:
        return None
    return _summed([_claude_call(use, results.get(call_id)) for call_id, use in uses.items()])


def opencode_tool_uses(lines: list[str]) -> list[ToolUse] | None:
    """The tool calls of an opencode event stream, one entry per tool, sorted by name.

    A call is a `tool_use` event, failed when its part's state is `error`, timed by the
    state's `time.start` and `time.end` in milliseconds. `None` when a line cannot be read;
    `[]` for no call.
    """
    try:
        events = _objects(lines)
        calls = [_opencode_call(event) for event in events if event.get("type") == "tool_use"]
    except _Unreadable:
        return None
    return _summed(calls)


def _objects(lines: list[str]) -> list[dict[str, object]]:
    return [_object(line) for line in lines if line.strip()]


def _object(line: str) -> dict[str, object]:
    try:
        value: object = json.loads(line)
    # The decoder recurses per nesting level, so a deeply nested line raises RecursionError.
    except (ValueError, RecursionError) as error:
        raise _Unreadable from error
    return _as_object(value)


def _as_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _Unreadable
    return {str(key): item for key, item in value.items()}


def _text(event: dict[str, object], key: str) -> str:
    value = event.get(key)
    if not isinstance(value, str):
        raise _Unreadable
    return value


def _timestamp(event: dict[str, object]) -> datetime | None:
    value = event.get("timestamp")
    if not isinstance(value, str):
        return None
    try:
        at = datetime.fromisoformat(value)
    except ValueError:
        return None
    # A time without an offset cannot be set against one with an offset; it gives no time.
    return at if at.tzinfo is not None else None


def _content_items(event: dict[str, object]) -> list[dict[str, object]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [_as_object(item) for item in content if isinstance(item, dict)]


def _claude_call(
    use: tuple[str, datetime | None], result: tuple[bool, datetime | None] | None
) -> _Call:
    tool, called_at = use
    if result is None:
        # An unanswered call, as an interrupted run leaves it: neither failed nor timed.
        return _Call(tool=tool, failed=False, seconds=None)
    failed, answered_at = result
    seconds = None
    if called_at is not None and answered_at is not None:
        seconds = _non_negative((answered_at - called_at).total_seconds())
    return _Call(tool=tool, failed=failed, seconds=seconds)


def _opencode_call(event: dict[str, object]) -> _Call:
    part = _as_object(event.get("part"))
    state = _as_object(part.get("state", {}))
    return _Call(
        tool=_text(part, "tool"),
        failed=state.get("status") == "error",
        seconds=_opencode_seconds(state.get("time")),
    )


def _opencode_seconds(time: object) -> float | None:
    if not isinstance(time, dict):
        return None
    start, end = _milliseconds(time.get("start")), _milliseconds(time.get("end"))
    if start is None or end is None:
        return None
    return _non_negative((end - start) / 1000)


def _milliseconds(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        return float(value)
    except OverflowError:
        # An integer beyond the float range gives no time rather than a failed stage.
        return None


def _non_negative(seconds: float) -> float | None:
    # A clock that went backwards gives no time rather than a refused record.
    return seconds if math.isfinite(seconds) and seconds >= 0 else None


def _summed(calls: list[_Call]) -> list[ToolUse]:
    totals: dict[str, ToolUse] = {}
    for call in calls:
        name = call.tool if re.fullmatch(TOOL_NAME_PATTERN, call.tool) else OTHER_TOOL
        earlier = totals.get(name, ToolUse(tool=name, calls=0, failed=0, seconds=None))
        totals[name] = ToolUse(
            tool=name,
            calls=earlier.calls + 1,
            failed=earlier.failed + int(call.failed),
            seconds=_added(earlier.seconds, call.seconds),
        )
    return [totals[name] for name in sorted(totals)]


def _added(total: float | None, seconds: float | None) -> float | None:
    if seconds is None:
        return total
    if total is None:
        return seconds
    summed = total + seconds
    # Two huge times overflow to infinity; the total then stays where it was.
    return summed if math.isfinite(summed) else total
