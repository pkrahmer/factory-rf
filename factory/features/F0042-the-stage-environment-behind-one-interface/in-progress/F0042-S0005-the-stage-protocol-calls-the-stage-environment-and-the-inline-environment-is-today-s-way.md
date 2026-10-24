---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 413
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-24T16:31:13.045921Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T16:30:19.878240Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T16:30:19.883891Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T16:30:52.089440Z'
  stage: intake
  run: eac3596abc704aee8bfdddc25a3e03c9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T16:31:13.045921Z'
  stage: tests
---

# The stage protocol calls the stage environment, and the inline environment is today's way

## Description

The cycle of a v1.2 stage (`planning/v1.2-plan.md`, "The cycle of a stage") is one object the stage protocol calls: before the agent it prepares the place the agent works in, it runs the agent, and after the agent it takes the result. v1.1's own way is the second implementation of the same interface: nothing to prepare, the agent in the factory's container through `run_sealed`, and the undo as the take. This story adds the interface `StageEnvironment` in `factory.application.stage_environment` with its three operations, `InlineEnvironment` as today's behaviour, and `stage_environment_of(boundaries)`, which gives the inline environment for now (S0007 adds the container one). `StageLauncher`, `AfterAgent` and `StageRunner` call the environment instead of `run_sealed` and `UndoService`, and the preflight's agent-run probe runs through it too; none of them knows podman, zfs or `sudo`. `AgentAftermath.undo` becomes `take: TakeReport`, so the aftermath and the journal's closing paragraph read one type whatever the environment, and the undo's `UndoReport` is turned into a `TakeReport` whose `left` is its reverted and deleted paths joined. The journal's sentence stays `The factory undid changes outside the write paths: ...` (decision 9 of `feature.md`). Every stage behaves exactly as today: the suite's stage, after-agent, launch, finish, probe and fault-path tests stay green with the two assertions decision 18 e names changed. This story also writes the decision-log entry of the design. What stays: `run_sealed`, `SealedRun`, `UndoService` and `UndoReport`, used by the inline environment, untouched; and `StallService` (`factory.application.stalls`), which still undoes on its own after a stall: the stall's take under the container environment is S0007's.

## Interface

`factory.application.stage_environment` (`application`), new:

```python
class StageEnvironment(ABC):
    """Where a stage's agent works and how its result comes back: one cycle behind one interface."""

    @abstractmethod
    def prepare(self, commit: CommitId, branch: str, *, sync_time_limit: timedelta) -> None:
        """Make the place the agent works in hold `branch` at `commit`, its tools synced.

        `SnapshotError` or `ContainerError` when that cannot be done; the sync's container
        gets `sync_time_limit`.
        """

    @abstractmethod
    def run_agent(
        self,
        request: AgentRunRequest,
        *,
        run: Callable[[AgentRunRequest], AgentRunResult] | None = None,
    ) -> SealedRun:
        """Run `request`'s agent in this environment, through `run` or the boundaries' runtime.

        `run` is called once; whatever it does inside (resumes after a provider limit) happens
        in the same prepared place. The result and the nested repositories removed after it.
        """

    @abstractmethod
    def take(self, stage_start: StageStart, work_item_path: str) -> TakeReport:
        """Bring the agent's result into the factory's work tree, as far as the role may write.

        `WorkItemFormatError` naming `work_item_path` when the work item is absent or
        unreadable at the stage-start commit; the work tree is then left untouched.
        """


class InlineEnvironment(StageEnvironment):
    """v1.1's way: the agent in the factory's own checkout, sealed around; the undo after."""

    def __init__(self, boundaries: Boundaries) -> None: ...


def stage_environment_of(boundaries: Boundaries) -> StageEnvironment:
    """The environment the boundaries describe: the inline one (S0007 adds the container one)."""
```

