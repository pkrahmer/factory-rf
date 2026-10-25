"""A stage whose agent leaves a git repository in the work tree ends as its decision says."""

from pathlib import Path

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.work_item import WorkItemState
from human_clone import HumanClone
from stage_run_support import CREATED, completed, open_story, pushed_state, run_stage


def test_a_nested_repository_left_by_the_agent_does_not_stall_the_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(
        boundaries,
        human,
        agent_home,
        state=WorkItemState(stage="intake", journal=[CREATED]),
        roles=("intake",),
    )
    agent_runtime.queue(
        ScriptedRun(writes={"sub/.git/HEAD": "ref: refs/heads/main\n"}, result=completed("tests"))
    )

    report = run_stage(boundaries)

    assert report.stall is None
    state = pushed_state(boundaries, remote)
    assert state.stage == "tests"
    last = state.journal[-1]
    assert (last.speaker, last.kind, last.stage) == ("intake", "result", "intake")
