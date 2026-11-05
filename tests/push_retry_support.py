"""A push case: a story opened at `tests` and a remote whose hook refuses a number of pushes."""

import shlex
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.handlers.recording import WorkItemRecorder
from factory.application.stage import AfterAgent, AgentAftermath, StageFinisher, StageLauncher
from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.application.opening import WorkItemOpening
from factory.hosting.domain.git import CommitId, GitOptions, PushOutcome
from factory.shared.adapters.clock import ManualWaiter
from factory.shared.domain.kill_points import KillPoints
from factory.work.domain.journal import FACTORY, NewEntry, append_entry
from git_support import CHECKOUT, PIPELINE_YAML, TEST_IDENTITY
from human_clone import HumanClone
from recording_log import RecordingLog
from stage_run_support import BRANCH, ENVIRONMENT, INSTANCE, PATH, WORK_ITEM, completed, open_story

RETRY = "push: retry "


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


def result_push(boundaries: Boundaries, agent_runtime: FakeAgentRuntime) -> Callable[[], object]:
    """The call that finishes a stage of the opened story and pushes its result."""
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(ScriptedRun(result=completed("doing")))
    launched = StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT).launch(prepared)
    aftermath = AfterAgent(boundaries, INSTANCE, definition).process(launched)
    assert isinstance(aftermath, AgentAftermath)
    finisher = StageFinisher(boundaries, INSTANCE, definition)
    return lambda: finisher.finish(aftermath)


def record_push(boundaries: Boundaries) -> Callable[[], object]:
    """The call that publishes a change recorded on the opened story's branch."""
    recorder = WorkItemRecorder(boundaries)
    recorder.check_out(BRANCH)
    entry = NewEntry(speaker=FACTORY, kind="result", text="recorded")
    recorder.write(PATH, append_entry(recorder.read(PATH), entry))
    return lambda: recorder.publish(BRANCH, "the subject")


def open_push_case(
    kind: str,
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
    push = result_push(recording, agent_runtime) if kind == "result" else record_push(recording)
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
