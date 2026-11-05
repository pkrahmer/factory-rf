"""A refused or unreachable push of a stage's result or a recorded change is tried again."""

import contextlib
from datetime import timedelta
from pathlib import Path

import pytest

from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.pipeline.application.boundaries import Boundaries
from factory.shared.domain.errors import PushFailed
from factory.shared.domain.kill_points import KillPoints
from support.human_clone import HumanClone
from support.push_retry_support import PushCase, open_push_case
from support.stage_run_support import BRANCH, pushed_state

WAITS = [timedelta(seconds=5), timedelta(seconds=15), timedelta(seconds=45)]


@pytest.fixture(params=["result", "record"])
def case(
    request: pytest.FixtureRequest,
    boundaries: Boundaries,
    *,
    tmp_path: Path,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    kill_points: KillPoints,
) -> PushCase:
    """A story opened at `tests`, ready to push its stage's result or a recorded change."""
    return open_push_case(
        request.param,
        boundaries,
        tmp_path=tmp_path,
        remote=remote,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        kill_points=kill_points,
    )


@pytest.mark.parametrize(
    ("failures", "tries", "waits", "fails"),
    [
        pytest.param(2, 3, WAITS[:2], False, id="refused-twice"),
        pytest.param(3, 4, WAITS, False, id="refused-three-times"),
        pytest.param(4, 4, WAITS, True, id="refused-four-times"),
    ],
)
def test_a_refused_push_is_retried_at_most_three_times(
    case: PushCase, failures: int, tries: int, waits: list[timedelta], *, fails: bool
) -> None:
    case.arm(failures)

    if fails:
        with pytest.raises(PushFailed) as raised:
            case.push()
        assert "[remote rejected]" in str(raised.value)
    else:
        case.push()
        assert pushed_state(case.boundaries, case.remote).crashes == 0

    assert len(case.git.pushes) == tries
    assert len(case.retry_lines()) == min(failures, 3)
    assert case.waiter.waits == waits


@pytest.mark.parametrize("failures", [2, 4])
def test_the_retried_push_is_the_same_push_of_the_same_head(case: PushCase, failures: int) -> None:
    case.arm(failures)

    with contextlib.suppress(PushFailed):
        case.push()

    branches = {branch for branch, _ in case.git.pushes}
    heads = {head for _, head in case.git.pushes}
    assert branches == {BRANCH}
    assert len(heads) == 1
    assert set(case.received_heads()) == heads
    assert len(case.received_heads()) == len(case.git.pushes)


@pytest.mark.parametrize("failures", [2, 4])
def test_each_retry_line_names_its_try_its_wait_and_gits_reason(
    case: PushCase, failures: int
) -> None:
    case.arm(failures)

    message: str | None
    try:
        case.push()
    except PushFailed as error:
        message = str(error)
    else:
        message = None

    retries = min(failures, 3)
    lines = case.retry_lines()
    assert len(lines) == retries
    for number, (line, wait) in enumerate(zip(lines, (5, 15, 45), strict=False), start=1):
        prefix = f"push: retry {number} of 3 in {wait} s: "
        assert line.startswith(prefix)
        reason = line.removeprefix(prefix)
        assert "[remote rejected]" in reason
        if message is not None:
            assert reason in message


@pytest.mark.parametrize("refusal", ["fetch first", "non-fast-forward"])
def test_a_push_behind_the_remote_fails_at_once_without_a_retry(
    case: PushCase, human: HumanClone, refusal: str
) -> None:
    human.push_file(BRANCH, "human.txt", "pushed by the human\n")
    if refusal == "non-fast-forward":
        case.git.fetch()
    case.git.pushes.clear()

    with pytest.raises(PushFailed) as raised:
        case.push()

    assert len(case.git.pushes) == 1
    assert case.waiter.waits == []
    assert case.retry_lines() == []
    message = str(raised.value)
    assert "[rejected]" in message
    assert refusal in message


def test_a_push_to_an_unreachable_remote_is_retried_and_names_gits_reason(
    case: PushCase,
) -> None:
    case.git.pushes.clear()
    case.remote.rename(case.remote.with_name("moved.git"))

    with pytest.raises(PushFailed) as raised:
        case.push()

    assert len(case.git.pushes) == 4
    assert case.waiter.waits == WAITS
    assert "does not appear to be a git repository" in str(raised.value)
