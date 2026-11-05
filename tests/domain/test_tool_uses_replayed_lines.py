"""Claude Code's tool calls read only from the lines that made them, not from replayed copies."""

import json

import pytest

from factory.agents.domain.tool_uses import claude_tool_uses
from factory.domain.cost_records import ToolUse

CALLED = "2026-11-04T10:00:00.000Z"
ANSWERED = "2026-11-04T10:00:02.500Z"
ELSEWHEN = "2026-11-04T10:00:09.000Z"
LATER = "2026-11-04T10:00:05.000Z"


def _use(call_id: str = "toolu_01", name: str = "Bash") -> dict[str, object]:
    return {"type": "tool_use", "id": call_id, "name": name, "input": {"command": "ls"}}


def _result(call_id: str = "toolu_01", *, failed: bool = False) -> dict[str, object]:
    return {"type": "tool_result", "tool_use_id": call_id, "content": "done", "is_error": failed}


def _line(kind: str | None, item: dict[str, object], at: str | None) -> str:
    event: dict[str, object] = {"message": {"content": [item]}, "timestamp": at}
    if kind is not None:
        event["type"] = kind
    return json.dumps(event)


def _prompt() -> str:
    return json.dumps(
        {"type": "user", "timestamp": CALLED, "message": {"content": "Write the tests."}}
    )


BLOB_USE = _line("api-request-blob", _use(), None)


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(
            [
                _prompt(),
                _line("assistant", _use(), CALLED),
                BLOB_USE,
                _line("user", _result(), ANSWERED),
            ],
            id="blob-after-the-assistant-line",
        ),
        pytest.param(
            [
                _prompt(),
                BLOB_USE,
                _line("assistant", _use(), CALLED),
                _line("user", _result(), ANSWERED),
            ],
            id="blob-before-the-assistant-line",
        ),
        pytest.param(
            [
                _prompt(),
                BLOB_USE,
                _line("assistant", _use(), CALLED),
                BLOB_USE,
                _line("user", _result(), ANSWERED),
            ],
            id="two-blob-lines",
        ),
    ],
)
def test_a_replayed_tool_use_without_a_time_keeps_the_call_s_seconds(lines: list[str]) -> None:
    assert claude_tool_uses(lines) == [ToolUse(tool="Bash", calls=1, failed=0, seconds=2.5)]


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param("api-request-blob", id="api-request-blob"),
        pytest.param("attachment", id="attachment"),
        pytest.param(None, id="no-type"),
    ],
)
def test_a_tool_use_only_on_a_line_of_another_type_is_no_call(kind: str | None) -> None:
    lines = [
        _prompt(),
        _line("assistant", _use("toolu_01", "Bash"), CALLED),
        _line("user", _result("toolu_01"), ANSWERED),
        _line(kind, _use("toolu_02", "Read"), CALLED),
        _line(kind, _use("toolu_03", "Bash"), CALLED),
    ]

    assert claude_tool_uses(lines) == [ToolUse(tool="Bash", calls=1, failed=0, seconds=2.5)]


@pytest.mark.parametrize(
    ("kind", "failed"),
    [
        pytest.param("api-request-blob", 0, id="api-request-blob"),
        pytest.param("attachment", 0, id="attachment"),
        pytest.param("user", 1, id="user"),
    ],
)
def test_a_failed_result_marks_a_call_failed_only_on_a_user_line(kind: str, failed: int) -> None:
    lines = [
        _prompt(),
        _line("assistant", _use(), CALLED),
        _line(kind, _result(failed=True), ANSWERED),
    ]

    result = claude_tool_uses(lines) or []

    assert [(use.tool, use.calls, use.failed) for use in result] == [("Bash", 1, failed)]


@pytest.mark.parametrize(
    "second_time",
    [pytest.param(LATER, id="second-line-later"), pytest.param(None, id="second-line-null")],
)
def test_a_repeated_assistant_tool_use_keeps_the_first_line_s_time(
    second_time: str | None,
) -> None:
    lines = [
        _prompt(),
        _line("assistant", _use(), CALLED),
        _line("assistant", _use(), second_time),
        _line("user", _result(), ANSWERED),
    ]

    result = claude_tool_uses(lines) or []

    assert [(use.tool, use.seconds) for use in result] == [("Bash", 2.5)]


@pytest.mark.parametrize("kind", ["api-request-blob", "attachment"])
@pytest.mark.parametrize(
    "before", [pytest.param(True, id="before"), pytest.param(False, id="after")]
)
def test_a_replayed_tool_result_with_another_time_does_not_change_seconds(
    kind: str, *, before: bool
) -> None:
    replayed = _line(kind, _result(), ELSEWHEN)
    answered = _line("user", _result(), ANSWERED)
    lines = [
        _prompt(),
        _line("assistant", _use(), CALLED),
        *([replayed, answered] if before else [answered, replayed]),
    ]

    result = claude_tool_uses(lines) or []

    assert [(use.tool, use.seconds) for use in result] == [("Bash", 2.5)]


@pytest.mark.parametrize(
    ("second_time", "second_failed"),
    [
        pytest.param(LATER, False, id="second-line-later"),
        pytest.param(None, False, id="second-line-null"),
        pytest.param(LATER, True, id="second-line-failed"),
    ],
)
def test_a_repeated_user_tool_result_keeps_the_first_line_s_time_and_outcome(
    second_time: str | None, *, second_failed: bool
) -> None:
    lines = [
        _prompt(),
        _line("assistant", _use(), CALLED),
        _line("user", _result(), ANSWERED),
        _line("user", _result(failed=second_failed), second_time),
    ]

    assert claude_tool_uses(lines) == [ToolUse(tool="Bash", calls=1, failed=0, seconds=2.5)]
