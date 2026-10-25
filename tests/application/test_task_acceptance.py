"""The story form check and the composed prompt of an acceptance, beside those of a story."""

from pathlib import Path

import pytest

from factory.application.acceptance import AcceptanceService
from factory.application.boundaries import Boundaries
from factory.application.task import StoryFormChecker, TaskComposer, TaskContext
from factory.domain.acceptance import AcceptanceState, acceptance_prompt
from factory.domain.agent_runs import AgentDefinition
from factory.domain.errors import WorkItemFormatError
from factory.domain.paths import STORY_FORM_FILE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.prompts import PromptFacts, allowed_decisions, compose_prompt
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import run_git
from human_clone import HumanClone

TODO = "factory/features/F0002-todo"
ACCEPTANCE = "F0002-A0001"
REPORT = f"{TODO}/in-progress/F0002-A0001-acceptance.md"
STORY_ID = "F0001-S0002"
STORY_PATH = "factory/features/F0001-example/in-progress/F0001-S0002-second.md"
REPORT_BODY = "# Acceptance of Todo service\n\n## Journal\n"
ENVIRONMENT = {"PATH": "/opt/guard", "HOME": "/home/factory"}
FACT_PREFIX = "Archived stories:"


@pytest.fixture
def todo(boundaries: Boundaries, human: HumanClone) -> None:
    """Push the feature `F0002-todo` with two archived stories to `main` and fetch."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")
    boundaries.git.fetch()


def _document(acceptance: bool, stage: str = "acceptance") -> WorkItemDocument:
    state = AcceptanceState(stage=stage) if acceptance else WorkItemState(stage=stage)
    return WorkItemDocument(state=state, body=REPORT_BODY)


def _context(stage: str, *, acceptance: bool) -> TaskContext:
    work_item = ACCEPTANCE if acceptance else STORY_ID
    return TaskContext(
        work_item=work_item,
        path=REPORT if acceptance else STORY_PATH,
        stage=stage,
        document=_document(acceptance, stage),
        branch=f"work-item/{work_item}",
        pull_request=7,
        findings=[],
    )


def _agent() -> AgentDefinition:
    return AgentDefinition(
        name="acceptance-reviewer",
        model="sonnet",
        tools=["Read"],
        budget_usd=1,
        instructions="Do the work.",
    )


def _base_prompt(definition: PipelineDefinition, context: TaskContext) -> str:
    facts = PromptFacts(
        work_item=context.work_item,
        path=context.path,
        stage=context.stage,
        allowed_decisions=allowed_decisions(definition.stages[context.stage].next),
        branch=context.branch,
        pull_request=context.pull_request,
        round=0,
        findings=[] if context.stage == definition.first_stage() else None,
    )
    return compose_prompt(facts)


def _compose(boundaries: Boundaries, definition: PipelineDefinition, context: TaskContext) -> str:
    return TaskComposer(boundaries, definition, ENVIRONMENT).compose(context, _agent()).prompt


def _remove_form_at_main(boundaries: Boundaries, tmp_path: Path) -> None:
    directory = tmp_path / "human"
    run_git(directory, "rm", "-q", STORY_FORM_FILE)
    run_git(directory, "commit", "-q", "-m", "remove the story form")
    run_git(directory, "push", "-q", "origin", "main")
    boundaries.git.fetch()


@pytest.mark.parametrize("acceptance", [True, False], ids=["acceptance-state", "plain-state"])
def test_only_an_acceptance_report_meets_the_story_form_without_its_sections(
    boundaries: Boundaries, acceptance: bool
) -> None:
    findings = StoryFormChecker(boundaries).findings(_document(acceptance))

    assert (findings == []) is acceptance


@pytest.mark.usefixtures("human")
@pytest.mark.parametrize("acceptance", [True, False], ids=["acceptance-state", "plain-state"])
def test_a_missing_story_form_is_an_error_only_for_a_story(
    boundaries: Boundaries, tmp_path: Path, acceptance: bool
) -> None:
    _remove_form_at_main(boundaries, tmp_path)
    checker = StoryFormChecker(boundaries)

    if acceptance:
        assert checker.findings(_document(acceptance)) == []
    else:
        with pytest.raises(WorkItemFormatError):
            checker.findings(_document(acceptance))


@pytest.mark.usefixtures("todo")
def test_an_acceptance_at_the_acceptance_stage_gets_the_feature_facts_appended(
    boundaries: Boundaries, definition: PipelineDefinition, tmp_path: Path
) -> None:
    context = _context("acceptance", acceptance=True)

    prompt = _compose(boundaries, definition, context)

    later = AcceptanceService(boundaries, definition).facts("F0002")
    facts = later.model_copy(update={"disk_before": None})
    assert prompt == acceptance_prompt(_base_prompt(definition, context), facts)
    assert prompt.split("\n")[-7:] == ["", *facts.lines()]
    assert facts.lines()[-2:] == [
        f"Disk now: disk acceptance: {tmp_path} 1000.0 GB free, 0.0 GB used; "
        f"{tmp_path / 'state'} 1000.0 GB free, 0.0 GB used",
        "Disk at the previous record: none",
    ]


@pytest.mark.usefixtures("todo")
@pytest.mark.parametrize(
    ("stage", "acceptance"),
    [("acceptance", False), ("intake", False), ("review", True)],
    ids=["story-at-acceptance", "story-at-intake", "acceptance-at-review"],
)
def test_no_facts_are_appended_off_the_acceptance_stage_or_for_a_story(
    boundaries: Boundaries,
    definition: PipelineDefinition,
    *,
    stage: str,
    acceptance: bool,
) -> None:
    context = _context(stage, acceptance=acceptance)

    prompt = _compose(boundaries, definition, context)

    assert [line for line in prompt.split("\n") if line.startswith(FACT_PREFIX)] == []


@pytest.mark.usefixtures("todo")
@pytest.mark.parametrize("acceptance", [True, False], ids=["acceptance", "story"])
def test_without_an_acceptance_stage_the_prompt_is_unchanged(
    boundaries: Boundaries, definition: PipelineDefinition, acceptance: bool
) -> None:
    without = definition.model_copy(update={"acceptance_stage": None})
    context = _context("acceptance", acceptance=acceptance)

    prompt = _compose(boundaries, without, context)

    assert prompt == _base_prompt(without, context)
