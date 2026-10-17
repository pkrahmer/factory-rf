---
stage: doing
pr: 193
blocked: asked
comments_seen: 1
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: concrete. It names the new module `src/factory/application/sealed_runs.py` and the signature `run_sealed(boundaries: Boundaries, request: AgentRunRequest) -> AgentRunResult`. It gives the call order (seal, run, `check_seal` in a `finally`) and says which error wins. It names both callers (`StageLauncher.launch`, `agent_run_probe_item`), the exceptions the probe still catches, and the dispatcher's re-raise before `except Exception`.
   - Criteria: each can be tested by one test function. Criterion 2 is a parametrized table. Every behaviour the Interface states has a criterion: seal before run (1), the check after the run (2), `RepositoryUnsealed` winning over a run error with the run error as `__context__` (2), no run when the seal fails (2), both callers (3), and the dispatcher pass-through (4). Every rule has its failing side and its passing side. The failing sides are a swapped `.git`, a symlinked `.git`, a missing `.git` (no request recorded), and an unsealed run that also raises. The passing sides are a run error with `.git` left alone, which propagates unchanged, and a handler's other `GitError`, which is still counted.
   - Demo: the one pytest command is runnable and names the new and the existing test modules. Its `Expect:` line can be checked against the last line: `<n> passed`, with no failed, error or skipped count.
   - Architecture: `run_sealed` sits in `factory.application` and uses only the `Boundaries`' git and agent runtime interfaces. It names no concrete tool, and no layer rule is broken. The tests mirror the package under `tests/application/`, use the real-clone `boundaries` fixture, and wrap `FakeAgentRuntime`.
   - Scope: it stays inside S0009 of F0014 (FEATURE decisions 19 to 21, 24 and 30). The nested-repository search (S0010) and the login probe (S0003) are left out, and no test of an earlier story changes. The source files it touches are the ones FEATURE lists for S0009.
3. tester: Wrote red tests for the criteria that carry behaviour (1 to 4). Criteria 5 to 7 need no new test: 5 is the existing suites, 6 is `make check`, 7 is the docs stage's.

   Criterion → test:
   - criterion 1: tests/application/test_sealed_runs.py::test_the_run_sees_a_sealed_git_folder_and_its_result_is_returned. The test sets `.git` to 0o2775 and `.git/config` to 0o666. `ModeRecordingRuntime` records the modes during the run and must see 0o2755 and 0o644. `run_sealed` must return the runtime's result.
   - criterion 2: tests/application/test_sealed_runs.py::test_a_run_raises_unless_git_is_sealed_before_and_after_it, one parametrized test with five rows:
     - folder-in-place: `.git` is renamed to `.git-moved`, and a copy of it at 0o2775 is put in its place, so the only fault is the write bits.
     - link-in-place: a symbolic link to `.git-moved` is put in its place.
     - swap-then-runtime-error: the same swap, but no run is queued, so the fake raises `AgentRuntimeError`. Expects `RepositoryUnsealed` with that error as `__context__`.
     - missing-before-the-run: expects `RepositoryUnsealed` and no request recorded.
     - runtime-error-git-alone: expects exactly `AgentRuntimeError`.
   - criterion 3: tests/application/test_sealed_runs.py::test_launch_raises_when_the_run_swaps_git checks that `StageLauncher.launch` raises `RepositoryUnsealed`. tests/application/test_sealed_runs.py::test_the_probe_raises_when_the_run_swaps_git_and_the_preflight_lets_it_out covers the probe: `agent_run_probe_item` raises it, and `Preflight.run` lets it out when the probe is one of `MachineChecks`' extra items.
   - criterion 4: tests/application/test_dispatcher_unsealed.py::test_a_handlers_unsealed_repository_passes_uncounted_and_another_git_error_counts has two rows. With `RepositoryUnsealed`, the error is raised and none is counted. With a plain `GitError`, the outcome is "error" and one error is counted.

   How the test runtimes work: `SwappingRuntime` and `ModeRecordingRuntime` are `AgentRuntime` implementations written in the test, wrapping `FakeAgentRuntime`. The swap first removes an old `.git-moved` if one is there, so the preflight's second probe run can swap again.

   Files created:
   - tests/application/test_sealed_runs.py
   - tests/application/test_dispatcher_unsealed.py

   The one `make test` run failed as expected:
   - test_sealed_runs.py does not import: there is no module `factory.application.sealed_runs`.
   - The dispatcher's `unsealed` row fails, because the error is still counted today.
   - The dispatcher's `other-git-error` row already passes; that is the side that should keep working.

   `make lint` is green. The type check was skipped, as this stage says.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/application/test_sealed_runs.py - ImportError while importing tes...
4. coder: Implemented and committed (62639596); `make check` is red only in `make types`, because of the new test `tests/application/test_dispatcher_unsealed.py`, which I may not edit.

   Built:
   - `src/factory/application/sealed_runs.py`: `run_sealed(boundaries, request)` calls `git.seal()`, then `agent_runtime.run(request)` in a `try`, and `git.check_seal()` in its `finally`. So a `RepositoryUnsealed` after the run wins, with the run's error as its `__context__`, and a failed seal starts no run.
   - `src/factory/application/stage.py`: `StageLauncher.launch` runs the agent through `run_sealed`. Its docstring now lists `RepositoryUnsealed` among what propagates.
   - `src/factory/application/preflight.py`: `agent_run_probe_item` runs the probe through `run_sealed` and still catches only `AgentDefinitionError` and `AgentRuntimeError`.
   - `src/factory/application/dispatcher.py`: `dispatch` re-raises `RepositoryUnsealed` before its `except Exception`, without counting it. `Handler.handle`'s docstring says so.

   Check status: `make lint`, `layers`, `sast`, `secrets`, `licenses` and `test` are all green; every test passes, including the new ones. `make types` fails on one line:
   `tests/application/test_dispatcher_unsealed.py:43: error: Incompatible types in assignment (expression has type "Literal['raised']", variable has type "Literal['handled', 'error', 'reported', 'capped']")`
   In the `try` branch, mypy infers `outcome` as `DispatchOutcome` from `dispatcher.dispatch(event)`. The `except` branch then assigns `"raised"`, which is not one of those values.

   Options:
   (a) The tester annotates the variable as `outcome: str` before the `try` (for example `outcome: str = ""`, or annotate the first assignment). This is a one-line test change, and the code stays as it is.
   (b) I widen `Dispatcher.dispatch`'s return type to `str`, or add `"raised"` to `DispatchOutcome`. Either one weakens the code's type to fit a test, and `dispatch` never returns "raised".
   I would choose (a). If you agree, the next doing run ends with `tests`, naming that change.

   Refactor: I read the diff once. It is small and has no duplication, so I changed nothing.
