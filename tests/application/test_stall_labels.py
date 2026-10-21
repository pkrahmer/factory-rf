"""What a stall leaves on the pull request: the red check's output fenced, and the stage label."""

from datetime import timedelta
from pathlib import Path

import pytest

from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.opening import PreparedWorkItem, WorkItemOpening
from factory.application.stage import StageReport, StageRunner
from factory.application.stalls import StallContext, StallResult, StallService
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import HostingServiceError
from factory.domain.hosting import PostKey
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import install_agents
from human_clone import HumanClone
from stage_run_support import pushed, pushed_state

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
NOTES = "notes.md"
STORY = """\
# First story

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
"""
CREATED = JournalRecord(number=1, speaker="human", kind="created")
CREATED_LINE = "\n1. 2026-10-12 human: created.\n"
PRINTED = [f"line {number}" for number in range(1, 21)]
DIED = AgentRunResult(end_reason="died", duration=timedelta(minutes=3))
RETRYING = "Retrying on the next tick."


def _makefile(check_lines: list[str], check_status: int) -> str:
    names = ["lint", "check", "test"]
    targets = []
    for name in names:
        lines = check_lines if name == "check" else []
        status = check_status if name == "check" else 0
        recipe = [*(f"@echo '{line}'" for line in lines), f"@exit {status}"]
        targets.append(f"{name}:\n" + "".join(f"\t{line}\n" for line in recipe))
    return f".PHONY: {' '.join(names)}\n\n" + "\n".join(targets)


def _open_existing(
    boundaries: Boundaries,
    human: HumanClone,
    *,
    stage: str,
    main_files: dict[str, str] | None = None,
) -> None:
    """Start the story on `main` and push its branch with a document in `stage`, then fetch."""
    for path, text in (main_files or {}).items():
        human.push_file("main", path, text)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(
        state=WorkItemState(stage=stage, journal=[CREATED]), body=STORY + CREATED_LINE
    )
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()


def _open_new(boundaries: Boundaries, human: HumanClone) -> None:
    """Start the story on `main` only: the factory has not opened it yet."""
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    boundaries.git.fetch()


def _run(boundaries: Boundaries) -> StageReport:
    return StageRunner(boundaries, INSTANCE, pipeline_definition(boundaries), ENVIRONMENT).run(
        WORK_ITEM, PATH
    )


def _prepare_new(boundaries: Boundaries, human: HumanClone) -> PreparedWorkItem:
    _open_new(boundaries, human)
    return WorkItemOpening(boundaries, pipeline_definition(boundaries)).prepare(WORK_ITEM, PATH)


def _first_stage_context(prepared: PreparedWorkItem, **changes: object) -> StallContext:
    context = StallContext(
        work_item=WORK_ITEM,
        stage="intake",
        branch=prepared.branch,
        path=PATH,
        stage_start=None,
        document=prepared.document,
    )
    return context.model_copy(update=changes)


def _stall(boundaries: Boundaries, context: StallContext) -> StallResult:
    return StallService(boundaries, INSTANCE, pipeline_definition(boundaries)).stall(
        context, "died"
    )


def _block(note: str) -> tuple[str, list[str]]:
    """The note's sentence line and the lines inside its fenced block."""
    lines = note.split("\n")
    [sentence] = [line for line in lines if line.startswith("Stalled (")]
    opening = lines.index("```text")
    closing = lines.index("```", opening + 1)
    return sentence, lines[opening + 1 : closing]


def test_a_red_check_through_the_stage_runner_posts_its_tail_in_a_block(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    remote: Path,
) -> None:
    install_agents(agent_home, ["coder"])
    _open_existing(boundaries, human, stage="doing", main_files={"Makefile": _makefile(PRINTED, 1)})
    completed = AgentRunResult(
        end_reason="completed", decision="review", entry="done.", duration=timedelta(minutes=1)
    )
    agent_runtime.queue(ScriptedRun(result=completed))

    report = _run(boundaries)

    assert report.stall is not None
    assert report.stall.reason == "check_red"
    [post] = hosting.factory_posts(report.pull_request)
    sentence, block = _block(post.body)
    assert sentence.endswith(RETRYING)
    assert block[:-1] == PRINTED[6:]
    assert block[-1].startswith("make: ")
    assert "check] Error 1" in block[-1]
    assert "line 6" not in block
    document = pushed(boundaries, remote)
    assert document.state is not None
    assert document.state.journal[-1].kind == "stall"
    journal_text = entry_text(document, document.state.journal[-1].number)
    assert "line 20" in journal_text
    assert "check] Error 1" in journal_text


def test_a_new_work_item_whose_first_stage_stalls_gets_its_stage_label(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ["intake"])
    _open_new(boundaries, human)
    agent_runtime.queue(ScriptedRun(result=DIED))

    report = _run(boundaries)

    assert report.stall is not None
    assert report.stall.reason == "died"
    assert hosting.labels(report.pull_request) == ["stage:intake"]


def test_a_merge_conflict_stall_leaves_the_label_of_its_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    hosting: FakeHostingService,
) -> None:
    install_agents(agent_home, ["coder"])
    _open_existing(boundaries, human, stage="doing", main_files={NOTES: "base\n"})
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    boundaries.git.fetch()

    report = _run(boundaries)

    assert report.stall is not None
    assert report.stall.reason == "merge_conflict"
    assert hosting.labels(report.pull_request) == ["stage:doing"]


def test_a_note_already_posted_still_gets_the_label_written(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
) -> None:
    prepared = _prepare_new(boundaries, human)
    pull_request = WorkItemOpening(boundaries, pipeline_definition(boundaries)).ensure_pull_request(
        WORK_ITEM, prepared.document
    )
    state = prepared.document.state
    assert state is not None
    key = PostKey(work_item=WORK_ITEM, kind="stall", n=str(len(state.journal) + 1))
    hosting.post_comment(pull_request.number, "the note, posted before.", key)

    result = _stall(boundaries, _first_stage_context(prepared, pull_request=pull_request))

    assert result.note == "already_posted"
    assert hosting.labels(pull_request.number) == ["stage:intake"]


def test_a_failing_label_write_raises_after_the_stall_is_pushed_and_said(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    remote: Path,
) -> None:
    prepared = _prepare_new(boundaries, human)
    hosting.fail_next("set_labels")

    with pytest.raises(HostingServiceError):
        _stall(boundaries, _first_stage_context(prepared))

    state = pushed_state(boundaries, remote)
    assert state.attempts == 1
    assert state.journal[-1].kind == "stall"
    [pull] = hosting.pull_requests()
    assert len(hosting.factory_posts(pull.number)) == 1


def test_a_failing_note_writes_no_label(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
) -> None:
    prepared = _prepare_new(boundaries, human)
    hosting.fail_next("post_comment")

    with pytest.raises(HostingServiceError):
        _stall(boundaries, _first_stage_context(prepared))

    [pull] = hosting.pull_requests()
    assert hosting.labels(pull.number) == []
