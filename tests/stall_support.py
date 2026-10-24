"""Shared helpers of the stall tests: a work item opened on its branch, a launch and a context."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.stage import LaunchedStage, StageLauncher, StartedStage
from factory.application.stalls import StallContext
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.git import CommitId
from factory.domain.hosting import PullRequestView
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import install_agents
from human_clone import HumanClone
from observing_runtime import ObservingRuntime
from stage_run_support import BACKLOG_PATH, BRANCH, ENVIRONMENT, INSIDE, INSTANCE, PATH, WORK_ITEM
from take_support import AGENT_TEXT

ELSEWHERE = "elsewhere"
STORY = "# First story\n\n## Description\n\nText.\n\n## Journal\n"
BRANCH_BODY = STORY + "\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker="human", kind="created")
OUTSIDE = "src/b.py"
COMMITTED_ELSEWHERE = "tests/test_elsewhere.py"
WRITES = {INSIDE: AGENT_TEXT, OUTSIDE: AGENT_TEXT}
DIED = AgentRunResult(end_reason="died", duration=timedelta(minutes=3))


class SwitchingRuntime(ObservingRuntime):
    """Commits on another branch and leaves the checkout there, then lets the delegate play."""

    elsewhere_head: CommitId | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Switch to `ELSEWHERE`, commit a file there, then play the scripted run on it."""
        self._checkout.checkout(ELSEWHERE, start_point="HEAD")
        target = request.working_directory / COMMITTED_ELSEWHERE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(AGENT_TEXT, encoding="utf-8")
        self.elsewhere_head = self._checkout.commit("the agent's commit elsewhere")
        return super().run(request)


def open_work_item(boundaries: Boundaries, human: HumanClone, state: WorkItemState) -> None:
    """Start the story on `main` and push its branch with a document in `state`, then fetch."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(state=state, body=BRANCH_BODY)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()


def launched_stage(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    run: ScriptedRun,
    runtime: AgentRuntime | None = None,
) -> LaunchedStage:
    """Prepare the opened work item and launch its stage with `run` queued, through `runtime`."""
    definition = pipeline_definition(boundaries)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(run)
    used = boundaries if runtime is None else replace(boundaries, agent_runtime=runtime)
    return StageLauncher(used, INSTANCE, definition, ENVIRONMENT).launch(prepared)


def launch_stage(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    run: ScriptedRun,
    runtime: AgentRuntime | None = None,
) -> StartedStage:
    """The started stage of `launched_stage`."""
    return launched_stage(boundaries, agent_runtime, run, runtime).started


def started_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    state: WorkItemState | None = None,
    run: ScriptedRun | None = None,
) -> StartedStage:
    """Open the work item in stage `tests` and launch it with `run`, by default a death."""
    install_agents(agent_home, ["tester"])
    open_work_item(boundaries, human, state or WorkItemState(stage="tests", journal=[CREATED]))
    return launch_stage(boundaries, agent_runtime, run or ScriptedRun(writes=WRITES, result=DIED))


def stall_context(
    started: StartedStage,
    *,
    pull_request: PullRequestView | None = None,
    document: WorkItemDocument | None = None,
) -> StallContext:
    """The stall context of `started`, with `pull_request` and `document` as given."""
    return StallContext(
        work_item=started.work_item,
        stage=started.stage,
        branch=started.branch,
        path=started.path,
        stage_start=started.stage_start,
        document=document,
        pull_request=pull_request,
    )
