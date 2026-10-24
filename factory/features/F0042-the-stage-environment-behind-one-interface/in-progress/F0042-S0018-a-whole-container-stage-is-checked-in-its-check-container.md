---
stage: approval
blocked: null
round: 1
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
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T22:33:08.785239Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T22:35:58.287184Z'
  stage: doing
  run: dd71fe0cc4bf49b1a3de66703c93450f
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T22:36:58.392115Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T22:38:13.487460Z'
  stage: review
  run: 34f912027edc4fa6859d633387ef253e
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T22:38:33.451059Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T22:38:48.173391Z'
  stage: doing
  run: 7367e26c2ffb4b698b02d55a05ed5c38
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T22:39:09.643795Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-24T22:42:34.346236Z'
  stage: tests
  run: 29e98948b6ad45f9a1b79c0b7b10c6b4
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-24T22:42:54.920027Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-24T22:45:50.240213Z'
  stage: doing
  run: e7a25c5421de44c7b740b8da85d232a1
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-24T22:46:10.710508Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-24T22:47:33.954127Z'
  stage: review
  run: 444aebce122a483698af4ecd1b84104a
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-24T22:47:54.750217Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-24T22:48:33.751409Z'
  stage: docs
  run: c530836dacba4c20b2ca96c28ad29006
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-24T22:48:54.285069Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T22:49:28.588475Z'
  stage: smoke-test
  run: 73759e60de364597a083aa3bbd100b8f
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
6. factory: started doing as self.
7. coder: No code was needed. The Interface says nothing under `src/factory/` changes, and the new tests in `tests/application/test_container_stage_checks.py`, along with the moved helpers, already pass against the existing behaviour. I ran `make check` in the foreground and it ends with `check: green` (`test: green (67.2 s)`, total coverage 99.19 %).

   - Built: nothing. `git diff main -- src` is empty, and I changed no file.
   - Main choice: I left `src/` alone. The other option was to tidy code the new tests touch, such as the container stage path. I rejected it because the story is limited to tests and helper moves, and anything more would go beyond its scope (R13).
   - Refactor: there is no diff of mine to review, so nothing needed changing.
   - Noticed, not touched: the tester also changed `tests/application/test_stall_container.py`, `tests/application/test_nested_repositories.py`, `tests/adapters/test_podman_timeout_status.py` and `tests/adapters/test_podman_runs_results.py`. The Interface does not name these files, but criterion 4's single-definition counts require the changes. The reviewer may want to confirm that each test there kept its name.
   - The docs criterion (`docs/project-guide/stage-environment.md` and `docs/project-guide/README.md`) belongs to the documenter.
   - The journal did not change the meaning of the task.

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: Review of `git diff main...HEAD -- . ':!factory'` (18 test files, nothing under `src/`) against criteria 1 to 4 and the Interface. The three new tests cover criteria 1, 2 and 3. The helper moves meet criterion 4: each of `FIVE_MINUTES`, `BROKEN_FRONT_MATTER`, `without_work_item`, `with_broken_work_item`, `IMAGE` and `leave` is now defined once. `test_stage_environment.py` imports no `_` name. No test was renamed. The coder's journal entry 7 reports `check: green`. Groups 1 to 3 pass. Group 4 fails on one copy:

   1. `tests/application/test_container_stage_checks.py:59-70` (the `staged` fixture) and `:33-35`: the fixture copies the whole-stage setup of `tests/application/test_container_environment_take.py:128-135` line for line. That covers the inline sync target `"\nsync:\n\t@echo synced > .synced\n"` and `.gitignore` `".synced\n"`, which repeat `container_support.SYNC_RECIPE`/`SYNC_MARKER`, then `open_story`, `container_dataset`, the queued `completed("doing")` and `WorkspaceRuntime` writing `INSIDE`/`NOTES`. It also repeats the constants `AGENT_TEXT`, `INSIDE` and `NOTES`. `AGENT_TEXT` is already shared in `tests/take_support.py:15`. `test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean` then repeats the five assertions of `test_a_whole_stage_takes_the_agents_work_from_the_dataset` word for word. This is the kind of copy the story exists to remove. Fix: under the standing leave, the tester moves the setup into one shared helper in `tests/container_support.py`. It builds the sync target from `SYNC_RECIPE`/`SYNC_MARKER`, holds `INSIDE` and `NOTES`, takes `AGENT_TEXT` from `take_support`, and takes `project_commands` as an optional argument. `staged` and the earlier whole-stage test both use it. The five shared assertions can become one shared check, or the two whole-stage tests can be rows of one parametrized test over the project commands (host `MakeProjectCommands` against `ContainerMakeCommands`). Each earlier test keeps its name and what it checks.

   Earlier tests: all 17 files below are changed under the standing leave to move a shared test helper. Each change only moves a constant or helper to a shared module or uses the shared one in place of a copy. Every test keeps its name and what it checks, and the tester's entry 5 names each file.
   - tests/adapters/test_podman_runs_results.py: standing leave (`IMAGE` from `podman_support`)
   - tests/adapters/test_podman_timeout_status.py: standing leave (`IMAGE` from `podman_support`)
   - tests/application/test_container_environment.py: standing leave (`FIVE_MINUTES` from `container_support`)
   - tests/application/test_container_environment_take.py: standing leave (`FIVE_MINUTES` from `container_support`)
   - tests/application/test_nested_repositories.py: standing leave (`_leave` copy replaced by `sealed_run_support.leave`)
   - tests/application/test_sealed_runs.py: standing leave (`_leave` moved to `sealed_run_support.leave`)
   - tests/application/test_sealed_runs_runner.py: standing leave (`leave` from `sealed_run_support`)
   - tests/application/test_stage_environment.py: standing leave (`leave`, `without_work_item`, `with_broken_work_item` from shared modules)
   - tests/application/test_stall_container.py: standing leave (`FIVE_MINUTES` from `container_support`)
   - tests/application/test_take.py: standing leave (`BROKEN_FRONT_MATTER` from `take_support`)
   - tests/application/test_take_edges.py: standing leave (`BROKEN_FRONT_MATTER` copy and the two baseline helpers replaced by `undo_support`'s)
   - tests/application/test_undo.py: standing leave (`BROKEN_FRONT_MATTER` from `take_support`, the two baseline helpers moved to `undo_support`)
   - tests/container_support.py: standing leave (receives `FIVE_MINUTES`)
   - tests/entry/test_wiring_stage_environment.py: standing leave (`IMAGE` from `podman_support`, `DATASET` from `zfs_support`, same values)
   - tests/sealed_run_support.py: standing leave (receives `leave`)
   - tests/take_support.py: standing leave (receives `BROKEN_FRONT_MATTER`; `PATH` now from `stage_run_support`, the same string, to avoid an import cycle)
   - tests/undo_support.py: standing leave (receives `without_work_item`, `with_broken_work_item`)
10. factory: started doing as self.
11. coder: Round 1: I changed no code and no file. The reviewer's only finding (entry 9) is a copied test helper. `CLAUDE.md` gives a standing leave for that kind of move, and only the tester may make it, so I am sending the item back to the tests stage.

    - Built: nothing. `git diff main -- src` is still empty.
    - The test change I ask for, under the standing leave: move the whole-stage setup into one shared helper in `tests/container_support.py`. The setup is currently copied in the `staged` fixture of `tests/application/test_container_stage_checks.py` (lines 33-35 and 59-70) and in `tests/application/test_container_environment_take.py` (lines 128-135). The helper should:
      - build the sync target and `.gitignore` from `SYNC_RECIPE`/`SYNC_MARKER`;
      - hold `INSIDE` and `NOTES`;
      - take `AGENT_TEXT` from `take_support`;
      - accept `project_commands` as an optional argument.
      Both `staged` and `test_a_whole_stage_takes_the_agents_work_from_the_dataset` should use it. Then do one of these for the five assertions that the two whole-stage tests repeat: move them into one shared check, or make the two tests rows of one parametrized test over the project commands (host `MakeProjectCommands` against `ContainerMakeCommands`). Every earlier test keeps its name and what it checks, and the tester's entry names each earlier test file it changed.
    - Main choice: I hand this to the tester and do not edit the tests myself (R9). The other option was to treat it as a question for the human. I rejected that because `CLAUDE.md` already allows this exact move without asking.
    - Refactor: nothing of mine to refactor.
    - Noticed, not touched: nothing further. The docs criterion is still the documenter's.
    - The journal did not change the meaning of the task.
12. factory: started tests as self.
13. tester: Round 1: I made the test change the coder asked for in entry 11, which answers the reviewer's finding in entry 9. I made it under the standing leave in `CLAUDE.md` to move a shared test helper. No test was renamed, and each still checks the same thing.

    What changed:
    - tests/container_support.py now holds `INSIDE` and `NOTES`.
    - It also holds `whole_stage(boundaries, *, human, agent_home, agent_runtime, tmp_path, project_commands=None) -> tuple[Dataset, StageReport]`:
      - it opens the story with `stage_makefile()` plus a `sync` target built from `SYNC_RECIPE`;
      - it writes `.gitignore` from `SYNC_MARKER`;
      - it builds the dataset, queues `completed("doing")` and writes `INSIDE`/`NOTES` through `WorkspaceRuntime` with `AGENT_TEXT` from `take_support`, then runs the stage.
    - `project_commands` is an optional `Callable[[Dataset], ProjectCommands]`, because `ContainerMakeCommands` needs the dataset's fakes, which exist only once the helper has built the dataset. When it is not given, the host's project commands stay.
    - It also holds `assert_taken_and_pushed(boundaries, remote, report)`, the five assertions the two whole-stage tests repeated. I chose the shared check over the reviewer's other option, one parametrized test, because a parametrized test would have merged two tests into one and lost a name.

    Earlier test file changed under the standing leave:
    - tests/application/test_container_environment_take.py: `test_a_whole_stage_takes_the_agents_work_from_the_dataset` now uses `whole_stage` and `assert_taken_and_pushed`. The module's own copies of `AGENT_TEXT` (now from `take_support`), `INSIDE` and `NOTES` are gone.

    This story's own test file changed too:
    - tests/application/test_container_stage_checks.py: the `staged` fixture calls `whole_stage` with `ContainerMakeCommands` as `project_commands`, and `test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean` calls `assert_taken_and_pushed`. Its copies of `AGENT_TEXT`, `INSIDE` and `NOTES` are gone.

    Mapping (unchanged):
    - criterion 1: tests/application/test_container_stage_checks.py::test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean
    - criterion 2: tests/application/test_container_stage_checks.py::test_the_sync_and_each_check_run_in_their_containers_on_the_taken_result
    - criterion 3: tests/application/test_container_stage_checks.py::test_the_next_prepare_starts_from_the_pushed_result_and_nothing_else
    - criterion 4: the helper moves of entry 5, plus this one
    - criteria 5 and 6: no test (`make check` and the docs)

    Files created: none this round. Modules the test run could not import: none.

    Checks:
    - `make test` is green (64.2 s, coverage 99.19 %). I ran it once, before shortening a docstring line, which is the only change since.
    - `make lint` and `make types` are green.

    Open: nothing.

    `lint`: lint: green (0.6 s)
    `test`: test: green (65.6 s)
14. factory: started doing as self.
15. coder: Round 1: I changed no code and no file. The reviewer's finding (entry 9) was a copied whole-stage setup in the tests. The tester fixed it in entry 13 by adding `whole_stage` and `assert_taken_and_pushed` to `tests/container_support.py`, and both whole-stage tests now use them. Nothing was left for the coder to do.

    - Built: nothing. `git diff main -- src` is empty.
    - Main choice: I handed the work item to review without touching code. The other option was to change something under `src/` that the new tests call. I rejected it because the story builds nothing under `src/` (R13).
    - Refactor: I have no diff of my own, so nothing needed changing.
    - Noticed, not touched: the tester kept two separate test functions with a shared check instead of one parametrized test, so that both test names stay. The reviewer offered either option.
    - The docs criterion is still the documenter's.
    - The journal did not change the meaning of the task.

    `check`: check: green (test: green (69.6 s), coverage 99.19 %)

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
16. factory: started review as self.
17. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`. The diff changes 18 test files and nothing under `src/` or `docs/`. I checked it against criteria 1 to 4, the Interface and the finding in entry 9.

    no findings

    - Entry 9's finding is fixed. `tests/container_support.py:260-300` now holds `whole_stage`, which builds the sync target from `SYNC_RECIPE` and `.gitignore` from `SYNC_MARKER`, takes `AGENT_TEXT` from `take_support`, and takes `project_commands` as an optional factory. It also holds `assert_taken_and_pushed`, the five shared assertions. Both whole-stage tests use them. `test_a_whole_stage_takes_the_agents_work_from_the_dataset` keeps its name, and it keeps the same Makefile, `.gitignore`, run and assertions as on `main`.
    - Criterion 1: `test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean` uses `ContainerMakeCommands(snapshots, containers, boundaries.git, checkout=boundaries.checkout)`, as the Interface says. Its five assertions are the criterion's five.
    - Criterion 2: comparing the whole list `[stage_start, "lint", "test"]` checks that there are exactly three calls, in that order. The dataset's checkout is then checked for `tests/test_a.py` and for the absence of `notes.md`.
    - Criterion 3: one parametrized test with three rows (`stray-file-gone`, `home-leftover-gone`, `taken-file-kept`). It calls `prepare` of a new `ContainerEnvironment` on the same fakes at `branch_head(remote)`.
    - Criterion 4: by grep, `FIVE_MINUTES`, `BROKEN_FRONT_MATTER`, `def without_work_item`, `def with_broken_work_item` and `IMAGE = "factory-stage:1"` are each defined once under `tests/`. `test_stage_environment.py` imports no `_` name.
    - The failing side of the write-path rule (`notes.md` left out, and named in the journal) is tested. The Interface states no numeric limit. Entry 15 records `check: green`.
    - Groups 2 and 3: nothing under `src/` changed, and no suppression marker was added.
    - Considered and rejected: `INSIDE` and `NOTES` in `container_support.py` have the same values as constants in `stall_support.py`, `test_stage_run.py` and others. Those copies were on `main` before this story, and the diff moved a copy out of `test_container_environment_take.py` without adding one. The story names no move for them, so this is not a finding.

    Earlier tests (all changed under the standing leave to move a shared test helper; each change only moves a constant or helper to a shared module, or uses the shared one in place of a copy; every test keeps its name and what it checks):
    - tests/adapters/test_podman_runs_results.py: standing leave (`IMAGE` from `podman_support`)
    - tests/adapters/test_podman_timeout_status.py: standing leave (`IMAGE` from `podman_support`)
    - tests/application/test_container_environment.py: standing leave (`FIVE_MINUTES` from `container_support`)
    - tests/application/test_container_environment_take.py: standing leave (`FIVE_MINUTES`, `INSIDE`, `NOTES` and the whole-stage setup and assertions from `container_support`; `AGENT_TEXT` from `take_support`)
    - tests/application/test_nested_repositories.py: standing leave (its `_leave` copy replaced by `sealed_run_support.leave`)
    - tests/application/test_sealed_runs.py: standing leave (`_leave` moved to `sealed_run_support.leave`)
    - tests/application/test_sealed_runs_runner.py: standing leave (`leave` from `sealed_run_support`)
    - tests/application/test_stage_environment.py: standing leave (`leave`, `without_work_item` and `with_broken_work_item` from shared modules)
    - tests/application/test_stall_container.py: standing leave (`FIVE_MINUTES` from `container_support`)
    - tests/application/test_take.py: standing leave (`BROKEN_FRONT_MATTER` from `take_support`)
    - tests/application/test_take_edges.py: standing leave (`BROKEN_FRONT_MATTER` and the two baseline helpers replaced by the shared ones)
    - tests/application/test_undo.py: standing leave (`BROKEN_FRONT_MATTER` from `take_support`; the two baseline helpers moved to `undo_support`)
    - tests/container_support.py: standing leave (receives `FIVE_MINUTES`, `INSIDE`, `NOTES`, `whole_stage` and `assert_taken_and_pushed`)
    - tests/entry/test_wiring_stage_environment.py: standing leave (`IMAGE` from `podman_support` and `DATASET` from `zfs_support`, same values)
    - tests/sealed_run_support.py: standing leave (receives `leave`)
    - tests/take_support.py: standing leave (receives `BROKEN_FRONT_MATTER`; `PATH` now from `stage_run_support`, the same string, to avoid an import cycle)
    - tests/undo_support.py: standing leave (receives `without_work_item` and `with_broken_work_item`)
18. factory: started docs as self.
19. documenter: Docs round for F0042-S0018. The diff touches only tests (18 files, nothing under `src/`), so the documentation change is the docs criterion plus the helper homes. I changed only documents, so I did not run `make check`; the factory's checks run right after this stage.

    Files changed:
    - `docs/project-guide/stage-environment.md`, *Wiring and tests*: names `tests/application/test_container_stage_checks.py` as the whole stage through the check container (the sync container, one check container per check on the taken result, and the next `prepare` starting from the pushed head with nothing left over). It also lists `whole_stage` and `assert_taken_and_pushed` among the `tests/container_support.py` helpers, and says the older whole-stage test in `test_container_environment_take.py` uses the host's project commands.
    - `docs/project-guide/README.md`, *Shared test helpers*: added entries for `container_support.py` (now with `FIVE_MINUTES`, `whole_stage`, `assert_taken_and_pushed`), `take_support.py` (`BROKEN_FRONT_MATTER`), `sealed_run_support.py` (`leave`), `podman_support.py` (`IMAGE`) and `zfs_support.py` (`DATASET`). Four of these modules had no entry at all. I extended the `undo_support.py` entry with `without_work_item` and `with_broken_work_item`.

    Cross-read and found current against the diff: the *Shared test helpers* list apart from the entries above, and *The take* and the rest of `stage-environment.md`. No `src/` behaviour changed, so no other document moves.

    Findings for the coder: none. The code and the Interface agree, since nothing under `src/` changed.

    Stale text I saw and did not touch: none that is unrelated. I did not check the other entries of the *Shared test helpers* list one by one against the files. The ones I added come from the files' current content.

    I did not run the examples, because there are none beyond the story's smoke-test commands, which belong to the next stage.

    `check`: check: green (not run again: passed on tree f66258edd2b5 at 2026-10-24T22:44:29Z)
    `secrets`: secrets: green (1.9 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: I ran both smoke-test commands from the repository root, exactly as written. Both met their `Expect:` lines.

    Command 1:
    ```bash
    uv run pytest tests/application/test_container_stage_checks.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
    ```
    ```
    1
    ```
    It met `Expect: 1`. I also ran pytest on the module without the filter to see the summary line: `5 passed in 1.55s`.

    Command 2:
    ```bash
    grep -rlE '^(FIVE_MINUTES|BROKEN_FRONT_MATTER) = ' tests | wc -l; grep -rlE '^def _?(without_work_item|with_broken_work_item)\(' tests | wc -l; grep -rl '^IMAGE = "factory-stage:1"' tests | wc -l
    ```
    ```
    2
    1
    1
    ```
    It met `Expect: three lines, 2, 1, 1`.

    Checking against the acceptance criteria:
    - Criterion 4: I listed the definitions by line. Each one appears exactly once:
      - `FIVE_MINUTES` in `tests/container_support.py:36`
      - `BROKEN_FRONT_MATTER` in `tests/take_support.py:16`
      - `without_work_item` and `with_broken_work_item` in `tests/undo_support.py:69` and `:76`
      - `IMAGE = "factory-stage:1"` in `tests/podman_support.py:10`

      The other `IMAGE = "build-7"` constants are a different value and outside the criterion. A grep found no `import _` of a name from another test module in `tests/application/test_stage_environment.py`.
    - Criteria 1–3: the passing module is the smoke test's evidence for them.
    - Criteria 5 (`make check`) and 6 (docs): the smoke test does not target them, and nothing it showed contradicts them.

    Findings: none. Open: nothing.
