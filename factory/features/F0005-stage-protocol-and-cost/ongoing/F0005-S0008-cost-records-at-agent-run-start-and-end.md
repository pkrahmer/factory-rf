---
stage: review
pr: 65
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Cost records at agent run start and end

## Assignment (as of log entry 1)

Give every agent run a cost record from its start. When a run starts, a record with status `started` is added to the work item's sidecar file; when it ends, the same record is completed with the duration, the end reason, the turns, the tokens and the cost that the agent runtime reported, and nothing it did not report: unknown stays `None`, never zero, never estimated (R24). The records are not pushed before the run; they travel in the stage's next commit, the stall commit or the result commit, so a crashed stage's records are discarded with it (F0008). The undo of F0004 reverts every path outside the write paths, and the sidecar is such a path, so the records are kept in memory during the run and written to the sidecar again after every undo. A run that ended with `ok: false` has its record like any other (GH4.2; the bill that counts it is S0009). Covers GH4.1 and GH4.2 (the record side); implements R24; keeps kept thing 20 (a cost record per agent run). The image recorded in each record is F0010's (ST5.4): `image` stays `None` here.

## Interface

`src/factory/application/costs.py`

```python
class CostRun(BaseModel):
    path: str
    run: str
    records: list[CostRecord]

class CostRecorder:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def begin(self, started: StartedStage, role: str) -> CostRun: ...
    def complete(self, run: CostRun, result: AgentRunResult) -> CostRun: ...
    def write(self, run: CostRun) -> None: ...
```

Changes to earlier modules, each with its criterion:

The tester of this story adds `cost=` to each test of S0003, S0004, S0005 or S0007 that builds `LaunchedStage` or `AgentAftermath` directly, and adds the sidecar's path to each exact comparison of an `UndoReport` there (`StallResult.undo` included); no other earlier test changes.

```python
class LaunchedStage(BaseModel):
    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    cost: CostRun

class AgentAftermath(BaseModel):
    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    decision: str
    document: WorkItemDocument
    entry: NewEntry
    undo: UndoReport
    form_findings: list[FormFinding]
    cost: CostRun

class StallContext(BaseModel):
    work_item: WorkItemId
    stage: Name
    branch: str
    path: str
    stage_start: StageStart | None
    document: WorkItemDocument | None = None
    pull_request: PullRequestView | None = None
    cost: CostRun | None = None
```

Types: `CostRecord` from `factory.domain.cost_records`, `AgentRunResult` from `factory.domain.agent_runs`, `StartedStage` and `LaunchedStage` from `factory.application.stage`. `costs` imports `StartedStage` only under `TYPE_CHECKING` (with `from __future__ import annotations`, as `factory.domain.journal` does), because `stage` imports `costs` for `CostRun`. `CostRun` is frozen and forbids unknown keys; `path` is `cost_records_path(started.path)` and `records` holds every record of the work item, the run's last.

- `begin` reads the sidecar in the work tree with `CostRecordReader.read(checkout / path)` (a missing file is `[]`), adds `CostRecord(run=<uuid4 hex>, work_item, stage, role, attempt=<the state's attempts>, status="started", started_at=Clock.now())` with every other field `None`, writes all records with `CostRecordWriter.write` and returns the `CostRun`.
- `complete` replaces the run's record (same `run`) by `status="completed"`, `duration_seconds=<result.duration in seconds>`, `end_reason`, `turns`, `tokens` and `cost_usd` copied from the result as they are (`None` stays `None`, `Decimal("0")` stays `Decimal("0")`), writes all records and returns the new `CostRun`.
- `write` writes `run.records` to `run.path`, replacing the file, whatever the file held.
- `StageLauncher.launch` calls `begin` after it composes the request and right before the runtime runs, and `complete` right after the runtime returns; `LaunchedStage.cost` is the completed run.
- `AfterAgent.process` calls `CostRecorder.write(launched.cost)` right after its undo and passes `cost=launched.cost` in every `StallContext`; `AgentAftermath.cost` is that run. `StageFinisher.finish` passes `aftermath.cost` in the `StallContext` of a red check. `StallService.stall` calls `CostRecorder.write(context.cost)` right after its undo when `context.cost` is not `None`.
- No cost record is committed or pushed before the run: the stage-start commit holds the records of earlier stages only.
- The sidecar is a file the factory rewrites itself, so S0005 leaves `cost_records_path(started.path)` out of the paths the entry says were undone (S0005 rule 5, FEATURE decision 27): an agent that wrote only inside its write paths gets an entry without the paragraph about undone changes, and the pushed sidecar holds the completed record.

