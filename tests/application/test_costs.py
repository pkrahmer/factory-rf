"""Cost records: begun before the agent runs, completed after it, rewritten after every undo."""

import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.files import CostRecordReader
from factory.application.git import Git
from factory.application.opening import WorkItemOpening
from factory.application.stage import LaunchedStage, StageLauncher, StageReport, StageRunner
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, EndReason, TokenCounts
from factory.domain.cost_records import CostRecord
from factory.domain.git import CommitId
from factory.domain.identifiers import branch_name
from factory.domain.journal import JournalRecord
from factory.domain.paths import cost_records_path
from factory.domain.work_item import WorkItemDocument, WorkItemState
from git_support import PIPELINE_YAML, install_agents, remote_commit
from human_clone import HumanClone
from observing_runtime import ObservingRuntime
from stage_run_support import ENVIRONMENT, INSTANCE

WORK_ITEM = "F0001-S0001"
BRANCH = branch_name(WORK_ITEM)
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
PATH = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
SIDECAR = cost_records_path(PATH)
INSIDE = "tests/test_a.py"
AGENT_TEXT = "written by the agent\n"
ENTRY = "tests written."
UNDONE_PARAGRAPH = "The factory undid changes outside the write paths"
RUN_ID = re.compile(r"^[0-9a-f]{32}$")
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
EARLIER = CostRecord(
    run="b" * 32,
    work_item=WORK_ITEM,
    stage="intake",
    role="intake",
    attempt=0,
    status="completed",
    started_at=datetime(2026, 10, 11, 9, 0, tzinfo=UTC),
    duration_seconds=30.0,
    end_reason="completed",
)
FAILED_REASONS: list[EndReason] = ["no_result", "time_limit", "budget", "died"]


