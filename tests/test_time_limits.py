"""The shared time limits leave a child room to start and stay below every stand-in's wait."""

import operator
from collections.abc import Callable

import pytest

from adapters import opencode_stand_in
from adapters import test_opencode_events as opencode_events
from adapters import test_opencode_resume_session as opencode_resume_session
from adapters import test_opencode_sudo_time_limit as opencode_sudo_time_limit
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT


@pytest.mark.parametrize(
    ("left", "relation", "right"),
    [
        pytest.param(ROOMY_LIMIT.total_seconds(), operator.eq, 10.0, id="limit"),
        pytest.param(ROOMY_BOUND_SECONDS, operator.eq, 25, id="bound"),
        pytest.param(ROOMY_BOUND_SECONDS - ROOMY_LIMIT.total_seconds(), operator.ge, 10, id="room"),
        pytest.param(
            opencode_stand_in.WAIT_SECONDS, operator.gt, ROOMY_BOUND_SECONDS, id="stand-in-wait"
        ),
        pytest.param(
            opencode_resume_session.WAIT_SECONDS,
            operator.gt,
            ROOMY_BOUND_SECONDS,
            id="resume-session-wait",
        ),
        pytest.param(
            opencode_events.WAIT_SECONDS, operator.gt, ROOMY_BOUND_SECONDS, id="events-wait"
        ),
        pytest.param(
            ROOMY_LIMIT.total_seconds(),
            operator.lt,
            opencode_sudo_time_limit.PAST_LIMIT_SECONDS,
            id="sudo-past-limit",
        ),
        pytest.param(
            opencode_sudo_time_limit.PAST_LIMIT_SECONDS,
            operator.lt,
            ROOMY_BOUND_SECONDS,
            id="sudo-within-bound",
        ),
    ],
)
def test_the_roomy_limit_leaves_room_and_stays_below_every_wait(
    *, left: float, relation: Callable[[float, float], bool], right: float
) -> None:
    assert relation(left, right), f"{left} {relation.__name__} {right}"


@pytest.mark.parametrize(
    ("left", "relation", "right", "first_line"),
    [
        pytest.param(30, operator.gt, 30, "30 gt 30", id="broken"),
        pytest.param(11.5, operator.lt, 25, None, id="holds"),
    ],
)
def test_a_relation_that_breaks_names_its_values(
    *,
    left: float,
    relation: Callable[[float, float], bool],
    right: float,
    first_line: str | None,
) -> None:
    try:
        test_the_roomy_limit_leaves_room_and_stays_below_every_wait(
            left=left, relation=relation, right=right
        )
    except AssertionError as error:
        message: str | None = str(error).splitlines()[0]
    else:
        message = None
    assert message == first_line
