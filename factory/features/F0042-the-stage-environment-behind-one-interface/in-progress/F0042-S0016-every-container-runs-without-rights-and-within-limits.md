---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 420
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T20:27:49.238444Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T20:27:49.244418Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T20:28:10.015632Z'
  stage: intake
  run: 9694797ef2ee49f2894d5aa27a9c98c9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T20:28:30.160352Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T20:31:29.042732Z'
  stage: tests
  run: ad9b2dd47a044da191bc0b7ab0e0b513
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T20:31:49.600984Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T20:34:51.119017Z'
  stage: doing
  run: f7b7ea12a55d41b68e3e73b098468e55
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T20:35:12.740377Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T20:36:00.096264Z'
  stage: review
  run: 264b8004616848b7bc39e41b200b6664
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T20:36:20.848434Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T20:36:48.258157Z'
  stage: doing
  run: b8cff0a2444e4b40bb77a72840f872a8
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T20:37:08.716159Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-24T20:40:14.958672Z'
  stage: tests
  run: 95756ae8e2284fbea4d2890f4c18ea65
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-24T20:40:35.758204Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-24T20:43:26.053928Z'
  stage: doing
  run: 6a7c9da3a2a1474ea8210d63b6567a2e
---

# Every container runs without rights and within limits

## Description

A v1.2 stage runs every project command, the sync and the agent in a throwaway rootless container (`PodmanRuns`, S0003). Today such a container keeps podman's default capabilities, may start any number of processes and may take all the machine's memory. Code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) runs in these containers, and F0044 (the layers go) removes the second user and the kernel's write guard, so the container's own fence is what stays. This story narrows it. Every container is started with no capabilities (`--cap-drop=all`), cannot gain rights through a set-uid program (`--security-opt=no-new-privileges`), and is limited to 4096 processes and 4 GB of memory. Every container keeps podman's default network: the sync container needs the package index, the agent's container the model's API, and the check container runs `make sync` first, which needs the package index when the take changed `uv.lock` or `pyproject.toml` (the human's choice, 2026-10-24, over a check without network). Measured on 2026-10-24 on the local VM (Ubuntu 24.04, podman 4.9.3, rootless as `factory`): all four words are accepted, the container's effective capabilities are `0000000000000000`, a write to the dataset still works under `--userns=keep-id`, `--pids-limit=50` stops the 49th fork with "can't fork: Resource temporarily unavailable", `--memory=64m` sets the container's `memory.max` to 67108864, and the user's systemd delegates the `cpu memory pids` controllers. What stays: the `inline` environment and `self` are untouched (they run no container); the interface `ContainerRuns`, `ContainerCall` and every caller are unchanged; the exit statuses and time limits are read as today, with S0015's 255; a container killed for its memory before its time limit is an ordinary failure with its exit status, as any other. Decision 23 of `feature.md`.

## Interface

`factory.adapters.podman_runs` (`adapters`):

```python
PIDS_LIMIT = 4096
MEMORY_LIMIT = "4g"
```

- `PodmanRuns.launch` puts these four words right after `--timeout <seconds>` and before the first `--env`, in this order: `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g` (the last two built from the constants). Each word carries a comment that says what it keeps out. `PodmanRuns.run` starts the words of `launch`, as today.
- Nothing else changes: `ContainerRuns`, `ContainerCall`, `FakeContainerRuns` and the callers stay as they are.

Tests (the tester writes them): new rows in a new test module, for example `tests/adapters/test_podman_runs_fence.py`, with the stand-in `podman` of `tests/podman_support.py`. The one earlier test this story changes, and nothing else in it (decision 18 (j)): `tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line`, whose expected words gain the four words `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g` after `2400`.

## Acceptance criteria

