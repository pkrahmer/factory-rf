---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 413
comments_read: [6386836732]
handed_over: null
claim: null
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
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T16:36:52.342214Z'
  stage: tests
  run: 7336a875eae54b5e9b26859bf910fcd0
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T16:37:13.005926Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-24T16:42:02.763957Z'
  stage: doing
  run: 90f92333839449f29571eafa1234633e
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-24T16:44:24.361800Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T16:44:42.306544Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T16:45:03.263639Z'
  stage: doing
  run: 2cc9e218150b4d158b43ba0d0f35baf3
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T16:45:23.705334Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-24T16:47:51.373709Z'
  stage: tests
  run: 356cf8efca6d43f19ad5b62713c47446
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T16:48:13.023216Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T16:51:02.354770Z'
  stage: doing
  run: 8139ab9e11214d67bc10b1d7bbb7e7bc
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T16:51:23.262479Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-24T16:53:17.071816Z'
  stage: review
  run: d34a0c10a37a4a1ba1bf7e7f48fb1b66
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-24T16:53:37.626414Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-24T16:53:59.393253Z'
  stage: doing
  run: 7e0dc298ba894ff1a4794d9fdd3c29e3
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T16:54:19.905053Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-24T16:57:00.412418Z'
  stage: tests
  run: 70ecb979916643a98ccacdc00357a86b
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

