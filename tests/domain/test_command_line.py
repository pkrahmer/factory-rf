"""The line a stage's entry gets for a project command's result."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.domain.checks import CheckResult, ReusedRun, command_line

RESULT = CheckResult(
    command="check",
    status="passed",
    exit_status=0,
    duration=timedelta(seconds=3),
    last_line="12 passed",
    output_tail="",
)
REUSED = RESULT.model_copy(
    update={
        "reused": ReusedRun(tree="a" * 40, at=datetime(2026, 10, 12, 12, 0, 0, 250000, tzinfo=UTC))
    }
)


@pytest.mark.parametrize(
    ("result", "line"),
    [
        pytest.param(RESULT, "`check`: 12 passed", id="run"),
        pytest.param(
            REUSED,
            "`check`: 12 passed (not run again: passed on tree aaaaaaaaaaaa"
            " at 2026-10-12T12:00:00Z)",
            id="reused",
        ),
    ],
)
def test_the_command_line_names_the_run_a_reused_result_took(
    result: CheckResult, line: str
) -> None:
    assert command_line(result) == line
