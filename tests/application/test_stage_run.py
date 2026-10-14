"""A whole stage run: prepare, claim, agent run, after the agent, decision, checks, result."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.git import Git
from factory.application.stage import StageReport, StageRunner
from factory.domain.agent_runs import QUESTION, AgentRunRequest, AgentRunResult
from factory.domain.git import CommitId
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents, remote_commit
from human_clone import HumanClone

INSTANCE = "factory-1"
WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}
INSIDE = "tests/test_a.py"
AGENT_TEXT = "written by the agent\n"
NOTES = "notes.md"
BUILT = "build/out.txt"
IGNORED = "ignored/out.txt"
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


class CommittingRuntime(AgentRuntime):
    """Notes the head a run starts on, optionally commits a file as the agent, then delegates."""

    def __init__(self, delegate: FakeAgentRuntime, git: Git, *, commits: bool) -> None:
        """Run on `delegate`; commit `INSIDE` through `git` when `commits`."""
        self._delegate = delegate
        self._git = git
        self._commits = commits
        self.start_head: str | None = None
        self.agent_commit: CommitId | None = None

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Note the head, commit when asked, then let the delegate play."""
        self.start_head = self._git.status().head
        if self._commits:
            target = request.working_directory / INSIDE
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(AGENT_TEXT, encoding="utf-8")
            self.agent_commit = self._git.commit("the agent's own commit")
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()


def _target(name: str, status: int, extra: list[str]) -> str:
    recipe = [*extra, f"@echo '{name} done'", f"@exit {status}"]
    return f"{name}:\n" + "".join(f"\t{line}\n" for line in recipe)


def _makefile(statuses: dict[str, int] | None = None, extra: list[str] | None = None) -> str:
    exits = statuses or {}
    names = ["lint", "check", "test"]
    targets = [_target(name, exits.get(name, 0), extra or []) for name in names]
    return f".PHONY: {' '.join(names)}\n\n" + "\n".join(targets)


def _completed(decision: str = "doing") -> AgentRunResult:
    return AgentRunResult(
        end_reason="completed", decision=decision, entry="done.", duration=timedelta(minutes=1)
    )


def _open(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    *,
    makefile: str | None = None,
    main_files: dict[str, str] | None = None,
) -> WorkItemState:
    """Push the Makefile and `main_files`, start the story and push its branch in `tests`."""
    install_agents(agent_home, ["tester"])
    human.push_file("main", "Makefile", makefile or _makefile())
    for path, text in (main_files or {}).items():
        human.push_file("main", path, text)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    state = WorkItemState(stage="tests", journal=[CREATED])
    document = WorkItemDocument(state=state, body=STORY + CREATED_LINE)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    return state


def _run(boundaries: Boundaries) -> StageReport:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    return StageRunner(boundaries, INSTANCE, definition, ENVIRONMENT).run(WORK_ITEM, PATH)


def _head(remote: Path) -> CommitId:
    commit = remote_commit(remote, BRANCH)
    assert commit is not None
    return commit


def _pushed_state(boundaries: Boundaries, remote: Path) -> WorkItemState:
    text = boundaries.git.show_file(_head(remote), PATH)
    assert text is not None
    state = boundaries.work_item_reader.parse(text).state
    assert state is not None
    return state


@pytest.mark.parametrize(
    "commits", [False, True], ids=["agent-committed-nothing", "agent-committed"]
)
@pytest.mark.parametrize(
    ("decision", "statuses"),
    [("doing", {}), (QUESTION, {}), ("doing", {"lint": 1})],
    ids=["move", "question", "stall"],
)
def test_a_run_adds_exactly_one_commit_of_its_own(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    decision: str,
    statuses: dict[str, int],
    commits: bool,
) -> None:
    _open(boundaries, human, agent_home, makefile=_makefile(statuses))
    agent_runtime.queue(ScriptedRun(result=_completed(decision)))
    runtime = CommittingRuntime(agent_runtime, boundaries.git, commits=commits)

    report = _run(replace(boundaries, agent_runtime=runtime))

    base = runtime.agent_commit if commits else runtime.start_head
    assert base is not None
    assert report.commit == _head(remote)
    [own] = boundaries.git.log(report.commit, since=base)
    assert own.parents == [base]
    if runtime.agent_commit is not None:
        assert boundaries.git.show_file(runtime.agent_commit, INSIDE) == AGENT_TEXT


def test_the_result_commit_holds_what_a_check_created_unless_it_is_ignored(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    creates = [
        "@mkdir -p build ignored",
        f"@echo built > {BUILT}",
        f"@echo built > {IGNORED}",
    ]
    _open(
        boundaries,
        human,
        agent_home,
        makefile=_makefile(extra=creates),
        main_files={".gitignore": "ignored/\n"},
    )
    agent_runtime.queue(ScriptedRun(result=_completed("doing")))

    report = _run(boundaries)

    assert report.rule == 6
    assert report.commit == _head(remote)
    assert boundaries.git.show_file(report.commit, BUILT) == "built\n"
    assert boundaries.git.show_file(report.commit, IGNORED) is None


def test_a_branch_that_cannot_take_the_main_branch_stalls_before_the_claim(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    started = _open(boundaries, human, agent_home, main_files={NOTES: "base\n"})
    human.push_file(BRANCH, NOTES, "branch\n")
    human.push_file("main", NOTES, "main\n")
    boundaries.git.fetch()

    report = _run(boundaries)

    state = _pushed_state(boundaries, remote)
    assert report.rule is None
    assert report.stall is not None
    assert report.stall.reason == "merge_conflict"
    assert report.next_stage == report.stage == "tests"
    assert agent_runtime.requests() == []
    assert state.claim is None
    assert "started" not in [record.kind for record in state.journal]
    assert state.attempts == started.attempts + 1


def test_a_died_agent_run_ends_in_a_stall_report(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(
        ScriptedRun(result=AgentRunResult(end_reason="died", duration=timedelta(minutes=3)))
    )

    report = _run(boundaries)

    assert report.rule is None
    assert report.stall is not None
    assert report.stall.reason == "died"
    assert report.commit == report.stall.commit == _head(remote)


def test_the_agent_runs_with_exactly_the_environment_given_to_the_runner(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=_completed("doing")))

    _run(boundaries)

    [request] = agent_runtime.requests()
    assert request.environment == ENVIRONMENT
