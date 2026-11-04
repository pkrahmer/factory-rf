"""A refused or unreachable push of a stage's result or a recorded change is tried again."""

import contextlib
import shlex
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualWaiter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import WorkItemRecorder
from factory.application.opening import WorkItemOpening
from factory.application.stage import AfterAgent, AgentAftermath, StageFinisher, StageLauncher
from factory.domain.errors import PushFailed
from factory.domain.git import CommitId, GitOptions, PushOutcome
from factory.domain.journal import FACTORY, NewEntry, append_entry
from factory.domain.kill_points import KillPoints
from git_support import CHECKOUT, PIPELINE_YAML, TEST_IDENTITY
from human_clone import HumanClone
from recording_log import RecordingLog
from stage_run_support import (
    BRANCH,
    ENVIRONMENT,
    INSTANCE,
    PATH,
    WORK_ITEM,
    completed,
    open_story,
    pushed_state,
)

RETRY = "push: retry "
WAITS = [timedelta(seconds=5), timedelta(seconds=15), timedelta(seconds=45)]


class RecordingGit(GitCli):
    """The real git, which records each push's branch and the head it pushes."""

    def __init__(self, directory: Path, options: GitOptions) -> None:
        super().__init__(directory, options)
        self.pushes: list[tuple[str, CommitId | None]] = []

    def push(self, branch: str) -> PushOutcome:
        self.pushes.append((branch, self.resolve("HEAD")))
        return super().push(branch)


@dataclass
class PushCase:
    """One way to reach a push: the call that pushes and what the test reads afterwards."""

    push: Callable[[], object]
    git: RecordingGit
    log: RecordingLog
    waiter: ManualWaiter
    boundaries: Boundaries
    remote: Path
    received: Path

    def arm(self, failures: int) -> None:
        """Make the remote refuse the next `failures` pushes as a server error."""
        left = self.remote / "failures-left"
        left.write_text(f"{failures}\n", encoding="utf-8")
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text(
            "#!/bin/sh\n"
            f'while read old new ref; do echo "$new" >> {shlex.quote(str(self.received))}; done\n'
            f"left=$(cat {shlex.quote(str(left))})\n"
            'if [ "$left" -gt 0 ]; then\n'
            f"  echo $((left - 1)) > {shlex.quote(str(left))}\n"
            "  echo 'Internal Server Error' >&2\n"
            "  exit 1\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        self.git.pushes.clear()

    def retry_lines(self) -> list[str]:
        """The retry lines written so far."""
        return [line for line in self.log.lines if line.startswith(RETRY)]

    def received_heads(self) -> list[str]:
        """The commit ids the remote's hook was offered, one per try."""
        if not self.received.exists():
            return []
        return self.received.read_text(encoding="utf-8").split()


def _result_push(boundaries: Boundaries, agent_runtime: FakeAgentRuntime) -> Callable[[], object]:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(ScriptedRun(result=completed("doing")))
    launched = StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT).launch(prepared)
    aftermath = AfterAgent(boundaries, INSTANCE, definition).process(launched)
    assert isinstance(aftermath, AgentAftermath)
    finisher = StageFinisher(boundaries, INSTANCE, definition)
    return lambda: finisher.finish(aftermath)


def _record_push(boundaries: Boundaries) -> Callable[[], object]:
    recorder = WorkItemRecorder(boundaries)
    recorder.check_out(BRANCH)
    entry = NewEntry(speaker=FACTORY, kind="result", text="recorded")
    recorder.write(PATH, append_entry(recorder.read(PATH), entry))
    return lambda: recorder.publish(BRANCH, "the subject")


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
    options = GitOptions(kill_points=kill_points, identity=TEST_IDENTITY)
    git = RecordingGit(tmp_path / CHECKOUT, options)
    log = RecordingLog()
    recording = replace(boundaries, git=git, log=log)
    open_story(recording, human, agent_home)
    push = (
        _result_push(recording, agent_runtime)
        if request.param == "result"
        else _record_push(recording)
    )
    assert isinstance(recording.waiter, ManualWaiter)
    return PushCase(
        push=push,
        git=git,
        log=log,
        waiter=recording.waiter,
        boundaries=recording,
        remote=remote,
        received=tmp_path / "received-heads",
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