- `InlineEnvironment.prepare(...)` does nothing and reads nothing (a `commit`, a `branch` and any `sync_time_limit` are accepted and ignored).
- `InlineEnvironment.run_agent(request, run=run)` is `run_sealed(boundaries, request, run=run)` and returns what it returns.
- `InlineEnvironment.take(stage_start, work_item_path)` is `UndoService(boundaries).undo(stage_start, work_item_path)` turned into `TakeReport(left=sorted({*reverted, *deleted}), restored_work_item=restored_work_item)`.
- `SealedRun` is the model of `factory.application.sealed_runs`; `TakeReport` the one of `factory.application.take` (S0004); `StageStart` of `factory.application.claims`; `CommitId` of `factory.domain.git`. The interface follows `CLAUDE.md` (abstract base class, docstring-only abstract methods, no state); `tests/application/test_interfaces.py` gains it (decision 18 e).

`factory.application.stage` (`application`):

```python
class StageLauncher:
    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
        *,
        stage_environment: StageEnvironment | None = None,
    ) -> None: ...


class AfterAgent:
    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        *,
        stage_environment: StageEnvironment | None = None,
    ) -> None: ...


class AgentAftermath(BaseModel):
    ...
    take: TakeReport     # in place of `undo: UndoReport`
    ...
```

- `stage_environment` `None` means `stage_environment_of(boundaries)`. `StageRunner.__init__` builds one environment with `stage_environment_of(boundaries)` and gives it to both its launcher and its after-agent, so that one object sees a stage's prepare and take.
- `StageLauncher.launch`, after the claim is pushed and the pull request ensured and before the cost record begins: `stage_environment.prepare(started.stage_start.commit, started.branch, sync_time_limit=<the sync limit>)`, where the sync limit is `definition.project_commands["sync"].time_limit` in minutes when the definition has a `sync` command and otherwise the default of a project command, `ProjectCommandDefinition().time_limit` (10 minutes) (decision 3). Then `stage_environment.run_agent(request, run=PatientRuns(boundaries).run)` in place of `run_sealed(...)`. `SnapshotError` and `ContainerError` from `prepare` propagate as `AgentRuntimeError` does.
- `AfterAgent.process`: `take = stage_environment.take(started.stage_start, started.path)` in place of the undo, at the same point; the entry's closing paragraph names `sorted(path for path in take.left if path != <the own cost records path>)`, as today it names the reverted and deleted paths less the sidecar; `AgentAftermath.take` carries the report.
- `StageFinisher` is unchanged (the checks go through `boundaries.project_commands`).
- `factory.application.preflight.agent_run_probe_item`: `stage_environment_of(boundaries).run_agent(request)` in place of `run_sealed(boundaries, request)`; the item's reading of the result and of the nested repositories is unchanged.

Tests (the tester writes them): `tests/application/test_stage_environment.py` (the interface and `InlineEnvironment` against `run_sealed` and the undo, on the `boundaries` fixture with `FakeAgentRuntime`), `tests/application/test_stage_environment_protocol.py` (a stand-in `StageEnvironment` that records its calls, given to `StageLauncher` and `AfterAgent`, to pin the order and the arguments), and the two assertions of `tests/application/test_after_agent.py` named in decision 18 e. `tests/application/test_stage_run.py`, `test_stage_launch.py`, `test_stage_finish.py`, `test_sealed_runs*.py`, `test_undo.py`, `test_agent_run_probe*.py` and the fault-path tests are not changed and stay green.

## Acceptance criteria

