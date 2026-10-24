---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 419
comments_read: []
handed_over: null
claim: null
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
