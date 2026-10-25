"""Builders for whole stage runs: a story started on `main`, its branch, a Makefile and a run."""

from datetime import timedelta
from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.application.stage import StageReport, StageRunner
from factory.domain.agent_runs import AgentRunResult
from factory.domain.git import CommitId
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, SYNC_TARGET, install_agents, remote_commit
from human_clone import HumanClone

INSTANCE = "factory-1"
INSIDE = "tests/test_a.py"
NOTES = "notes.md"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
SMOKE_TEST_SECTION = """\
## Smoke test

```bash
true
```
Expect: nothing.

"""
STORY = f"""\
# First story

## Description

Text.

## Interface

None.

## Acceptance criteria

1. It works.
2. make check stays green.
3. docs: none, nothing changes.

{SMOKE_TEST_SECTION}## Journal
"""
WITHOUT_SMOKE_TEST = STORY.replace(SMOKE_TEST_SECTION, "")
CREATED = JournalRecord(number=1, speaker="human", kind="created")
CREATED_LINE = "\n1. 2026-10-12 human: created.\n"


def _target(name: str, status: int, extra: list[str]) -> str:
    recipe = [*extra, f"@echo '{name} done'", f"@exit {status}"]
    return f"{name}:\n" + "".join(f"\t{line}\n" for line in recipe)


def stage_makefile(statuses: dict[str, int] | None = None, extra: list[str] | None = None) -> str:
    """A Makefile whose `lint`, `check` and `test` print a line and exit, and a silent `sync`."""
    exits = statuses or {}
    names = ["lint", "check", "test"]
    targets = [_target(name, exits.get(name, 0), extra or []) for name in names]
    return f".PHONY: {' '.join(names)}\n\n" + "\n".join(targets) + f"\n{SYNC_TARGET}"


def completed(decision: str = "doing") -> AgentRunResult:
    """A completed agent run that ends with `decision`."""
    return AgentRunResult(
        end_reason="completed", decision=decision, entry="done.", duration=timedelta(minutes=1)
    )


def open_story(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    *,
    makefile: str | None = None,
    main_files: dict[str, str] | None = None,
    state: WorkItemState | None = None,
    body: str = STORY,
    roles: tuple[str, ...] = ("tester",),
) -> WorkItemState:
    """Push the Makefile and `main_files`, start the story and push its branch in `state`.

    The state is by default the stage `tests` with the human's created record.
    """
    install_agents(agent_home, list(roles))
    human.push_file("main", "Makefile", makefile or stage_makefile())
    for path, text in (main_files or {}).items():
        human.push_file("main", path, text)
    human.push_file("main", BACKLOG_PATH, body)
    human.start(BACKLOG_PATH)
    opened = state or WorkItemState(stage="tests", journal=[CREATED])
    document = WorkItemDocument(state=opened, body=body + CREATED_LINE)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    return opened


def run_stage(boundaries: Boundaries) -> StageReport:
    """Run the work item's stage once under `PIPELINE_YAML`."""
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return StageRunner(boundaries, INSTANCE, definition, ENVIRONMENT).run(WORK_ITEM, PATH)


def branch_head(remote: Path) -> CommitId:
    """The commit the remote's work item branch points at."""
    commit = remote_commit(remote, BRANCH)
    assert commit is not None
    return commit


def pushed(boundaries: Boundaries, remote: Path) -> WorkItemDocument:
    """The work item at the head of the remote's branch."""
    text = boundaries.git.show_file(branch_head(remote), PATH)
    assert text is not None
    return boundaries.work_item_reader.parse(text)


def pushed_state(boundaries: Boundaries, remote: Path) -> WorkItemState:
    """The work item's state at the head of the remote's branch."""
    state = pushed(boundaries, remote).state
    assert state is not None
    return state