Tests: `tests/application/test_costs.py`; the stage, stall and result paths are driven through `StageRunner` and `StallService` with `FakeAgentRuntime` and a subclass of `ObservingRuntime` (S0003's `tests/observing_runtime.py`, which stays as S0003 wrote it) in this story's own test module, that reads the sidecar from the work tree and from `origin/<branch>` when it is called. `CostRun` and the models grown above refuse unknown keys (criterion 15). Unless a criterion sets form findings, the work items are complete stories (every section of the fixture's form, criteria ending with `make check` … `green` and `docs:`, a smoke-test block followed by `Expect:`).

## Acceptance criteria

1. While the runtime runs, the sidecar at `cost_records_path(path)` in the work tree holds a record with status `started`, the work item, the stage, the stage's role, `attempt` equal to the state's attempts counter, `started_at` equal to the fixture clock, and `duration_seconds`, `end_reason`, `turns`, `tokens`, `cost_usd` and `image` all `None`.
2. A run id is 32 lowercase hexadecimal characters, differs between two runs of one work item, and the records of earlier stages stay in the file with the new record last.
3. Nothing is pushed before the run: when the runtime is called, `origin/<branch>` holds no sidecar for a work item at its first stage, and holds the previous stage's sidecar unchanged for a later one.
4. After a completed run the record has status `completed`, `duration_seconds` equal to the result's duration in seconds, and `end_reason`, `turns`, `tokens` and `cost_usd` equal to the result's.
5. A result that ended `died` or `time_limit` (parametrised) and reported no turns, tokens or cost gives a record with duration and end reason set and `turns`, `tokens` and `cost_usd` equal to `None`, not zero.
6. A result that reported a cost of `Decimal("0")` and zero tokens gives a record with those zeros: a reported zero is not turned into unknown.
7. After the run the file holds one record for the run, the completed one: the started record is replaced, not kept beside it.
8. A run that starts after a stall (the state's `attempts` is 1) has a record with `attempt` equal to 1.
9. The sidecar is written again after the undo: an agent that overwrites or deletes the sidecar file leaves, in the pushed commit, a file equal to the records in memory, the completed one included.
10. The result commit of a stage that moves contains the sidecar with the completed record (GH4.1: created at the start, completed at the end, committed with the next commit).
11. The stall commit of a run that ended `died` or `time_limit` (parametrised) contains the sidecar with that run's record: `end_reason` as the run ended, duration set, cost and tokens `None` (GH4.2).
12. The stall commit of a red check contains the run's record once, not twice.
13. A failing run (`end_reason` other than `completed`) has its record in the commit like a completed run; `CostRecord.ok` is `False` for it.
14. An agent that writes only inside its write paths gets a journal entry without the paragraph `The factory undid changes outside the write paths`, although the undo reverted or deleted its sidecar; the pushed sidecar holds its completed record.
15. `CostRun` is frozen and forbids unknown keys: assigning to `run` (through `setattr`, the field's name in a variable) and building it with an unknown field raise `ValidationError`; the same holds for `StallContext` built with an unknown field.
16. make check stays green.
17. docs: `docs/project-guide.md` states when a cost record is created, completed and committed (at the run's start and end, with the stage's next commit, never pushed alone) and that unknown cost and tokens are `None`; `docs/decisions.md` records that the sidecar is rewritten from memory after every undo, and that a crashed stage's records are discarded with the stage (R24).

## Demo

```bash
uv run pytest tests/application/test_costs.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `costs.py` names `CostRun` and `CostRecorder` with signatures. The changes to `LaunchedStage`, `AgentAftermath` and `StallContext` are concrete. The wiring in `StageLauncher`, `AfterAgent`, `StageFinisher` and `StallService` is stated call by call. The behaviours in the comments are `begin`, `complete`, `write` and the sidecar being left out of the undone paths. Each has a criterion: 1 and 2 for `begin`, 4 to 7 for `complete`, 9 for `write`, 14 for the undone paths.
   - Criteria: each is testable by one test function. The failing side is covered. Criterion 5 covers unknown staying `None`, and 6 covers a reported zero staying zero. Criterion 13 covers a failing run (`ok` is `False`). Criterion 3 covers nothing pushed before the run. Criterion 12 covers a record not duplicated. Criterion 15 covers unknown keys and frozen. One small gap: a `StallContext` with `cost=None` writes no sidecar. It is a default-path behaviour and not a stated rule, so I did not ask.
   - Demo: `uv run pytest tests/application/test_costs.py` is runnable. Its `Expect:` line is checkable (last line `passed`, no `failed` or `error`).
   - Architecture: the module sits in `factory.application`. It reaches the sidecar through `CostRecordReader` and `CostRecordWriter`, and it imports `StartedStage` under `TYPE_CHECKING` to avoid the import cycle. The layers are respected.
   - Scope: the story is within FEATURE.md's "Cost records" scope. `image` stays `None` (F0010), the bill is S0009's, and the crash discard is F0008's. Decisions 20, 27 and 32 match the story.
3. tester: Wrote the tests for every criterion in `tests/application/test_costs.py` (the only file created). It defines `SidecarRuntime`, a subclass of `ObservingRuntime` that stays as S0003 wrote it. When called, it reads the sidecar from the work tree and from the remote branch head, then delegates. The stage, stall and result paths go through `StageRunner`. Criteria 4–7 read `LaunchedStage.cost` from `StageLauncher.launch`. The work item is a complete story, with a Makefile of green `lint`/`check`/`test` targets (`lint` red for criterion 12).

   - criterion 1: tests/application/test_costs.py::test_the_sidecar_holds_a_started_record_while_the_runtime_runs
   - criterion 2: tests/application/test_costs.py::test_each_run_gets_a_new_hex_id_and_its_record_comes_after_the_earlier_ones (an earlier `intake` record on the branch, then a died run and a completed run)
   - criterion 3: tests/application/test_costs.py::test_no_cost_record_is_pushed_before_the_run [first-stage, later-stage]
   - criterion 4: tests/application/test_costs.py::test_a_completed_run_completes_its_record_with_the_reported_measures
   - criterion 5: tests/application/test_costs.py::test_unreported_measures_of_an_ended_run_stay_unknown [died, time_limit]
   - criterion 6: tests/application/test_costs.py::test_a_reported_zero_cost_and_zero_tokens_stay_zero
   - criterion 7: tests/application/test_costs.py::test_the_completed_record_replaces_the_started_one
   - criterion 8: tests/application/test_costs.py::test_a_run_after_a_stall_records_the_counted_attempt (state starts with `attempts: 1`)
   - criterion 9: tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo [overwritten, deleted] (the pushed sidecar must equal an exact expected `CostRecord`)
   - criterion 10: tests/application/test_costs.py::test_the_result_commit_of_a_moving_stage_holds_the_completed_record
   - criterion 11: tests/application/test_costs.py::test_the_stall_commit_of_an_ended_run_holds_its_record [died, time_limit]
   - criterion 12: tests/application/test_costs.py::test_the_stall_commit_of_a_red_check_holds_the_record_once
   - criterion 13: tests/application/test_costs.py::test_a_failing_run_is_committed_with_a_record_that_is_not_ok [no_result, time_limit, budget, died]
   - criterion 14: tests/application/test_costs.py::test_an_agent_inside_its_write_paths_is_not_told_of_the_sidecar_undo [sidecar-deleted, sidecar-reverted]
   - criterion 15: tests/application/test_costs.py::test_cost_runs_and_stall_contexts_are_frozen_and_forbid_unknown_keys
   - criteria 16 and 17 are the factory's `make check` and the documenter's; no tests.

   Earlier tests: none changed. No S0003/S0004/S0005/S0007 test builds `LaunchedStage` or `AgentAftermath` by keywords. The frozen/unknown-key tests use `dict(launched)` and `dict(aftermath)`, which will carry `cost`. `StallContext.cost` defaults to `None`, and no exact `UndoReport` comparison in those modules covers a launched stage's undo. The coder should still watch the earlier launch-driven tests: `begin` now leaves an untracked sidecar in the work tree.

   `make test` once: a collection error, `ModuleNotFoundError: No module named 'factory.application.costs'`. That is the one module the runner could not import. `make lint` is green after `ruff format`. I skipped the type check as the stage says: `StallContext(cost=...)` and `LaunchedStage.cost` do not exist yet.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the cost records for agent runs. `make check` is green and coverage is 99.4 %. Commits: 955e025 (feat) and 4cc62d8 (refactor).

   - `src/factory/application/costs.py` (new):
     - `CostRun` is frozen and forbids unknown keys.
     - `CostRecorder.begin` reads the sidecar in the work tree and adds a `started` record. The record has a `uuid4().hex` run id, the state's `attempts` and `Clock.now()`. `begin` writes the sidecar and returns the run.
     - `complete` replaces the record with the same run id by its completed form. It copies duration, end reason, turns, tokens and cost exactly as reported (`None` stays `None`, a reported zero stays zero), then writes.
     - `write` replaces the file with the records held in memory.
     - `StartedStage` is imported only under `TYPE_CHECKING`, as the interface says.
   - `src/factory/application/stage.py`:
     - `LaunchedStage.cost` and `AgentAftermath.cost` are added.
     - `StageLauncher.launch` calls `begin` right before the runtime runs and `complete` right after it returns.
     - `AfterAgent.process` calls `CostRecorder.write(launched.cost)` right after its undo. Its `_stall` now takes the `LaunchedStage`, so every `StallContext` gets `cost=launched.cost`.
     - `StageFinisher._stall_red` passes `aftermath.cost`.
   - `src/factory/application/stalls.py`: `StallContext.cost` is added, defaulting to `None`. `StallService.stall` rewrites the sidecar right after its undo when `cost` is set.

   Main decision: the role passed to `begin` comes from the pipeline definition (`definition.stages[stage].role`), which `StageLauncher` now keeps. The alternative I rejected was reading it from the `AgentDefinition` the composer returns, because that would tie the record to the agent file's naming rather than the stage table.

   Refactor: the "stage has no role" check was now in two places, so I moved it into one module helper, `_role_of`, in `stage.py`. I changed nothing else.

   Noticed but did not touch:
   - `AfterAgent._entry` already left the sidecar out of the undone paths before this story, so no change was needed for criterion 14.
   - `begin` raises `ValueError` for a document without state (`costs.py` line 42). That branch is not covered, and the launcher refuses such a document earlier anyway.
   - Intake noted a gap: no test checks that a `StallContext` with `cost=None` writes no sidecar. The code doesn't write one in that case.

   No test changed. `## Assignment` is unchanged.

   `make check`: check: green
