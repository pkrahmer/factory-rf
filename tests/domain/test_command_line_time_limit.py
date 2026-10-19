"""The line a stage's entry gets for a command stopped at its time limit, and the lines it keeps."""

from datetime import timedelta

import pytest

from factory.domain.checks import CheckResult, command_line

STOPPED = CheckResult(
    command="mutants",
    status="time_limit",
    exit_status=None,
    duration=timedelta(seconds=600.7),
    last_line="1718/1858 mutants",
    output_tail="",
)
PASSED = CheckResult(
    command="mutants",
    status="passed",
    exit_status=0,
    duration=timedelta(seconds=540),
    last_line="mutants: 3 killed",
    output_tail="",
)
FAILED = CheckResult(
    command="mutants",
    status="failed",
    exit_status=1,
    duration=timedelta(seconds=540),
    last_line="mutants: partial, 3 killed",
    output_tail="",
)


@pytest.mark.parametrize(
    ("result", "line"),
    [
        pytest.param(
            STOPPED,
            "`mutants`: 1718/1858 mutants (stopped at its time limit after 600 s)",
            id="time-limit",
        ),
        pytest.param(
            STOPPED.model_copy(update={"duration": timedelta(seconds=599.999)}),
            "`mutants`: 1718/1858 mutants (stopped at its time limit after 599 s)",
            id="rounded-down",
        ),
        pytest.param(
            STOPPED.model_copy(update={"last_line": ""}),
            "`mutants`: (stopped at its time limit after 600 s)",
            id="empty-last-line",
        ),
        pytest.param(PASSED, "`mutants`: mutants: 3 killed", id="passed"),
        pytest.param(FAILED, "`mutants`: mutants: partial, 3 killed", id="failed"),
    ],
)
def test_only_a_command_stopped_at_its_time_limit_gets_the_stop_note(
    result: CheckResult, line: str
) -> None:
    assert command_line(result) == line
