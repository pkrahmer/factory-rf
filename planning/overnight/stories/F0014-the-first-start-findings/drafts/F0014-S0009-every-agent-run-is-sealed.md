# Every agent run is sealed

## Assignment (as of log entry 1)

F0014-S0006 made the factory alone write the checkout's `.git` and checks it at the start of every iteration. An agent run can still rename `.git` away and put a folder of its own in its place, since the work tree's root stays group-writable. So the factory seals `.git` right before every agent run and checks it right after, and a failed check ends the tick without any further git command in that checkout: the next iteration's preparation removes the checkout and clones it again (S0006). The stage's run and the preflight's probe both go through one function. No factory git command runs between an agent run and the check: `CostRecorder.complete` runs no git, and the stage's commit comes later. An agent process that outlives its run and swaps `.git` after the check is left out (FEATURE decision 21): the time limit ends the run's processes. This story is the run half of S0006 as the pre-check split it (FEATURE decisions 19 to 21, 24 and 30); it is built right after S0006 and before S0010, which adds the search for nested repositories to the same function, and S0003, whose probe runs through it. No earlier test changes.

## Interface

A new module `src/factory/application/sealed_runs.py`: `run_sealed(boundaries: Boundaries, request: AgentRunRequest) -> AgentRunResult`. It calls `boundaries.git.seal()`, then `boundaries.agent_runtime.run(request)`, and in a `finally` `boundaries.git.check_seal()`. So a `RepositoryUnsealed` after the run wins over an error of the run, which becomes its context. When the seal fails, no run starts.

`StageLauncher.launch` (`src/factory/application/stage.py`) and `agent_run_probe_item` (`src/factory/application/preflight.py`) call `run_sealed` in place of `agent_runtime.run`. The probe still catches only `AgentDefinitionError` and `AgentRuntimeError`, so a `RepositoryUnsealed` leaves the item as an exception, and `Preflight.run` lets it out, since the probe runs among the machine's items, outside the `except` of the probe of `main`. `launch`'s docstring adds `RepositoryUnsealed` to what propagates.

`src/factory/application/dispatcher.py`: `Dispatcher.dispatch` re-raises `RepositoryUnsealed` from a handler before its `except Exception`, without counting an error. Every other handler error is counted as now.

Tests: a new module `tests/application/test_sealed_runs.py`, on the `boundaries` fixture, whose git is a real clone. The runtimes that swap `.git` or record modes are implementations of `AgentRuntime` written in the test, wrapping `FakeAgentRuntime`. A group-writable `.git` is a `Path.chmod` by the test. The dispatcher's criterion goes into a new test module `tests/application/test_dispatcher_unsealed.py`. No test of an earlier story changes.

## Acceptance criteria

1. `run_sealed` seals before the run: a runtime that records, during its run, the modes of `.git` (set to `0o2775` by the test) and of `.git/config` (`0o666`) sees `0o2755` and `0o644`. `run_sealed` returns the runtime's result.
2. `run_sealed` raises in these cases, rows of one parametrized test:
   - after a run that renames `.git` to `.git-moved` and puts a folder at `0o2775` in its place: `RepositoryUnsealed`
   - after a run that puts a symbolic link to `.git-moved` in its place: `RepositoryUnsealed`
   - when the run makes that swap and then raises `AgentRuntimeError`: `RepositoryUnsealed`, whose `__context__` is the `AgentRuntimeError`
   - when `.git` is missing before the run: `RepositoryUnsealed`, and the runtime records no request
   - when the run raises `AgentRuntimeError` and leaves `.git` alone: that `AgentRuntimeError`
3. `StageLauncher.launch` and `agent_run_probe_item` run the agent through `run_sealed`, one test each. With a runtime that swaps `.git` as in criterion 2, `launch` raises `RepositoryUnsealed`, and the probe item raises it instead of returning a failed item. Raised from the probe, it leaves `Preflight.run` unhandled (the probe runs among the machine's items, outside the `except` of the probe of `main`), so the scheduler logs the iteration as failed.
4. `Dispatcher.dispatch` lets a handler's `RepositoryUnsealed` pass and counts no error for the event, while a handler's other `GitError` is counted as before (rows of one parametrized test).
5. What must still hold: the existing tests of the stage, the probe, the preflight, the tick and the dispatcher pass.
6. `make check` stays green.
7. docs: The project guide describes `run_sealed` and its two callers, and says that the dispatcher passes `RepositoryUnsealed` through and that a probe's `RepositoryUnsealed` ends the iteration. The decision log's entry "The factory alone writes the checkout's `.git`" gets the run half: why the check after the run, why the dispatcher does not count it, and the window left open (an agent process that outlives its run, decision 21). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_sealed_runs.py tests/application/test_dispatcher_unsealed.py tests/application/test_stage_launch.py tests/application/test_agent_run_probe.py tests/application/test_dispatcher.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
