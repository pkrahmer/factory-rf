"""The end of a stage: the decision, the checks and reports, the result commit and the labels."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.project_commands import ProjectCommands
from factory.application.stage import (
    STALL_TAIL_LINES,
    AfterAgent,
    AgentAftermath,
    StageFinisher,
    StageLauncher,
    StageReport,
)
from factory.domain.agent_runs import QUESTION, AgentRunResult
from factory.domain.checks import CheckResult
from factory.domain.errors import HostingServiceError, PushFailed
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import findings_question, round_cap_question
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from stage_run_support import ENVIRONMENT, INSTANCE, branch_head, pushed, pushed_state
from take_support import AGENT_TEXT

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
ROLES = ["intake", "tester", "coder", "reviewer", "documenter"]
OUTSIDE = "src/b.py"
ENTRY = "tests written."
TARGETS_LOG = "targets.log"
COMMANDS = ["lint", "check", "test", "coverage"]
GREEN_LINES = {
    "lint": ["lint ok"],
    "check": ["12 passed"],
    "test": ["3 passed"],
    "coverage": ["91 %"],
}
DEFINITION_YAML = (
    PIPELINE_YAML.replace(
        "  test: {time_limit: 10}\n", "  test: {time_limit: 10}\n  coverage: {time_limit: 3}\n"
    )
    .replace(
        "intake: {role: intake, next: [tests]}",
        "intake: {role: intake, next: [tests], checks: [lint]}",
    )
    .replace("checks: [lint], reports: [test]", "checks: [lint, check], reports: [test, coverage]")
    .replace(
        '  tester: {write_paths: ["tests/*"]}',
        '  tester: {write_paths: ["tests/*"], lease_duration: 70}',
    )
)
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


class RecordingCommands(ProjectCommands):
    """Records each command and its time limit, then lets the delegate run it."""

    def __init__(self, delegate: ProjectCommands) -> None:
        """Run every command on `delegate`."""
        self._delegate = delegate
        self.calls: list[tuple[str, timedelta]] = []

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        """Record, then delegate."""
        self.calls.append((command, time_limit))
        return self._delegate.run(command, time_limit=time_limit)


def _target(name: str, log: Path, lines: list[str], status: int) -> str:
    recipe = [
        f'@echo {name} >> "{log}"',
        f'@if [ -e {OUTSIDE} ]; then echo "{name} saw {OUTSIDE}" >> "{log}"; fi',
        *(f"@echo '{line}'" for line in lines),
        f"@exit {status}",
    ]
    return f"{name}:\n" + "".join(f"\t{line}\n" for line in recipe)


def _makefile(
    log: Path,
    lines: dict[str, list[str]] | None = None,
    statuses: dict[str, int] | None = None,
) -> str:
    """A Makefile whose targets log their names to `log`, print their lines and exit."""
    printed = {**GREEN_LINES, **(lines or {})}
    exits = statuses or {}
    targets = [_target(name, log, printed[name], exits.get(name, 0)) for name in COMMANDS]
    return f".PHONY: {' '.join(COMMANDS)}\n\n" + "\n".join(targets) + "\nsync:\n\t@:\n"


def _ran(log: Path) -> list[str]:
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if " saw " not in line]


def _definition(boundaries: Boundaries) -> PipelineDefinition:
    return boundaries.pipeline_reader.parse(DEFINITION_YAML)


def _completed(decision: str = "doing", entry: str = ENTRY) -> AgentRunResult:
    return AgentRunResult(
        end_reason="completed", decision=decision, entry=entry, duration=timedelta(minutes=1)
    )


def _aftermath(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    run: ScriptedRun,
    state: WorkItemState | None = None,
    body: str = STORY,
    makefile: str | None = None,
) -> AgentAftermath:
    """Open the work item in `state` with `body`, launch it with `run` and process the run."""
    install_agents(agent_home, ROLES)
    human.push_file("main", "Makefile", makefile or _makefile(tmp_path / TARGETS_LOG))
    human.push_file("main", BACKLOG_PATH, body)
    human.start(BACKLOG_PATH)
    document = WorkItemDocument(
        state=state or WorkItemState(stage="tests", journal=[CREATED]), body=body + CREATED_LINE
    )
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    boundaries.git.fetch()
    definition = _definition(boundaries)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    agent_runtime.queue(run)
    launched = StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT).launch(prepared)
    processed = AfterAgent(boundaries, INSTANCE, definition).process(launched)
    assert isinstance(processed, AgentAftermath)
    return processed


def _finish(boundaries: Boundaries, aftermath: AgentAftermath) -> StageReport:
    return StageFinisher(boundaries, INSTANCE, _definition(boundaries)).finish(aftermath)


def _rendered(boundaries: Boundaries, body: str, stage: str) -> str:
    document = WorkItemDocument(
        state=WorkItemState(stage=stage, journal=[CREATED]), body=body + CREATED_LINE
    )
    return boundaries.work_item_writer.render(document)


def _started_state(aftermath: AgentAftermath) -> WorkItemState:
    state = aftermath.started.document.state
    assert state is not None
    return state


def _records(state: WorkItemState) -> list[tuple[str, str]]:
    return [(record.speaker, record.kind) for record in state.journal]


def _agent_text(document: WorkItemDocument, speaker: str) -> str:
    state = document.state
    assert state is not None
    [record] = [record for record in state.journal if record.speaker == speaker]
    return entry_text(document, record.number)


def _note(hosting: FakeHostingService, report: StageReport) -> str:
    [post] = hosting.factory_posts(report.pull_request)
    return post.body


def test_a_forward_decision_with_green_checks_moves_the_work_item(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    assert state.stage == "doing"
    assert state.blocked is None
    assert state.claim is None
    assert state.pull_request == aftermath.started.pull_request.number
    assert report.rule == 6
    assert report.work_item == WORK_ITEM
    assert report.stage == "tests"
    assert report.next_stage == "doing"
    assert report.commit == branch_head(remote)
    assert report.pull_request == aftermath.started.pull_request.number
    assert report.stall is None


def test_the_checks_run_in_the_stages_order_each_once(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
    )

    _finish(boundaries, aftermath)

    checks = [name for name in _ran(tmp_path / TARGETS_LOG) if name in ("lint", "check")]
    assert checks == ["lint", "check"]


def test_the_checks_see_the_work_tree_after_the_undo(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(writes={OUTSIDE: AGENT_TEXT}, result=_completed("doing")),
    )

    _finish(boundaries, aftermath)

    log = (tmp_path / TARGETS_LOG).read_text(encoding="utf-8")
    assert "lint" in _ran(tmp_path / TARGETS_LOG)
    assert f"saw {OUTSIDE}" not in log


def test_a_red_check_stalls_the_stage_and_runs_nothing_after_it(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        state=WorkItemState(stage="tests", crashes=1, journal=[CREATED]),
        makefile=_makefile(tmp_path / TARGETS_LOG, statuses={"lint": 1}),
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    started = _started_state(aftermath)
    assert state.stage == "tests"
    assert state.attempts == started.attempts + 1
    assert state.crashes == started.crashes == 1
    assert report.rule == 5
    assert report.stall is not None
    assert report.stall.reason == "check_red"
    assert report.next_stage == report.stage == "tests"
    assert _ran(tmp_path / TARGETS_LOG) == ["lint"]


@pytest.mark.parametrize(
    ("printed", "present", "absent"),
    [(20, range(7, 21), "line 6"), (10, range(1, 11), None)],
    ids=["twenty-lines", "ten-lines"],
)
def test_the_stall_note_of_a_red_check_carries_the_tail_of_its_output(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    tmp_path: Path,
    printed: int,
    present: range,
    absent: str | None,
) -> None:
    lines = [f"line {number}" for number in range(1, printed + 1)]
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        makefile=_makefile(tmp_path / TARGETS_LOG, lines={"lint": lines}, statuses={"lint": 1}),
    )

    report = _finish(boundaries, aftermath)

    note = _note(hosting, report)
    assert STALL_TAIL_LINES == 15
    for number in present:
        assert f"line {number}" in note
    assert "Error 1" in note
    if absent is not None:
        assert absent not in note


def test_after_a_red_check_the_agents_entry_with_the_green_checks_stays_above_the_stall(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        makefile=_makefile(tmp_path / TARGETS_LOG, statuses={"check": 1}),
    )

    _finish(boundaries, aftermath)

    document = pushed(boundaries, remote)
    state = document.state
    assert state is not None
    assert _records(state)[-2:] == [("tester", "result"), ("factory", "stall")]
    assert entry_text(document, state.journal[-2].number).endswith("\n\n`lint`: lint ok")


def test_the_reports_run_in_order_after_the_checks_and_a_failing_one_holds_nothing(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        makefile=_makefile(tmp_path / TARGETS_LOG, statuses={"test": 1}),
    )

    report = _finish(boundaries, aftermath)

    assert _ran(tmp_path / TARGETS_LOG) == ["lint", "check", "test", "coverage"]
    assert report.rule == 6
    assert report.stall is None
    assert pushed_state(boundaries, remote).stage == "doing"


def test_each_green_check_and_each_report_adds_its_last_line_to_the_entry(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        makefile=_makefile(
            tmp_path / TARGETS_LOG,
            lines={"test": ["3 passed", "1 failed"]},
            statuses={"test": 1},
        ),
    )

    _finish(boundaries, aftermath)

    text = _agent_text(pushed(boundaries, remote), "tester")
    assert text == (
        f"{ENTRY}\n\n`lint`: lint ok\n`check`: 12 passed\n`test`: 1 failed\n`coverage`: 91 %"
    )


def test_an_entry_of_a_stage_without_checks_or_reports_gains_no_lines(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("docs", "reviewed.")),
        state=WorkItemState(stage="review", journal=[CREATED]),
    )

    report = _finish(boundaries, aftermath)

    assert report.rule == 6
    assert _ran(tmp_path / TARGETS_LOG) == []
    assert _agent_text(pushed(boundaries, remote), "reviewer") == "reviewed."


def test_a_question_blocks_the_stage_without_running_a_check(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed(QUESTION, "Which one, a or b?")),
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    assert _ran(tmp_path / TARGETS_LOG) == []
    assert state.stage == "tests"
    assert state.blocked == "question"
    assert _records(state)[-1] == ("tester", "question")
    assert report.rule == 2
    assert report.next_stage == report.stage == "tests"
    assert report.stall is None


@pytest.mark.parametrize(
    ("stage", "decision", "rule", "next_stage", "round_after"),
    [("docs", "doing", 3, "doing", 1), ("doing", "tests", 7, "tests", 0)],
    ids=["within-the-cap", "without-a-cap"],
)
def test_a_rework_moves_to_the_decisions_stage_without_running_a_check(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
    stage: str,
    decision: str,
    rule: int,
    next_stage: str,
    round_after: int,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed(decision, "sent back.")),
        state=WorkItemState(stage=stage, journal=[CREATED]),
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    assert _ran(tmp_path / TARGETS_LOG) == []
    assert report.rule == rule
    assert report.next_stage == next_stage
    assert state.stage == next_stage
    assert state.round == round_after
    assert state.attempts == _started_state(aftermath).attempts


@pytest.mark.parametrize(
    ("stage", "decision", "subject"),
    [
        ("tests", "doing", "work item F0001-S0001: tests ends: doing"),
        ("docs", "doing", "work item F0001-S0001: docs ends: doing"),
        ("tests", QUESTION, "work item F0001-S0001: tests ends: tests"),
    ],
    ids=["forward", "sent-back", "question"],
)
def test_the_commit_of_a_stage_end_carries_the_work_item_prefix(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    stage: str,
    decision: str,
    subject: str,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed(decision)),
        state=WorkItemState(stage=stage, journal=[CREATED]),
    )

    report = _finish(boundaries, aftermath)

    assert boundaries.git.log(report.commit)[0].subject == subject


def test_a_forward_decision_with_findings_after_the_run_asks_the_findings_question(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        body=WITHOUT_SMOKE_TEST,
    )

    report = _finish(boundaries, aftermath)

    document = pushed(boundaries, remote)
    state = document.state
    assert state is not None
    assert aftermath.form_findings != []
    assert report.rule == 1
    assert _ran(tmp_path / TARGETS_LOG) == []
    assert state.stage == "tests"
    assert state.blocked == "question"
    assert _records(state)[-2:] == [("tester", "result"), ("factory", "question")]
    question = entry_text(document, state.journal[-1].number)
    assert question == findings_question(aftermath.form_findings)


def test_a_first_stage_that_fixed_the_only_finding_moves_forward(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(
            writes={PATH: _rendered(boundaries, STORY, "intake")},
            result=_completed("tests", "accepted."),
        ),
        state=WorkItemState(stage="intake", journal=[CREATED]),
        body=WITHOUT_SMOKE_TEST,
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    assert aftermath.started.findings != []
    assert report.rule == 6
    assert _ran(tmp_path / TARGETS_LOG) == ["lint"]
    assert state.stage == "tests"
    assert state.blocked is None
    assert ("factory", "question") not in _records(state)


def test_a_rework_past_the_cap_blocks_the_stage_with_the_round_cap_question(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing", "sent back.")),
        state=WorkItemState(stage="docs", round=3, journal=[CREATED]),
    )

    report = _finish(boundaries, aftermath)

    document = pushed(boundaries, remote)
    state = document.state
    assert state is not None
    assert report.rule == 4
    assert _ran(tmp_path / TARGETS_LOG) == []
    assert state.stage == "docs"
    assert state.round == 4
    assert state.blocked == "round_cap"
    assert _records(state)[-1] == ("factory", "question")
    assert entry_text(document, state.journal[-1].number) == round_cap_question(4, 3)


@pytest.mark.parametrize(
    ("stage", "decision", "rounds", "body", "rule", "crashes"),
    [
        ("tests", "doing", 0, STORY, 6, 0),
        ("tests", "doing", 0, WITHOUT_SMOKE_TEST, 1, 1),
        ("tests", QUESTION, 0, STORY, 2, 1),
        ("docs", "doing", 0, STORY, 3, 1),
        ("docs", "doing", 3, STORY, 4, 1),
        ("doing", "tests", 0, STORY, 7, 1),
    ],
    ids=["rule-6", "rule-1", "rule-2", "rule-3", "rule-4", "rule-7"],
)
def test_a_move_keeps_the_counters_and_resets_crashes_only_on_a_forward_move(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
    stage: str,
    decision: str,
    rounds: int,
    body: str,
    rule: int,
    crashes: int,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed(decision, "done.")),
        state=WorkItemState(
            stage=stage,
            round=rounds,
            attempts=1,
            crashes=1,
            comments_read=[3],
            handed_over="coder",
            journal=[CREATED],
        ),
        body=body,
    )

    report = _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    started = _started_state(aftermath)
    assert report.rule == rule
    assert state.attempts == started.attempts
    assert state.comments_read == started.comments_read
    assert state.handed_over == started.handed_over
    assert state.crashes == crashes


@pytest.mark.parametrize(
    ("decision", "label"),
    [("doing", "stage:doing"), (QUESTION, "stage:tests")],
    ids=["move", "question"],
)
def test_the_labels_after_the_push_are_the_new_stages_label(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    tmp_path: Path,
    decision: str,
    label: str,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed(decision)),
    )

    report = _finish(boundaries, aftermath)

    assert hosting.labels(report.pull_request) == [label]


def test_a_failed_label_write_raises_after_the_result_commit_is_pushed(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    tmp_path: Path,
    remote: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
    )
    hosting.fail_next("set_labels")

    with pytest.raises(HostingServiceError):
        _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    assert state.stage == "doing"
    assert state.attempts == _started_state(aftermath).attempts
    assert ("factory", "stall") not in _records(state)
    assert hosting.factory_posts(aftermath.started.pull_request.number) == []


def test_a_rejected_push_of_the_result_raises_before_any_label_is_written(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    hosting: FakeHostingService,
    tmp_path: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
    )
    human.push_file(BRANCH, "elsewhere.md", "pushed by another clone\n")

    with pytest.raises(PushFailed):
        _finish(boundaries, aftermath)

    assert hosting.labels(aftermath.started.pull_request.number) == []


def test_each_check_and_report_runs_with_its_commands_time_limit(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
    )
    recording = RecordingCommands(boundaries.project_commands)
    used = replace(boundaries, project_commands=recording)

    _finish(used, aftermath)

    assert recording.calls == [
        ("lint", timedelta(minutes=5)),
        ("check", timedelta(minutes=10)),
        ("test", timedelta(minutes=10)),
        ("coverage", timedelta(minutes=3)),
    ]


def _report_fields() -> dict[str, object]:
    return {
        "work_item": WORK_ITEM,
        "stage": "tests",
        "next_stage": "doing",
        "rule": 6,
        "commit": "a" * 40,
        "pull_request": 1,
        "stall": None,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        *(("rule", rule) for rule in [1, 2, 3, 4, 5, 6, 7, None]),
        ("pull_request", 1),
        ("commit", "a" * 40),
    ],
)
def test_a_stage_report_accepts_values_its_types_allow(field: str, value: object) -> None:
    model: type[BaseModel] = StageReport

    report = model(**{**_report_fields(), field: value})

    assert getattr(report, field) == value


@pytest.mark.parametrize(
    ("field", "value"),
    [("rule", 0), ("rule", 8), ("pull_request", 0), ("commit", "a" * 39), ("unknown", 1)],
)
def test_a_stage_report_refuses_values_its_types_refuse(field: str, value: object) -> None:
    model: type[BaseModel] = StageReport

    with pytest.raises(ValidationError):
        model(**{**_report_fields(), field: value})


def test_a_stage_end_that_asks_a_question_stamps_both_entries_with_the_stage_and_its_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
    clock: ManualClock,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        body=WITHOUT_SMOKE_TEST,
    )

    _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    stamps = [(record.kind, record.at, record.stage, record.run) for record in state.journal]
    assert stamps[-2:] == [
        ("result", clock.now(), "tests", aftermath.cost.run),
        ("question", clock.now(), "tests", aftermath.cost.run),
    ]
    [started] = [record for record in state.journal if record.kind == "started"]
    assert started.stage == "tests"
    assert started.run is None


def test_a_red_check_stamps_the_entry_and_the_stall_with_the_stages_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    remote: Path,
    clock: ManualClock,
) -> None:
    aftermath = _aftermath(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        run=ScriptedRun(result=_completed("doing")),
        makefile=_makefile(tmp_path / TARGETS_LOG, statuses={"lint": 1}),
    )

    _finish(boundaries, aftermath)

    state = pushed_state(boundaries, remote)
    stamps = [(record.kind, record.at, record.stage, record.run) for record in state.journal]
    assert stamps[-2:] == [
        ("result", clock.now(), "tests", aftermath.cost.run),
        ("stall", clock.now(), "tests", aftermath.cost.run),
    ]
