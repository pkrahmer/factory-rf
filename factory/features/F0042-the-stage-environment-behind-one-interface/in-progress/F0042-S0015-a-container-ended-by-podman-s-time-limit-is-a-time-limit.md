---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 419
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-24T20:16:04.304293Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T20:05:57.158017Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T20:05:57.163994Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T20:06:14.797307Z'
  stage: intake
  run: 85ee350dffac4aa2bd600fbd946aa375
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T20:06:35.163354Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T20:10:20.546515Z'
  stage: tests
  run: 483b7d5bcedf4d32b0b62b5e2757e7b9
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T20:10:41.274580Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T20:13:42.882146Z'
  stage: doing
  run: cb14b2225e9a455c8ca2aa93c2311b71
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T20:14:03.938016Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T20:15:03.925456Z'
  stage: review
  run: ccb216ff9d89440ab4b3ea20967f3eb5
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T20:15:24.738334Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T20:15:43.470907Z'
  stage: doing
  run: 4ffa9efacfa847e6ab9751266ae1e868
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T20:16:04.304293Z'
  stage: tests
---

# A container ended by podman's time limit is a time limit

## Description

The factory reads a call that its own kill ended at the time limit as `time_limit`, not as a failure: exit status 137 or -9 at or after the limit (`KILL_STATUSES` in `factory.adapters.agent_launch`). A container in v1.2 is ended by podman's own `--timeout`, and podman 4.9.3, the version Ubuntu 24.04 ships and so the VM of F0043 (the machine and the stage image) runs, ends such a container with **exit status 255**, not 137: measured on 2026-10-24 on the local VM (`planning/overnight/gcp-prototype-results-local-2026-10-24.md`, answer 5; `podman run --rm --timeout 3 ... sleep 30` ended after 3.04 s with 255). Read as today, every container that runs into its time limit (a sync, a check, an agent's call) would be a failure with status 255, and a stage would stall with the wrong reason. This story makes the two readings of a container call, `PodmanRuns.run` (S0003) and the runtimes' reading with `in_container` (S0008), take 255 at or after the limit as the kill too, beside 137 and -9. What stays: a call that is not in a container is read exactly as today (255 is no kill there); 255 before the limit is an ordinary exit status 255, as today; nothing changes for an `inline` instance. Decision 22 of `feature.md`.

## Interface

`factory.adapters.agent_launch` (`adapters`):

```python
KILL_STATUSES = frozenset({137, -9})  # unchanged
PODMAN_TIMEOUT_STATUS = 255
CONTAINER_KILL_STATUSES = KILL_STATUSES | {PODMAN_TIMEOUT_STATUS}
```

- `PODMAN_TIMEOUT_STATUS` carries a comment that says why: podman's `--timeout` ends the container with 255 (podman 4.9.3, measured 2026-10-24).
- `killed_at_limit(..., in_container=True)` reads `exit_status in CONTAINER_KILL_STATUSES` and `duration >= time_limit`; with `in_container=False` it reads `KILL_STATUSES` exactly as today, for a call with an `os_user` and for one without.
- `read_call_end` passes `in_container` through as today; no other change.

`factory.adapters.podman_runs.PodmanRuns` (`adapters`): its reading of a run's end (`_killed_at_limit` today) uses `CONTAINER_KILL_STATUSES` from `agent_launch`, not a copy: a run that ends with 137, -9 or 255 at or after its `time_limit` is a `ContainerResult` with `timed_out=True` and `exit_status=None`; 255 before the limit is `timed_out=False` with `exit_status=255`.

Tests (the tester writes them): new rows in new test modules, for example `tests/adapters/test_podman_timeout_status.py` and `tests/adapters/test_agent_launch_container_kill.py`, with the stand-in `podman` of `tests/podman_support.py` and the `recorder` fixture. No earlier test changes: every existing row with 137 or -9 stays as it is and green.

## Acceptance criteria

