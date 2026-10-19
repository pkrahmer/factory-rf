"""The opencode runtime reads a result block, the model time and the denials as they are."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step
from adapters.opencode_stand_in import (
    opencode_request,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
    tool_use,
)
from factory.adapters.opencode_runtime import parse_result_block

GIT_PUSH = json.dumps({"command": "git push"}, sort_keys=True)
FAILED = tool_use(1150, tool_input={"command": "false"}, error="exit 1", start=1100, end=1200)
REFUSED = tool_use(1500, error="permission denied by rule git push*", start=1300, end=1500)


def _block(*lines: str) -> str:
    return "\n".join(["Done.", "<factory-result>", *lines, "</factory-result>"])


@pytest.mark.parametrize(
    ("block", "expected"),
    [
        pytest.param(
            _block("decision: question", "entry:", "First line.", "", "Third line."),
            ("question", "First line.\n\nThird line."),
            id="lines-kept",
        ),
        pytest.param(
            _block("decision: question", "note:", "First line."), None, id="no-entry-label"
        ),
        pytest.param(_block("question", "entry:", "First line."), None, id="no-decision-label"),
        pytest.param(
            _block("decision: question", "entry: First line."), None, id="entry-on-its-label"
        ),
        pytest.param(
            _block("decision: question", "entry:", "", "   ", "  First line.  ", "", "  "),
            ("question", "First line."),
            id="padded",
        ),
    ],
)
def test_a_result_block_keeps_its_entry_s_lines_and_needs_both_labels(
    block: str, expected: tuple[str, str] | None
) -> None:
    assert parse_result_block(block, ["question"]) == expected


STEP = [
    step_start(1000),
    tool_use(1150, start=1100, end=1200),
    tool_use(1500, start=1300, end=1500),
    text(result_text(), 1900),
    step_finish(2000),
]


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(STEP, id="two-tool-calls"),
        pytest.param([tool_use(400, start=0, end=400), *STEP], id="tool-call-before-the-step"),
    ],
)
def test_the_model_time_takes_off_every_tool_call_of_its_step(
    tmp_path: Path, lines: list[str]
) -> None:
    runtime = stand_in_runtime(tmp_path, [Step(stdout=stdout(*lines))])

    result = runtime.run(opencode_request(tmp_path / "work"))

    assert result.model_duration == timedelta(milliseconds=700)


def _denying(error: str) -> str:
    return tool_use(1500, error=error, start=1300, end=1500)


@pytest.mark.parametrize(
    ("tool_lines", "details"),
    [
        pytest.param([FAILED, REFUSED], [GIT_PUSH], id="failure-then-denial"),
        pytest.param([REFUSED, FAILED], [GIT_PUSH], id="denial-then-failure"),
        pytest.param([_denying("no permission for git push")], [GIT_PUSH], id="permission"),
        pytest.param([_denying("git push was denied")], [GIT_PUSH], id="denied"),
        pytest.param([_denying("Permission Denied")], [GIT_PUSH], id="any-case"),
        pytest.param(
            [tool_use(1500, status="completed", error="denied", start=1300, end=1500)],
            [],
            id="not-an-error",
        ),
    ],
)
def test_every_refused_tool_call_is_a_denial_and_no_other(
    tmp_path: Path, tool_lines: list[str], details: list[str]
) -> None:
    lines = [step_start(1000), *tool_lines, text(result_text(), 1900), step_finish(2000)]
    runtime = stand_in_runtime(tmp_path, [Step(stdout=stdout(*lines))])

    result = runtime.run(opencode_request(tmp_path / "work"))

    assert [denial.detail for denial in result.permission_denials] == details