1. `PodmanRuns.launch` with the mounts, environment and time limit of 40 minutes of `test_launch_pins_the_podman_command_line`: the words are `[<podman>, "run", "--rm", "--userns=keep-id", "--timeout", "2400", "--cap-drop=all", "--security-opt=no-new-privileges", "--pids-limit=4096", "--memory=4g", "--env", ...]`, with the `--env`, `--volume`, `--workdir`, image and command words exactly as that test pins them, and no word that starts with `--network`.
2. `PodmanRuns.run` with the stand-in `podman` of `tests/podman_support.py`: the arguments of its recorded call (`podman.calls()`) hold `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g`, right after the `--timeout` word and its seconds.
3. `PIDS_LIMIT == 4096` and `MEMORY_LIMIT == "4g"`; with both replaced through `monkeypatch.setattr` on `factory.adapters.podman_runs` by `64` and `"64m"`, `launch` gives `--pids-limit=64` and `--memory=64m` in their places (one test).
4. `tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line` passes with exactly the change named in the Interface.
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, the section *The podman adapter*: the four words, each with what it keeps out; that every container keeps the default network and why (the sync and the check's `make sync`: the package index; the agent: the model's API); the limits as constants and why 4096 and 4 GB (the suite's workers under `-n auto` on the VM's cores, one container at a time on a machine of 8 GB); the measured facts of 2026-10-24 from the Description. `docs/operator-guide.md`, the section *The agent in a container*: its `podman run` words gain the four words, and one paragraph on a `container` instance's fence (no capabilities, no new rights, the two limits, the network kept), and that a memory kill before the time limit is an ordinary failure (a failed check, usually with make's exit status 2 when the kernel ended one of its children, 137 when it ended the container's first process). `docs/decisions.md`: a short entry "Every container runs without rights and within limits" (the reason: F0044 removes the second user and the write guard, so the container's own fence is what stays; why the network stays: the check's `make sync` needs the package index after a change of `uv.lock`, and the agent needs the model's API, so cutting it is a later step, for example an allow-list). `README.md`: none.

## Smoke test

```bash
uv run python -c 'from datetime import timedelta as t; from pathlib import Path as P; from factory.adapters.podman_runs import PodmanRuns as R; print(R("podman", "img", P("/srv/w")).launch(["true"], mounts=[], environment={}, time_limit=t(seconds=5), working_directory="/work").argv[6:11])' 2>/dev/null
```
Expect: one line, `['--cap-drop=all', '--security-opt=no-new-privileges', '--pids-limit=4096', '--memory=4g', '--volume']`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: `factory.adapters.podman_runs` names `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"` and gives the exact placement and order of the four words in `PodmanRuns.launch`, after `--timeout <seconds>` and before the first `--env`. `launch` and `run` are real operations in `podman_runs.py`, and the argv layout I read there matches the stated position. It changes no interface, DTO or caller.
   - Criteria: each can be tested by one test function. They cover the exact argv with no `--network` word (1), the recorded call of `run` through the stand-in podman (2), and both constants plus their monkeypatched replacement (3). They also cover the one earlier test that changes, named with its change (4). The rules are the two limits and the four words. They have no failing side to test: the story validates nothing and rejects no input, so no refusal criterion is missing. The decision 18 (j) leave covers the earlier test, with the human's word.
   - Smoke test: the command is runnable. The `PodmanRuns("podman", "img", Path)` constructor matches, and with empty mounts and environment `argv[6:11]` is the four words followed by `--volume`, because `/work` is always the first volume. The `Expect:` line is a single exact list. No pytest is run, so the `-q` rule does not apply.
   - Architecture: the change stays in the adapters layer, in the one podman wrapper. `ContainerRuns` is untouched and the constants are module-level. The docs criterion names the files the documenter keeps.
   - Scope: this is S0016 of F0042, listed in the feature's Scope and Stories and Decision 23. It adds no `network` keyword, and removes no layer, so it stays outside the Out of scope list.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1–4. On purpose, they fail until the coder makes the change. Criteria 5 (`make check`) and 6 (docs) are for the coder's checks and the docs stage, so they have no test of their own.

   - criterion 1: tests/adapters/test_podman_runs_fence.py::test_launch_drops_every_right_and_limits_the_container. It uses the same mounts, environment and 40-minute limit as the earlier test, pins the full list of words with the four new ones after "2400", and checks that no word starts with `--network`.
   - criterion 2: tests/adapters/test_podman_runs_fence.py::test_a_run_starts_its_container_without_rights_and_within_limits. It runs through the stand-in `podman` with its default plan, and the four words must come right after the `--timeout` word and its seconds in `podman.calls()`.
   - criterion 3: tests/adapters/test_podman_runs_fence.py::test_the_limits_are_built_from_the_constants. It checks `PIDS_LIMIT == 4096` and `MEMORY_LIMIT == "4g"`, then uses `monkeypatch.setattr` to set them to 64 and "64m" and checks for `--pids-limit=64` and `--memory=64m` in their places.
   - criterion 4: tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line. The only change is the four words `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g` added after "2400", as the Interface names under decision 18 (j).

   Files: I created tests/adapters/test_podman_runs_fence.py and changed tests/adapters/test_podman_runs.py, which an earlier story wrote; the change is only the one the Interface names.

   `make test` result:
   - tests/adapters/test_podman_runs_fence.py could not be imported. The cause is the names `PIDS_LIMIT` and `MEMORY_LIMIT`, which `factory.adapters.podman_runs` does not define yet.
   - test_launch_pins_the_podman_command_line fails on the list of words, because the four new words are not there yet.

   `make lint` is green. I skipped the type check, as this stage's instructions say.

   I considered building criterion 1's call from a helper shared with the earlier module, and decided against it. Criterion 4 allows only the one change in that test, so I wrote the call again in the new module.

   Nothing in the criteria needed my interpretation, so there is no open question.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/adapters/test_podman_runs_fence.py - ImportError while importing test module '/work/checkout/tests/adapters/test_podman_runs_fence.py'.
