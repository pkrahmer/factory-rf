"""How a project command ended, said in words: its exit status, its signal or its time limit."""

from datetime import timedelta

import pytest

from factory.domain.checks import CheckResult, command_ending, status_of


@pytest.mark.parametrize(
    ("exit_status", "expected"),
    [
        pytest.param(0, "exit status 0", id="exit-status-0"),
        pytest.param(2, "exit status 2", id="exit-status-2"),
        pytest.param(-15, "signal 15", id="signal-15"),
        pytest.param(None, "time_limit", id="at-the-time-limit"),
    ],
)
def test_a_command_ending_names_the_exit_status_the_signal_or_the_time_limit(
    exit_status: int | None, expected: str
) -> None:
    result = CheckResult(
        command="lint",
        status=status_of(exit_status),
        exit_status=exit_status,
        duration=timedelta(seconds=3),
        last_line="",
        output_tail="",
    )

    assert command_ending(result) == expected
