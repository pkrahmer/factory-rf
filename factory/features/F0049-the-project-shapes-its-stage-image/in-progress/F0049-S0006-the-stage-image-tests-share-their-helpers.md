---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 532
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-11-04T03:00:05.151943Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T02:53:46.554270Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T02:53:46.560940Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T02:54:05.693191Z'
  stage: intake
  run: dedeb7b499f246449967edb6a2c29d36
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T02:54:11.863846Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T02:55:18.069110Z'
  stage: tests
  run: be37586595464d7a91e66a844c256ddf
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T02:55:23.838822Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T02:58:58.034318Z'
  stage: doing
  run: dde8291222ab4db59a971234d192b206
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T02:59:04.157282Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T02:59:36.881409Z'
  stage: review
  run: e814460b4c8e4baf947e3cfd7cd63450
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T02:59:42.816526Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-04T02:59:58.639848Z'
  stage: docs
  run: 7da8574b1a704728bc02bacc35422395
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T03:00:05.151943Z'
  stage: smoke-test
---

# The stage image's tests share their helpers and pin the image without an environment

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

The reviewers of F0049-S0002 and F0049-S0003 left notes that were not findings, and the coders carried them as "noticed, not touched" to the end of each story: copies of shared test values and helpers, and one side of `PodmanImages.path` that the code handles but no row pins. This story is for the tester alone and changes no code. `tests/adapters/test_podman_images.py` and `tests/entry/test_wiring_image_path.py` define the base `PATH` again (`SYSTEM_PATH`, `BASE_PATH`) in place of importing `SYSTEM_PATH` from `factory.domain.containers`; `tests/entry/test_wiring_image_path.py` copies `PROBE` and `COMPLETED` from `tests/entry/test_wiring_run.py`, and both hold values that `tests/probe_support.py` (`COMPLETED`, the probe's result) and `tests/agent_definition_support.py` (`COMPLETED`) already share; `Machine.log_lines` in `tests/application/test_tick_preflight.py` copies the body of `state_log_lines` of `tests/log_support.py`; and `test_path_is_the_images_configured_path_or_the_base_default` has no row for `podman image inspect` printing `null`, which podman prints for an image that configures no environment (`src/factory/adapters/podman_images.py` returns the default `PATH` for it). The move is made under the standing leave of `CLAUDE.md` (*Tests*): every earlier test keeps its name and checks the same thing. `STAND_IN` in `tests/adapters/test_podman_images.py`, a variant of `PODMAN_SCRIPT` in `tests/podman_support.py` that also lists the build context, stays as it is; folding the two is left to a later story.

## Interface

- No module under `src/factory/` changes.
- `tests/adapters/test_podman_images.py`: `SYSTEM_PATH` imported from `factory.domain.containers`; its local definition removed; a row `null` in `test_path_is_the_images_configured_path_or_the_base_default` whose printed output is `null` and whose expected `PATH` is `SYSTEM_PATH`.
- `tests/entry/test_wiring_image_path.py`: `BASE_PATH` replaced by `SYSTEM_PATH` from `factory.domain.containers`; `PROBE` imported as `COMPLETED as PROBE` from `tests/probe_support.py` and `COMPLETED` from `tests/agent_definition_support.py`, which hold the same values; `tests/entry/test_wiring_run.py` does the same (standing leave). The other modules that define their own `PROBE` or `COMPLETED` stay as they are.
- `tests/application/test_tick_preflight.py`: `Machine.log_lines` returns `state_log_lines(self.directory / "state")` from `tests/log_support.py` (standing leave). `log_lines` of `tests/log_support.py` keeps its body, which `tests/test_shared_bodies.py` uses as its sample.
- `tests/vm_support.py` keeps its own `SYSTEM_PATH`: it describes the VM's shell, not the image's default.

## Acceptance criteria

1. `PodmanImages.path` given inspect output `null` returns `/usr/local/bin:/usr/bin:/bin`, as a row of `test_path_is_the_images_configured_path_or_the_base_default` beside `with-path` and `without-path`.
2. Under `tests/`, outside `tests/vm_support.py`, no module assigns the text `"/usr/local/bin:/usr/bin:/bin"` to a name; the two modules above import `SYSTEM_PATH` from `factory.domain.containers`.
3. Neither `tests/entry/test_wiring_run.py` nor `tests/entry/test_wiring_image_path.py` assigns `PROBE` or `COMPLETED`; both import them from `tests/probe_support.py` and `tests/agent_definition_support.py`, and every test in both modules keeps its name and passes.
4. `Machine.log_lines` in `tests/application/test_tick_preflight.py` calls `state_log_lines`; every test in that module keeps its name and passes, and `tests/test_shared_bodies.py` passes unchanged.
5. `make check` stays green.
6. docs: none: no behaviour, command or decision changes, and the test conventions of `CLAUDE.md` already cover the move.

## Smoke test

```bash
grep -rlF '= "/usr/local/bin:/usr/bin:/bin"' tests | grep -v '^tests/vm_support.py$' | wc -l
grep -hE '^(PROBE|COMPLETED) = ' tests/entry/test_wiring_run.py tests/entry/test_wiring_image_path.py | wc -l
uv run pytest tests/adapters/test_podman_images.py tests/entry/test_wiring_image_path.py tests/entry/test_wiring_run.py tests/application/test_tick_preflight.py tests/test_shared_bodies.py 2>&1 | tail -1
```

Expect: `0`, `0`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete test modules and the shared sources (`factory.domain.containers.SYSTEM_PATH`, `tests/probe_support.py` and `tests/agent_definition_support.py` `COMPLETED`, `tests/log_support.py` `state_log_lines`). I checked that these exist and that the local copies it names exist (`SYSTEM_PATH` in `test_podman_images.py`, `BASE_PATH`/`PROBE`/`COMPLETED` in `test_wiring_image_path.py`, `PROBE`/`COMPLETED` in `test_wiring_run.py`). The `null` row has its printed output and expected value stated. No `src/` change, and `tests/vm_support.py` is explicitly kept.
   - Criteria: 1 (the `null` row, which covers the untested side), 2, 3 and 4 are each testable by one check. Criterion 3 and the grep in the smoke test also pin that no module assigns `PROBE`/`COMPLETED`. The Interface states no new rule or behaviour beyond these, so no failing side is missing. The moves rest on the standing leave in `CLAUDE.md` (*Tests*), and every earlier test keeps its name.
   - Smoke test: the grep and pytest commands are runnable. `pyproject.toml` already sets `-q` in `addopts` and the command passes none, so `tail -1` prints the summary line. Each `Expect:` (`0`, `0`, a line ending in `passed` with no `failed`) can be checked against the output.
   - Architecture: tests only, in the folders that mirror the package. Shared helpers go into support modules, as `CLAUDE.md` requires.
   - Scope: within F0049 as a follow-up of the S0002/S0003 reviewer notes. Nothing is in the feature's "Out of scope", and the story leaves `STAND_IN` alone.
4. factory: started tests as vm.
5. tester: This story only changes tests. The code already handles the new case, so nothing is red on purpose: the new `null` row and every moved test pass now. The coder has nothing to implement. What is left is the `make check` gate (criterion 5).

   Criterion → test:
   - criterion 1: tests/adapters/test_podman_images.py::test_path_is_the_images_configured_path_or_the_base_default[null]. This is a new row: inspect prints `null`, and the expected `PATH` is `SYSTEM_PATH`.
   - criterion 2: no test function of its own, because the criterion is about how the test modules are written. I changed tests/adapters/test_podman_images.py to import `SYSTEM_PATH` from `factory.domain.containers` and removed its own definition. In tests/entry/test_wiring_image_path.py I replaced `BASE_PATH` with `SYSTEM_PATH` from `factory.domain.containers`. The smoke test's first grep prints `0`.
   - criterion 3: tests/entry/test_wiring_run.py and tests/entry/test_wiring_image_path.py now import `COMPLETED as PROBE` from `probe_support` and `COMPLETED` from `agent_definition_support`. Their local definitions are gone, along with the imports of `AgentRunResult` (in both) and `timedelta` (in test_wiring_run.py) that nothing used any more. Every test in both modules keeps its name and passes, and the smoke test's second grep prints `0`.
   - criterion 4: in tests/application/test_tick_preflight.py, `Machine.log_lines` now returns `state_log_lines(self.directory / "state")` from `log_support`. Every test in the module keeps its name and passes. I did not touch tests/test_shared_bodies.py or `log_support.log_lines`, and tests/test_shared_bodies.py passes.
   - criteria 5 and 6 (`make check`, `docs:`): no test. They are not mine.

   Files changed (I created none):
   - tests/adapters/test_podman_images.py
   - tests/entry/test_wiring_image_path.py
   - tests/entry/test_wiring_run.py: earlier test file, changed under the standing leave in `CLAUDE.md` (*Tests*).
   - tests/application/test_tick_preflight.py: earlier test file, changed under the standing leave in `CLAUDE.md` (*Tests*).

   As the Interface says, I left tests/vm_support.py's own `SYSTEM_PATH` and `STAND_IN` as they are. The other modules that define their own `PROBE` or `COMPLETED` are also unchanged.

   Run: `uv run pytest -q` over the five modules the smoke test names: all passed, none failed. `make lint`: green. Every module was imported; the test run had no import failures.

   Rejected: a structural test that scans `tests/` for the `PATH` text or for assignments to `PROBE`/`COMPLETED`. It would add a standing rule that the criteria do not ask for. The smoke test's greps already check criteria 2 and 3.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Built nothing. This story changes only tests, and the tester already made those changes (tests/adapters/test_podman_images.py, tests/entry/test_wiring_image_path.py, tests/entry/test_wiring_run.py, tests/application/test_tick_preflight.py). The new `null` row passes against the existing `src/factory/adapters/podman_images.py`, so no code under `src/factory/` changes, as the Interface requires. `git diff main --stat -- src` is empty.

   Main choice: leave the working tree as the tester left it and only confirm the gate. The alternative I rejected was touching `PodmanImages.path` to name the `null` case explicitly. Behaviour would stay the same, but the Interface forbids any `src/` change.

   Checks:
   - `make check`: green (`test: green (85.6 s)`, `check: green`).
   - Smoke test greps: `0` and `0`.

   Refactor: there is no diff of mine, so there was nothing to refactor.

   The journal did not change the meaning of the task, so I did not rewrite the Description.

   Noticed, not touched: `STAND_IN` in tests/adapters/test_podman_images.py is still a variant of `PODMAN_SCRIPT` in tests/podman_support.py. The Description leaves that to a later story.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 43 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   I read the diff against `main`, which changes four test files and nothing under `src/`, and checked it against each criterion and the Interface:
   - Criterion 1: the new row `null` in `tests/adapters/test_podman_images.py::test_path_is_the_images_configured_path_or_the_base_default` sits beside `with-path` and `without-path`. Its stand-in prints `null\n` and the row expects `SYSTEM_PATH`. `src/factory/adapters/podman_images.py:76-82` returns `SYSTEM_PATH` when the parsed value is not a list, so the row checks the side the Description names.
   - Criterion 2: both modules import `SYSTEM_PATH` from `factory.domain.containers` (value `/usr/local/bin:/usr/bin:/bin`, `src/factory/domain/containers.py:17`). Under `tests/`, only `tests/vm_support.py:15` still assigns that text to a name. Every other occurrence is a literal inside a call or a dict, not an assignment.
   - Criterion 3: `tests/entry/test_wiring_run.py` and `tests/entry/test_wiring_image_path.py` no longer assign `PROBE` or `COMPLETED`. Each imports `COMPLETED as PROBE` from `tests/probe_support.py` and `COMPLETED` from `tests/agent_definition_support.py`. I compared the shared values with the removed copies and they are field for field identical. The imports that nothing used any more (`AgentRunResult` in both files, `timedelta` in `test_wiring_run.py`) are gone. `timedelta` is still used in `test_wiring_image_path.py:71`, so it stays there. No test name changed.
   - Criterion 4: `Machine.log_lines` now returns `state_log_lines(self.directory / "state")`, which has the same body as the removed copy. `tests/log_support.py` and `tests/test_shared_bodies.py` are unchanged.
   - Criterion 5: the coder's `make check` was green (journal entry 7). Criterion 6 (`docs: none`) still holds: no behaviour, command or decision changed.
   - Architecture, security and quality: the diff only touches tests and adds no silencing markers. Every copy the Description names is replaced by the shared one. `STAND_IN` and the other modules' own `PROBE`/`COMPLETED` are left alone, as the Description says.
   - Work item hygiene: the Description matches what was built. The tester's entry names the rejected structural test and why.

   Earlier tests (each file is on `main` and was changed with status `M`):
   - `tests/adapters/test_podman_images.py`: two leaves. The story the human created and started names the file. It replaces a local copy of `SYSTEM_PATH` with the shared constant, and it adds the `null` row. The earlier rows keep their ids and what they check.
   - `tests/entry/test_wiring_image_path.py`: the standing leave to move a shared test helper, plus the story's naming. It replaces the copies of `BASE_PATH`, `PROBE` and `COMPLETED` with the shared values. Every test keeps its name and what it checks.
   - `tests/entry/test_wiring_run.py`: the standing leave to move a shared test helper. It replaces the copies of `PROBE` and `COMPLETED` with the shared values. Every test keeps its name and what it checks.
   - `tests/application/test_tick_preflight.py`: the standing leave to move a shared test helper. `Machine.log_lines` now uses `state_log_lines` of `tests/log_support.py`. Every test keeps its name and what it checks.
10. factory: started docs as vm.
11. documenter: Files changed: none. The docs criterion says `none`: this story only moves shared test values and helpers in four test modules and adds one test row, and no behaviour, command or decision changes. The diff against `main` outside `factory/` and `docs/` is those four test files only, with nothing under `src/`.

    Cross-read and found current: `docs/project-guide/README.md` (test-helper rule at line 25 and `log_support.py` at line 66, which still describes `log_lines` as it is; `state_log_lines` and `test_shared_bodies.py` are unchanged), `docs/project-guide/watching.md` line 238 and `docs/project-guide/stage-environment.md` line 367 (both name `SYSTEM_PATH` as the default image `PATH`, which the diff does not touch). I searched the README and `docs/` for `BASE_PATH`, `log_lines`, `SYSTEM_PATH` and `test_wiring_image_path`, and found no stale mention.

    Findings for the coder: none. Stale text I noticed and left alone: none.

    `check`: check: green (not run again: passed on tree c75cce644896 at 2026-11-04T02:57:19Z)
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
