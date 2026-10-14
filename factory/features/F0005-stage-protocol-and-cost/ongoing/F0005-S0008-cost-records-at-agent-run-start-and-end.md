---
stage: ready
pr: null
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