1. `CONTAINER_KILL_STATUSES == frozenset({137, -9, 255})`, `PODMAN_TIMEOUT_STATUS == 255` and `KILL_STATUSES == frozenset({137, -9})` (one test).
2. `killed_at_limit` (rows of one parametrized test, `time_limit` 30 s): `in_container=True` with 255 at 30 s is `True`; with 255 at 29.9 s is `False`; with 137 at 30 s is `True`; with 1 at 30 s is `False`; `in_container=False` with `os_user="agent"` and 255 at 30 s is `False`; with `os_user="agent"` and 137 at 30 s is `True`; with `os_user=None` and 255 at 30 s is `False`.
3. `PodmanRuns.run` (rows of one parametrized test, the stand-in `podman` planned to exit with the row's status after the row's time, `time_limit` from the row): 255 at or after the limit gives `timed_out=True`, `exit_status=None`; 255 well before the limit gives `timed_out=False`, `exit_status=255`; 137 at or after the limit gives `timed_out=True` as today. A row whose stand-in must outlast the limit uses `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` of `tests/time_limits.py` as `CLAUDE.md` (*Tests*) says.
4. A Claude Code call in a container (the runtime built with `containers`, as S0008's tests build it) whose recorded `ProcessResult` has `exit_status=255`, `timed_out=False` and a duration of 30 s under a `time_limit` of 30 s ends with `end_reason` `time_limit` and is not resumed; the same at 29.9 s ends `died` (rows of one parametrized test); the same two rows for opencode.
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, the section on the podman adapter: one paragraph that podman's `--timeout` ends a container with 255 (podman 4.9.3, measured 2026-10-24 on the local VM), that the factory reads 137, -9 or 255 at or after the limit as the time limit for a container call and only 137 or -9 for any other call, and why 255 before the limit stays an ordinary exit status. `docs/operator-guide.md`, the section that explains a `time_limit` stall: one sentence that on a `container` instance podman's time limit ends a call with 255, which the factory reads as the time limit. `docs/decisions.md`: none (no lasting choice beyond the measured fact). `README.md`: none.

## Smoke test

```bash
uv run python -c 'from datetime import timedelta as t; from factory.adapters.agent_launch import CONTAINER_KILL_STATUSES as c, killed_at_limit as k; print(sorted(c), k(os_user=None, exit_status=255, duration=t(seconds=30), time_limit=t(seconds=30), in_container=True), k(os_user="agent", exit_status=255, duration=t(seconds=30), time_limit=t(seconds=30)))' 2>/dev/null
```
Expect: one line, `[-9, 137, 255] True False`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete. It names `factory.adapters.agent_launch` (`KILL_STATUSES`, `PODMAN_TIMEOUT_STATUS`, `CONTAINER_KILL_STATUSES`, `killed_at_limit`, `read_call_end`) and `factory.adapters.podman_runs.PodmanRuns`. I checked these against the source. `killed_at_limit` has the keyword signature the story uses. `podman_runs._killed_at_limit` exists and currently imports `KILL_STATUSES`. `read_call_end` already takes `in_container`.
   Criteria: each is testable by one test function. Criterion 1 is the constants. Criterion 2 is a table of seven rows covering both sides of 255 and of the limit, `in_container` true and false, and `os_user` set and `None`. Criterion 3 covers 255 at the limit, 255 before it and 137 at the limit for `PodmanRuns`. Criterion 4 covers 255 at 30 s and at 29.9 s for Claude and for opencode. Every Interface rule has its failing side: 255 before the limit, and 255 outside a container.
   Smoke test: runnable. The one-line `python -c` uses the real keyword names, and the `Expect:` line `[-9, 137, 255] True False` can be checked exactly. It runs no pytest, so the `-q` rule does not apply.
   Architecture: the change stays in `factory.adapters`, where `podman_runs` already imports from `agent_launch`. It reuses one constant instead of a copy, and no new dependency or layer is involved.
   Scope: it is within F0042 (decision 22, built after S0009 and before S0010). It changes no earlier test; the story says so. The docs criterion names its files and the content for each.
4. factory: started tests as self.
5. tester: Tests written for criteria 1–4. They fail for the right reasons: the import fails, or a 255 at the limit is read as a failure. `make lint` is green.

   - criterion 1: tests/adapters/test_agent_launch_container_kill.py::test_a_container_s_kill_statuses_add_podman_s_timeout_status
   - criterion 2: tests/adapters/test_agent_launch_container_kill.py::test_255_at_the_limit_is_a_kill_only_in_a_container (the seven rows, `time_limit` 30 s)
   - criterion 3: tests/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run. It uses the stand-in `podman`. Rows: 255 at the limit, 255 at once, 137 at the limit. The time limit is `ROOMY_LIMIT`. A row at the limit has its stand-in wait `ROOMY_LIMIT` before it exits, and each row checks that the elapsed time stays under `ROOMY_BOUND_SECONDS`.
   - criterion 4: tests/adapters/test_runtime_podman_timeout_status.py::test_claude_code_in_a_container_reads_podman_s_255_at_the_limit_as_the_time_limit and ::test_opencode_in_a_container_reads_podman_s_255_at_the_limit_as_the_time_limit. Each has two rows, 30 s gives `time_limit` and 29.9 s gives `died`. The recorded `ProcessResult` has exit status 255 and `timed_out=False`. Claude goes through the `recorder` fixture. Opencode goes through a stand-in `run_streaming`, as in S0008's container tests. "Not resumed" is checked on the `time_limit` rows as exactly one recorded request. Both runtimes take their request from `opencode_request` of `tests/adapters/opencode_stand_in.py`.
   - criteria 5 and 6 (`make check`, docs): no test.

   Files created: tests/adapters/test_agent_launch_container_kill.py, tests/adapters/test_podman_timeout_status.py, tests/adapters/test_runtime_podman_timeout_status.py. No earlier test changed.

   Could not import: in `factory.adapters.agent_launch`, the names `CONTAINER_KILL_STATUSES` and `PODMAN_TIMEOUT_STATUS` do not exist yet, so test_agent_launch_container_kill.py does not collect. The other two modules import and fail on their `at-the-limit` rows (255 is read as `died` / `timed_out=False`). Their before-the-limit rows and the 137 row already pass, as they should.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/adapters/test_agent_launch_container_kill.py - ImportError while importing test module '/work/checkout/tests/adapters/test_agent_launch_container_kill.py'.
6. factory: started doing as self.
7. coder: Built: `src/factory/adapters/agent_launch.py` adds `PODMAN_TIMEOUT_STATUS = 255`, with a comment saying why: podman 4.9.3's `--timeout` ends a container with 255 (measured 2026-10-24). It also adds `CONTAINER_KILL_STATUSES = KILL_STATUSES | {PODMAN_TIMEOUT_STATUS}`. `killed_at_limit` now picks which set of kill statuses to read. With `in_container=True` it reads `CONTAINER_KILL_STATUSES`. With an `os_user` and no container it reads `KILL_STATUSES` as before. With neither it returns `False`. `read_call_end` is unchanged and still passes `in_container` through. In `src/factory/adapters/podman_runs.py`, `_killed_at_limit` now imports and reads `CONTAINER_KILL_STATUSES` from `agent_launch` instead of `KILL_STATUSES`, so there is no copy of the set.

   Main choice: I check `in_container` first and only then `os_user`. A container call can carry an `os_user` too, and it still has to accept 255. The alternative I rejected kept the old `killable` boolean and added a separate `exit_status == PODMAN_TIMEOUT_STATUS and in_container` clause. That puts two conditions on one decision and keeps the set out of sight. Picking one named set says the same thing directly.

   Refactor: I read the diff once and nothing needed changing. `make check` is green (`check: green`). The smoke test prints `[-9, 137, 255] True False` as expected.

   Noticed but did not touch: the docs this story's criterion 6 names, `docs/project-guide/stage-environment.md` and `docs/operator-guide.md`, are the documenter's job. The journal did not change what the task means, so I left the Description alone.

   `check`: check: green
   `duplicates`: duplicates: 16 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The source change matches the Interface. `PODMAN_TIMEOUT_STATUS = 255` has its why-comment, and `CONTAINER_KILL_STATUSES = KILL_STATUSES | {PODMAN_TIMEOUT_STATUS}`. `killed_at_limit` picks the set by `in_container` first, then by `os_user`. `read_call_end` is unchanged. `podman_runs._killed_at_limit` imports the shared set instead of keeping a copy.

   Groups 1 to 3 pass. Criteria 1 to 4 each have a test that checks what the criterion says. Both sides are covered: 255 at 30 s and at 29.9 s, and 255 in and out of a container. In criterion 3 the stand-in waits `ROOMY_LIMIT` under a process limit of `ROOMY_LIMIT` plus the 30 s grace, so the 255 is the reading under test and not the factory's own kill. The coder's journal says `make check` was green. The layers hold, and no silencing marker was added. Group 4 fails, in a test file the diff adds. At round 0 that sends the work item back:

   1. tests/adapters/test_runtime_podman_timeout_status.py:29-31: the `fake` fixture is a third copy of the `workspace` + `fake` fixtures in tests/adapters/test_claude_runtime_container.py:39-46 and tests/adapters/test_opencode_runtime_container.py:48-55. Fix: the tester moves `workspace` and `fake` to tests/conftest.py under the standing leave, and the three modules use them from there.
   2. tests/adapters/test_runtime_podman_timeout_status.py:34-39 and :84-85: `_request` copies `_request` of tests/adapters/test_opencode_runtime_container.py:58-66 (that one also takes `time_limit` and `os_user`). The inline `state` setup copies `_state` of the same module. Fix: move both helpers to tests/adapters/container_runtime_support.py under the standing leave, and have the earlier module and the new one import them. Every earlier test keeps its name and what it checks.

   Rejected as findings:
   - `PODMAN_TIMEOUT = 255` in the new runtime test. A literal pins the measured value.
   - The new runtime tests mirroring S0008's 137 tests. The story asks for new modules and no change to earlier tests.

   Earlier tests: none. Every test file the diff touches is new (status `A`).
10. factory: started doing as self.
11. coder: Round 1: both of the reviewer's findings are about copied test helpers. CLAUDE.md (*Tests*) gives a standing leave to move a shared test helper, and under it the tester makes the move, not the coder. So I changed no code and no test. The source change from round 0 stands as reviewed. I did not run `make check` again, because nothing changed this round.

    Moves for the tester:
    1. Move the `workspace` and `fake` fixtures to `tests/conftest.py`. They are now in `tests/adapters/test_claude_runtime_container.py:39-46` and `tests/adapters/test_opencode_runtime_container.py:48-55`, and copied as `fake` in `tests/adapters/test_runtime_podman_timeout_status.py:29-31`. Change all three modules to use the moved fixtures.
    2. Move `_request` and `_state` from `tests/adapters/test_opencode_runtime_container.py:58-66` to `tests/adapters/container_runtime_support.py`. `_request` keeps its `time_limit` and `os_user` parameters. Change `tests/adapters/test_opencode_runtime_container.py` and `tests/adapters/test_runtime_podman_timeout_status.py` to import them from there, replacing the new module's `_request` (:34-39) and its inline `state` setup (:84-85). Every earlier test keeps its name and what it checks.

    Main choice: I end with `tests` rather than `question`, because the standing leave covers both moves. The alternative, asking the human, is not needed here. Description unchanged: the review changed what the tests look like, not what the task means. Noticed but did not touch: nothing new.
12. factory: started tests as self.