class SidecarRuntime(ObservingRuntime):
    """Reads the sidecar from the work tree and from the remote branch, then delegates."""

    def __init__(
        self,
        delegate: FakeAgentRuntime,
        *,
        remote: Path,
        hosting: FakeHostingService,
        checkout: Git,
        work_tree: Path,
        reader: CostRecordReader,
    ) -> None:
        """Observe `BRANCH` on `remote`; read the sidecar under `work_tree` with `reader`."""
        super().__init__(delegate, remote=remote, branch=BRANCH, hosting=hosting, checkout=checkout)
        self._work_tree = work_tree
        self._reader = reader
        self.work_tree_records: list[list[CostRecord]] = []
        self.remote_sidecars: list[str | None] = []

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Read the sidecar in both places, then observe and play the request."""
        self.work_tree_records.append(self._reader.read(self._work_tree / SIDECAR))
        head = remote_commit(self._remote, BRANCH)
        self.remote_sidecars.append(
            None if head is None else self._checkout.show_file(head, SIDECAR)
        )
        return super().run(request)

    def started_run(self) -> str:
        """The run id of the record the last call found last in the work tree."""
        return self.work_tree_records[-1][-1].run


def _target(name: str, status: int) -> str:
    return f"{name}:\n\t@echo '{name} done'\n\t@exit {status}\n"


def _makefile(statuses: dict[str, int] | None = None) -> str:
    exits = statuses or {}
    names = ["lint", "check", "test"]
    targets = [_target(name, exits.get(name, 0)) for name in names]
    return f".PHONY: {' '.join(names)}\n\n" + "\n".join(targets)


def _completed(decision: str = "doing", **measures: object) -> AgentRunResult:
    return AgentRunResult.model_validate(
        {
            "end_reason": "completed",
            "decision": decision,
            "entry": ENTRY,
            "duration": timedelta(minutes=1),
            **measures,
        }
    )


def _ended(end_reason: EndReason) -> AgentRunResult:
    return AgentRunResult(end_reason=end_reason, duration=timedelta(minutes=3, seconds=20))


def _open(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    *,
    attempts: int = 0,
    makefile: str | None = None,
    sidecar: str | None = None,
) -> None:
    """Push the Makefile, start the story and push its branch in `tests`, the sidecar beside it."""
    install_agents(agent_home, ["tester"])
    human.push_file("main", "Makefile", makefile or _makefile())
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    state = WorkItemState(stage="tests", attempts=attempts, journal=[CREATED])
    document = WorkItemDocument(state=state, body=STORY + CREATED_LINE)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    if sidecar is not None:
        human.push_file(BRANCH, SIDECAR, sidecar)
    boundaries.git.fetch()


def _runtime(
    boundaries: Boundaries,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> SidecarRuntime:
    return SidecarRuntime(
        agent_runtime,
        remote=remote,
        hosting=hosting,
        checkout=boundaries.git,
        work_tree=boundaries.checkout,
        reader=boundaries.cost_reader,
    )


def _run(boundaries: Boundaries, runtime: SidecarRuntime) -> StageReport:
    used = replace(boundaries, agent_runtime=runtime)
    definition = used.pipeline_reader.parse(PIPELINE_YAML)
    return StageRunner(used, INSTANCE, definition, ENVIRONMENT).run(WORK_ITEM, PATH)


def _launch(boundaries: Boundaries) -> LaunchedStage:
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    return StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT).launch(prepared)


def _records_at(boundaries: Boundaries, commit: CommitId) -> list[CostRecord]:
    text = boundaries.git.show_file(commit, SIDECAR)
    assert text is not None
    return boundaries.cost_reader.parse(text)


def _head(remote: Path) -> CommitId:
    commit = remote_commit(remote, BRANCH)
    assert commit is not None
    return commit


def test_the_sidecar_holds_a_started_record_while_the_runtime_runs(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    clock: ManualClock,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)
    now = clock.now()

    _run(boundaries, runtime)

    [[record]] = runtime.work_tree_records
    assert record.status == "started"
    assert record.work_item == WORK_ITEM
    assert record.stage == "tests"
    assert record.role == "tester"
    assert record.attempt == 0
    assert record.started_at == now
    assert record.duration_seconds is None
    assert record.end_reason is None
    assert record.turns is None
    assert record.tokens is None
    assert record.cost_usd is None
    assert record.image is None


def test_each_run_gets_a_new_hex_id_and_its_record_comes_after_the_earlier_ones(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _open(boundaries, human, agent_home, sidecar=boundaries.cost_writer.render([EARLIER]))
    agent_runtime.queue(ScriptedRun(result=_ended("died")))
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    _run(boundaries, runtime)
    report = _run(boundaries, runtime)

    first, second = runtime.work_tree_records
    assert first[:-1] == [EARLIER]
    assert [record.run for record in second[:-1]] == [EARLIER.run, first[-1].run]
    assert second[-1].status == "started"
    runs = [first[-1].run, second[-1].run]
    assert all(RUN_ID.match(run) for run in runs)
    assert runs[0] != runs[1]
    pushed = _records_at(boundaries, report.commit)
    assert [record.run for record in pushed] == [EARLIER.run, *runs]


@pytest.mark.parametrize("earlier", [False, True], ids=["first-stage", "later-stage"])
def test_no_cost_record_is_pushed_before_the_run(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    earlier: bool,
) -> None:
    sidecar = boundaries.cost_writer.render([EARLIER]) if earlier else None
    _open(boundaries, human, agent_home, sidecar=sidecar)
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    _run(boundaries, runtime)

    assert runtime.remote_sidecars == [sidecar]


def test_a_completed_run_completes_its_record_with_the_reported_measures(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    _open(boundaries, human, agent_home)
    tokens = TokenCounts(input=1200, output=340, cache_read=56, cache_creation=7)
    result = _completed(
        duration=timedelta(minutes=2, seconds=5, milliseconds=250),
        turns=9,
        tokens=tokens,
        cost_usd=Decimal("0.4231"),
    )
    agent_runtime.queue(ScriptedRun(result=result))

    launched = _launch(boundaries)

    assert launched.cost.path == SIDECAR
    record = launched.cost.records[-1]
    assert record.run == launched.cost.run
    assert record.status == "completed"
    assert record.duration_seconds == result.duration.total_seconds()
    assert record.end_reason == "completed"
    assert record.turns == 9
    assert record.tokens == tokens
    assert record.cost_usd == Decimal("0.4231")


@pytest.mark.parametrize("end_reason", ["died", "time_limit"])
def test_unreported_measures_of_an_ended_run_stay_unknown(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    end_reason: EndReason,
) -> None:
    _open(boundaries, human, agent_home)
    result = _ended(end_reason)
    agent_runtime.queue(ScriptedRun(result=result))

    launched = _launch(boundaries)

    record = launched.cost.records[-1]
    assert record.status == "completed"
    assert record.duration_seconds == result.duration.total_seconds()
    assert record.end_reason == end_reason
    assert record.turns is None
    assert record.tokens is None
    assert record.cost_usd is None


def test_a_reported_zero_cost_and_zero_tokens_stay_zero(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    _open(boundaries, human, agent_home)
    zero = TokenCounts(input=0, output=0)
    agent_runtime.queue(ScriptedRun(result=_completed(turns=0, tokens=zero, cost_usd=Decimal("0"))))

    launched = _launch(boundaries)

    record = launched.cost.records[-1]
    assert record.turns == 0
    assert record.tokens == zero
    assert record.cost_usd is not None
    assert record.cost_usd == Decimal("0")


def test_the_completed_record_replaces_the_started_one(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=_completed()))

    launched = _launch(boundaries)

    [record] = boundaries.cost_reader.read(boundaries.checkout / SIDECAR)
    assert record.run == launched.cost.run
    assert record.status == "completed"
    assert launched.cost.records == [record]


def test_a_run_after_a_stall_records_the_counted_attempt(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _open(boundaries, human, agent_home, attempts=1)
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    [[started]] = runtime.work_tree_records
    assert started.attempt == 1
    [pushed] = _records_at(boundaries, report.commit)
    assert pushed.attempt == 1


@pytest.mark.parametrize("deletes", [False, True], ids=["overwritten", "deleted"])
def test_the_sidecar_is_written_again_after_the_undo(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    clock: ManualClock,
    deletes: bool,
) -> None:
    _open(boundaries, human, agent_home)
    if deletes:
        scripted = ScriptedRun(deletes=[SIDECAR], result=_completed())
    else:
        scripted = ScriptedRun(writes={SIDECAR: "overwritten by the agent\n"}, result=_completed())
    agent_runtime.queue(scripted)
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)
    now = clock.now()

    report = _run(boundaries, runtime)

    assert report.commit == _head(remote)
    expected = CostRecord(
        run=runtime.started_run(),
        work_item=WORK_ITEM,
        stage="tests",
        role="tester",
        attempt=0,
        status="completed",
        started_at=now,
        duration_seconds=60.0,
        end_reason="completed",
        denials=0,
        denied_paths=[],
        instance="factory-1",
    )
    assert _records_at(boundaries, report.commit) == [expected]


def test_the_result_commit_of_a_moving_stage_holds_the_completed_record(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    assert report.rule == 6
    assert report.commit == _head(remote)
    [record] = _records_at(boundaries, report.commit)
    assert record.run == runtime.started_run()
    assert record.status == "completed"


@pytest.mark.parametrize("end_reason", ["died", "time_limit"])
def test_the_stall_commit_of_an_ended_run_holds_its_record(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    end_reason: EndReason,
) -> None:
    _open(boundaries, human, agent_home)
    result = _ended(end_reason)
    agent_runtime.queue(ScriptedRun(result=result))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    assert report.stall is not None
    assert report.stall.reason == end_reason
    [record] = _records_at(boundaries, report.stall.commit)
    assert record.run == runtime.started_run()
    assert record.end_reason == end_reason
    assert record.duration_seconds == result.duration.total_seconds()
    assert record.cost_usd is None
    assert record.tokens is None


def test_the_stall_commit_of_a_red_check_holds_the_record_once(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
) -> None:
    _open(boundaries, human, agent_home, makefile=_makefile({"lint": 1}))
    agent_runtime.queue(ScriptedRun(result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    assert report.stall is not None
    assert report.stall.reason == "check_red"
    text = boundaries.git.show_file(report.stall.commit, SIDECAR)
    assert text is not None
    assert text.count(runtime.started_run()) == 1
    [record] = boundaries.cost_reader.parse(text)
    assert record.status == "completed"


@pytest.mark.parametrize("end_reason", FAILED_REASONS)
def test_a_failing_run_is_committed_with_a_record_that_is_not_ok(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    end_reason: EndReason,
) -> None:
    _open(boundaries, human, agent_home)
    agent_runtime.queue(ScriptedRun(result=_ended(end_reason)))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    assert report.commit == _head(remote)
    [record] = _records_at(boundaries, report.commit)
    assert record.run == runtime.started_run()
    assert record.status == "completed"
    assert record.end_reason == end_reason
    assert record.ok is False


@pytest.mark.parametrize("earlier", [False, True], ids=["sidecar-deleted", "sidecar-reverted"])
def test_an_agent_inside_its_write_paths_is_not_told_of_the_sidecar_undo(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    hosting: FakeHostingService,
    earlier: bool,
) -> None:
    sidecar = boundaries.cost_writer.render([EARLIER]) if earlier else None
    _open(boundaries, human, agent_home, sidecar=sidecar)
    agent_runtime.queue(ScriptedRun(writes={INSIDE: AGENT_TEXT}, result=_completed()))
    runtime = _runtime(boundaries, agent_runtime, remote, hosting)

    report = _run(boundaries, runtime)

    assert report.rule == 6
    work_item = boundaries.git.show_file(report.commit, PATH)
    assert work_item is not None
    assert ENTRY in work_item
    assert UNDONE_PARAGRAPH not in work_item
    assert boundaries.git.show_file(report.commit, INSIDE) == AGENT_TEXT
    record = _records_at(boundaries, report.commit)[-1]
    assert record.run == runtime.started_run()
    assert record.status == "completed"
