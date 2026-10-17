---
stage: done
pr: 193
blocked: null
comments_seen: 2
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
5. human (pull request comment, 2026-10-17): (a): the tester annotates `outcome: str` before the `try`; the code keeps `DispatchOutcome`. The criterion is unchanged.
6. coder: The human answered option (a) in entry 5, so this run sends the ticket back to the tester for one test change. I changed no code. The implementation in 62639596 stays as it is, and `Dispatcher.dispatch` keeps its `DispatchOutcome` return type.

   The test change, in `tests/application/test_dispatcher_unsealed.py`, in `test_a_handlers_unsealed_repository_passes_uncounted_and_another_git_error_counts`: before the `try`, declare `outcome: str`. That way the `except RepositoryUnsealed` branch's `outcome = "raised"` passes `mypy --strict` (it fails now with "Literal['raised']" not assignable to `DispatchOutcome`, at line 43). Nothing else in the test or its parameter rows changes.

   After that change, `make types` should be the last red check. In entry 4, lint, layers, sast, secrets, licenses and test were all green. I did not run `make check` in this run, because nothing changed.
7. tester: Made the one test change the human approved in entry 5 and the coder named in entry 6. In `tests/application/test_dispatcher_unsealed.py::test_a_handlers_unsealed_repository_passes_uncounted_and_another_git_error_counts` I declared `outcome: str` just before the `try`. Now the `except RepositoryUnsealed` branch can assign `outcome = "raised"` and still pass `mypy --strict`, while `Dispatcher.dispatch` keeps its `DispatchOutcome` return type. I changed nothing else: not the parameter rows, not the assertions, not any other test.

   After the change:
   - `make test`: test: green (29.8 s)
   - `make lint`: lint: green (0.1 s)
   - `make types`: types: green. This was the check that was red in entry 4. I did not run the full `make check`; the factory runs it next.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (28.9 s)
8. coder: The tester's change in entry 7 made `make types` green. I ran `make check` on the committed state and it ended with `check: green` (test: green, coverage 99.48 %). This run changed no code. The implementation is still the one in 62639596:
   - `src/factory/application/sealed_runs.py`: `run_sealed` calls `git.seal()`, then the agent run in a `try`, then `git.check_seal()` in its `finally`. If the seal fails, no run starts. If the check after the run fails, its `RepositoryUnsealed` wins, and the run's error becomes its `__context__`.
   - `src/factory/application/stage.py` (`StageLauncher.launch`) and `src/factory/application/preflight.py` (`agent_run_probe_item`) both run the agent through `run_sealed`. The probe still catches only `AgentDefinitionError` and `AgentRuntimeError`. `launch`'s docstring now lists `RepositoryUnsealed` among what it lets through.
   - `src/factory/application/dispatcher.py`: `dispatch` re-raises `RepositoryUnsealed` before its `except Exception` and does not count it as an error.

   Main decision: I used `try/finally` and not an explicit `except` that wraps the run's error. With `finally`, Python's implicit exception chaining sets `__context__` for us, which is exactly the behaviour the Interface asks for.

   Refactor: I read the diff (4 files, +30/−8) again and found no duplication and nothing unclear, so I changed nothing.

   Open: the docs criterion (7) is for the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
