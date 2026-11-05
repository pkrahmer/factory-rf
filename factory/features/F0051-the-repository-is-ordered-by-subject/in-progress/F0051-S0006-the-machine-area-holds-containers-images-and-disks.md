---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 561
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-05T03:28:55.141032Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T03:13:30.662144Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T03:13:30.668826Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T03:13:48.450409Z'
  stage: intake
  run: 3718a90250ba441da93dbc470520fb46
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T03:13:53.348965Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T03:16:41.246228Z'
  stage: tests
  run: 022ced2962d748f69c4dcb3b81ee9298
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T03:16:46.530861Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-05T03:22:48.813581Z'
  stage: doing
  run: a6b056cc25ab43b483a379b970daf571
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-05T03:22:56.462476Z'
  stage: tests
- number: 9
  speaker: tester
  kind: result
  at: '2026-11-05T03:23:31.803104Z'
  stage: tests
  run: 5fb0aa8149ca41c5b6b5552ba70801b0
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T03:23:36.801720Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-05T03:28:49.712873Z'
  stage: doing
  run: 07ee2d4707984192bfbc34dbd21f3b95
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T03:28:55.141032Z'
  stage: review
---

# The machine area holds containers, images and disks

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `machine` area: containers, images, the stage environment, snapshots, disks, the preflight, the project's commands and the machine's power. Each of its 24 modules moves from its layer package to the same layer inside `factory.machine`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/machine/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.machine`, `factory.machine.domain`, `factory.machine.application`, `factory.machine.adapters`; and the same folders under `tests/machine/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.containers` → `factory.machine.domain.containers`
- `factory.domain.disk` → `factory.machine.domain.disk`
- `factory.domain.preflight` → `factory.machine.domain.preflight`
- `factory.domain.command_records` → `factory.machine.domain.command_records`
- `factory.domain.stage_layer` → `factory.machine.domain.stage_layer`
- `factory.application.containers` → `factory.machine.application.containers`
- `factory.application.disk_records` → `factory.machine.application.disk_records`
- `factory.application.images` → `factory.machine.application.images`
- `factory.application.machine_stop_exit` → `factory.machine.application.machine_stop_exit`
- `factory.application.preflight` → `factory.machine.application.preflight`
- `factory.application.project_commands` → `factory.machine.application.project_commands`
- `factory.application.stage_environment` → `factory.machine.application.stage_environment`
- `factory.application.snapshots` → `factory.machine.application.snapshots`
- `factory.adapters.podman_images` → `factory.machine.adapters.podman_images`
- `factory.adapters.podman_runs` → `factory.machine.adapters.podman_runs`
- `factory.adapters.fake_containers` → `factory.machine.adapters.fake_containers`
- `factory.adapters.fake_images` → `factory.machine.adapters.fake_images`
- `factory.adapters.fake_snapshots` → `factory.machine.adapters.fake_snapshots`
- `factory.adapters.copy_snapshots` → `factory.machine.adapters.copy_snapshots`
- `factory.adapters.zfs_snapshots` → `factory.machine.adapters.zfs_snapshots`
- `factory.adapters.disk_space` → `factory.machine.adapters.disk_space`
- `factory.adapters.make_commands` → `factory.machine.adapters.make_commands`
- `factory.adapters.power_off` → `factory.machine.adapters.power_off`
- `factory.adapters.preflight_stamp_file` → `factory.machine.adapters.preflight_stamp_file`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `machine` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/machine/<its layer>/` when every one of its imports from `factory` is a module of the `machine` area or of an area already moved before it and at least one is of `machine`.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The package docstrings are exactly: `factory.machine`: "The machine area: containers, images, snapshots, disks and the preflight."; each layer package: "The machine area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.machine.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.machine`, `factory.machine.domain`, `factory.machine.application`, `factory.machine.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `machine` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `machine` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.machine.domain.containers as m; print(m.__name__)"
```
Expect: `factory.machine.domain.containers`

```bash
test -e src/factory/domain/containers.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names 4 new packages with exact docstrings and 24 concrete old→new module moves (5 domain, 8 application, 11 adapters, which matches the Description's count). The tester's and coder's split of work follows feature decision 5.
   - Criteria: each is testable by one parametrized test (one row per module for 1 and 3). Criterion 1 includes the AREAS key per decision 8. This is a pure move with no new rules, so there is no failing side to cover. Criterion 4 gives the rule for which test modules move.
   - Smoke test: three commands are runnable. The pytest one passes no `-q` and relies on the project's addopts; its `tail -1 | grep -c passed` expectation (`1`) is checkable. The other two Expect lines are exact outputs.
   - Architecture: modules go to the machine area with their layers inside, as feature decisions 1 and 2 say. The moves stay inside the layer rules. No re-export is left behind (decision 4).
   - Scope: the story is inside F0051 scope (S0006 in the story list). It changes no behaviour or names, and it leaves docs/decisions.md alone. I did not open the source tree to confirm that each of the 24 old modules exists.
4. factory: started tests as vm.
5. tester: Round 0. The Interface asks for every test change the move needs to happen in this run, before the code moves, under the leave of feature decision 5, so I made them all here. Every earlier test keeps its name and checks the same thing.

   I added the `machine` row to `AREAS` in `tests/test_areas.py`, holding the 24 modules of the table. Nothing else in that module changed. Its tests are already parametrized over `AREAS`, so I wrote no new test functions:
   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (the `machine.<layer>.<name>` rows; the key and its modules are the new `AREAS["machine"]` entry)
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.machine`, `factory.machine.adapters`, `factory.machine.application`, `factory.machine.domain`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module; `source_search.imports` covers the three import forms)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own checks the modules now under `tests/machine/`.
   - criteria 5 and 6: these are the closing ones and are not tested.

   Test changes (feature decision 5):
   1. I used sed to rewrite every `factory.<layer>.<name>` of the 24 modules under `tests/` (except `tests/test_areas.py`) to `factory.machine.<layer>.<name>`. This covers dotted keys in string literals too, such as `modules()[...]` and `test_make_search`'s expected set. I rewrote the `from factory.<layer> import <name>` forms by hand:
      - `tests/test_one_stage_environment.py` (preflight, stage_environment)
      - `tests/adapters/test_runtimes_without_wrapper.py` and `tests/test_second_user_removed.py` (preflight)
      - `tests/conftest.py`, `tests/adapters/test_podman_runs_fence.py` and `tests/adapters/test_podman_runs_job_profile.py` (podman_runs)
      - `tests/adapters/test_make_last_line_shared.py`, `tests/adapters/test_make_commands.py` and `tests/test_second_user_removed.py` (make_commands)
      Then I ran `ruff check --fix tests` and `ruff format tests`.
   2. I changed the guards that pin the old layout:
      - `tests/test_make_search.py`: in `CHECK_MODULES`, `application/project_commands.py` → `machine/application/project_commands.py` and `adapters/make_commands.py` → `machine/adapters/make_commands.py`.
      - `tests/shared/adapters/test_run_or_raise.py::test_the_wrappers_hold_no_copy_of_the_run_or_raise_block`: `SRC / "adapters"` → `SRC / "machine" / "adapters"`. All three of its rows (zfs_snapshots, power_off, podman_runs) are moved modules.
      No other test names a source path of a moved module or the path of a moved test module.
   3. I created empty `tests/machine/__init__.py` and `tests/machine/{domain,application,adapters}/__init__.py`.
   4. I used `git mv` to move 41 test modules to the same layer under `tests/machine/`. These are the ones criterion 4's rule selects once the imports are rewritten, and each imports at least one `factory.machine` module.
      - From `tests/domain/` (11): test_command_records, test_container_extra_environment, test_containers, test_containers_beneath_or_at, test_containers_job_options, test_disk, test_disk_records, test_preflight, test_preflight_stamp, test_preflight_stop_records_paths, test_stage_layer.
      - From `tests/application/` (8): test_container_environment_extra, test_container_items, test_containers_interface, test_disk_space_interface, test_opencode_item_container, test_preflight_snapshots_item, test_snapshots_interface, test_token_file_item.
      - From `tests/adapters/` (22): test_agent_launch_container, test_agent_launch_extra, test_claude_runtime_container, test_copy_snapshots, test_disk_space, test_fake_containers, test_fake_snapshots, test_opencode_runtime_container, test_opencode_runtime_lockdown, test_podman_images, test_podman_runs, test_podman_runs_fence, test_podman_runs_instance_label, test_podman_runs_job_profile, test_podman_runs_results, test_podman_timeout_status, test_power_off, test_preflight_stamp_file, test_process_exit, test_runtime_podman_timeout_status, test_zfs_snapshots, test_zfs_snapshots_drop_caches.
      None of them builds a path from its own `__file__`. The only `__file__` among them is inside test_podman_images's stand-in script, which refers to the stand-in's own folder.

   Files I created: the four `tests/machine/**/__init__.py` files. Earlier test files I changed: `tests/test_areas.py`, `tests/test_make_search.py`, `tests/shared/adapters/test_run_or_raise.py`, and the import lines of every test and support file the rewrite touched, `tests/conftest.py` included. The 41 modules above were moved.

   Run: `uv run pytest -q` over the 121 changed or moved test files. It stops at collection with `ModuleNotFoundError: No module named 'factory.machine'` (`tests/wiring_support.py:11`, reached through `tests/acceptance_walk.py`). That is the right reason. The runner could not import `factory.machine`, its three layer packages, or any of the 24 modules under them. `make lint`: `lint: green (0.1 s)`.

   A note for the coder: `pyproject.toml` per-file-ignores, the mutmut settings, the import-linter contracts and `security/duplicates-baseline.txt` may still name old `src/factory/<layer>/` paths of these modules. I did not check them; they are outside my write paths.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Round 0. I moved the 24 modules and all the code passes, except for one guard test that still pins the old layout. That test needs a change from the tester, so I am ending with `tests`.

   The change: in `tests/test_stop_table.py::test_production_code_names_every_reason_of_a_repository_stop`, the prefix filter `name.startswith(("factory.application", "factory.entry"))` should also accept `factory.machine.application`. The constant `_MAIN_FAILING = "main_branch_failing"` now lives in `src/factory/machine/application/preflight.py`, so the `[main_branch_failing]` row fails:
   ```
   FAILED tests/test_stop_table.py::test_production_code_names_every_reason_of_a_repository_stop[main_branch_failing] - AssertionError: assert 'main_branch_failing' in {'', '\n', '\n\n', '\n\nCost: ',...
   ```
   That is the only failure in `make check`. lint, types, layers, sast, secrets and licenses are green, and every other test passes (coverage 99.26 %). Adding `"factory.machine.application"` to the tuple restores what the test checked before the move. A pattern like `factory.*.application` would be broader, and the choice is the tester's.

   What I built, all in `src/` and with no behaviour change:
   - New packages, with the Interface's exact docstrings:
     - `src/factory/machine/__init__.py`
     - `src/factory/machine/domain/__init__.py`
     - `src/factory/machine/application/__init__.py`
     - `src/factory/machine/adapters/__init__.py`
   - The 24 modules of the table, each moved with `git mv` to `src/factory/machine/<layer>/<name>.py`.
   - Every `factory.<layer>.<name>` import of a moved module rewritten under `src/`, then `ruff check --fix` and `ruff format` for the import order. That touched 35 files in total (82 lines in, 82 out). No `from factory.<layer> import <name>` forms and no relative imports were in `src/`. No re-export or file is left at an old path.

   Main choice: a mechanical rewrite of the dotted path, module by module, with a word boundary (`\b`). I rejected rewriting by package prefix because `factory.application` still holds modules that are not moving.

   Refactor step: there was nothing to change; the diff is only paths and import order.

   Noticed but not touched:
   - `pyproject.toml` already has the human's per-file-ignores for `src/factory/machine/adapters/{make_commands,podman_runs}.py`. The stale entries for the old `src/factory/adapters/` paths are still there (lines 63 and 66). They are the human's lines and do no harm.
   - `security/duplicates-baseline.txt` lines 37 to 41 still name `src/factory/adapters/{fake_containers,fake_images,fake_snapshots,make_commands}.py`. `make duplicates` is a record, not a check. After S0005 the human updated these paths themselves, so I left them.

   Docs (criterion 6) are the documenter's.
8. factory: started tests as vm.
9. tester: Mode: a test change the human approved. I made the change the coder's entry 7 names, and nothing else.

   What I changed: `tests/test_stop_table.py::test_production_code_names_every_reason_of_a_repository_stop` filters modules by prefix. That filter was `("factory.application", "factory.entry")` and is now `("factory.application", "factory.machine.application", "factory.entry")`. The reason: the constant `"main_branch_failing"` moved with `preflight` to `src/factory/machine/application/preflight.py`. Adding that one package brings back the set of modules the test read before the move, so the test checks the same thing it did then. I rejected a wider pattern such as `factory.*.application`, because it would also bring in application packages that the test never read before. The test keeps its name.

   Earlier test file changed: `tests/test_stop_table.py`, one line, under feature decision 5's leave for test changes the move needs. I created no files.

   Run: `uv run pytest -q tests/test_stop_table.py` passed all 26 tests, and every module imported. `make lint`: lint: green (0.1 s).

   `lint`: lint: green (0.2 s)
10. factory: started doing as vm.
11. coder: Round 0, second run in doing. The tester made the change I asked for in entry 7, so I changed no code this time. `make check` now ends with `check: green`: coverage is 99.26 % and `test: green (133.6 s)`.

    What I built (from entry 7, already on the branch):
    - `src/factory/machine/__init__.py` and `src/factory/machine/{domain,application,adapters}/__init__.py`, each with the docstring the Interface gives.
    - The 24 modules of the table, each moved with `git mv` to `src/factory/machine/<layer>/<name>.py`.
    - Every import of a moved module rewritten under `src/`. Nothing is left at an old path and there is no re-export.

    Main choice: I rewrote each module's dotted path one by one, matching on word boundaries. I rejected rewriting by package prefix, because `factory.<layer>` still holds modules that are not moving.

    Refactor: nothing to change. The diff is only paths and import order.

    What the journal changed: the tester widened the prefix filter in `tests/test_stop_table.py` to take in `factory.machine.application`. The Description's meaning stays the same.

    Noticed but not touched:
    - `pyproject.toml` still has per-file-ignores for the old `src/factory/adapters/{make_commands,podman_runs}.py` paths, beside the new ones.
    - `security/duplicates-baseline.txt` still names the old `src/factory/adapters/` paths of fake_containers, fake_images, fake_snapshots and make_commands.

    Both files are the human's. The docs of criterion 6 are the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 10 new, 35 known, 8 gone
12. factory: started review as vm.
