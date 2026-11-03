---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 510
comments_read: [6593349810]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-03T01:52:50.442397Z'
  lease_duration: 60
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
6. `make check` stays green.
7. docs: `docs/operator-guide.md`: in the idle shutdown's paragraph *In a job*, that a machine stop which stands for ten minutes ends the process with status 1, so the execution ends as failed and the job's log names the stop, and that a VM keeps waiting for a fix; in the list of stops or the preflight's part, the same in one sentence. `docs/decisions.md`: an entry *In a job a machine stop ends the process*, from the feature's decision 13. `README.md`: none.

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
