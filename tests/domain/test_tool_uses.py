"""Each runtime's transcript summed up per tool: calls, failed calls and seconds, no content."""

from collections.abc import Callable

import pytest

from factory.domain.cost_records import ToolUse
from factory.domain.tool_uses import claude_tool_uses, opencode_tool_uses
from tool_use_support import Call, claude_lines, opencode_lines

Reading = Callable[[list[Call]], list[ToolUse] | None]
LONG = "a" * 65


def _claude(calls: list[Call]) -> list[ToolUse] | None:
    return claude_tool_uses(claude_lines(calls))


def _opencode(calls: list[Call]) -> list[ToolUse] | None:
    return opencode_tool_uses(opencode_lines(calls))


@pytest.fixture(
    params=[pytest.param(_claude, id="claude-code"), pytest.param(_opencode, id="opencode")]
)
def read(request: pytest.FixtureRequest) -> Reading:
    """Write the calls in one runtime's form and read them back through its function."""
    reading: Reading = request.param
    return reading


@pytest.mark.parametrize(
    ("calls", "expected"),
    [
        pytest.param(
            [Call("Bash", seconds=1.5), Call("Read", seconds=0.5), Call("Bash", seconds=2.0)],
            [
                ToolUse(tool="Bash", calls=2, failed=0, seconds=3.5),
                ToolUse(tool="Read", calls=1, failed=0, seconds=0.5),
            ],
            id="two-tools",
        ),
        pytest.param([], [], id="no-tool-call"),
    ],
)
def test_a_run_gives_one_entry_per_tool_with_its_calls_failures_and_seconds(
    read: Reading, *, calls: list[Call], expected: list[ToolUse]
) -> None:
    assert read(calls) == expected


def test_a_failed_call_counts_in_failed(read: Reading) -> None:
    assert read([Call("Bash", failed=True, seconds=1.0)]) == [
        ToolUse(tool="Bash", calls=1, failed=1, seconds=1.0)
    ]


def test_a_tool_used_three_times_once_failed_sums_into_one_entry(read: Reading) -> None:
    calls = [Call("Bash", seconds=1.0), Call("Bash", failed=True, seconds=1.0), Call("Bash")]

    assert read(calls) == [ToolUse(tool="Bash", calls=3, failed=1, seconds=3.5)]


@pytest.mark.parametrize(
    ("tool", "counted_as"),
    [
        pytest.param("run tests", "other", id="space"),
        pytest.param("files/read", "other", id="slash"),
        pytest.param(LONG, "other", id="65-characters"),
        pytest.param("a" * 64, "a" * 64, id="64-characters"),
        pytest.param(
            "mcp__files:read-v1.2", "mcp__files:read-v1.2", id="underscore-colon-dash-dot"
        ),
    ],
)
def test_a_tool_name_outside_the_form_is_counted_under_other(
    read: Reading, *, tool: str, counted_as: str
) -> None:
    assert read([Call(tool, seconds=1.0)]) == [
        ToolUse(tool=counted_as, calls=1, failed=0, seconds=1.0)
    ]


def test_bad_names_and_a_tool_named_other_merge_into_one_other_entry(read: Reading) -> None:
    calls = [
        Call("run tests", failed=True, seconds=1.0),
        Call("Bash", seconds=0.5),
        Call(LONG, seconds=2.0),
        Call("other", seconds=0.5),
    ]

    assert read(calls) == [
        ToolUse(tool="Bash", calls=1, failed=0, seconds=0.5),
        ToolUse(tool="other", calls=3, failed=1, seconds=3.5),
    ]


@pytest.mark.parametrize(
    "function",
    [
        pytest.param(claude_tool_uses, id="claude-code"),
        pytest.param(opencode_tool_uses, id="opencode"),
    ],
)
def test_lines_that_cannot_be_read_give_no_tools(
    function: Callable[[list[str]], list[ToolUse] | None],
) -> None:
    assert function(["this is not a JSON line"]) is None


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [pytest.param(2.5, 2.5, id="with-times"), pytest.param(None, None, id="without-times")],
)
def test_seconds_come_from_the_transcript_s_times(
    read: Reading, *, seconds: float | None, expected: float | None
) -> None:
    [use] = read([Call("Bash", seconds=seconds)]) or []

    assert use.seconds == expected


def test_tools_are_sorted_by_name_whatever_order_they_first_appear_in(read: Reading) -> None:
    result = read([Call("Read"), Call("Bash"), Call("Edit"), Call("Read")]) or []

    assert [use.tool for use in result] == ["Bash", "Edit", "Read"]


def test_a_call_without_a_result_is_a_call_not_failed_and_adds_no_seconds() -> None:
    lines = claude_lines([Call("Bash", seconds=1.5), Call("Bash", seconds=4.0, answered=False)])

    assert claude_tool_uses(lines) == [ToolUse(tool="Bash", calls=2, failed=0, seconds=1.5)]
