"""A retried push of a stage's result names the server's words, not git's porcelain frame."""

import contextlib
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.domain.errors import PushFailed
from factory.domain.kill_points import KillPoints
from human_clone import HumanClone
from push_retry_support import PushCase, open_push_case


@pytest.fixture
def result_case(
    boundaries: Boundaries,
    *,
    tmp_path: Path,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    kill_points: KillPoints,
) -> PushCase:
    """A story opened at `tests`, ready to push its stage's result."""
    return open_push_case(
        "result",
        boundaries,
        tmp_path=tmp_path,
        remote=remote,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        kill_points=kill_points,
    )


def test_a_retry_line_holds_the_servers_message_and_no_porcelain_done(
    result_case: PushCase,
) -> None:
    result_case.arm(4)

    with contextlib.suppress(PushFailed):
        result_case.push()

    lines = result_case.retry_lines()
    assert lines
    for line in lines:
        assert "remote: Internal Server Error" in line
        assert "[remote rejected]" in line
        assert "Done" not in line