6. factory: started doing as self.
7. coder: Built: `src/factory/adapters/podman_runs.py`. It gains the module constants `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"`, with one comment on why those sizes. `PodmanRuns.launch` now puts four words right after `--timeout <seconds>` and before the first `--env`, in this order: `--cap-drop=all`, `--security-opt=no-new-privileges`, `f"--pids-limit={PIDS_LIMIT}"`, `f"--memory={MEMORY_LIMIT}"`. Each word has a comment that says what it keeps out. `run` still uses the words of `launch`, so it gets the fence too. No test was changed, and nothing else changed: `ContainerRuns`, `ContainerCall`, `FakeContainerRuns` and the callers are as they were.

   Main choice: I wrote the four words inline in the argv list, each with its own comment, and read the constants each time `launch` is called. That way the monkeypatched values in criterion 3 take effect. I rejected a module-level `_FENCE` list built once at import. It would hide the per-word comments behind one name, and it would freeze the limits at import time, so the monkeypatch test would fail.

   Refactor: I read the diff and found nothing to change.

   Checks: `make check` is green (`check: green`, `test: green (67.7 s)`, coverage 99.20 %). The smoke test prints `['--cap-drop=all', '--security-opt=no-new-privileges', '--pids-limit=4096', '--memory=4g', '--volume']`.

   Noticed but did not touch: nothing.

   Open: the docs in criterion 6 are for the docs stage.

   `check`: check: green
   `duplicates`: duplicates: 16 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/adapters/podman_runs.py, tests/adapters/test_podman_runs.py, tests/adapters/test_podman_runs_fence.py) against the work item.

   Groups 1 to 3 pass. Criteria 1 to 4 each have a test that checks what the criterion says. Criterion 1 pins the full argv and checks that no word starts with `--network`. Criterion 2 checks the recorded call's words right after `--timeout` and its seconds. Criterion 3 checks both constants and their monkeypatched values in one test. Criterion 4 is the earlier test with exactly the four added words. The Interface states no rule with a refused side, and the coder's journal entry 7 records `make check` green. In `src/`, the four words sit in the stated order between `--timeout <seconds>` and the `--env` words, each with a comment saying what it keeps out. The constants are read on every call, so `run` picks them up through `launch`. The change stays in the one podman adapter, with no marker and no secret. I also ran `make duplicates`: none of its new findings are in the lines this diff adds.

   Findings:
   1. tests/adapters/test_podman_runs_fence.py:13-24. The `IMAGE = "factory-stage:1"` constant and the `runs` fixture (`PodmanRuns(str(podman.path), IMAGE, Path("/srv/factory/vm/work"))`) are a second copy of `IMAGE` and the `runs` fixture in tests/adapters/test_podman_runs.py:13-18. Fix: the tester moves the fixture and its constant to `tests/conftest.py` (or a shared module at the `tests/` root) under the standing leave to move a shared test helper. Both modules then use it from there, and every earlier test keeps its name and what it checks. Criterion 3's test (lines 113-118) could also build its expected words from `FENCE` instead of listing the two capability words again.

   Earlier tests:
   - tests/adapters/test_podman_runs.py (M): the human's leave. The story's Interface names `test_launch_pins_the_podman_command_line` under decision 18 (j), and the diff makes only the four-word change named there.
10. factory: started doing as self.
11. coder: Round 1. This entry deals only with the reviewer's finding in entry 9. I changed no code in `src/`, and I made no edits at all in this round.

    The finding is a test helper copied between modules. Moving it is a change to tests, which the coder never makes. `CLAUDE.md`'s standing leave to move a shared test helper covers it, so I hand it to the tester.

    The move for the tester:
    - Move `IMAGE = "factory-stage:1"` to `tests/podman_support.py` (a shared module at the `tests/` root, next to the `Podman` stand-in).
    - Move the `runs` fixture (`PodmanRuns(str(podman.path), IMAGE, Path("/srv/factory/vm/work"))`) to `tests/conftest.py`, next to the `podman` fixture.
    - Change two earlier test files to use them from there:
      - `tests/adapters/test_podman_runs.py` (remove its `IMAGE` and `runs`)
      - `tests/adapters/test_podman_runs_fence.py` (remove its `IMAGE` and `runs`)
    - Every test keeps its name and checks the same thing.
    - The reviewer's optional point applies inside this story's own module: in `tests/adapters/test_podman_runs_fence.py::test_the_limits_are_built_from_the_constants`, build the expected words from `FENCE[:2]` instead of listing the two capability words again.

    Rejected: changing anything in `src/factory/adapters/podman_runs.py`. The finding names no fault in the code.

    Noticed, not touched: `tests/adapters/test_podman_runs_results.py:18` and `tests/adapters/test_podman_timeout_status.py:12` hold the same `IMAGE = "factory-stage:1"` copy. The leave covers moving them to the shared constant too, but the reviewer did not name them, so the tester decides. `test_podman_runs_results.py` has its own `runs` fixture over a `workspace` path, which is a different fixture and should stay.
