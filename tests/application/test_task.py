"""The agent of a stage, the request composed for its run and the story form checked at main."""

from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.task import StoryFormChecker, TaskComposer, TaskContext
from factory.domain.agent_runs import AgentDefinition
from factory.domain.errors import AgentDefinitionMissing, WorkItemFormatError
from factory.domain.journal import JournalKind, JournalRecord
from factory.domain.paths import STORY_FORM_FILE
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.prompts import PromptFacts, allowed_decisions, compose_prompt
from factory.domain.story_form import FormFinding
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import CHECKOUT, PIPELINE_YAML, STORY_FORM, install_agents, run_git, write_files
from human_clone import HumanClone

PATH = "factory/features/F0001-example/in-progress/F0001-S0002-second.md"
ROLES = ["intake", "tester", "coder"]
ENVIRONMENT = {"PATH": "/opt/guard", "HOME": "/home/factory"}
FINDINGS = [FormFinding(line=None, message="a"), FormFinding(line=None, message="b")]
FORMAT_LINE = "Format check found: 1. a 2. b"
MODE_LINE_5 = "Mode: a test change the human approved; the coder's journal entry 5 names it."
STORY = """\
# Second story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.

## Journal

1. 2026-10-12 human: created.
"""
WITHOUT_SMOKE_TEST = STORY.replace("## Smoke test\n\n```bash\ntrue\n```\nExpect: nothing.\n\n", "")

Entry = tuple[str, JournalKind, str]


def _definition(text: str = PIPELINE_YAML) -> PipelineDefinition:
    return RuamelPipelineDefinitionReader().parse(text)


def _document(entries: list[Entry], round_: int = 0) -> WorkItemDocument:
    records = [
        JournalRecord(number=number, speaker=speaker, kind=kind)
        for number, (speaker, kind, _) in enumerate(entries, start=1)
    ]
    lines = [
        f"{number}. {speaker}: {text}" for number, (speaker, _, text) in enumerate(entries, start=1)
    ]
    body = STORY.partition("## Journal\n")[0] + "## Journal\n\n" + "\n".join(lines) + "\n"
    state = WorkItemState(stage="intake", round=round_, journal=records)
    return WorkItemDocument(state=state, body=body)


CREATED: list[Entry] = [("human", "created", "created."), ("factory", "started", "started.")]
CODER_RESULT_5: list[Entry] = [
    *CREATED,
    ("intake", "result", "accepted."),
    ("tester", "result", "tests written."),
    ("coder", "result", "the test is wrong; the human approved a change."),
]


def _context(
    stage: str,
    *,
    document: WorkItemDocument | None = None,
    findings: list[FormFinding] | None = None,
) -> TaskContext:
    return TaskContext(
        work_item="F0001-S0002",
        path=PATH,
        stage=stage,
        document=document or _document(CREATED),
        branch="work-item/F0001-S0002",
        pull_request=7,
        findings=FINDINGS if findings is None else findings,
    )


def _agent(name: str = "tester") -> AgentDefinition:
    return AgentDefinition(
        name=name, model="sonnet", tools=["Read"], budget_usd=1, instructions="Do the work."
    )


def _composer(boundaries: Boundaries, definition: PipelineDefinition | None = None) -> TaskComposer:
    return TaskComposer(boundaries, definition or _definition(), ENVIRONMENT)


def _prompt_lines(boundaries: Boundaries, stage: str, entries: list[Entry]) -> list[str]:
    context = _context(stage, document=_document(entries))
    return _composer(boundaries).compose(context, _agent()).prompt.split("\n")


def _mode_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith("Mode:")]


def _story_document(body: str = STORY) -> WorkItemDocument:
    state = WorkItemState(
        stage="intake", journal=[JournalRecord(number=1, speaker="human", kind="created")]
    )
    return WorkItemDocument(state=state, body=body)


def _push_form(human: HumanClone, boundaries: Boundaries, text: str) -> None:
    human.push_file("main", STORY_FORM_FILE, text)
    boundaries.git.fetch()


def test_the_first_stage_gets_the_findings_and_a_later_stage_does_not(
    boundaries: Boundaries,
) -> None:
    composer = _composer(boundaries)

    first = composer.compose(_context("intake"), _agent("intake")).prompt.split("\n")
    later = composer.compose(_context("doing"), _agent("coder")).prompt.split("\n")

    assert FORMAT_LINE in first
    assert not [line for line in later if line.startswith("Format check")]


def test_the_tester_gets_the_mode_line_after_a_coder_result(boundaries: Boundaries) -> None:
    lines = _prompt_lines(boundaries, "tests", CODER_RESULT_5)

    assert _mode_lines(lines) == [MODE_LINE_5]


@pytest.mark.parametrize(
    ("stage", "entries"),
    [
        (
            "tests",
            [
                *CREATED,
                ("coder", "result", "done."),
                ("tester", "result", "coder: the test change is made."),
            ],
        ),
        ("tests", CREATED),
        ("doing", CODER_RESULT_5),
    ],
    ids=["tester-speaks-last", "no-result-record", "coder-stage"],
)
def test_the_mode_line_comes_only_from_a_coder_result_at_a_tester_stage(
    boundaries: Boundaries, stage: str, entries: list[Entry]
) -> None:
    lines = _prompt_lines(boundaries, stage, entries)

    assert _mode_lines(lines) == []


