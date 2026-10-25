"""The stall takes through its stage environment, handed over by each holder, inline by default."""

import ast
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import get_args, override

import pytest

import factory.application.stalls
from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.opening import WorkItemOpening
from factory.application.stage import AfterAgent, AgentAftermath, LaunchedStage, StageFinisher
from factory.application.stage_environment import StageEnvironment
from factory.application.stalls import StallContext, StallResult, StallService
from factory.application.take import TakeReport
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.decisions import StallReason
from factory.domain.errors import ContainerError, SnapshotError, WorkItemFormatError
from factory.domain.git import CommitId, WorkTreeStatus
from factory.domain.paths import cost_records_path
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemState
from git_support import install_agents, remote_commit
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    INSTANCE,
    PATH,
    WORK_ITEM,
    completed,
    open_story,
    stage_makefile,
)
from stall_support import (
    CREATED,
    DIED,
    SwitchingRuntime,
    launched_stage,
    open_work_item,
    stall_context,
    started_stage,
)

TAKEN = TakeReport(left=["src/b.py"], restored_work_item=False)


class TakingEnvironment(StageEnvironment):
    """Records each take with its arguments, does `on_take` inside it, and returns `TAKEN`."""

    def __init__(self, on_take: Callable[[], None] | None = None) -> None:
        self._on_take = on_take
        self.takes: list[tuple[StageStart, str]] = []

    @override
    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        raise AssertionError("a stall prepares nothing")

    @override
    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> AgentRunResult:
        raise AssertionError("a stall runs no agent")

    @override
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        self.takes.append((stage_start, work_item_path))
        if self._on_take is not None:
            self._on_take()
        return TAKEN


def _stall_through(
    boundaries: Boundaries,
    environment: StageEnvironment,
    context: StallContext,
    reason: StallReason = "died",
) -> StallResult:
    definition = pipeline_definition(boundaries)
    service = StallService(boundaries, INSTANCE, definition, stage_environment=environment)
    return service.stall(context, reason)


def _not_started(boundaries: Boundaries, human: HumanClone) -> StallContext:
    open_work_item(boundaries, human, WorkItemState(stage="tests", journal=[CREATED]))
    WorkItemOpening(boundaries, pipeline_definition(boundaries)).prepare(WORK_ITEM, PATH)
    return StallContext(
        work_item=WORK_ITEM, stage="tests", branch=BRANCH, path=PATH, stage_start=None
    )


@pytest.mark.parametrize("reason", get_args(StallReason))
def test_a_stall_with_a_stage_start_takes_once_through_its_environment_whatever_the_reason(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    reason: StallReason,
) -> None:
    environment = TakingEnvironment()
    if reason == "merge_conflict":
        context = _not_started(boundaries, human)
    else:
        started = started_stage(
            boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime
        )
        context = stall_context(started, pull_request=started.pull_request)

    result = _stall_through(boundaries, environment, context, reason)

    if context.stage_start is None:
        assert environment.takes == []
        assert result.take is None
    else:
        assert environment.takes == [(context.stage_start, PATH)]
        assert result.take == TAKEN


def test_the_stall_module_imports_no_name_of_the_undo() -> None:
    path = Path(factory.application.stalls.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)] + [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]

    assert "factory.application.undo" not in modules


@pytest.mark.parametrize("row", ["checkout-back-on-the-branch", "sidecar-after-the-take"])
def test_the_take_runs_after_the_checkout_is_back_and_before_the_sidecar_is_written(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    row: str,
) -> None:
    install_agents(agent_home, ["tester"])
    open_work_item(boundaries, human, WorkItemState(stage="tests", journal=[CREATED]))
    sidecar = cost_records_path(PATH)
    statuses: list[WorkTreeStatus] = []
    if row == "checkout-back-on-the-branch":
        runtime = SwitchingRuntime(
            agent_runtime, remote=remote, branch=BRANCH, hosting=hosting, checkout=boundaries.git
        )
        launched = launched_stage(boundaries, agent_runtime, ScriptedRun(result=DIED), runtime)
        environment = TakingEnvironment(lambda: statuses.append(boundaries.git.status()))
        context = stall_context(launched.started, pull_request=launched.started.pull_request)
        reason: StallReason = "left_branch"
    else:
        launched = launched_stage(boundaries, agent_runtime, ScriptedRun(result=DIED))
        environment = TakingEnvironment((boundaries.checkout / sidecar).unlink)
        context = stall_context(
            launched.started, pull_request=launched.started.pull_request
        ).model_copy(update={"cost": launched.cost})
        reason = "died"

    result = _stall_through(boundaries, environment, context, reason)

    if row == "checkout-back-on-the-branch":
        [status] = statuses
        assert status.branch == BRANCH
        assert status.head == launched.started.stage_start.commit
    else:
        text = boundaries.git.show_file(result.commit, sidecar)
        assert text is not None
        assert text.count(launched.cost.run) == 1


@pytest.mark.parametrize(
    "fault",
    [
        pytest.param(SnapshotError("changed_paths", "no base"), id="snapshot"),
        pytest.param(ContainerError("run", "no podman"), id="container"),
        pytest.param(WorkItemFormatError("missing", PATH), id="work-item-format"),
    ],
)
def test_a_fault_of_the_take_ends_the_stall_before_anything_is_written_or_said(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    fault: Exception,
) -> None:
    started = started_stage(
        boundaries, human=human, agent_home=agent_home, agent_runtime=agent_runtime
    )
    number = started.pull_request.number
    before = (boundaries.checkout / PATH).read_text(encoding="utf-8")
    labels = hosting.labels(number)

    def refuse() -> None:
        raise fault

    with pytest.raises(type(fault)) as raised:
        _stall_through(
            boundaries,
            TakingEnvironment(refuse),
            stall_context(started, pull_request=started.pull_request),
        )

    assert raised.value is fault
    assert (boundaries.checkout / PATH).read_text(encoding="utf-8") == before
    assert remote_commit(remote, BRANCH) == started.stage_start.commit
    assert hosting.factory_posts(number) == []
    assert hosting.labels(number) == labels


def _finish(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    environment: StageEnvironment,
    launched: LaunchedStage,
) -> StallResult | None:
    aftermath = AfterAgent(boundaries, INSTANCE, definition).process(launched)
    assert isinstance(aftermath, AgentAftermath)
    finisher = StageFinisher(boundaries, INSTANCE, definition, stage_environment=environment)
    return finisher.finish(aftermath).stall


def _process(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    environment: StageEnvironment,
    launched: LaunchedStage,
) -> StallResult | None:
    after = AfterAgent(boundaries, INSTANCE, definition, stage_environment=environment)
    processed = after.process(launched)
    assert isinstance(processed, StallResult)
    return processed


Holder = Callable[
    [Boundaries, PipelineDefinition, StageEnvironment, LaunchedStage], StallResult | None
]


@pytest.mark.parametrize(
    ("result", "holder"),
    [
        pytest.param(completed("doing"), _finish, id="finisher-red-check"),
        pytest.param(DIED, _process, id="after-agent-early-stall"),
    ],
)
def test_each_holder_hands_its_environment_to_its_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    result: AgentRunResult,
    holder: Holder,
) -> None:
    open_story(boundaries, human, agent_home, makefile=stage_makefile({"lint": 1}))
    launched = launched_stage(boundaries, agent_runtime, ScriptedRun(result=result))
    environment = TakingEnvironment()

    stall = holder(boundaries, pipeline_definition(boundaries), environment, launched)

    assert environment.takes == [(launched.started.stage_start, PATH)]
    assert stall is not None
    assert stall.take == TAKEN
