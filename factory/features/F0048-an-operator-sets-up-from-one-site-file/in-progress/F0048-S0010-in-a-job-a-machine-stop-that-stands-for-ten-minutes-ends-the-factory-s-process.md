---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 510
comments_read: [6593349810]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T01:48:13.042987Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T01:48:13.049237Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T01:48:30.728166Z'
  stage: intake
  run: 2c16476198aa479e8bd2ed2806c47089
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T01:52:24.305779Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T01:52:27.166605Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T01:52:45.004087Z'
  stage: intake
  run: 7d9fa92636d949688f02a13ee7c7be48
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T01:52:50.442397Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T01:56:13.607668Z'
  stage: tests
  run: 7e37009ea8424aa691d71dadff3db83c
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T01:56:19.531735Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-03T02:03:21.647825Z'
  stage: doing
  run: 03f774929e4443f9be9f1b1c106875ef
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-03T02:03:27.853199Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-03T02:05:07.309292Z'
  stage: review
  run: 02b6639c03904a3fbf8229ad2a0afca8
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-03T02:05:14.033796Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-03T02:05:32.047337Z'
  stage: doing
  run: b2c0c26ff2c043199bce0a867c25f984
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T02:05:37.712753Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-03T02:07:48.671159Z'
  stage: tests
  run: 884259bcabda44378bb3f576606416d8
---

# In a job a machine stop that stands for ten minutes ends the factory's process

## Description

