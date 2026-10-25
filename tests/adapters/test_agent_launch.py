"""The shared words of a run's start, its rules, its refusals and its resume share."""

from datetime import timedelta
from decimal import Decimal

import pytest

from factory.adapters.agent_launch import (
    Launch,
    first_word,
    killed_at_limit,
    launch,
    line_starting,
    resume_budget,
)

SUDO = "/usr/bin/sudo"
ARGV = ["claude", "-p", "x"]
ENVIRONMENT = {"HOME": "/home/agent", "PATH": "/bin"}
LIMIT = timedelta(seconds=30)


@pytest.mark.parametrize(
    ("os_user", "time_limit", "expected"),
    [
        pytest.param(
            None,
            timedelta(seconds=30),
            Launch(argv=ARGV, env=ENVIRONMENT, time_limit=timedelta(seconds=30)),
            id="without-user",
        ),
        pytest.param(
            "agent",
            timedelta(seconds=29.2),
            Launch(
                argv=[
                    *(SUDO, "-n", "-u", "agent", "--"),
                    *("timeout", "--signal=KILL", "30s"),
                    *("env", "-i", "HOME=/home/agent", "PATH=/bin"),
                    *ARGV,
                ],
                env={},
                time_limit=timedelta(seconds=59.2),
            ),
            id="with-user-rounded-up",
        ),
        pytest.param(
            "agent",
            timedelta(seconds=30),
            Launch(
                argv=[
                    *(SUDO, "-n", "-u", "agent", "--"),
                    *("timeout", "--signal=KILL", "30s"),
                    *("env", "-i", "HOME=/home/agent", "PATH=/bin"),
                    *ARGV,
                ],
                env={},
                time_limit=timedelta(seconds=60),
            ),
            id="with-user-whole-seconds",
        ),
    ],
)
def test_launch_runs_the_call_as_the_user_under_a_kill_timeout_with_its_environment_alone(
    os_user: str | None, time_limit: timedelta, expected: Launch
) -> None:
    started = launch(
        ARGV, ENVIRONMENT, os_user=os_user, sudo_executable=SUDO, time_limit=time_limit
    )

    assert started == expected


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        pytest.param(
            "a note\nfactory-confine: first\nfactory-confine: second\n",
            "factory-confine: first",
            id="first-of-two",
        ),
        pytest.param("a note\nsudo: other\n", None, id="no-match"),
        pytest.param("a note factory-confine: inside\n", None, id="not-at-line-start"),
    ],
)
def test_line_starting_finds_the_first_line_that_starts_with_the_prefix(
    stderr: str, expected: str | None
) -> None:
    assert line_starting(stderr, "factory-confine:") == expected


@pytest.mark.parametrize(
    ("os_user", "exit_status", "duration", "expected"),
    [
        pytest.param("agent", 137, LIMIT, True, id="137-at-limit"),
        pytest.param("agent", -9, LIMIT, True, id="minus-9-at-limit"),
        pytest.param("agent", 137, LIMIT + timedelta(seconds=1), True, id="above-limit"),
        pytest.param("agent", 137, LIMIT - timedelta(milliseconds=1), False, id="below-limit"),
        pytest.param(None, 137, LIMIT, False, id="without-user"),
        pytest.param("agent", 1, LIMIT, False, id="exit-1"),
    ],
)
def test_killed_at_limit_needs_a_user_a_kill_status_and_the_limit_reached(
    os_user: str | None, exit_status: int, duration: timedelta, expected: bool
) -> None:
    killed = killed_at_limit(
        os_user=os_user, exit_status=exit_status, duration=duration, time_limit=LIMIT
    )

    assert killed is expected


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        pytest.param("\n2.1.296 (Claude Code)\n", "2.1.296", id="version"),
        pytest.param("", None, id="empty"),
        pytest.param("  \n", None, id="blank"),
    ],
)
def test_first_word_is_the_first_word_of_the_first_non_blank_line(
    output: str, expected: str | None
) -> None:
    assert first_word(output) == expected


@pytest.mark.parametrize(
    ("budget", "expected"),
    [
        pytest.param("1", "0.50", id="below-minimum"),
        pytest.param("2", "0.50", id="at-minimum"),
        pytest.param("4", "1.00", id="quarter"),
        pytest.param("2.50", "0.63", id="rounded-up"),
    ],
)
def test_resume_budget_is_a_quarter_at_least_fifty_cents(budget: str, expected: str) -> None:
    result = resume_budget(Decimal(budget))

    assert result == Decimal(expected)
    assert str(result) == expected
