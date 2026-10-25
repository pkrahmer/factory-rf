"""A stage's request and the probe's work in the dataset's checkout."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.application.task import TaskComposer, TaskContext
from factory.domain.agent_runs import AgentDefinition
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents
from probe_support import COMPLETED, ENVIRONMENT
from stage_run_support import BRANCH, CREATED, CREATED_LINE, PATH, STORY, WORK_ITEM


def _stage_request(
    boundaries: Boundaries, _settings: InstanceSettings, _runtime: FakeAgentRuntime
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
    return (
        TaskComposer(boundaries, definition, ENVIRONMENT).compose(context, agent).working_directory
    )


def _probe_request(
    boundaries: Boundaries, settings: InstanceSettings, runtime: FakeAgentRuntime
) -> Path:
    runtime.queue(ScriptedRun(result=COMPLETED))
    agent_run_probe_item(boundaries, settings, ENVIRONMENT)
    [request] = runtime.requests()
    return request.working_directory


@pytest.mark.parametrize("request_of", [_stage_request, _probe_request], ids=["stage", "probe"])
def test_the_request_works_in_the_dataset_s_checkout(
    boundaries: Boundaries,
    probe_settings: InstanceSettings,
    *,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    request_of: Callable[[Boundaries, InstanceSettings, FakeAgentRuntime], Path],
) -> None:
    install_agents(agent_home, ["intake", "coder", "reviewer"])

    found = request_of(boundaries, probe_settings, agent_runtime)

    assert found == boundaries.snapshots.mount_point / "checkout"