def test_a_later_stall_and_comment_do_not_hide_the_test_change(boundaries: Boundaries) -> None:
    entries: list[Entry] = [
        *CODER_RESULT_5,
        ("factory", "stall", "the tester stalled."),
        ("human", "comment", "please hurry."),
    ]

    lines = _prompt_lines(boundaries, "tests", entries)

    assert _mode_lines(lines) == [MODE_LINE_5]


def test_the_request_shares_the_allowed_decisions_and_the_facts_of_the_context(
    boundaries: Boundaries,
) -> None:
    context = _context("doing", document=_document(CREATED, round_=2))

    request = _composer(boundaries).compose(context, _agent("coder"))

    decisions = allowed_decisions(["review", "tests"])
    facts = PromptFacts(
        work_item="F0001-S0002",
        path=PATH,
        stage="doing",
        allowed_decisions=decisions,
        branch="work-item/F0001-S0002",
        pull_request=7,
        round=2,
    )
    assert request.allowed_decisions == decisions
    assert request.prompt == compose_prompt(facts)
    lines = request.prompt.split("\n")
    assert "Round: 2" in lines
    assert f"Allowed decisions: {', '.join(decisions)}" in lines


@pytest.mark.parametrize(
    ("stage", "minutes"),
    [("tests", 25), ("doing", 40)],
    ids=["role-sets-25", "role-sets-none"],
)
def test_the_time_limit_is_the_roles_minutes(
    boundaries: Boundaries, stage: str, minutes: int
) -> None:
    text = PIPELINE_YAML.replace(
        'tester: {write_paths: ["tests/*"]}', 'tester: {write_paths: ["tests/*"], time_limit: 25}'
    )
    composer = _composer(boundaries, _definition(text))

    request = composer.compose(_context(stage), _agent())

    assert request.time_limit == timedelta(minutes=minutes)


def test_the_request_carries_the_agent_checkout_and_guard_without_os_user(
    boundaries: Boundaries,
) -> None:
    agent = _agent()
    context = _context("tests")

    request = _composer(boundaries).compose(context, agent)

    assert request.agent == agent
    assert request.working_directory == boundaries.checkout


def test_the_request_holds_the_given_environment_unchanged(boundaries: Boundaries) -> None:
    request = _composer(boundaries).compose(_context("tests"), _agent())

    assert request.environment == {"PATH": "/opt/guard", "HOME": "/home/factory"}


def test_agent_reads_the_definition_of_the_stages_role(
    boundaries: Boundaries, agent_home: Path
) -> None:
    install_agents(agent_home, ROLES)

    agent = _composer(boundaries).agent("tests")

    assert agent.name == "tester"
    assert agent == boundaries.agent_definitions.read("tester")


def test_agent_for_a_stage_without_a_role_names_the_stage(
    boundaries: Boundaries, agent_home: Path
) -> None:
    install_agents(agent_home, ROLES)

    with pytest.raises(ValueError, match="approval"):
        _composer(boundaries).agent("approval")


def test_agent_for_a_role_without_an_agent_file_is_missing(
    boundaries: Boundaries, agent_home: Path
) -> None:
    install_agents(agent_home, ROLES)

    with pytest.raises(AgentDefinitionMissing) as caught:
        _composer(boundaries).agent("review")

    assert caught.value.name == "reviewer"


@pytest.mark.parametrize(
    ("body", "complete"),
    [(STORY, True), (WITHOUT_SMOKE_TEST, False)],
    ids=["complete", "without-smoke-test"],
)
def test_the_form_check_finds_nothing_only_in_a_complete_story(
    boundaries: Boundaries, body: str, complete: bool
) -> None:
    findings = StoryFormChecker(boundaries).findings(_story_document(body))

    assert (findings == []) is complete


def test_the_form_is_read_at_main_on_the_remote_not_in_the_work_tree(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path
) -> None:
    checker = StoryFormChecker(boundaries)
    longer = STORY_FORM + "\n## Risks\n"
    write_files(tmp_path / CHECKOUT, {STORY_FORM_FILE: longer})

    in_work_tree = checker.findings(_story_document())
    _push_form(human, boundaries, longer)
    at_main = checker.findings(_story_document())

    assert in_work_tree == []
    assert [finding.message for finding in at_main] == ["missing section: ## Risks"]


@pytest.mark.usefixtures("human")
def test_a_form_absent_at_main_is_a_format_error(boundaries: Boundaries, tmp_path: Path) -> None:
    directory = tmp_path / "human"
    run_git(directory, "rm", "-q", STORY_FORM_FILE)
    run_git(directory, "commit", "-q", "-m", "remove the story form")
    run_git(directory, "push", "-q", "origin", "main")
    boundaries.git.fetch()

    with pytest.raises(WorkItemFormatError) as caught:
        StoryFormChecker(boundaries).findings(_story_document())

    assert caught.value.path == "factory/story-form.md"


def _context_values() -> dict[str, Any]:
    return {
        "work_item": "F0001-S0002",
        "path": PATH,
        "stage": "tests",
        "document": _document(CREATED),
        "branch": "work-item/F0001-S0002",
        "pull_request": 7,
        "findings": [],
    }


@pytest.mark.parametrize(("pull_request", "accepted"), [(1, True), (0, False)])
def test_task_context_holds_the_pull_request_limit_on_both_sides(
    pull_request: int, accepted: bool
) -> None:
    values = {**_context_values(), "pull_request": pull_request}

    if accepted:
        assert TaskContext.model_validate(values).pull_request == pull_request
    else:
        with pytest.raises(ValidationError):
            TaskContext.model_validate(values)
