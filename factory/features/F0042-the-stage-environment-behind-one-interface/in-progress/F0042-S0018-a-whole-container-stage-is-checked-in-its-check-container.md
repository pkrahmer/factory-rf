---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 426
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T22:26:50.691104Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T22:26:50.697079Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T22:27:10.176523Z'
  stage: intake
  run: f1e50fe04e7a46a09640977d99ae4b1a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T22:27:30.567732Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T22:32:47.251790Z'
  stage: tests
  run: fd62ef8100b44778890aefae112363a0
---

# A whole container stage is checked in its check container, and the stage environment's tests share their helpers

<!-- proposed by feature acceptance of 2026-10-24; refine before starting -->

## Description

F0042's promise is the whole cycle of a `container` stage: the reset, the sync container, the base moved, the agent on the dataset, the take, the checks in a check container on the taken result, and nothing left for the next stage. Each piece has its tests, but no test runs them together. `tests/application/test_container_environment_take.py` runs a whole stage with the host's `MakeProjectCommands`, and `tests/adapters/test_make_commands_container.py` runs the check container alone. The feature's acceptance ran the combination once, as a script, and it was green. This story pins it as tests, so that a later change, F0044's removal of the layers above all, cannot break the joint unseen. The behaviour exists, so these tests are expected to pass when they are written; a red one is a fault of the feature, and the tester ends with `question` naming it.

The story also moves the copies of shared test helpers that the feature's reviewers named, under the standing leave of `CLAUDE.md`. Nothing under `src/` changes.

## Interface

None under `src/factory/`. The tester writes:

- `tests/application/test_container_stage_checks.py` (new): a whole stage through `StageRunner` on the `boundaries` fixture. The boundaries hold `FakeSnapshots` and `FakeContainerRuns` from `container_support.container_dataset`, `ContainerMakeCommands(snapshots, containers, git, checkout=boundaries.checkout)` as `project_commands`, and `container_support.WorkspaceRuntime` as the agent runtime. The story is opened with `stage_run_support.open_story`, a `Makefile` of `stage_makefile()` plus a `sync` target that writes the git-ignored marker `.synced`, and it runs under `PIPELINE_YAML`, where the `tests` stage checks `lint` and reports `test`.
- Moves under the standing leave, each earlier test keeping its name and what it checks:
  - `FIVE_MINUTES` goes once into `tests/container_support.py`, used by `test_container_environment.py` and `test_container_environment_take.py`.
  - `BROKEN_FRONT_MATTER` goes once into `tests/take_support.py`, used by `test_take.py` and `test_take_edges.py`.
  - `_without_work_item` and `_with_broken_work_item` go once into `tests/undo_support.py`, without the leading underscore, used by `test_undo.py`, `test_take_edges.py` and `test_stage_environment.py`.
  - `tests/entry/test_wiring_stage_environment.py` uses `podman_support.IMAGE` and `zfs_support.DATASET` in place of its own copies.
  - `tests/application/test_stage_environment.py` imports no name that starts with `_` from another test module. Where it needs `_leave` of `test_sealed_runs.py`, that helper moves to a shared module under `tests/`.

## Acceptance criteria

