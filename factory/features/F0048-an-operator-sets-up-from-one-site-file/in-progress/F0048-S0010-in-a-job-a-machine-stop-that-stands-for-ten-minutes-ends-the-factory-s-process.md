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
uv run pytest -q tests/entry/test_run_idle_exit.py 2>&1 | tail -n 1
```

Expect: one line that says the tests passed and names no failure.

## Journal
