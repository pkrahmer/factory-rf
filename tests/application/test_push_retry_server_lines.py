"""A retried push of a stage's result keeps two server lines and leaves out git's summary line."""

import contextlib
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.domain.errors import PushFailed
from factory.domain.kill_points import KillPoints
from human_clone import HumanClone
from push_retry_support import PushCase, open_push_case

ONE_LINE = "  echo 'Internal Server Error' >&2\n"
TWO_LINES = "  echo 'Internal Server Error' >&2\n  echo 'request id 1234' >&2\n"


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


def _arm_with_two_lines(case: PushCase, failures: int) -> None:
    case.arm(failures)
    hook = case.remote / "hooks" / "pre-receive"
    text = hook.read_text(encoding="utf-8")
    assert ONE_LINE in text
    hook.write_text(text.replace(ONE_LINE, TWO_LINES), encoding="utf-8")


def test_a_retry_line_holds_both_server_lines_and_no_summary_line(
    result_case: PushCase,
) -> None:
    _arm_with_two_lines(result_case, 4)

    with contextlib.suppress(PushFailed):
        result_case.push()

    lines = result_case.retry_lines()
    assert lines
    for line in lines:
        assert "remote: Internal Server Error" in line
        assert "remote: request id 1234" in line
        assert "[remote rejected]" in line
        assert "failed to push some refs" not in line