12. factory: started tests as self.
13. tester: Round 1, test change only. I moved the copied test helper that the reviewer flagged in entry 9 and the coder handed on in entry 11, under the standing leave in `CLAUDE.md` to move a shared test helper. Every test keeps its name and checks the same thing.

    What I changed:
    - tests/podman_support.py: it now holds `IMAGE = "factory-stage:1"`.
    - tests/conftest.py: a new `runs` fixture (`PodmanRuns(str(podman.path), IMAGE, Path("/srv/factory/vm/work"))`) sits next to the `podman` fixture. I added the imports of `IMAGE` and `PodmanRuns` that it needs.
    - tests/adapters/test_podman_runs.py (an earlier story's file, changed under the standing leave): I removed its own `IMAGE` and `runs` fixture. It now takes `IMAGE` from `podman_support` and `runs` from conftest.
    - tests/adapters/test_podman_runs_fence.py (this story's file): the same removal. I also made the reviewer's optional change: `test_the_limits_are_built_from_the_constants` now builds the two capability words of its expected list from `FENCE[:2]`.

    Criterion → test mapping (unchanged from entry 5):
    - criterion 1: tests/adapters/test_podman_runs_fence.py::test_launch_drops_every_right_and_limits_the_container
    - criterion 2: tests/adapters/test_podman_runs_fence.py::test_a_run_starts_its_container_without_rights_and_within_limits
    - criterion 3: tests/adapters/test_podman_runs_fence.py::test_the_limits_are_built_from_the_constants
    - criterion 4: tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line

    Not changed, on purpose: tests/adapters/test_podman_runs_results.py:18 and tests/adapters/test_podman_timeout_status.py:12 still hold their own copies of `IMAGE`. The handover named only the two modules above, and I made exactly that move. Those copies could move under the same leave in a later story. `test_podman_runs_results.py` keeps its own module-level `runs` fixture over `workspace`. It overrides the conftest fixture, as it should.

    Checks:
    - `make test` is green (`test: green (67.2 s)`, coverage 99.20 %), and every module imports.
    - `make lint` is green.
    - I also ran `make types` after the conftest change, and it is green.

    Open: nothing.

    `lint`: lint: green (0.5 s)
    `test`: test: green (66.2 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester moved the test helper. I made no edits in this round. The reviewer's finding in entry 9 (the copied `IMAGE` constant and `runs` fixture) was a change to tests only. The tester made it in entry 13: `IMAGE` now lives in `tests/podman_support.py`, the `runs` fixture in `tests/conftest.py`, and `test_the_limits_are_built_from_the_constants` builds its expected words from `FENCE[:2]`. The finding named no fault in `src/factory/adapters/podman_runs.py`, so the code stays as entry 7 built it.

    What I built (entry 7, unchanged): `src/factory/adapters/podman_runs.py` defines `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"`. `PodmanRuns.launch` puts four words right after `--timeout <seconds>` and before the first `--env`: `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit={PIDS_LIMIT}` and `--memory={MEMORY_LIMIT}`, each with a comment that says what it keeps out.

    Main choice (entry 7): the four words sit inline in the argument list, and the constants are read on every call, so the values patched in the constants test take effect. I rejected a module-level fence list built once at import: it would freeze the limits at import time and hide the comment on each word.

    Refactor: no new diff in this round, so nothing to change.

    Checks: `make check` is green (`check: green`, `test: green (66.6 s)`, coverage 99.20 %).

    Noticed but did not touch (as entries 11 and 13 say): `tests/adapters/test_podman_runs_results.py:18` and `tests/adapters/test_podman_timeout_status.py:12` still hold their own copies of `IMAGE = "factory-stage:1"`. The standing leave allows a later move of those too.

    Open: the docs in criterion 6 are for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 16 new, 36 known, 2 gone