On a VM a machine stop waits for a fix the operator makes on the machine, so the idle shutdown does not count a tick that ended at a stop, and the machine stays up while the stop stands. In a Cloud Run job nobody can fix anything on the machine: its file system is memory and is gone with the execution, and the only fix is a new execution with other settings. On 2026-11-02 (`planning/cloud-sandbox/TRIAL-2-F0001-IN-A-JOB.md`, finding 4) a run that stopped at the preflight (`tool:uv: uv is not on the PATH`) held its eight CPUs for over forty minutes, until its job was deleted, and the platform showed it as running, not as failed. This story ends the factory's process when a machine stop has stood for ten minutes and the idle shutdown's action is `exit` (the job profile's setting since F0047-S0008). The process ends with status 1, so the execution ends as failed and the stop's line is the last the log shows. A VM (`poweroff`, or the idle shutdown off) keeps today's behaviour, and so does a stop of any other scope: a repository stop is lifted by a push to `main`, which a job can see.

## Interface

- The rule holds when `FACTORY_IDLE_SHUTDOWN_MINUTES` is above 0 and `FACTORY_IDLE_SHUTDOWN_ACTION` is `exit`. It is a fixed ten minutes, not a setting.
- When a stop of scope `machine` has stood for ten minutes or more (counted from the stop's own time `at`) at the end of a tick, or of an iteration that ran no tick, the factory writes the line `machine stop: standing for 10 minutes in a job, ending the factory's process: <the stop's reason>: <its detail>` to the factory log and ends the loop as the idle exit does. `main` then returns 1, not 0.
- A machine stop that is lifted before the ten minutes (the preflight passes on a later tick) ends nothing; a new machine stop counts from its own time.
- The idle exit itself is unchanged: after an idle stretch `main` still returns 0.
- Where the rule lives and how it reaches the loop is the coder's choice within the layers; it reads the stops the factory already keeps (the health status) and the clock of the boundaries, and it starts no process.

Tests (the tester writes them): a new module under `tests/entry/` beside `tests/entry/test_run_idle_exit.py`, the scheduler with the suite's scripted ticks and a manual clock, no sleep. Every existing idle-shutdown test passes unchanged.

## Acceptance criteria

1. With minutes 30 and `exit`, a machine stop raised at time T and still standing: the loop runs on at T + 9 minutes and ends after the first tick or iteration at T + 10 minutes or later; the log holds the line of the Interface with the stop's reason and detail; no tick runs after it; `main` with that runner returns 1.
2. The sides of the ten minutes, as rows of one parametrized test: a stop standing 9 minutes 59 seconds ends nothing, one standing exactly 10 minutes ends the loop.
3. A machine stop lifted at T + 5 minutes ends nothing, and a second machine stop raised at T + 8 minutes ends the loop only at T + 18 minutes.
4. The rule does not hold, as rows of one parametrized test, and the loop runs on past T + 30 minutes with the stop standing: `poweroff`; minutes 0 with `exit`; a stop of scope `repository` with `exit`.
5. The idle exit is unchanged: idle ticks with no stop end the loop after the idle stretch and `main` returns 0.
6. A machine stop raised again on every tick with its `at` at that tick's time, as the preflight raises it (raises at T, T + 5 and T + 9 minutes), ends the loop at the first tick at T + 10 minutes or later: the count runs from the first raise of an unbroken stretch, not from the latest `at`.
7. When a machine stop ends the loop, the line of the Interface is the last line of the factory log.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: in the idle shutdown's paragraph *In a job*, that a machine stop which stands for ten minutes ends the process with status 1, so the execution ends as failed and the job's log names the stop, and that a VM keeps waiting for a fix; in the list of stops or the preflight's part, the same in one sentence. `docs/decisions.md`: an entry *In a job a machine stop ends the process*, from the feature's decision 13. `README.md`: none.

## Smoke test

```bash
grep -n "standing for 10 minutes in a job" docs/operator-guide.md | head -1 | cut -d: -f1 | grep -c .
```

Expect: one line, `1`.

```bash
uv run pytest tests/entry/test_run_idle_exit.py 2>&1 | tail -n 1
```

Expect: one line that says the tests passed and names no failure.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: 1. Smoke test, second block: `uv run pytest -q tests/entry/test_run_idle_exit.py 2>&1 | tail -n 1` passes `-q`, but `pyproject.toml` line 100 already sets `addopts = "-q --strict-markers ..."`. That makes `-qq`, and pytest prints no summary line. The `Expect:` ("says the tests passed and names no failure") cannot be met. Options: (a) drop `-q` from the command, which is what I would choose; (b) change the Expect to the exit status, for example `; echo $?` with `Expect: 0`. Please pick one.

   The format check passed. The Interface, the criteria (both sides of the ten minutes, the lifted stop, the three non-holding cases, the idle exit), the scope and the architecture are otherwise fine. The first smoke test block is runnable but is only decidable once the docs stage has run.
4. 2026-11-03 human: (a), as you propose: drop `-q` from the second smoke test command; the Expect stays.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: the rule's conditions (minutes above 0, action `exit`), the fixed ten minutes counted from the stop's `at`, the exact log line, return status 1, the lifted and renewed stop, and the unchanged idle exit are all stated. The placement is left to the coder within the layers, and the story says it reads the health status and the boundary clock and starts no process.
   - Criteria: criteria 1 to 5 each fit one test function. Criterion 1 covers the main path, the log line with reason and detail, no tick after it, and `main` returning 1. Criterion 2 covers both sides of the ten minutes. Criterion 3 covers the lifted stop and the renewed stop counting from its own time. Criterion 4 covers the three cases where the rule does not hold (`poweroff`, minutes 0, scope `repository`). Criterion 5 covers the idle exit returning 0. Criteria 6 and 7 close the list as the form requires.
   - Smoke test: I carried in the human's answer from journal entry 4 and dropped `-q` from the second command, because `pyproject.toml` already sets `-q` in `addopts`. The `Expect:` line is unchanged. The first block (a grep for the guide's line, expecting `1`) is runnable and checkable once the docs stage has run.
   - Architecture: the rule needs no new layer. It reads the stops the factory already keeps and acts through the existing loop exit, so it fits the layers in `CLAUDE.md`.
   - Scope: the story matches `feature.md` (S0010, decision 13). `src/factory/` is touched only for the machine-stop rule in a job, which the feature's out-of-scope section allows.
7. factory: started tests as vm.
8. tester: Wrote the tests for criteria 1 to 5 in a new module beside `tests/entry/test_run_idle_exit.py`. Every test drives `main` with a runner that calls `run_instance`, the way the existing idle-exit test of `main` does. The ticks are scripted and run on the manual clock, with no sleep. The scripted tick raises, keeps or lifts one stop in the health status (`health_store` of the state directory) at the step's time, so the stop's `at` is T. While the stop stands, the tick returns `TickOutcome(stopped=<reason>)`. The environment names `FACTORY_STATE` as the instance's state directory, so the coder may choose how `main` learns the status: an exception through the runner, or what the state directory holds.

   - criterion 1: tests/entry/test_run_machine_stop_exit.py::test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one
   - criterion 2: tests/entry/test_run_machine_stop_exit.py::test_a_machine_stop_ends_the_loop_from_ten_minutes_on (rows `9-minutes-59-seconds`, `10-minutes`)
   - criterion 3: tests/entry/test_run_machine_stop_exit.py::test_a_lifted_machine_stop_ends_nothing_and_a_new_one_counts_from_its_own_time
   - criterion 4: tests/entry/test_run_machine_stop_exit.py::test_a_standing_stop_ends_nothing_where_the_rule_does_not_hold (rows `poweroff`, `idle-shutdown-off`, `repository-stop`)
   - criterion 5: tests/entry/test_run_machine_stop_exit.py::test_the_idle_exit_without_a_stop_still_ends_the_loop_with_status_zero
   - criteria 6 and 7: no test (`make check`, and docs for the docs stage).

   Files: I created `tests/entry/test_run_machine_stop_exit.py`. Under the standing leave to move a shared test helper, I moved the fixtures `instance_settings` and `on_the_manual_clock` from `tests/entry/test_run_idle_exit.py` to `tests/conftest.py`. I changed `tests/entry/test_run_idle_exit.py` only to drop those two fixtures and the imports they alone used; every test in it keeps its name and checks the same thing.

   Run: `uv run pytest -q tests/entry/test_run_machine_stop_exit.py tests/entry/test_run_idle_exit.py` failed exactly the three tests where the loop should end: criterion 1, criterion 2's `10-minutes` row and criterion 3. The other new tests and every idle-exit test passed. The runner imported every module; nothing is missing, because the behaviour does not exist yet and the failures are wrong results. After that run I changed only the fixture's and helper's arguments to keyword-only, which ruff's PLR0917 asked for. `make lint` is green. I skipped the type check, as the stage says.

   Rejected: checking that the stop's line is the last line of the log. The Description says it but criterion 1 does not, so I left it out.

   Open, for the coder: `StopService.raise_stop` puts each raise into the health status through `with_stop`, which replaces a standing stop of the same reason. The preflight raises again on every failing tick with `at=clock.now()`, so as the code stands now the stop's `at` moves forward on each tick. The rule counts from the stop's own `at`, and these tests write `at` once.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Built the rule that, in a job, a machine stop standing for ten minutes ends the factory's process with status 1. `make check` is green.

    - `src/factory/application/machine_stop_exit.py` (new): `MachineStopExit` with `MACHINE_STOP_LIMIT = timedelta(minutes=10)`. Its `observe()` reads the machine-scope stops from the health status. Once one has stood for the limit on the boundaries' clock, it writes `machine stop: standing for 10 minutes in a job, ending the factory's process: <reason>: <detail>`, sets `ended` and calls `request_stop`. It starts no process.
    - `src/factory/entry/wiring.py`: `machine_stop_exit_of(settings, boundaries, request_stop)` returns the rule only when the idle shutdown is on with `exit`, and `None` otherwise. Like `_idle_power`, it raises `ValueError` when it gets no `request_stop`.
    - `src/factory/entry/run.py`: `run_instance` wraps the scheduler's `prepare` and `tick` with `_observed_iteration`. `observe` then runs after every tick, or after a `prepare` that left no tick to run. After the loop it raises `MachineStopStood` if the rule ended it, and `main` turns that into status 1. The idle exit still returns 0.
    - `src/factory/domain/errors.py`: `MachineStopStood(FactoryError)`.

    Main choice: where the time is counted from. The tester flagged that the preflight raises its machine stop again on every failing tick, and `HealthStatus.with_stop` replaces the stop, so its `at` moves forward each tick. Counting naively from `at` would therefore never fire in production. `MachineStopExit` keeps, per reason, the earliest `at` of an unbroken stretch, and forgets it once the stop is lifted. So the count runs from the stop's own first time, and a new stop counts from its own time. I rejected changing `with_stop` to keep the standing stop's `at`: that would change what the health status and its other readers mean, beyond this story.

    Second choice: how the check reaches the loop. I first added an `after_iteration` hook to `Scheduler`. Ruff refused six constructor arguments (PLR0913/PLR0917), so I left `Scheduler` untouched and composed the hook in `run_instance`.

    Refactor: `observed_iteration` served only `run_instance`, so I made it private and took it out of `__all__`. Nothing else needed changing.

    Noticed but not touched:
    - `HealthStatus.with_stop` moves a re-raised stop's `at` forward, so the health file shows the last raise rather than the first. Whether that is intended is a question for another story.
    - Two lines are uncovered: the observation after a `prepare` that is not ready (`run.py`, the `observe()` in `observed_prepare`), and the `ValueError` without `request_stop` in `wiring.py`. Coverage is 99.5 %, well above the 90 % minimum.

    The journal did not change the meaning of the task. Its only change was the smoke test's dropped `-q`, which intake had already carried in.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Findings:

    1. Criterion 6 added: it needs its test. The preflight raises its stop again on every failing tick. `StopService.raise_stop` and `HealthStatus.with_stop` then replace the stop, so its `at` moves forward. `MachineStopExit.observe` in `src/factory/application/machine_stop_exit.py` keeps the earliest `at` of an unbroken stretch in `_since`, but every test in `tests/entry/test_run_machine_stop_exit.py` writes `at` only once. If the `min(...)` were removed, every test would still pass, and the rule would never fire in production. The fix is a test whose tick raises the stop again with the tick's time at T, T+5 and T+9, and that expects the loop to end at T+10. The Interface's words "counted from the stop's own time `at`" now mean the first raise of the stretch, as the coder chose (journal entry 10).
    2. Criterion 7 added: it needs its test. The Description says "the stop's line is the last the log shows", and the code does this: nothing is written after `observe`, and the comment on the `except MachineStopStood` branch in `main` says so. No criterion named it, and the tester left it out on purpose (journal entry 8). The fix is to check, in criterion 1's test, that the log's last line is `_line("preflight_failed")`.
    3. The test for criterion 1 (`tests/entry/test_run_machine_stop_exit.py::test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one`) does not test what the Interface rule and criterion 1 promise for "an iteration that ran no tick". The path where `prepare` returns `False` (`observed_prepare` in `_observed_iteration`, `src/factory/entry/run.py`) runs in no test; the coder reported this line as uncovered. The fix is a case, either a row of that test or a test of its own, in which `prepare` returns `False` while a machine stop stands, for example a remote whose `main` lacks the pipeline definition so that `RepositoryWaiter` holds `repository_unavailable`, with the stop written into the health status. It should expect the loop to end at the first iteration at T+10 or later and `main` to return 1.
    4. `_StopTick` in `tests/entry/test_run_machine_stop_exit.py` copies `_ScriptedTick` from `tests/entry/test_run_idle_exit.py`: `_start`, `_steps`, `runs`, `exhausted` and the clock advance to each step's time. `_RunMain.__call__` also copies the `build_tick` patch from `_scripted` and the `runner` from `test_main_returns_zero_after_the_idle_exit_ends_the_loop`. The fix is to move `_ScriptedTick` and `_scripted` to a `tests/*_support.py` module under the standing leave, and to build the stop tick and the `main` runner on them.

    Architecture: holds. `MachineStopExit` is in `factory.application`, reads only `HealthStatusStore`, `Clock` and `FactoryLog`, and starts no process. The wiring is in `factory.entry.wiring`, and the composition is in `factory.entry.run`.
    Security: clean. There are no markers, no secrets and no strings handed to a shell.
    Description: matches what was built. The docs criterion (now 9) still describes what the reader must know.

    Earlier tests:
    - `tests/conftest.py`: standing leave to move a shared test helper. The fixtures `instance_settings` and `on_the_manual_clock` moved here from `tests/entry/test_run_idle_exit.py` unchanged.
    - `tests/entry/test_run_idle_exit.py`: standing leave to move a shared test helper. Only those two fixtures and the imports they alone used were removed; every test keeps its name and checks the same thing.
13. factory: started doing as vm.
14. coder: Round 1: I changed no code. All four of the reviewer's findings (entry 12) are test changes, and the code they test is already in place from my round-0 entry (10). For the tester:

    1. Criterion 6 needs its test, in `tests/entry/test_run_machine_stop_exit.py`. A tick raises the machine stop again, with `at` set to that tick's time, at T, T + 5 and T + 9 minutes. The test expects the loop to end at the first tick at T + 10 minutes or later. This test fails if `MachineStopExit.observe` (`src/factory/application/machine_stop_exit.py`) dropped the `min(...)` that keeps the earliest `at` of an unbroken stretch.
    2. Criterion 7 needs its test. In criterion 1's test (`test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one`), also check that the stop's line from the Interface is the last line of the factory log.
    3. Criterion 1's "an iteration that ran no tick" needs a case, either a row of criterion 1's test or a test of its own. In it, `prepare` returns `False` while a machine stop stands in the health status, for example a remote whose `main` lacks the pipeline definition. The case expects the loop to end at the first iteration at T + 10 minutes or later, and `main` to return 1. The path it covers is `observed_prepare` in `_observed_iteration`, `src/factory/entry/run.py`.
    4. A shared test helper moves, under the standing leave. Move `_ScriptedTick` and `_scripted` from `tests/entry/test_run_idle_exit.py` to a new `tests/*_support.py` module. Build `_StopTick` and `_RunMain` in `tests/entry/test_run_machine_stop_exit.py` on them, including the `build_tick` patch and the `main` runner of `test_main_returns_zero_after_the_idle_exit_ends_the_loop`. Every earlier test keeps its name and checks the same thing.

    Main choice: I end with `tests` and change no code. The alternative I rejected was adding code to fit the coverage gap of finding 3: the path exists and only lacks its test.

    The journal changed the meaning of the task: the reviewer added criteria 6 and 7, which the Description already holds, and the work item is outside my write paths, so I did not rewrite anything.

    Noticed but not touched: `HealthStatus.with_stop` still moves a re-raised stop's `at` forward, so the health file shows the last raise rather than the first. This is unchanged from my round-0 entry.

    Refactor: there is no diff this round, so there was nothing to refactor.
15. factory: started tests as vm.
16. tester: Made the four test changes the reviewer listed in entry 12 and the coder named in entry 14. I did not change any code.

    Mapping (every test is in `tests/entry/test_run_machine_stop_exit.py`):
    - criterion 1: `test_a_machine_stop_standing_ten_minutes_in_a_job_ends_the_loop_and_main_returns_one`. Its iteration that runs no tick is covered by `test_a_machine_stop_ends_the_loop_after_iterations_that_ran_no_tick` (new; reviewer finding 3).
      - In the new test, a repository URL that does not exist makes `prepare` return `False` on every iteration, while a machine stop written at T stands in the health status.
      - The loop's sleep moves the manual clock forward and fails the test once the clock passes T + 30 minutes.
      - The test expects every pause before T + 10 minutes, the loop ended at T + 10 minutes or later, no tick run, `main` returning 1, the stop's line written once, and that line last in the log.
    - criterion 2: `test_a_machine_stop_ends_the_loop_from_ten_minutes_on` (rows `9-minutes-59-seconds`, `10-minutes`)
    - criterion 3: `test_a_lifted_machine_stop_ends_nothing_and_a_new_one_counts_from_its_own_time`
    - criterion 4: `test_a_standing_stop_ends_nothing_where_the_rule_does_not_hold` (rows `poweroff`, `idle-shutdown-off`, `repository-stop`)
    - criterion 5: `test_the_idle_exit_without_a_stop_still_ends_the_loop_with_status_zero`
    - criterion 6: `test_a_machine_stop_raised_again_on_every_tick_counts_from_its_first_raise` (new). The stop is raised again with that tick's time at T, T+5, T+9 and T+10. The loop should end after the fourth tick. Without the `min(...)` in `MachineStopExit.observe`, the T+10 raise would reset the count, so the test would fail.
    - criterion 7: criterion 1's test now also checks that the log's last line ends with the stop's line. The no-tick test checks the same.
    - criteria 8 and 9: no test (`make check`, and the docs for the docs stage).

    Files:
    - Created `tests/scripted_tick_support.py`.
    - Changed `tests/entry/test_run_machine_stop_exit.py` (my own module from entry 8).
    - Changed `tests/entry/test_run_idle_exit.py` under the standing leave to move a shared test helper (reviewer finding 4). Its `_ScriptedTick`, `_scripted`, `_run` and the inline `main` runner of `test_main_returns_zero_after_the_idle_exit_ends_the_loop` moved to the support module, under these names:
      - `ScriptedTick`: now generic over a step's action, with a `play` function; the idle tests play the outcome itself.
      - `installed`: the `build_tick` patch.
      - `scripted`, `run_loop` and `run_main`.
      - Every test in `tests/entry/test_run_idle_exit.py` keeps its name and checks the same thing. The stop tick in the new module is now a `ScriptedTick` with a play that raises, lifts or keeps the stop.

    One change the move needed: `run_main`'s runner keeps each loop's stop event before the loop runs. This is because `run_instance` raises `MachineStopStood` and so returns no event. `run_loop` takes the event as an optional keyword argument.

    Run: `uv run pytest -q tests/entry/test_run_machine_stop_exit.py tests/entry/test_run_idle_exit.py tests/test_shared_imports.py` passed all 30 tests. The code exists from round 0, so these tests are green, not red. Every module imported. `make lint` is green. Because the code exists, I also ran `make types`, and it is green.

    Rejected: putting the no-tick case in as a row of criterion 1's test. It needs a different repository, a sleep that moves the clock, and no scripted ticks, so it is its own test.

    `lint`: lint: green (0.1 s)
