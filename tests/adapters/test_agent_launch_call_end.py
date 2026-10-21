"""The reading of a runtime call's end: its time limit first, then the refusals with it."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.agent_launch import (
    CallEnd,
    LoginFiles,
    Starters,
    read_call_end,
    state_directory_error,
)
from factory.domain.errors import AgentRuntimeError

STARTERS = Starters(
    sudo_executable="/usr/bin/sudo",
    confine_executable="/opt/factory/bin/factory-confine",
    login_files=LoginFiles(),
)
LIMIT = timedelta(seconds=30)
CONFINE_STDERR = "factory-confine: landlock is not available\n"
CONFINE_REFUSAL = (
    "/opt/factory/bin/factory-confine refused the agent run: "
    "factory-confine: landlock is not available"
)


@pytest.mark.parametrize(
    ("os_user", "exit_status", "duration", "timed_out", "expected"),
    [
        pytest.param(None, -9, LIMIT, False, False, id="no-user-kill-status"),
        pytest.param(None, None, LIMIT, True, True, id="process-timed-out"),
        pytest.param("agent", 137, LIMIT, False, True, id="user-137-at-limit"),
        pytest.param("agent", -9, timedelta(seconds=31), False, True, id="user-9-above-limit"),
        pytest.param(
            "agent", 137, timedelta(seconds=29.9), False, False, id="user-137-below-limit"
        ),
        pytest.param("agent", 0, LIMIT, False, False, id="user-status-0-at-limit"),
    ],
)
def test_a_call_end_is_read_as_timed_out_when_its_own_timeout_killed_it_at_the_limit(
    os_user: str | None,
    exit_status: int | None,
    duration: timedelta,
    timed_out: bool,
    expected: bool,
) -> None:
    end = CallEnd(
        stderr="",
        printed=True,
        exit_status=exit_status,
        duration=duration,
        timed_out=timed_out,
    )

    reading = read_call_end(end, time_limit=LIMIT, os_user=os_user, starters=STARTERS)

    assert reading is expected


def _refused_end(*, printed: bool, exit_status: int, duration: timedelta, stderr: str) -> CallEnd:
    return CallEnd(
        stderr=stderr,
        printed=printed,
        exit_status=exit_status,
        duration=duration,
        timed_out=False,
    )


@pytest.mark.parametrize(
    ("os_user", "end", "refusal"),
    [
        pytest.param(
            "agent",
            _refused_end(
                printed=False,
                exit_status=1,
                duration=timedelta(seconds=1),
                stderr="sudo: a password is required\n",
            ),
            "/usr/bin/sudo refused the agent run: sudo: a password is required",
            id="sudo-refused",
        ),
        pytest.param(
            None,
            _refused_end(
                printed=False, exit_status=1, duration=timedelta(seconds=1), stderr=CONFINE_STDERR
            ),
            CONFINE_REFUSAL,
            id="wrapper-refused",
        ),
        pytest.param(
            "agent",
            _refused_end(printed=True, exit_status=137, duration=LIMIT, stderr=CONFINE_STDERR),
            CONFINE_REFUSAL,
            id="printed-and-killed-is-read-for-refusals",
        ),
        pytest.param(
            "agent",
            _refused_end(
                printed=True, exit_status=0, duration=timedelta(seconds=1), stderr=CONFINE_STDERR
            ),
            None,
            id="printed-before-the-limit",
        ),
        pytest.param(
            None,
            _refused_end(printed=False, exit_status=0, duration=timedelta(seconds=1), stderr=""),
            None,
            id="nothing-said",
        ),
    ],
)
def test_a_call_end_raises_the_refusal_read_after_its_time_limit(
    os_user: str | None, end: CallEnd, refusal: str | None
) -> None:
    if refusal is None:
        reading = read_call_end(end, time_limit=LIMIT, os_user=os_user, starters=STARTERS)
        assert reading is False
    else:
        with pytest.raises(AgentRuntimeError) as raised:
            read_call_end(end, time_limit=LIMIT, os_user=os_user, starters=STARTERS)
        assert raised.value.detail == refusal


def test_the_state_directory_error_names_the_directory_and_the_cause() -> None:
    error = state_directory_error(Path("/state/runs"), PermissionError(13, "Permission denied"))

    assert isinstance(error, AgentRuntimeError)
    assert error.detail == (
        "cannot write the state directory /state/runs: [Errno 13] Permission denied"
    )