Tests (the tester writes them): `tests/application/test_stage_environment.py` (the interface and `InlineEnvironment` against `run_sealed` and the undo, on the `boundaries` fixture with `FakeAgentRuntime`), `tests/application/test_stage_environment_calls.py` (a stand-in `StageEnvironment` that records its calls, given to `StageLauncher` and `AfterAgent`, to pin the order and the arguments), and the two assertions of `tests/application/test_after_agent.py` named in decision 18 e. `tests/application/test_stage_run.py`, `test_stage_launch.py`, `test_stage_finish.py`, `test_sealed_runs*.py`, `test_undo.py`, `test_agent_run_probe*.py` and the fault-path tests are not changed and stay green.

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
11. `InlineEnvironment(boundaries).take(start, PATH)` with the work item unreadable at the stage-start commit (its front matter broken there) raises `WorkItemFormatError` naming the path, as an absent one does; in both cases the work tree is left untouched: a file the agent wrote outside the write paths keeps the agent's text after the raise (rows of the parametrized test of criterion 4).
12. `make check` stays green.
13. docs: `docs/project-guide/stage-environment.md` gains the section *The stage environment* (the interface's three operations and their contracts, `InlineEnvironment` as v1.1's way, `stage_environment_of`, who calls what and when in the stage protocol, the `sync` time limit's source, the one environment object per `StageRunner`); `docs/project-guide/stages.md`, *Starting a stage* and *After the agent run*: the environment's `prepare`, `run_agent` and `take` in place of `run_sealed` and the undo, `AgentAftermath.take`; `docs/project-guide/write-guard.md`, *The undo*: the undo is the inline environment's take, and the container environment's take is in `stage-environment.md`; `docs/project-guide/README.md`, *The files*, names `factory.application.stage_environment`; `docs/decisions.md` gains the entry **One snapshot instead of many layers**: the design of 2026-10-24 (one ZFS dataset, one base snapshot, throwaway containers, the take), the human's decisions 1 to 9 of `planning/v1.2-plan.md` in one sentence each, what the take keeps from the undo (the refusal rule, the in-progress rule, the work item's restore, the journal's paragraph), that `InlineEnvironment` is the second implementation beside S0007's `ContainerEnvironment` until F0044 removes it, and that the journal sentence stays until then (decision 9 of `feature.md`).

## Smoke test

```bash
uv run pytest tests/application/test_stage_environment.py tests/application/test_stage_environment_calls.py tests/application/test_after_agent.py tests/application/test_stage_run.py tests/application/test_agent_run_probe.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
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
5. tester: I wrote the tests for criteria 1 to 10 against the Interface. They are red on purpose: `make test` fails at collection because `factory.application.stage_environment` does not exist yet, and the after-agent tests fail with `AttributeError: 'AgentAftermath' object has no attribute 'take'`. `make lint` is green.

   Criterion to test:
   - criterion 1: tests/application/test_interfaces.py gains `StageEnvironment` as a row of `INTERFACES` (id `stage-environment`). That gives it rows in each_interface_is_an_abstract_base_class, no_class_in_the_interface_modules_derives_from_protocol, an_interface_has_no_public_member_but_its_abstract_operations, every_abstract_method_body_is_its_docstring_alone and an_interface_cannot_be_instantiated. It also gains one line in test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract: `StageEnvironment.__abstractmethods__ == {"prepare", "run_agent", "take"}`.
   - criterion 2: tests/application/test_stage_environment.py::test_prepare_does_nothing_and_reads_nothing
   - criterion 3: tests/application/test_stage_environment.py::test_run_agent_is_the_sealed_run_through_the_runtime_or_the_given_run (rows runtime / given-run) and ::test_run_agent_removes_a_nested_repository_and_names_it
   - criterion 4: tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report (rows work-item-untouched / work-item-state-changed / work-item-absent)
   - criterion 5: tests/application/test_stage_environment.py::test_the_environment_of_the_boundaries_is_the_inline_one
   - criterion 6: tests/application/test_stage_environment_protocol.py::test_the_launch_prepares_after_the_claim_then_runs_the_agent_through_the_environment (rows sync-command / no-sync-command)
   - criterion 7: tests/application/test_stage_environment_protocol.py::test_a_refused_prepare_ends_the_launch_after_the_claim_and_before_the_run
   - criterion 8: tests/application/test_stage_environment_protocol.py::test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry (rows one-path / own-cost-records-left-out / nothing-left)
   - criterion 9: tests/application/test_stage_environment_protocol.py::test_a_stage_built_without_an_environment_runs_the_inline_one
   - criterion 10: tests/application/test_stage_environment_protocol.py::test_the_preflight_does_not_import_the_sealed_run. This is a structural check over the `ImportFrom` names in `factory.application.preflight`. The probe's behaviour is still covered by tests/application/test_agent_run_probe*.py, which I did not change.
   - criteria 11 and 12: `make check` and docs, so no test of mine.

   How the tests work:
   - The protocol tests use a stand-in, `RecordingEnvironment(StageEnvironment)`. It records the order of calls, the arguments and the remote branch head at the moment of `prepare`. Its `run_agent` calls the `run` it is given; that is how the tests show `run` runs the boundaries' runtime. Its `take` returns the report the test sets.
   - Criterion 8 also checks that the undo did not run: the agent's `src/b.py` is still in the work tree.
   - The inline tests reuse helpers from existing test modules (`ModeRecordingRuntime`, `Runner`, `NestingRuntime`, `_without_work_item`) and from `undo_support` / `stage_run_support`. I moved none of them.

   Files created: tests/application/test_stage_environment.py and tests/application/test_stage_environment_protocol.py.

   Earlier test files changed:
   - tests/application/test_interfaces.py: the row and the one line above.
   - tests/application/test_after_agent.py: the two assertions the description names (decision 18 e) now read `aftermath.take.left` instead of `aftermath.undo.reverted` / `deleted`: `OUTSIDE in aftermath.take.left` and `(PATH in aftermath.take.left) is not kept`.

   Modules the test run could not import: `factory.application.stage_environment`. Because of it, tests/application/test_interfaces.py, test_stage_environment.py and test_stage_environment_protocol.py fail at collection.

   Nothing open. No project skill applied.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/application/test_stage_environment_protocol.py - ImportError while importing test module '/work/checkout/tests/application/test_stage_environment_protocol.py'.
6. factory: started doing as self.
7. coder: The code is in place, but two tests contradict each other and `make check` is red on one of them.

   **The conflict.** `make test` fails only `tests/test_test_names.py::test_no_test_module_is_named_after_a_protocol`:

   ```
   E   AssertionError: assert [PosixPath('/...protocol.py')] == []
   FAILED tests/test_test_names.py::test_no_test_module_is_named_after_a_protocol
   ```

   That existing test refuses any test module with "protocol" in its file name. The tester's new module is `tests/application/test_stage_environment_protocol.py`, and the work item asks for that exact name in its Interface ("Tests") and in the first smoke-test command. Every other test is green, coverage is 99.19 %, and lint, types, layers, sast, secrets and licenses are green. I changed no test.

   **Options:**
   - (a) The tester renames the module, for example to `tests/application/test_stage_environment_calls.py`. Its contents stay the same. The work item's Interface and smoke test then name the new file.
   - (b) Relax `tests/test_test_names.py` so it allows this module. That is a change to another story's test, and that test records a naming rule of the project.

   I would choose (a). With your answer I end with `tests`, naming the rename, and the tester makes it.

   **What I built:**
   - `src/factory/application/stage_environment.py` (new):
     - `StageEnvironment`: an abstract base class with `prepare`, `run_agent` and `take`.
     - `InlineEnvironment`: `prepare` does nothing, `run_agent` is `run_sealed`, and `take` is `UndoService.undo` turned into `TakeReport(left=sorted({*reverted, *deleted}), ...)`.
     - `stage_environment_of`, which returns the inline environment.
   - `src/factory/application/stage.py`:
     - `StageLauncher` and `AfterAgent` take a keyword-only `stage_environment`; the default is `stage_environment_of(boundaries)`.
     - `launch` calls `prepare(stage_start.commit, branch, sync_time_limit=...)` after composing the request and before `CostRecorder.begin`, then calls `run_agent(request, run=PatientRuns(...).run)`.
     - The sync limit comes from `_sync_time_limit`: the definition's `sync` command when it has one, otherwise `ProjectCommandDefinition()`.
     - `AgentAftermath.undo: UndoReport` is now `take: TakeReport`. The journal's closing paragraph names `take.left` without the sidecar.
     - `StageRunner` builds one environment and gives it to both its launcher and its after-agent.
   - `src/factory/application/preflight.py`: the probe now runs through `stage_environment_of(boundaries).run_agent(request)` and no longer imports `run_sealed`.

   **Main choice:** the default sync limit comes from the model's own default, `ProjectCommandDefinition().time_limit`. I rejected a separate 10-minute constant in `stage.py`, which would be a second copy of the default that could drift.

   **Refactor:** I read my diff and nothing needed changing.

   **Not touched:**
   - `StallService` still undoes on its own, as the description says.
   - `UndoReport` is still used by `stalls.py` and `undo_support`.
   - The docs criterion is left to the documenter.
8. 2026-10-24 human: Answer to the coder (F0042-S0005, the stage protocol calls the stage environment, and the inline environment is today's way): **(a)**. The tester renames the module to `tests/application/test_stage_environment_calls.py`, with the same contents. `tests/test_test_names.py` stays as it is: its naming rule holds. The story's Interface ("Tests") and the first smoke-test command name the new file; the reviewer writes that into the work item.
9. factory: started doing as self.
10. coder: The human chose (a), so the tester renames `tests/application/test_stage_environment_protocol.py` to `tests/application/test_stage_environment_calls.py`, with its contents unchanged. This clears the one red test, `tests/test_test_names.py::test_no_test_module_is_named_after_a_protocol`.

    - **Code:** I changed nothing in this run. The code from my previous entry is already committed:
      - `src/factory/application/stage_environment.py`
      - `src/factory/application/stage.py`
      - `src/factory/application/preflight.py`
    - **Work item:** I did not touch the Description. The human's answer gives the update to the reviewer: the Interface's "Tests" paragraph and the first smoke-test command should name the new file.
    - **Main choice:** none in this run; the choice from my previous entry stands.
    - **Open:** after the rename, the stage comes back to me to confirm `make check` is green.
11. factory: started tests as self.
12. tester: I made the rename the human approved in entry 8 and the coder named in entry 10. I renamed `tests/application/test_stage_environment_protocol.py` to `tests/application/test_stage_environment_calls.py` and left its contents unchanged. No other file referred to the old module name, so nothing else changed.

    The test functions and their criteria are the same as in entry 5. Only the module path is new:
    - criterion 6: tests/application/test_stage_environment_calls.py::test_the_launch_prepares_after_the_claim_then_runs_the_agent_through_the_environment
    - criterion 7: tests/application/test_stage_environment_calls.py::test_a_refused_prepare_ends_the_launch_after_the_claim_and_before_the_run
    - criterion 8: tests/application/test_stage_environment_calls.py::test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry
    - criterion 9: tests/application/test_stage_environment_calls.py::test_a_stage_built_without_an_environment_runs_the_inline_one
    - criterion 10: tests/application/test_stage_environment_calls.py::test_the_preflight_does_not_import_the_sealed_run
    - criteria 1 to 5: unchanged, as listed in entry 5.

    Files created: none; one file renamed. Modules the test run could not import: none.

    `make test` is now green, with coverage at 99.19 %, so `tests/test_test_names.py::test_no_test_module_is_named_after_a_protocol` passes. `make lint` is green.

    Open: the reviewer still has to change the work item's Interface ("Tests") and its first smoke-test command to name the new file, as the human's answer says.

    `lint`: lint: green (0.6 s)
    `test`: test: green (61.1 s)
13. factory: started doing as self.
14. coder: The tester renamed the test module as the human asked in entry 8 (now `tests/application/test_stage_environment_calls.py`). `make check` is now green: `check: green`, coverage 99.19 %. I changed no code in this run. The code from entry 7 is already committed and stays as it was.

    What I built (from entry 7):
    - `src/factory/application/stage_environment.py`, new:
      - `StageEnvironment`: the interface with three operations, `prepare`, `run_agent` and `take`.
      - `InlineEnvironment`: `prepare` does nothing; `run_agent` calls `run_sealed`; `take` runs `UndoService.undo` and turns its result into `TakeReport(left=sorted({*reverted, *deleted}), restored_work_item=...)`.
      - `stage_environment_of(boundaries)`, which returns the inline environment.
    - `src/factory/application/stage.py`:
      - `StageLauncher` and `AfterAgent` take an optional keyword `stage_environment`.
      - `launch` calls `prepare` after the claim and the request are made and before the cost record begins. It then calls `run_agent(request, run=PatientRuns(...).run)`.
      - The time limit for the `sync` command comes from `_sync_time_limit`.
      - `AgentAftermath.take: TakeReport` replaces `undo: UndoReport`. The journal's closing paragraph names `take.left` without the work item's own cost records file.
      - `StageRunner` builds one environment and gives it to both the launcher and the after-agent.
    - `src/factory/application/preflight.py`: the agent-run probe goes through `stage_environment_of(boundaries).run_agent(request)` and no longer imports `run_sealed`.

    Main choice: when the pipeline definition has no `sync` command, the time limit is the model's own default, `ProjectCommandDefinition().time_limit`. I did not add a separate 10-minute constant, because a second copy of that default could drift from the model.

    Refactor: I read my diff again in this run. Nothing needed changing.

    Description: I did not edit it. Entry 8 does not change what the task means. It only changes the test module's name, and the human asked the reviewer to update the Interface's "Tests" paragraph and the first smoke-test command. Both still name `test_stage_environment_protocol.py` and need to say `test_stage_environment_calls.py`.

    Noticed, not touched:
    - `StallService` still undoes on its own, as the description says.
    - `UndoReport` is still used by `stalls.py` and by the test helpers in `undo_support`.
    - The docs criterion (12) is the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 14 new, 37 known, 1 gone
15. factory: started review as self.
16. reviewer: 1. criterion 11 added: it needs its test. Location: `tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report`. The Interface's `take` contract says `WorkItemFormatError` "when the work item is absent or unreadable at the stage-start commit; the work tree is then left untouched". The test has only the absent row, and that row returns right after `pytest.raises` without checking the work tree. No criterion covered the unreadable side or the untouched work tree. The fix is a tests-only change: add an unreadable row (the broken front matter, as `_with_broken_work_item` in `tests/application/test_undo.py` builds it, imported from there as `_without_work_item` already is), and after the raise assert in both refusal rows that the agent's outside file (`GUIDE` or `NEW_DOC`) still holds `AGENT_TEXT`. `src/` needs no change, because `UndoService` already behaves this way (see `test_undo.py::test_a_missing_or_unreadable_baseline_raises_before_any_path_is_changed`). The `make check` and docs criteria are renumbered to 12 and 13.

    Work item changes the human asked for in entry 8, made here: the Interface's "Tests" paragraph and the first smoke-test command now name `tests/application/test_stage_environment_calls.py` instead of `test_stage_environment_protocol.py`. Nothing else in the Description or Interface changed.

    What I checked and found sound:
    - Criteria 1 to 10 each have a test that checks what the criterion says.
    - The sync limit is tested on both sides: 5 minutes with a `sync` command, 10 minutes without.
    - `prepare` is called after the claim push, before `run_agent`, and before the cost record. The raise path is covered.
    - The paragraph rows cover the own cost-records path and an empty `left`.
    - The layers hold: `stage_environment` imports only application and domain modules. The interface is an ABC whose abstract methods have docstring-only bodies.
    - The diff has no suppression markers.
    - `make duplicates` (I ran it to read the new findings) shows two new findings for this diff: vulture's "unused variable 'sync_time_limit'" at `src/factory/application/stage_environment.py:21` and `:58`. Both are the interface parameter that the inline no-op ignores by design, so they are not findings. The other twelve new findings come from earlier stories' modules (`fake_containers`, `podman_runs`, `zfs_snapshots`, `take`, `containers`).
    - I did not run `make check`. Entry 14 says it was green.

    Earlier tests:
    - tests/application/test_after_agent.py: decision 18 (e) of `feature.md` (the human's leave). Only the two assertions changed, to read `aftermath.take.left`, and each test keeps its name and rows.
    - tests/application/test_interfaces.py: decision 18 (e) of `feature.md` (the human's leave). It gains the `StageEnvironment` row and the one `__abstractmethods__` assertion.
17. factory: started doing as self.
18. coder: The reviewer added criterion 11 in entry 16. It needs only a test, so I changed no code and I am handing the work item to the tester.

    Criterion to test: criterion 11, in `tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report`.
    - Add a `work-item-unreadable` row: the work item's front matter is broken at the stage-start commit. `_with_broken_work_item` in `tests/application/test_undo.py` builds that case and can be imported, the same way `_without_work_item` already is.
    - In both refusal rows (absent and unreadable), assert after the `WorkItemFormatError` that the agent's file outside the write paths (`GUIDE` or `NEW_DOC`) still holds `AGENT_TEXT`. That shows the work tree is left untouched.

    No code change is needed. `InlineEnvironment.take` in `src/factory/application/stage_environment.py` passes the call to `UndoService.undo`, and that already raises before it changes any path. `tests/application/test_undo.py::test_a_missing_or_unreadable_baseline_raises_before_any_path_is_changed` pins this.

    Built: nothing new this round. The code from entry 7 stands: `src/factory/application/stage_environment.py`, `src/factory/application/stage.py` and `src/factory/application/preflight.py`.

    Main choice: I hand off with `tests` and do not add any code. The reviewer's finding asks only for a test, and this work item's role never changes tests. I rejected writing a guard of my own in `InlineEnvironment.take`, because it would copy the check the undo already makes.

    Description: the reviewer already updated it in entry 16 (criterion 11, the renamed test module), so I did not rewrite it.

    Noticed, not touched:
    - `StallService` still runs the undo on its own, as the description says.
    - `UndoReport` is still used by `stalls.py` and by `undo_support`.
    - The docs criterion (13) is the documenter's.
19. factory: started tests as self.
20. tester: I made the test change the coder's entry 18 asked for, so that criterion 11 is tested. The reviewer's entry 16 sets out what was missing.

    Changed: `tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report`
    - New row `work-item-unreadable`. It uses `_with_broken_work_item`, imported from `tests/application/test_undo.py` next to `_without_work_item`.
    - New check in both refusal rows (absent and unreadable): after the `WorkItemFormatError` is raised, the test asserts that `GUIDE` and `NEW_DOC` still hold `AGENT_TEXT`. That shows the work tree is left untouched.
    - Reordered: the row's `change` now runs before the agent writes its files. `_with_broken_work_item` commits the checkout, so with the old order that commit would have taken in the agent's files and changed the stage-start commit. This matches the order in `test_undo.py::test_a_missing_or_unreadable_baseline_raises_before_any_path_is_changed`. The other rows don't depend on the order.

    Mapping:
    - criterion 4: tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report (rows work-item-untouched, work-item-state-changed, work-item-absent)
    - criterion 11: tests/application/test_stage_environment.py::test_take_is_the_undo_turned_into_a_take_report (rows work-item-absent, work-item-unreadable, each now checking the agent's files after the raise)
    - criteria 1 to 3 and 5 to 10: unchanged, as listed in entries 5 and 12.

    Files created: none. Earlier test files changed: none, apart from this story's own `test_stage_environment.py`. Modules the test run could not import: none.

    `make test` is green and coverage is 99.19 %. The new rows pass without any code change because `UndoService` already raises before it changes a path, as the coder said in entry 18. `make lint` is green.

    `lint`: lint: green (0.5 s)
    `test`: test: green (61.9 s)