9. reviewer: no findings.

   What I checked, against the diff (`git diff main...HEAD -- . ':!factory'`, 6 files) and the code around it, not against the log:
   - Criterion 1: `test_the_run_sees_a_sealed_git_folder_and_its_result_is_returned` opens `.git` to 0o2775 and `.git/config` to 0o666. It asserts that the runtime sees 0o2755 and 0o644 during the run, and that it gets back the runtime's own result.
   - Criterion 2: `test_a_run_raises_unless_git_is_sealed_before_and_after_it` has the five rows the criterion lists, all in one parametrized test:
     - Folder in place, link in place, and swap followed by `AgentRuntimeError` all raise `RepositoryUnsealed`. The last row also asserts that `__context__` is the `AgentRuntimeError`.
     - A missing `.git` raises `RepositoryUnsealed` with no request recorded, so the failing side of "no run when the seal fails" is tested.
     - A run error that leaves `.git` alone raises exactly that `AgentRuntimeError`.
     - Each of these sides holds in `src/factory/application/sealed_runs.py`: `seal` runs outside the `try` and `check_seal` runs in the `finally`.
   - Criterion 3: `test_launch_raises_when_the_run_swaps_git` covers `StageLauncher.launch`. `test_the_probe_raises_when_the_run_swaps_git_and_the_preflight_lets_it_out` covers `agent_run_probe_item`, and also `Preflight.run` with the probe as one of `MachineChecks`' extra items. In the code:
     - `Preflight.run` (`src/factory/application/preflight.py`) catches `GitError` only around `_probe`, the probe of `main`. The machine's items are outside that `except`, so the error gets out.
     - From there, only `Scheduler._iterate`'s `except Exception` in `src/factory/application/scheduler.py` catches it, and it logs the iteration as failed.
   - Ending the tick: in `src/factory/application/stage.py`, a `RepositoryUnsealed` from `launch` passes `self._after.process` without any handler that runs git. `Tick.run` in `src/factory/application/tick.py` has no `except` around `dispatch`. `CheckoutPreparer._keep_or_clone_again` then clones again on the next iteration.
   - Callers: `run_sealed` is now the only caller of `agent_runtime.run` in `src/factory/application`.
   - Criterion 4: `test_a_handlers_unsealed_repository_passes_uncounted_and_another_git_error_counts` has two rows: the unsealed error is raised and not counted, and a plain `GitError` still counts. The re-raise in `src/factory/application/dispatcher.py` sits before `except Exception`, which needs it because `RepositoryUnsealed` is a subclass of `GitError`.
   - Test changes: no existing test changed. The only change to the new dispatcher test, the `outcome: str` annotation, was approved by the human in entry 5.
   - Architecture: `sealed_runs.py` sits in `factory.application` and uses only the `Git` and `AgentRuntime` interfaces through `Boundaries`. The tests' runtimes inherit `AgentRuntime` and wrap `FakeAgentRuntime`, and git is a real clone.
   - Security: no suppression markers, secrets, or strings built into shell or SQL commands.
   - Quality: the module and function docstrings are there, and the comments say why. `make duplicates` reported 0 new.
   - Make check: green according to the coder's entry 8. I did not run it myself, as this stage says.
   - Ticket hygiene: entry 8 gives the main decision (`try/finally` and its implicit `__context__` instead of wrapping the error explicitly). The Assignment matches what was built, and criterion 7 still says what the documenter must write.
10. documenter: wrote the docs criterion (7) and found no findings for the coder.

    Files changed:
    - docs/project-guide.md: added a paragraph "Every agent run is sealed" before the `CheckoutPreparer` text. It covers `run_sealed`, its order (seal, run, `check_seal` in a `finally`), which error wins, the two callers, and the tests. The preflight paragraph now says the probe runs through `run_sealed` and that its `RepositoryUnsealed` is not caught, so it leaves `Preflight.run` and the scheduler logs the iteration as failed. The dispatcher paragraph now says `RepositoryUnsealed` is re-raised and not counted, and that other errors are counted as before.
    - docs/decisions.md: the entry "The factory alone writes the checkout's `.git`" gets the run half in place of the "S0009 adds…" pointer. It gives why the check comes after the run, why the dispatcher does not count the error, and the open window (an agent process that outlives its run, decision 21, closed only by the time limit).

    Cross-read and found current: the project guide's sections on `Git.seal` and `check_seal`, the stage launcher and the scheduler's checkout preparation, plus the decisions entries on hooks and the shared checkout. I did not read README or the operator guide in depth, because the criterion says no other document changes.

    `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, since I changed only docs; the factory runs it next.

    Stale text seen and not touched: none.

    `make check`: check: green
    `make documents`: documents ok
11. demo: no findings.

    Command 1, run from the repository root:
    `uv run pytest --no-header -p no:cacheprovider tests/application/test_sealed_runs.py tests/application/test_dispatcher_unsealed.py tests/application/test_stage_launch.py tests/application/test_agent_run_probe.py tests/application/test_dispatcher.py`

    ```
    ................................................................         [100%]
    64 passed in 3.32s
    ```

    Meets its `Expect:` line. The last line says `64 passed`, with no `failed`, `error` or `skipped` count.

    Checked against the acceptance criteria:
    - Criteria 1 to 4: their tests are in `test_sealed_runs.py` and `test_dispatcher_unsealed.py`, and all of them passed in this run.
    - Criterion 5: the existing suites for the stage launcher, the agent-run probe and the dispatcher passed in the same run.
    - Criteria 6 (`make check`) and 7 (docs): the demo does not exercise them, and nothing in its output contradicts them. Entries 8 and 10 report `check: green` and `documents ok`. The factory runs `make check` itself after this stage.

    Nothing is open.
12. done (pull request merged); cost: 9 runs, 7.2 min, 64 turns, 241k tokens in (1128k more from cache), 27k out, $1.74
