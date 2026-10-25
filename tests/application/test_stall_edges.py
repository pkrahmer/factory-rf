"""The stalls at their edges: no detail, a commit before the agent left, a red check's files."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.journal import entry_text
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    INSIDE,
    NOTES,
    PATH,
    completed,
    open_story,
    run_stage,
)

ELSEWHERE = "elsewhere"


class CommitThenLeaveRuntime(AgentRuntime):
    """Commits a file on the work branch, checks out another branch, then delegates."""

    def __init__(self, delegate: FakeAgentRuntime, git: Git) -> None:
        """Run on `delegate`; commit and switch through `git`."""
        self._delegate = delegate
        self._git = git

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Commit `INSIDE`, switch to `ELSEWHERE` at `HEAD`, then let the delegate play."""
        target = request.working_directory / INSIDE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("written by the agent\n", encoding="utf-8")
        self._git.commit("the agent's commit")
        self._git.checkout(ELSEWHERE, start_point="HEAD")
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()


Setup = Callable[[Boundaries, HumanClone, Path, FakeAgentRuntime], Boundaries]


def _merge_conflict(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, _: FakeAgentRuntime
) -> Boundaries:
    open_story(boundaries, human, agent_home, main_files={NOTES: "base\n"})
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    boundaries.git.fetch()
    return boundaries


def _left_branch(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, agent_runtime: FakeAgentRuntime
) -> Boundaries:
    open_story(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=completed()))
    return replace(boundaries, agent_runtime=CommitThenLeaveRuntime(agent_runtime, boundaries.git))


@pytest.mark.parametrize(
    ("setup", "note", "entry"),
    [
        pytest.param(
            _merge_conflict,
            "Stalled (attempt 1 of 2): merging the main branch conflicts and the merge was"
            " aborted. Retrying on the next tick.",
            "Stage tests stalled (attempt 1 of 2): merging the main branch conflicts and the"
            " merge was aborted",
            id="merge-conflict",
        ),
        pytest.param(
            _left_branch,
            "Stalled (attempt 1 of 2): the agent left the work item's branch."
            " Retrying on the next tick.",
            "Stage tests stalled (attempt 1 of 2): the agent left the work item's branch",
            id="left-branch",
        ),
    ],
)
def test_a_stall_without_a_detail_says_only_its_reason(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    setup: Setup,
    note: str,
    entry: str,
) -> None:
    report = run_stage(setup(boundaries, human, agent_home, agent_runtime))

    [post] = hosting.factory_posts(report.pull_request)
    assert post.body.splitlines()[0] == note
    text = boundaries.git.show_file(report.commit, PATH)
    assert text is not None
    document = boundaries.work_item_reader.parse(text)
    assert document.state is not None
    assert entry_text(document, document.state.journal[-1].number) == entry


def test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    report = run_stage(_left_branch(boundaries, human, agent_home, agent_runtime))

    assert report.stall is not None
    assert report.stall.reason == "left_branch"
    log = boundaries.git.log(report.commit, since="origin/main")
    assert [commit.subject for commit in log] == [
        "work item F0001-S0001: tests stalled",
        "work item F0001-S0001: tests starts as factory-1",
        "write factory/features/F0001-example/in-progress/F0001-S0001-first.md",
    ]
    assert boundaries.git.show_file(report.commit, INSIDE) is None
