"""An acceptance runs its stage through the same stage protocol as a story."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.stage import StageReport, StageRunner
from factory.domain.acceptance import acceptance_description
from factory.domain.agent_runs import AgentRunResult
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemState
from git_support import install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
TODO = "factory/features/F0002-todo"
ACCEPTANCE = "F0002-A0001"
BRANCH = f"work-item/{ACCEPTANCE}"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}


@pytest.fixture
def report_path(
    boundaries: Boundaries, definition: PipelineDefinition, human: HumanClone, agent_home: Path
) -> str:
    """Push the feature `F0002-todo`, open its acceptance and return the report's path."""
    install_agents(agent_home, definition.roles)
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()
    return AcceptanceService(boundaries, definition).open("F0002").path


@pytest.fixture
def report(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    agent_runtime: FakeAgentRuntime,
    report_path: str,
) -> StageReport:
    """Run the acceptance's stage with the agent scripted to decide `approval`."""
    result = AgentRunResult(
        end_reason="completed",
        decision="approval",
        entry="the feature holds together.",
        duration=timedelta(minutes=1),
    )
    agent_runtime.queue(ScriptedRun(result=result))
    return StageRunner(boundaries, INSTANCE, definition, ENVIRONMENT).run(ACCEPTANCE, report_path)


def _pushed_state(boundaries: Boundaries, path: str) -> WorkItemState:
    boundaries.git.fetch()
    text = boundaries.git.show_file(f"origin/{BRANCH}", path)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    return state


def test_an_acceptance_reaches_approval_although_its_report_has_no_story_sections(
    boundaries: Boundaries, report: StageReport, report_path: str
) -> None:
    state = _pushed_state(boundaries, report_path)

    assert report.next_stage == "approval"
    assert report.rule == 6
    assert state.blocked is None
    assert "question" not in [record.kind for record in state.journal]


@pytest.mark.usefixtures("report")
def test_the_reviewer_prompt_ends_with_the_feature_facts_at_main(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    later = AcceptanceService(boundaries, definition).facts("F0002")
    facts = later.model_copy(update={"disk_before": None})

    prompt = agent_runtime.requests()[0].prompt

    assert prompt.split("\n")[-6:] == facts.lines()
    assert facts.lines()[-2:] == [
        f"Disk now: disk acceptance: {tmp_path} 1000.0 GB free, 0.0 GB used; "
        f"{tmp_path / 'state'} 1000.0 GB free, 0.0 GB used",
        "Disk at the previous record: none",
    ]


def test_the_protocol_opens_the_acceptance_pull_request_and_records_it(
    boundaries: Boundaries, report: StageReport, report_path: str, hosting: FakeHostingService
) -> None:
    state = _pushed_state(boundaries, report_path)

    [pull_request] = hosting.pull_requests()
    assert pull_request.title == "F0002-A0001: Acceptance of Todo service"
    assert pull_request.branch == BRANCH
    assert pull_request.draft
    assert pull_request.number == report.pull_request
    assert state.stage == "approval"
    assert state.pull_request == pull_request.number


def test_an_acceptance_that_ends_with_approval_has_its_report_in_the_description_at_once(
    boundaries: Boundaries, report: StageReport, report_path: str, hosting: FakeHostingService
) -> None:
    boundaries.git.fetch()
    text = boundaries.git.show_file(f"origin/{BRANCH}", report_path)
    assert text is not None
    document = boundaries.work_item_reader.parse(text)

    assert hosting.get_pull_request(report.pull_request).draft
    assert _pushed_state(boundaries, report_path).handed_over is None
    assert hosting.description(report.pull_request) == acceptance_description(
        document, "acceptance-reviewer"
    )
