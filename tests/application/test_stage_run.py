"""A whole stage run: prepare, claim, agent run, after the agent, decision, checks, result."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.domain.agent_runs import QUESTION, AgentRunRequest, AgentRunResult
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    ENVIRONMENT,
    NOTES,
    branch_head,
    completed,
    open_story,
    pushed_state,
    run_stage,
    stage_makefile,
)

BUILT = "build/out.txt"
IGNORED = "ignored/out.txt"


class HeadNotingRuntime(AgentRuntime):
    """Notes the head a run starts on, then delegates."""

    def __init__(self, delegate: FakeAgentRuntime, git: Git) -> None:
        """Run on `delegate`; read the head through `git`."""
        self._delegate = delegate
        self._git = git
        self.start_head: str | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Note the head, then let the delegate play."""
        self.start_head = self._git.status().head
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()


@pytest.mark.parametrize(
    ("decision", "statuses"),
    [("doing", {}), (QUESTION, {}), ("doing", {"lint": 1})],
    ids=["move", "question", "stall"],
)
def test_a_run_adds_exactly_one_commit_of_its_own(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    decision: str,
    statuses: dict[str, int],
) -> None:
    open_story(boundaries, human, agent_home, makefile=stage_makefile(statuses))
    agent_runtime.queue(ScriptedRun(result=completed(decision)))
    runtime = HeadNotingRuntime(agent_runtime, boundaries.git)

    report = run_stage(replace(boundaries, agent_runtime=runtime))

    base = runtime.start_head
    assert base is not None
    assert report.commit == branch_head(remote)
    [own] = boundaries.git.log(report.commit, since=base)
    assert own.parents == [base]


def test_the_result_commit_holds_what_a_check_created_unless_it_is_ignored(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    creates = [
        "@mkdir -p build ignored",
        f"@echo built > {BUILT}",
        f"@echo built > {IGNORED}",
    ]
    open_story(
        boundaries,
        human,
        agent_home,
        makefile=stage_makefile(extra=creates),
        main_files={".gitignore": "ignored/\n"},
    )
    agent_runtime.queue(ScriptedRun(result=completed("doing")))

    report = run_stage(boundaries)

    assert report.rule == 6
    assert report.commit == branch_head(remote)
    assert boundaries.git.show_file(report.commit, BUILT) == "built\n"
    assert boundaries.git.show_file(report.commit, IGNORED) is None


def test_a_branch_that_cannot_take_the_main_branch_stalls_before_the_claim(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = open_story(boundaries, human, agent_home, main_files={NOTES: "base\n"})
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    boundaries.git.fetch()

    report = run_stage(boundaries)

    state = pushed_state(boundaries, remote)
    assert report.rule is None
    assert report.stall is not None
    assert report.stall.reason == "merge_conflict"
    assert report.next_stage == report.stage == "tests"
    assert agent_runtime.requests() == []
    assert state.claim is None
    assert "started" not in [record.kind for record in state.journal]
    assert state.attempts == started.attempts + 1


def test_a_died_agent_run_ends_in_a_stall_report(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(
        ScriptedRun(result=AgentRunResult(end_reason="died", duration=timedelta(minutes=3)))
    )

    report = run_stage(boundaries)

    assert report.rule is None
    assert report.stall is not None
    assert report.stall.reason == "died"
    assert report.commit == report.stall.commit == branch_head(remote)


def test_the_agent_runs_with_exactly_the_environment_given_to_the_runner(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=completed("doing")))

    run_stage(boundaries)

    [request] = agent_runtime.requests()
    assert request.environment == ENVIRONMENT