1. `StageEnvironment` is an abstract base class whose abstract members are exactly `{"prepare", "run_agent", "take"}`; it cannot be instantiated; its module names no `Protocol` (rows of the parametrized tests of `tests/application/test_interfaces.py`, which gains it).
2. `InlineEnvironment(boundaries).prepare("a" * 40, "work-item/F0001-S0001", sync_time_limit=timedelta(minutes=5))` returns `None` and changes nothing: `boundaries.git.status()` and `boundaries.git.work_tree_id()` are the same before and after, and the fake runtime got no request.
3. `InlineEnvironment(boundaries).run_agent(request)` with a queued `FakeAgentRuntime` run that writes `tests/test_a.py` returns a `SealedRun` whose `result` is the queued one and whose `nested_repositories` is `[]`; the `.git` folder is sealed during the run and the agent's run saw it so (as `tests/application/test_sealed_runs_runner.py` reads it); with `run=<a recorder>` the recorder is called once with the request and the runtime is not called (rows of one parametrized test); a run that leaves `notes/.git` returns `nested_repositories` `["notes/.git"]` and the folder is gone.
4. `InlineEnvironment(boundaries).take(start, PATH)` after an agent wrote `docs/new.md` (outside the write paths), changed `docs/guide.md` and wrote `src/kept.py` (inside) returns `TakeReport(left=["docs/guide.md", "docs/new.md"], restored_work_item=False)`, the two outside paths are back as committed and `src/kept.py` keeps the agent's text; with the work item's state changed by the agent, `restored_work_item` is true; a work item absent at the stage-start commit raises `WorkItemFormatError` naming the path (rows of one parametrized test).
5. `stage_environment_of(boundaries)` returns an `InlineEnvironment`.
6. `StageLauncher` calls the environment in order: with a recording stand-in environment, `launch(prepared)` calls `prepare(<the stage-start commit>, "work-item/F0001-S0001", sync_time_limit=timedelta(minutes=5))` when the definition's `project_commands` holds `sync: {time_limit: 5}`, and with `sync_time_limit=timedelta(minutes=10)` when the definition has no `sync` (rows of one parametrized test); the `prepare` call comes after the claim's push (the remote's branch already holds the stage-start commit when the stand-in is called) and before `run_agent`; `run_agent` is called once with the composed request, and its `run` is a callable that runs the boundaries' runtime (calling it runs the queued fake run).
7. A `prepare` that raises `SnapshotError("reset", "no base")` ends `launch` with that error, after the claim was pushed (the remote's branch holds the stage-start commit) and before any agent run (the fake runtime got no request) and before a cost record was begun (the sidecar `cost_records_path(PATH)` does not exist in the work tree).
8. `AfterAgent.process` calls `take(<the stage start>, PATH)` once on its environment and not the undo (a stand-in environment whose `take` returns `TakeReport(left=["src/b.py"], restored_work_item=False)`: the aftermath's `take` is that report, and the entry's text ends with `\n\nThe factory undid changes outside the write paths: src/b.py.`); a `left` that holds the own cost records path and `src/b.py` gives a paragraph naming `src/b.py` only; an empty `left` gives no paragraph (rows of one parametrized test).
9. `StageLauncher(boundaries, INSTANCE, definition, ENVIRONMENT)` and `AfterAgent(boundaries, INSTANCE, definition)` built without the keyword run the inline environment: a whole stage through `StageRunner` on the `boundaries` fixture, whose agent writes a file outside the write paths, ends as today with that file put back and the entry's paragraph naming it (one test in the new module, beside `tests/application/test_stage_run.py`, which is unchanged and green). The one environment object per `StageRunner` is pinned by S0007 through its one timing line per stage.
10. `agent_run_probe_item` runs the probe through the environment: on the `boundaries` fixture it behaves as today (`tests/application/test_agent_run_probe*.py` unchanged and green: a completed run passes, a run that leaves `x/.git` fails the item naming the path), and the module `factory.application.preflight` no longer imports `run_sealed` (a structural assertion in the new module over the module's imports, so that the probe cannot bypass the environment).
11. `make check` stays green.
12. docs: `docs/project-guide/stage-environment.md` gains the section *The stage environment* (the interface's three operations and their contracts, `InlineEnvironment` as v1.1's way, `stage_environment_of`, who calls what and when in the stage protocol, the `sync` time limit's source, the one environment object per `StageRunner`); `docs/project-guide/stages.md`, *Starting a stage* and *After the agent run*: the environment's `prepare`, `run_agent` and `take` in place of `run_sealed` and the undo, `AgentAftermath.take`; `docs/project-guide/write-guard.md`, *The undo*: the undo is the inline environment's take, and the container environment's take is in `stage-environment.md`; `docs/project-guide/README.md`, *The files*, names `factory.application.stage_environment`; `docs/decisions.md` gains the entry **One snapshot instead of many layers**: the design of 2026-10-24 (one ZFS dataset, one base snapshot, throwaway containers, the take), the human's decisions 1 to 9 of `planning/v1.2-plan.md` in one sentence each, what the take keeps from the undo (the refusal rule, the in-progress rule, the work item's restore, the journal's paragraph), that `InlineEnvironment` is the second implementation beside S0007's `ContainerEnvironment` until F0044 removes it, and that the journal sentence stays until then (decision 9 of `feature.md`).

## Smoke test

```bash
uv run pytest tests/application/test_stage_environment.py tests/application/test_stage_environment_protocol.py tests/application/test_after_agent.py tests/application/test_stage_run.py tests/application/test_agent_run_probe.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
uv run python - <<'EOF'
from factory.application.stage_environment import InlineEnvironment, StageEnvironment
from factory.application.take import TakeReport

print(sorted(StageEnvironment.__abstractmethods__), issubclass(InlineEnvironment, StageEnvironment))
print(TakeReport(left=["docs/new.md", "docs/guide.md"], restored_work_item=False).model_dump())
EOF
```
Expect: two lines, `['prepare', 'run_agent', 'take'] True` and `{'left': ['docs/new.md', 'docs/guide.md'], 'restored_work_item': False}`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: `factory.application.stage_environment` names `StageEnvironment` (prepare, run_agent, take, with exact signatures and raised errors), `InlineEnvironment(boundaries)` and `stage_environment_of(boundaries)`. It also names the `StageLauncher`, `AfterAgent` and `AgentAftermath.take` changes and the preflight probe change. Each inline operation is defined by what it delegates to (`run_sealed`, `UndoService`, `TakeReport(left=sorted({*reverted, *deleted}), ...)`), and the sync-limit rule and the closing-paragraph rule are stated.
   - Criteria: 1 to 10 are each testable by one test function or one parametrized test. Every Interface rule has its own criterion on both sides:
     - sync limit: 5 min with a `sync` command, 10 min without (criterion 6).
     - the order of prepare and run_agent, after the claim's push and before the cost record (6 and 7).
     - `SnapshotError` from prepare (7).
     - the cost-records path left out of the paragraph, and an empty `left` giving no paragraph (8).
     - `WorkItemFormatError` on an absent work item (4).
     - `run` given or not given, and nested repositories (3).
     - the default environment when the keyword is omitted (9).
     - the probe no longer importing `run_sealed` (10).
     Criterion 11 is `make check`; criterion 12 is the docs criterion and closes the list. No Interface rule is left without a criterion.
   - Smoke test: both blocks are runnable. The project's pytest `addopts` already holds `-q` and the first command passes none, so the `N passed in` summary line the `grep` expects is printed. Both `Expect:` lines are checkable against the output (`1`, and the two exact lines).
   - Architecture: the interface sits in `factory.application` as an ABC with docstring-only abstract methods, as CLAUDE.md requires. `InlineEnvironment` composes existing application services and is the only place that knows `run_sealed` and the undo. Nothing in `domain` or `adapters` changes, so the layer order holds. It uses `TakeReport` from S0004, built before this story.
   - Scope: it is inside `feature.md`'s Scope for S0005 and decisions 1 to 4, 9 and 18 e. The journal sentence is unchanged (decision 9). `StallService` is left alone (decision 20). The only changes to earlier tests are the two assertions in `test_after_agent.py` and the `test_interfaces.py` addition, which decision 18 e allows.
4. factory: started tests as self.
