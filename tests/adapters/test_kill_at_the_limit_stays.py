"""The kill of a call at its time limit stays without the leftovers program."""

import sys
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.agent_launch import killed_at_limit
from factory.adapters.process import ProcessRequest, run_process
from time_limits import ROOMY_BOUND_SECONDS

LIMIT = timedelta(seconds=30)


def _timed_out_in_bound(tmp_path: Path) -> bool:
    request = ProcessRequest(
        argv=[sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        time_limit=timedelta(seconds=1),
    )
    start = time.monotonic()
    result = run_process(request)
    return result.timed_out and time.monotonic() - start < ROOMY_BOUND_SECONDS


@pytest.mark.parametrize(
    ("seen", "expected"),
    [
        pytest.param(
            lambda _: killed_at_limit(
                os_user="agent", exit_status=137, duration=LIMIT, time_limit=LIMIT
            ),
            True,
            id="sudo-at-the-limit",
        ),
        pytest.param(
            lambda _: killed_at_limit(
                os_user="agent",
                exit_status=137,
                duration=timedelta(seconds=29.9),
                time_limit=LIMIT,
            ),
            False,
            id="sudo-before-the-limit",
        ),
        pytest.param(
            lambda _: killed_at_limit(
                os_user=None, exit_status=255, duration=LIMIT, time_limit=LIMIT, in_container=True
            ),
            True,
            id="container-at-the-limit",
        ),
        pytest.param(
            lambda _: killed_at_limit(
                os_user=None, exit_status=255, duration=LIMIT, time_limit=LIMIT
            ),
            False,
            id="not-in-a-container",
        ),
        pytest.param(_timed_out_in_bound, True, id="session-kill"),
    ],
)
def test_a_call_is_still_killed_at_its_time_limit(
    tmp_path: Path, seen: Callable[[Path], bool], *, expected: bool
) -> None:
    assert seen(tmp_path) is expected
