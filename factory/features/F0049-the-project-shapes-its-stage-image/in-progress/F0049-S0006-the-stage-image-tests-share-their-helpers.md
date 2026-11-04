---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 532
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-04T02:55:23.838822Z'
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