1. In the whole stage, the agent writes `tests/test_a.py` (inside the tester's write paths) and `notes.md` (outside them) into the dataset's checkout. Afterwards:
   - the pushed commit is the remote branch's head;
   - it holds `tests/test_a.py` with the agent's text and no `notes.md`;
   - the pushed work item's journal names `notes.md`;
   - the factory log holds exactly one line with `stage environment:`;
   - the host's `git status` lists no change.
2. In the same stage, `FakeContainerRuns.calls` holds exactly three calls, in this order. The first is the sync container's, whose last word is the stage-start commit. The second is a check container whose last word is `lint`. The third is a check container whose last word is `test`. After the stage, the dataset's checkout holds `tests/test_a.py` and no `notes.md`: the check ran on the rolled-back base with the taken file.
3. After that stage, the test writes `stray.txt` into the dataset's checkout and `leftover` into the dataset's `home/`. It then calls `prepare` of a new `ContainerEnvironment` on the same fakes, at the head of the remote branch. Each row of a parametrized test checks one result: `stray.txt` is gone; `home/leftover` is gone; `tests/test_a.py` is present with the agent's text.
4. The helper moves:
   - `FIVE_MINUTES`, `BROKEN_FRONT_MATTER`, `def _without_work_item`, `def _with_broken_work_item` and `IMAGE = "factory-stage:1"` are each defined at most once under `tests/`;
   - `tests/application/test_stage_environment.py` has no `import _` of a name from another test module;
   - every earlier test keeps its name, and the tester's entry names each earlier test file it changed.
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, *Wiring and tests*, names `tests/application/test_container_stage_checks.py` as the whole stage through the check container. `docs/project-guide/README.md`, *Shared test helpers*, names the helpers that moved, with their new homes.

## Smoke test

```bash
uv run pytest tests/application/test_container_stage_checks.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
grep -rlE '^(FIVE_MINUTES|BROKEN_FRONT_MATTER) = ' tests | wc -l; grep -rlE '^def _?(without_work_item|with_broken_work_item)\(' tests | wc -l; grep -rl '^IMAGE = "factory-stage:1"' tests | wc -l
```
Expect: three lines, `2`, `1`, `1`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no `src/` change. It names the new test module and its fixtures (`boundaries`, `FakeSnapshots`, `FakeContainerRuns`, `ContainerMakeCommands`, `WorkspaceRuntime`, `open_story`, `stage_makefile`, `PIPELINE_YAML`). It names the target of each helper move. I checked that `container_support.container_dataset`, `WorkspaceRuntime`, `stage_run_support.open_story` and `stage_makefile`, and the `take_support`, `undo_support`, `podman_support` and `zfs_support` modules exist under `tests/`.
   - Criteria: each is testable. Criterion 1 is one stage with five assertions. Criterion 2 pins the three calls and their order. Criterion 3 is a parametrized test with one result per row. Criterion 4 is a count of definitions, with `make check` as the check on the earlier test names. The failing side of the write-path rule (`notes.md` is left out and named in the journal) is covered in criteria 1 and 2.
   - Smoke test: both commands are runnable. Pytest's `addopts` already sets `-q` and the command passes none, so the summary line `N passed in` exists. The second block's three lines (`2`, `1`, `1`) match the patterns of criterion 4.
   - Architecture: nothing is built under `src/`. The tests go in `tests/application/` (the stage and its environment) and use the shared helper modules at the `tests/` root. That fits the layout in `CLAUDE.md`.
   - Scope: this matches F0042's goal of a whole container stage, and it stays inside "Out of scope" because no layer is removed. The helper moves are under the standing leave in `CLAUDE.md`, and the story names each helper and each test file it affects.
4. factory: started tests as self.
5. tester: The tests are written. The story said the behaviour already exists, and the new tests pass: `make test` was green (67.1 s) and `make lint` is green. `make types` is green as well. I ran it because every module under test already exists.

   Mapping:
   - criterion 1: tests/application/test_container_stage_checks.py::test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean
   - criterion 2: tests/application/test_container_stage_checks.py::test_the_sync_and_each_check_run_in_their_containers_on_the_taken_result
   - criterion 3: tests/application/test_container_stage_checks.py::test_the_next_prepare_starts_from_the_pushed_result_and_nothing_else (rows `stray-file-gone`, `home-leftover-gone`, `taken-file-kept`)
   - criterion 4: the helper moves below. The smoke test's grep counts now give `2`, `1`, `1`, and `test_stage_environment.py` imports no `_` name from another test module.
   - criterions 5 and 6: no test. `make check` belongs to the coder; the docs belong to the documenter.

   A fixture `staged` runs the whole stage once per test. It uses `container_dataset` and `ContainerMakeCommands(snapshots, containers, git, checkout=boundaries.checkout)` as `project_commands`, `WorkspaceRuntime` writing `tests/test_a.py` and `notes.md`, and `open_story` with `stage_makefile()` plus a `sync` target that writes the git-ignored `.synced`. Criterion 2 needs the stage-start commit, and the test reads it as the parent of the pushed result commit (`report.commit^`), the claim commit. The sync call's last word matches it, so the run confirms that reading.

   Files created: tests/application/test_container_stage_checks.py.

   Earlier test files changed under the standing leave. Every test keeps its name and checks the same thing:
   - tests/container_support.py: now holds `FIVE_MINUTES`.
   - tests/application/test_container_environment.py, tests/application/test_container_environment_take.py and tests/application/test_stall_container.py: their copies of `FIVE_MINUTES` are gone. The Interface did not name `test_stall_container.py`, but criterion 4 and the smoke test's `2` need its copy gone.
   - tests/take_support.py: now holds `BROKEN_FRONT_MATTER`. It takes `PATH`, the same string, from `stage_run_support` instead of `undo_support`, because `undo_support` now imports from `take_support` and the old import would be a cycle.
   - tests/application/test_take.py, tests/application/test_take_edges.py and tests/application/test_undo.py: they use `BROKEN_FRONT_MATTER` from take_support.
   - tests/undo_support.py: now holds `without_work_item` and `with_broken_work_item`, without the underscore. test_take_edges.py, test_undo.py and test_stage_environment.py use them from there.
   - tests/sealed_run_support.py: now holds `leave` (formerly `_leave` of test_sealed_runs.py). tests/application/test_sealed_runs.py, tests/application/test_sealed_runs_runner.py, tests/application/test_stage_environment.py and tests/application/test_nested_repositories.py use it. The last one held its own copy of `_leave`.
   - tests/entry/test_wiring_stage_environment.py uses `podman_support.IMAGE` and `zfs_support.DATASET`.
   - tests/adapters/test_podman_timeout_status.py and tests/adapters/test_podman_runs_results.py use `podman_support.IMAGE`. Criterion 4 allows only one `IMAGE = "factory-stage:1"` under `tests/`, so their copies had to go.

   Modules the test run could not import: none. Open: nothing.

   `lint`: lint: green (0.5 s)
   `test`: test: green (66.3 s)
