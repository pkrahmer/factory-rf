"""Stages on the `boundaries` fixture run in the container environment on its fakes."""

from collections.abc import Callable
from pathlib import Path

import pytest

from container_support import inline_boundaries, timing_lines
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.application.task import TaskComposer, TaskContext
from factory.domain.agent_runs import AgentDefinition, AgentRunResult
from factory.domain.journal import entry_text
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from probe_support import COMPLETED, ENVIRONMENT
from stage_run_support import (
    BRANCH,
    CREATED,
    CREATED_LINE,
    PATH,
    STORY,
    WORK_ITEM,
    completed,
    open_story,
    pushed,
    run_stage,
)

KEPT = "tests/test_new.py"
FORBIDDEN = "src/forbidden.py"
KEPT_TEXT = "def test_new() -> None:\n    assert True\n"
FORBIDDEN_TEXT = "FORBIDDEN = 1\n"
RESET_PREFIX = "stage environment: reset"


def _stage_request(
    boundaries: Boundaries, _settings: InstanceSettings, _: FakeAgentRuntime
) -> Path:
    context = TaskContext(
        work_item=WORK_ITEM,
        path=PATH,
        stage="tests",
        document=WorkItemDocument(
            state=WorkItemState(stage="tests", journal=[CREATED]), body=STORY + CREATED_LINE
        ),
        branch=BRANCH,
        pull_request=7,
        findings=[],
    )
    agent = AgentDefinition(
        name="tester", model="sonnet", tools=["Read"], budget_usd=1, instructions="Do the work."
    )
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    request = TaskComposer(boundaries, definition, ENVIRONMENT).compose(context, agent)
    return request.working_directory


def _probe_request(
    boundaries: Boundaries, settings: InstanceSettings, agent_runtime: FakeAgentRuntime
) -> Path:
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    agent_run_probe_item(boundaries, settings, ENVIRONMENT)
    [request] = agent_runtime.requests()
    return request.working_directory


RequestOf = Callable[[Boundaries, InstanceSettings, FakeAgentRuntime], Path]


@pytest.mark.parametrize("request_of", [_stage_request, _probe_request], ids=["stage", "probe"])
@pytest.mark.parametrize("with_snapshots", [True, False], ids=["snapshots", "no-snapshots"])
def test_the_request_works_in_the_datasets_checkout_when_the_boundaries_hold_snapshots(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    tmp_path: Path,
    request_of: RequestOf,
    with_snapshots: bool,
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])
    used = boundaries if with_snapshots else inline_boundaries(boundaries)
    expected = tmp_path / "workspace" / "checkout" if with_snapshots else boundaries.checkout

    assert request_of(used, probe_settings, agent_runtime) == expected


def test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(boundaries, human, agent_home)
    writes = {KEPT: KEPT_TEXT, FORBIDDEN: FORBIDDEN_TEXT}
    agent_runtime.queue(ScriptedRun(writes=writes, result=completed("doing")))

    report = run_stage(boundaries)

    git = boundaries.git
    assert git.show_file(report.commit, KEPT) == KEPT_TEXT
    assert git.show_file(report.commit, FORBIDDEN) is None
    document = pushed(boundaries, remote)
    assert document.state is not None
    [record] = [record for record in document.state.journal if record.speaker == "tester"]
    assert FORBIDDEN in entry_text(document, record.number).split("\n\n")[-1]
    texts = [line.split(" ", 1)[1] for line in timing_lines(boundaries)]
    assert len([text for text in texts if text.startswith(RESET_PREFIX)]) == 1
    assert git.status().changes == []
    assert (boundaries.checkout / KEPT).read_text(encoding="utf-8") == KEPT_TEXT
    assert not (boundaries.checkout / FORBIDDEN).exists()


def test_a_died_run_on_the_fixture_stalls_without_its_writes_outside_the_write_paths(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(boundaries, human, agent_home)
    died = AgentRunResult(end_reason="died", duration=COMPLETED.duration)
    agent_runtime.queue(ScriptedRun(writes={FORBIDDEN: FORBIDDEN_TEXT}, result=died))

    report = run_stage(boundaries)

    assert report.stall is not None
    assert boundaries.git.show_file(report.commit, FORBIDDEN) is None
    state = pushed(boundaries, remote).state
    assert state is not None
    assert (state.journal[-1].speaker, state.journal[-1].kind) == ("factory", "stall")
