"""The shared time limits leave a child room to start and stay below every stand-in's wait."""

from datetime import timedelta

import pytest

from adapters import opencode_stand_in
from adapters import test_claude_runtime_confinement as claude_confinement
from adapters import test_opencode_events as opencode_events
from adapters import test_opencode_resume_session as opencode_resume_session
from adapters import test_opencode_sudo_time_limit as opencode_sudo_time_limit
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT


@pytest.mark.parametrize(
    "holds",
    [
        pytest.param(timedelta(seconds=10) == ROOMY_LIMIT, id="limit"),
        pytest.param(ROOMY_BOUND_SECONDS == 25, id="bound"),
        pytest.param(ROOMY_BOUND_SECONDS - ROOMY_LIMIT.total_seconds() >= 10, id="room"),
        pytest.param(
            claude_confinement.WAIT_SECONDS > ROOMY_BOUND_SECONDS, id="claude-confinement-wait"
        ),
        pytest.param(opencode_stand_in.WAIT_SECONDS > ROOMY_BOUND_SECONDS, id="stand-in-wait"),
        pytest.param(
            opencode_resume_session.WAIT_SECONDS > ROOMY_BOUND_SECONDS, id="resume-session-wait"
        ),
        pytest.param(opencode_events.WAIT_SECONDS > ROOMY_BOUND_SECONDS, id="events-wait"),
        pytest.param(
            ROOMY_LIMIT.total_seconds() < opencode_sudo_time_limit.PAST_LIMIT_SECONDS,
            id="sudo-past-limit",
        ),
        pytest.param(
            opencode_sudo_time_limit.PAST_LIMIT_SECONDS < ROOMY_BOUND_SECONDS,
            id="sudo-within-bound",
        ),
    ],
)
def test_the_roomy_limit_leaves_room_and_stays_below_every_wait(*, holds: bool) -> None:
    assert holds
