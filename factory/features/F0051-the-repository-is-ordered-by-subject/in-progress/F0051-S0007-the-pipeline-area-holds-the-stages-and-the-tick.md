---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 562
comments_read: [6649241093, 6649574994]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T03:39:39.403589Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T03:39:39.410082Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T03:40:02.178460Z'
  stage: intake
  run: 9b3d0beebc6e43e9be5a6a06cc886dad
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T03:40:07.227126Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T03:45:30.213443Z'
  stage: tests
  run: 41c4309683e04e2e90b5f771de853a1f
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T03:45:36.006483Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-11-05T03:49:51.869380Z'
  stage: doing
  run: ca6bf6fbb3b2404a83914576765db165
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-11-05T03:55:46.295451Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T03:55:48.881975Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T03:58:51.883100Z'
  stage: doing
  run: bb5444732b594d4c847d3fa4fba364c1
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-05T03:58:57.124094Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-05T04:00:30.146191Z'
  stage: tests
  run: 8b9998dc1c8b448da5b28fa69e0f8383
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-05T04:00:35.462320Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-05T04:05:55.946705Z'
  stage: doing
  run: 135d5e6949c448a3836fb1489103309d
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T04:06:01.069731Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: question
  at: '2026-11-05T04:11:19.357087Z'
  stage: review
  run: 55e125550bef4aa481102a956ad4c1da
  blocked: question
- number: 17
  speaker: human
  kind: comment
  at: '2026-11-05T04:21:17.902128Z'
  stage: review
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-05T04:21:20.471227Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-05T04:23:06.955531Z'
  stage: review
  run: 0fb92c858c8442e7aee6ac8f26823a7e
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-05T04:23:12.434955Z'
  stage: docs
- number: 21
  speaker: documenter
  kind: result
  at: '2026-11-05T04:24:32.253424Z'
  stage: docs
  run: 65530bb8c0dc4449be7dad456c0f0009
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-05T04:24:37.675842Z'
  stage: smoke-test
- number: 23
  speaker: smoke-tester
  kind: result
  at: '2026-11-05T04:26:35.570471Z'
  stage: smoke-test
  run: 42242ed8814441a491a163ea0fa4e837
---

# The pipeline area holds the stages and the tick

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `pipeline` area: the pipeline definition, stages, checks, events, the tick, the scheduler and dispatcher, the handlers, claims, leases, stops, stalls, recovery and `Boundaries`. Each of its 27 modules moves from its layer package to the same layer inside `factory.pipeline`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/pipeline/<layer>/` (feature decision 5). It is the last move: afterwards `src/factory/` holds only the seven areas, `entry/` and `contract/`; the old layer packages `factory.domain`, `factory.application` and `factory.adapters` are gone, and every test module still left under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to the area of the module it imports most, except that one that imports `factory.entry` moves to `tests/entry/` and one that imports no factory module moves to the `tests/` root, because an area folder holds only test modules that import their own area and no `factory.entry`. No behaviour changes: every test that passed before passes after. Only its import lines and paths change, apart from the guards that pin the old layout (feature decision 5) and the three test changes the human allowed in journal entry 8.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.pipeline`, `factory.pipeline.domain`, `factory.pipeline.application`, `factory.pipeline.adapters`; and the same folders under `tests/pipeline/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.checks` → `factory.pipeline.domain.checks`
- `factory.domain.evaluation` → `factory.pipeline.domain.evaluation`
- `factory.domain.events` → `factory.pipeline.domain.events`
- `factory.domain.fault_paths` → `factory.pipeline.domain.fault_paths`
- `factory.domain.known_results` → `factory.pipeline.domain.known_results`
- `factory.domain.lease` → `factory.pipeline.domain.lease`
- `factory.domain.pipeline_definition` → `factory.pipeline.domain.pipeline_definition`
- `factory.domain.recovery` → `factory.pipeline.domain.recovery`
- `factory.domain.stop_table` → `factory.pipeline.domain.stop_table`
- `factory.domain.stops` → `factory.pipeline.domain.stops`
- `factory.domain.tick_status` → `factory.pipeline.domain.tick_status`
- `factory.application.boundaries` → `factory.pipeline.application.boundaries`
- `factory.application.claims` → `factory.pipeline.application.claims`
- `factory.application.dispatcher` → `factory.pipeline.application.dispatcher`
- `factory.application.handlers` → `factory.pipeline.application.handlers` (a package)
- `factory.application.idle_shutdown` → `factory.pipeline.application.idle_shutdown`
- `factory.application.known_results` → `factory.pipeline.application.known_results`
- `factory.application.pipeline_loading` → `factory.pipeline.application.pipeline_loading`
- `factory.application.recovery` → `factory.pipeline.application.recovery`
- `factory.application.scheduler` → `factory.pipeline.application.scheduler`
- `factory.application.stage` → `factory.pipeline.application.stage`
- `factory.application.stalls` → `factory.pipeline.application.stalls`
- `factory.application.stops` → `factory.pipeline.application.stops`
- `factory.application.take` → `factory.pipeline.application.take`
- `factory.application.task` → `factory.pipeline.application.task`
- `factory.application.tick` → `factory.pipeline.application.tick`
- `factory.adapters.pipeline_yaml` → `factory.pipeline.adapters.pipeline_yaml`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `pipeline` with the modules above; nothing else in that module changes.
- Every test module still under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/<area>/<its layer>/` of the area of the module it imports most; the three folders are then removed.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The recipe the earlier moves used, so that no run needs to read their journals: one `sed -E` over `src/` and `tests/` that rewrites `factory\.(domain|application|adapters)\.(<the names of the table>)` to `factory.pipeline..`; then the `from factory.<layer> import a, b` lines that mix moved and unmoved names, split by hand; then `ruff check --fix` and `ruff format`. `handlers` is a package: its submodules `factory.application.handlers.<name>` follow with it.
- The package docstrings are exactly: `factory.pipeline`: "The pipeline area: the pipeline definition, the stages, the tick and its handlers."; each layer package: "The pipeline area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.pipeline.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.pipeline`, `factory.pipeline.domain`, `factory.pipeline.application`, `factory.pipeline.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. `tests/domain/`, `tests/application/` and `tests/adapters/` do not exist.
5. `src/factory/` holds exactly `__init__.py`, the seven area packages, `entry/` and `contract/`; `factory.domain`, `factory.application` and `factory.adapters` cannot be imported.
6. `make check` stays green.
7. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `pipeline` and what it holds, in one sentence. Every place in `README.md`, `docs/operator-guide.md` or `docs/project-guide/` that names `factory.domain`, `factory.application` or `factory.adapters` as a package names the area package or layer that holds it now; the `make mutants` examples use an existing area package, for example `MODULES='factory.machine.domain.disk factory.pipeline.application'`. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.pipeline.domain.checks as m; print(m.__name__)"
```
Expect: `factory.pipeline.domain.checks`

```bash
test -e src/factory/domain/checks.py && echo still there || echo moved
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
   - Interface: concrete. It gives 27 old → new module paths (11 domain, 15 application including the `handlers` package, 1 adapter), the four new packages with exact docstrings, and the test folders. The `AREAS` change is named. The recipe and the tester/coder split are stated.
   - Criteria: each is testable by one parametrized test function. 1 has a row per module, covers the key and exact module set of `AREAS` (standing answer 8), and has both sides: the new path imports and the old path does not exist. 2 checks the four packages import and have a docstring. 3 has one row per module and covers all three import forms. 4 and 5 are existence and absence checks, with the old layer packages not importable. 6 and 7 are the closing criteria. The docstring text and the `__init__.py` files are not tested, per standing answer 8, so I did not ask for criteria for them.
   - Smoke test: runnable. The pytest line passes no `-q` and `pyproject.toml` `addopts` already sets one `-q`, so the summary line exists and `grep -c passed` gives 1. Each `Expect:` can be checked against the output.
   - Architecture: matches `CLAUDE.md`. Each layer stays inside `factory.pipeline` and keeps its name and content, with no re-export left behind. `Layers` losing the optional old layers and `make areas` are the human's changes at S0007's start and merge, not this story's scope.
   - Scope: within F0051 (S0007 in the feature's list, the pipeline area last). It touches none of the feature's out-of-scope items and changes no behaviour. The names `known_results`, `recovery` and `stops` exist in both the domain and application layers, and each is listed in its own layer, so there is no ambiguity.
4. factory: started tests as vm.
5. tester: Wrote this story's tests and made the test-side move from the Interface: imports rewritten, test modules moved with `git mv`, guards changed under feature decision 5. The tests are now red on purpose.

   Criterion → test:
   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (rows `pipeline.<layer>.<name>`; `AREAS` gains the `pipeline` key with the 27 modules of the table, and nothing else in the module changed)
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.pipeline`, `factory.pipeline.domain`, `.application`, `.adapters`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (rows `pipeline.<layer>.<name>`; `imported_modules` covers all three import forms)
   - criterion 4: tests/test_old_layer_packages_removed.py::test_no_test_folder_of_an_old_layer_is_left (one row per layer)
   - criterion 5: tests/test_old_layer_packages_removed.py::test_the_package_holds_only_its_init_the_areas_entry_and_contract and ::test_an_old_layer_package_cannot_be_imported (one row per layer). The listing leaves out `__pycache__`, because it is not tracked.
   - criteria 6 and 7: the closing ones, not tested here.

   Files created: tests/test_old_layer_packages_removed.py; `__init__.py` (empty, like the existing test packages) in tests/pipeline/, tests/pipeline/{domain,application,adapters}/, tests/pipeline/application/handlers/, and in any area layer folder that did not have one yet.

   Test-side move:
   - Imports: the sed from the recipe ran over `tests/`, plus the two `from factory.domain import lease|checks` lines and then `ruff check --fix` and `ruff format`. No file under `tests/` imports an old path now.
   - Where the 219 test modules from tests/{domain,application,adapters} went (moved with `git mv`). "The area of the module it imports most" needed a rule, so I used this one:
     - Into tests/pipeline/<layer>/ (handlers into tests/pipeline/application/handlers/, with their conftest.py), if any of these holds:
       - it is under `handlers/`;
       - its name starts with a pipeline subject (`test_checks|evaluation|events|fault_paths|known_results|lease|pipeline|recovery|stop|tick|boundaries|claims|dispatcher|idle_shutdown|scheduler|stage|stall|take|task`) and it imports `factory.pipeline`;
       - pipeline is tied for the most distinct imported modules.
     - Otherwise into the area with the most distinct imported modules, with `shared` losing ties.
     - Exceptions:
       - five modules that import `factory.entry` went to tests/entry/: test_board_reader_acceptance, test_tick_agent_definition, test_tick_project_agent, test_watcher_main_ref, test_runtimes_without_wrapper. In an area folder they would fail test_areas.py's guard, which allows only area imports.
       - six modules that import no factory module went to the tests/ root: test_contract_login, test_contract_provider_limit, test_opencode_limit_wait_on_stderr, test_opencode_resume_session, test_opencode_runtime_transcript, test_pipeline_stage_moves. In an area folder they would fail the same guard's "imports own area" check.
     - I checked by hand: every moved module imports its own area and no area folder holds a `factory.entry` import.
   - The support modules claude_stand_in.py, container_runtime_support.py, opencode_stand_in.py and pygithub_stand_ins.py moved from tests/adapters/ to the tests/ root (standing leave), and `from adapters.X` became `from X`.
   - The old folders' `__init__.py` files were removed with `git rm`; tests/domain, tests/application and tests/adapters are gone.

   Earlier test files I changed for the new layout (feature decision 5 / standing leave). Every test keeps its name and checks the same thing:
   - tests/test_layers.py: `LAYERS` is now `pipeline.domain`, `pipeline.application`, `pipeline.adapters`, `entry`. The domain-bottom check now imports `factory.pipeline.domain` and allows only domain packages.
   - tests/test_stop_table.py: prefix `factory.application` → `factory.pipeline.application`.
   - tests/test_agent_run_request_search.py: `WITHOUT_PROCESS_ENVIRONMENT` → pipeline domain and application.
   - tests/entry/test_wiring.py: `factory.adapters` → `factory.pipeline.adapters`.
   - tests/hosting/domain/test_hosting.py (was tests/domain/test_hosting.py): `_is_domain` `factory.domain` → `factory.pipeline.domain`.
   - Path strings:
     - tests/test_make_search.py: `pipeline/domain/checks.py`
     - tests/test_opencode_shared_steps.py: `STAND_IN`
     - tests/test_suite_held_once.py: entry/test_runtimes_without_wrapper.py, pipeline/application/test_stage_on_container_fakes.py
     - tests/test_suite_leftovers.py: hosting/application/test_checkout_preparer.py
     - tests/test_suite_old_names.py: test_contract_provider_limit.py at the root
   - Depth fixes after moving one level deeper:
     - tests/machine/application/test_interfaces.py: `TESTS = parents[2]`
     - tests/pipeline/adapters/test_pipeline_yaml_tool_paths.py: `ROOT = parents[3]`

   Red run: `uv run pytest -q` over the 332 test files this stage wrote, moved or changed ends at tests/conftest.py → tests/acceptance_walk.py:8 with `ModuleNotFoundError: No module named 'factory.pipeline'`. That is the right reason. `make lint`: green.

   Module the test run could not import: `factory.pipeline` (and so every `factory.pipeline.*` module).

   Open for the coder: pyproject.toml:156-157 still deselects `tests/domain/test_hosting.py::…` for mutmut; that file is now tests/hosting/domain/test_hosting.py. It is outside my write paths and outside `make check`.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Stopped with the move done in `src/` and `make check` red. What is left is outside my write paths: one change in `pyproject.toml` and some test changes.

   Done (left in the working tree):
   - The 27 modules of the table, and the `handlers` package, moved with `git mv` to `src/factory/pipeline/{domain,application,adapters}/`.
   - `src/factory/pipeline/__init__.py` and the three layer `__init__.py` files created, with the docstrings from the Interface.
   - The old `__init__.py` files removed with `git rm`. `src/factory/` now holds `__init__.py`, the seven areas, `entry/` and `contract/`.
   - Imports under `src/` rewritten with the recipe's sed, then `ruff check --fix` and `ruff format`. No `src/` file names an old path.
   - lint, types, sast, secrets and licenses: green.

   Red 1, `make layers`: `Module 'factory.domain' does not exist.` The two forbidden contracts in `pyproject.toml` (lines 103–104 and 110–111) still name `factory.domain`, `factory.domain.**`, `factory.application`, `factory.application.**`, `factory.adapters` and `factory.adapters.**`. I removed exactly those entries in a temporary copy (`sed -E 's/, "factory\.(domain|application|adapters)(\.\*\*)?"//g'`) and ran `lint-imports --config` on it: 4 contracts kept, 0 broken. The optional `(adapters)`, `(application)`, `(domain)` entries in `Layers` cause no error. `pyproject.toml` is not in the coder's write paths. Intake also counted this as the human's change at the start of S0007, and it is not on `main` yet. The `tests/domain/test_hosting.py` mutmut deselect at lines 156–157, which the tester named, needs the same treatment.

   Red 2, `make test`: 16 failures, all on the test side:
   - 12 rows call `importlib.util.find_spec("factory.<old layer>.<x>")` (or `import_module`) on modules removed long ago. With the parent package gone, this raises `ModuleNotFoundError` instead of returning None. The files: tests/test_checkout_hygiene_removed.py [sealed-runs-module], tests/test_docker_path_removed.py [sessions-module], tests/entry/test_mutation_report_removed.py [report-rules], tests/test_undo_removed.py [undo-module], tests/test_home_reset_removed.py (4 rows), tests/test_hook_removed.py [adapter-module], tests/test_kernel_guard_removed.py [factory.adapters.landlock, factory.domain.confinement], tests/test_leftovers_program_removed.py [factory.domain.leftovers].
   - tests/pipeline/application/test_tick.py:488, test_the_tick_knows_no_run_record_and_no_lock [application/tick.py, domain/evaluation.py]: `E FileNotFoundError: ... '/work/checkout/src/factory/application/tick.py'`. The paths in its rows need the `pipeline/` prefix.
   - tests/test_areas.py:262, test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own [shared/domain/test_settings_model_rules.py, hosting/domain/test_hosting.py]: `E AssertionError: ... imports areas not yet moved: ['factory']`. Both modules `import factory` for `factory.__file__`. The tester moved them into area folders, and there the guard refuses a bare `factory` import.

   Question: may I go ahead like this?
   (a) You make the `pyproject.toml` change above on `main`, and I end the next run with `tests` so the tester can make these test changes under feature decision 5:
     - catch the parent package's absence in the removed-module checks, e.g. `find_spec` inside `try`/`except ModuleNotFoundError` counting as gone;
     - prefix test_tick's paths with `pipeline/`;
     - for the two `import factory` modules, either move them to the `tests/` root or let the guard accept a bare `import factory`.
   (b) You add `pyproject.toml` to this story's coder write paths, and I make the import-linter change myself.
   I would choose (a). Nothing else in `src/` is open. I have not run the refactor step yet, because `make check` is not green.
8. 2026-11-05 human: Answer of the human:

   **(a).** `pyproject.toml` on `main` no longer names `factory.domain`, `factory.application` or `factory.adapters` (with or without `.**`) in the three forbidden contracts; `lint-imports` is green on `main` with it. The next stage merges `main` into the branch. The mutmut deselect of `tests/domain/test_hosting.py` is only read by `make mutants`, so it follows after the merge, with the other follow-ups.

   End with `tests`. Leave for the tester under feature decision 5, as you list them:
   - the removed-module checks count a `ModuleNotFoundError` from `find_spec` or `import_module` (the parent package being gone) as "gone", each test keeping its name and what it checks;
   - `tests/pipeline/application/test_tick.py`'s paths take the `pipeline/` prefix;
   - `tests/test_areas.py`'s guard accepts a bare `import factory` in an area folder (it belongs to no area, as S0001's tester already wrote), so the two modules stay where they moved.
9. factory: started doing as vm.
10. coder: Following the human's answer (a): the tester should make the three test changes the human approved under feature decision 5. Each test keeps its name and still checks the same thing:
    - In the removed-module checks, a `ModuleNotFoundError` from `find_spec` or `import_module` (the parent package is gone) counts as "gone". These are the 12 rows in tests/test_checkout_hygiene_removed.py [sealed-runs-module], tests/test_docker_path_removed.py [sessions-module], tests/entry/test_mutation_report_removed.py [report-rules], tests/test_undo_removed.py [undo-module], tests/test_home_reset_removed.py (4 rows), tests/test_hook_removed.py [adapter-module], tests/test_kernel_guard_removed.py [factory.adapters.landlock, factory.domain.confinement] and tests/test_leftovers_program_removed.py [factory.domain.leftovers].
    - In tests/pipeline/application/test_tick.py::test_the_tick_knows_no_run_record_and_no_lock, the paths in the rows `application/tick.py` and `domain/evaluation.py` take the `pipeline/` prefix.
    - In tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own, the guard accepts a bare `import factory` in an area folder. That makes tests/shared/domain/test_settings_model_rules.py and tests/hosting/domain/test_hosting.py pass where they now are.

    What I did this run (in `src/` only):
    - The last run had left one tracked file behind: `src/factory/application/handlers/__init__.py`. That kept a `src/factory/application/` folder alive. I moved it with `git mv` to `src/factory/pipeline/application/handlers/__init__.py`, the package's `__init__.py`, which was missing there.
    - `src/factory/` now holds exactly `__init__.py`, the seven areas, `entry/` and `contract/`.

    Main choice: I moved the leftover file instead of writing a new `__init__.py`. The move keeps the original docstring and the file's history.

    `make check` after the merge of `main`:
    - lint, types, layers, sast, secrets and licenses are green. layers is green because `pyproject.toml` on `main` no longer names the old packages.
    - test is red with exactly the 16 failures listed above, all on the test side.

    Refactor: not run yet. It waits until `make check` is green. The `src/` diff is a mechanical move, and I see nothing in it to change.

    Noticed but not touched: the `tests/domain/test_hosting.py` mutmut deselect in pyproject.toml (the human leaves it for after the merge). It is outside my write paths.
11. factory: started tests as vm.
12. tester: I made the three test changes the human approved in entry 8, as the coder listed them in entry 10. These change existing tests and add no new criterion, so there is no criterion → test mapping this run, and no new test files. Every test keeps its name and checks the same thing.

    1. Removed-module checks. A `ModuleNotFoundError` raised because the parent package is gone now counts as "gone".
       - New shared helper `module_exists(module) -> bool` in tests/module_names.py, beside `has_name`. It wraps `importlib.util.find_spec` and returns False on `ModuleNotFoundError`. I used one helper instead of eight copies of try/except.
       - Rows changed to use it:
         - tests/test_checkout_hygiene_removed.py [sealed-runs-module]
         - tests/test_docker_path_removed.py (`_sessions_module_is_gone`)
         - tests/entry/test_mutation_report_removed.py (all four rows; the "found" rows still expect True)
         - tests/test_undo_removed.py [undo-module] (the expected value went from None to False)
         - tests/test_home_reset_removed.py (test_the_modules_of_the_home_reset_are_gone)
         - tests/test_hook_removed.py [adapter-module, entry-module] (expected None → False)
         - tests/test_kernel_guard_removed.py (test_the_wrapper_and_the_kernel_s_modules_are_gone)
         - tests/test_leftovers_program_removed.py (test_the_leftovers_modules_are_gone)
       - ruff removed the `importlib.util` imports that were no longer used.
    2. tests/pipeline/application/test_tick.py::test_the_tick_knows_no_run_record_and_no_lock: the rows `application/tick.py` and `domain/evaluation.py` are now `pipeline/application/tick.py` and `pipeline/domain/evaluation.py`. Both files exist.
    3. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own: the `outside` list now leaves out a bare `factory` import, because it belongs to no area. tests/shared/domain/test_settings_model_rules.py and tests/hosting/domain/test_hosting.py stay where they are.

    Earlier test files changed (by the human's leave in entry 8, under feature decision 5):
    - tests/module_names.py
    - tests/test_checkout_hygiene_removed.py
    - tests/test_docker_path_removed.py
    - tests/entry/test_mutation_report_removed.py
    - tests/test_undo_removed.py
    - tests/test_home_reset_removed.py
    - tests/test_hook_removed.py
    - tests/test_kernel_guard_removed.py
    - tests/test_leftovers_program_removed.py
    - tests/pipeline/application/test_tick.py
    - tests/test_areas.py

    Run: I ran `uv run pytest -q` once over those files and it ended with every test passing. `make lint`: green. Every module imported; none were missing.

    Still open, as the human said in entry 8: the mutmut deselect of `tests/domain/test_hosting.py` in pyproject.toml. It is outside my write paths.

    `lint`: lint: green (0.2 s)
13. factory: started doing as vm.
14. coder: I checked `make check` on the committed state, which holds the move from the earlier doing runs and the three test changes from the tester's entry 12. It ends `test: green (131.0 s)` and `check: green`, with total branch coverage at 99.26 %. I made no code changes this run.

    What I built (all of it in the earlier doing runs, under `src/` only):
    - The 27 modules of the table, including the `handlers` package with its `__init__.py`, moved with `git mv` to `src/factory/pipeline/{domain,application,adapters}/`.
    - `src/factory/pipeline/__init__.py` and `src/factory/pipeline/{domain,application,adapters}/__init__.py` created, each with the docstring the Interface gives.
    - The old `__init__.py` files of `factory.domain`, `factory.application` and `factory.adapters` removed. `src/factory/` now holds exactly `__init__.py`, the seven areas, `entry/` and `contract/`.
    - Imports rewritten with the recipe's sed, then `ruff check --fix` and `ruff format`. A grep over `src/` for `factory.(domain|application|adapters)` and `factory/(domain|application|adapters)/` finds nothing.

    Main choice: each file was moved whole with `git mv`, the leftover `handlers/__init__.py` included, so every module keeps its content and its history. I rejected writing a fresh `__init__.py` for `handlers`, and I rejected leaving re-exports at the old paths, which feature decision 4 rules out.

    Refactor: I read the `src/` diff, which is a mechanical move plus import rewrites. Nothing in it needed changing.

    The journal did not change what the task means. The human's answer in entry 8 only decided who makes the `pyproject.toml` change and the test changes, so the Description stays as it is.

    Noticed, not touched: in `pyproject.toml`, the mutmut deselect of `tests/domain/test_hosting.py` (that file is now `tests/hosting/domain/test_hosting.py`). Only `make mutants` reads it, it is outside my write paths, and the human left it as a follow-up after the merge (entry 8).

    `check`: check: green
    `duplicates`: duplicates: 9 new, 36 known, 7 gone
15. factory: started review as vm.
16. reviewer: Question for the human: criterion 7 (docs) covers only the module paths in the table. It does not cover the docs that name the three packages this story removes, and after this story they point at nothing:
    - docs/operator-guide.md:148: `make mutants MODULES=factory.application ...`. That example would now mutate nothing.
    - docs/project-guide/processes-and-checks.md:120: "the fakes of `factory.adapters`".
    - docs/project-guide/processes-and-checks.md:174: the example `MODULES='factory.machine.domain.disk factory.application'`.
    - docs/project-guide/watching.md:274: "called in `factory.application`".
    - docs/project-guide/work-items.md:190: "one reader class and one writer class in `factory.adapters`, behind an interface in `factory.application`".

    Only the reviewer, intake and smoke-test can write the work item, so sending it back to `doing` cannot fix the criterion. Options:
    (a) On the rerun I extend criterion 7 with: "every place in `README.md`, `docs/operator-guide.md` or `docs/project-guide/` that names `factory.domain`, `factory.application` or `factory.adapters` as a package names the area package or layer that holds it now". Then I pass the story to `docs`.
    (b) Criterion 7 stays as it is, and these lines go to a later story.
    I would choose (a): this is the story that removes those packages.

    Review of the diff (round 0), apart from that: no findings.
    - Group 1: criteria 1 to 3 are the rows `pipeline.<layer>.<name>` and the four packages in tests/test_areas.py. Criteria 4 and 5 are in tests/test_old_layer_packages_removed.py. Each test checks what its criterion says, and the coder's `make check` was green (entry 14).
    - Group 2: the src/ diff is 27 modules moved with `git mv` (handlers with its `__init__.py`), four new package `__init__.py` files with the Interface's docstrings, the three old `__init__.py` files removed, and import lines rewritten. Apart from import lines and docstrings, no src/ line changed. `src/factory/` holds exactly the areas, `entry/`, `contract/` and `__init__.py`, and no src/ file names an old path.
    - Group 3: no new noqa, nosec, nosemgrep, allowlist or type: ignore marker.
    - Group 4: I ran `make duplicates`: 9 new. Five are the old baseline entries under their new paths, and the same five show as gone: hand_over/acceptance, stage/stalls, dispatcher `unhandled_kinds`, stage `next_stage`, take `restored_work_item`. The other four (claude_runtime/opencode_runtime similar code, and three cost_records dead-code variables) are in files this diff does not touch. Still open, outside every stage's write paths: `security/duplicates-baseline.txt` (lines 2, 3, 19, 20, 33) keeps the old paths, and the `tests/domain/test_hosting.py` mutmut deselect in `pyproject.toml` is stale (entry 8 leaves it as a follow-up).
    - Group 5: covered by the question and the corrections below.

    description corrected: "every test module still left under ... moves to the area of the module it imports most" -> the same, plus: a module that imports `factory.entry` moves to `tests/entry/`, and one that imports no factory module moves to the `tests/` root. The guard in tests/test_areas.py and CLAUDE.md's rule for modules outside the layers settle that.
    description corrected: "with only its import lines and paths changed" -> "Only its import lines and paths change, apart from the guards that pin the old layout (feature decision 5) and the three test changes the human allowed in journal entry 8."

    Earlier tests (paths under tests/; FD5 = feature decision 5's leave: import lines and module/file paths of moved modules rewritten, test module moved with `git mv`, test package created, or a guard of the old layout changed). For every FD5 line I read the non-import lines of the diff, and each test keeps its name and what it checks:
    module_names.py: human's leave, entry 8 (`module_exists` added)
    test_checkout_hygiene_removed.py: human's leave, entry 8
    test_docker_path_removed.py: human's leave, entry 8
    test_home_reset_removed.py: human's leave, entry 8
    test_hook_removed.py: human's leave, entry 8
    test_kernel_guard_removed.py: human's leave, entry 8, plus FD5 (module path)
    test_leftovers_program_removed.py: human's leave, entry 8
    test_undo_removed.py: human's leave, entry 8, plus FD5 (module path)
    entry/test_mutation_report_removed.py: human's leave, entry 8
    application/test_tick.py -> pipeline/application/test_tick.py: FD5 (move), human's leave, entry 8 (`pipeline/` path prefix)
    test_areas.py: the story's Interface (`AREAS` row), human's leave, entry 8 (bare `import factory`)
    adapters/claude_stand_in.py -> claude_stand_in.py: standing leave to move a shared test helper
    adapters/container_runtime_support.py -> container_runtime_support.py: standing leave to move a shared test helper
    adapters/opencode_stand_in.py -> opencode_stand_in.py: standing leave to move a shared test helper
    adapters/pygithub_stand_ins.py -> pygithub_stand_ins.py: standing leave to move a shared test helper
    adapters/__init__.py -> pipeline/__init__.py: FD5
    application/__init__.py -> pipeline/adapters/__init__.py: FD5
    application/handlers/__init__.py -> pipeline/application/__init__.py: FD5
    domain/__init__.py -> pipeline/application/handlers/__init__.py: FD5
    test_layers.py: FD5 (guard)
    domain/test_hosting.py -> hosting/domain/test_hosting.py: FD5 (guard)
    test_agent_run_request_search.py: FD5 (guard)
    test_stop_table.py: FD5
    test_opencode_shared_steps.py: FD5 (path of the moved stand-in)
    test_suite_held_once.py: FD5 (paths)
    test_suite_leftovers.py: FD5 (paths)
    test_suite_old_names.py: FD5 (paths)
    test_make_search.py: FD5 (paths)
    application/test_interfaces.py -> machine/application/test_interfaces.py: FD5 (depth)
    adapters/test_pipeline_yaml_tool_paths.py -> pipeline/adapters/test_pipeline_yaml_tool_paths.py: FD5 (depth)
    acceptance_walk.py: FD5
    branch_reading.py: FD5
    claude_resume_support.py: FD5
    conftest.py: FD5
    container_extra_support.py: FD5
    container_support.py: FD5
    cost_image_support.py: FD5
    crash_support.py: FD5
    definition_support.py: FD5
    document_texts.py: FD5
    evaluation_support.py: FD5
    git_support.py: FD5
    known_results_support.py: FD5
    power_support.py: FD5
    preflight_support.py: FD5
    project_command_support.py: FD5
    proof_support.py: FD5
    push_retry_support.py: FD5
    remote_outage_support.py: FD5
    scripted_tick_support.py: FD5
    shipped_agents.py: FD5
    stage_run_support.py: FD5
    stall_support.py: FD5
    take_support.py: FD5
    template_make_support.py: FD5
    tick_support.py: FD5
    torn_record_support.py: FD5
    undo_support.py: FD5
    watch_support.py: FD5
    wiring_support.py: FD5
    work_item_support.py: FD5
    write_path_support.py: FD5
    test_claim_ownership.py: FD5
    test_claude_files.py: FD5
    test_fault_paths_table.py: FD5
    test_model_configuration.py: FD5
    test_no_journal_reading.py: FD5
    test_one_stage_environment.py: FD5
    test_shared_branch_helpers.py: FD5
    test_shared_definition.py: FD5
    test_shared_imports.py: FD5
    test_suite_fixtures.py: FD5
    test_template_makefile.py: FD5
    test_template_sync.py: FD5
    test_time_limits.py: FD5
    domain/test_contract_login.py -> test_contract_login.py: FD5
    domain/test_contract_provider_limit.py -> test_contract_provider_limit.py: FD5
    adapters/test_opencode_limit_wait_on_stderr.py -> test_opencode_limit_wait_on_stderr.py: FD5
    adapters/test_opencode_resume_session.py -> test_opencode_resume_session.py: FD5
    adapters/test_opencode_runtime_transcript.py -> test_opencode_runtime_transcript.py: FD5
    adapters/test_pipeline_stage_moves.py -> test_pipeline_stage_moves.py: FD5
    shared/domain/test_duplicates.py: FD5
    domain/test_settings_model_rules.py -> shared/domain/test_settings_model_rules.py: FD5
    application/test_acceptance_reviewer_role.py -> shared/application/test_acceptance_reviewer_role.py: FD5
    application/test_acceptance_ticks_closed.py -> shared/application/test_acceptance_ticks_closed.py: FD5
    application/test_push_retry.py -> shared/application/test_push_retry.py: FD5
    agents/adapters/test_calls_as_the_factory_user.py: FD5
    agents/adapters/test_claude_runtime.py: FD5
    agents/adapters/test_claude_runtime_api_login.py: FD5
    agents/adapters/test_claude_runtime_denial_paths.py: FD5
    agents/adapters/test_claude_runtime_environment.py: FD5
    agents/adapters/test_claude_runtime_login.py: FD5
    agents/adapters/test_claude_runtime_no_hook.py: FD5
    agents/adapters/test_claude_runtime_provider_limit.py: FD5
    agents/adapters/test_claude_runtime_resume.py: FD5
    agents/adapters/test_claude_runtime_resume_session.py: FD5
    agents/adapters/test_opencode_budget.py: FD5
    agents/adapters/test_opencode_left_out_tools.py: FD5
    agents/adapters/test_opencode_measures.py: FD5
    agents/adapters/test_opencode_provider_limit.py: FD5
    agents/adapters/test_opencode_resumed_words.py: FD5
    agents/adapters/test_opencode_runtime.py: FD5
    agents/adapters/test_opencode_runtime_launch.py: FD5
    agents/adapters/test_opencode_runtime_provider.py: FD5
    agents/adapters/test_opencode_runtime_runs_folder.py: FD5
    agents/adapters/test_runtime_died_text.py: FD5
    agents/adapters/test_runtime_state_directory_write.py: FD5
    agents/adapters/test_shipped_agents_effect.py: FD5
    application/test_after_agent_edges.py -> agents/application/test_after_agent_edges.py: FD5
    application/test_agent_definition_reader.py -> agents/application/test_agent_definition_reader.py: FD5
    application/test_agent_run_probe.py -> agents/application/test_agent_run_probe.py: FD5
    application/test_agent_run_probe_api_login.py -> agents/application/test_agent_run_probe_api_login.py: FD5
    application/test_agent_run_probe_factory_user.py -> agents/application/test_agent_run_probe_factory_user.py: FD5
    application/test_agent_run_probe_login.py -> agents/application/test_agent_run_probe_login.py: FD5
    application/test_agent_run_probe_opencode.py -> agents/application/test_agent_run_probe_opencode.py: FD5
    application/test_agent_run_probe_project_agent.py -> agents/application/test_agent_run_probe_project_agent.py: FD5
    application/test_patient_runs.py -> agents/application/test_patient_runs.py: FD5
    application/test_preflight.py -> agents/application/test_preflight.py: FD5
    application/test_project_agents.py -> agents/application/test_project_agents.py: FD5
    application/test_sealed_runs_runner.py -> agents/application/test_sealed_runs_runner.py: FD5
    application/test_write_paths_guard.py -> agents/application/test_write_paths_guard.py: FD5
    application/test_board_reader_acceptance.py -> entry/test_board_reader_acceptance.py: FD5
    adapters/test_runtimes_without_wrapper.py -> entry/test_runtimes_without_wrapper.py: FD5
    application/test_tick_agent_definition.py -> entry/test_tick_agent_definition.py: FD5
    application/test_tick_project_agent.py -> entry/test_tick_project_agent.py: FD5
    application/test_watcher_main_ref.py -> entry/test_watcher_main_ref.py: FD5
    entry/test_entry_arguments.py: FD5
    entry/test_health.py: FD5
    entry/test_health_missing.py: FD5
    entry/test_run.py: FD5
    entry/test_run_fetch_before_tick.py: FD5
    entry/test_run_health_file.py: FD5
    entry/test_run_idle_exit.py: FD5
    entry/test_run_idle_shutdown.py: FD5
    entry/test_run_image_sizes.py: FD5
    entry/test_run_machine_stop_exit.py: FD5
    entry/test_run_one_fetch.py: FD5
    entry/test_run_project_image_rebuild.py: FD5
    entry/test_run_stop_requested.py: FD5
    entry/test_watch.py: FD5
    entry/test_watch_acceptance.py: FD5
    entry/test_watch_agent_definition.py: FD5
    entry/test_watch_main.py: FD5
    entry/test_watch_own_claim.py: FD5
    entry/test_watch_settings.py: FD5
    entry/test_wiring.py: FD5 (guard)
    entry/test_wiring_acceptance.py: FD5
    entry/test_wiring_api_login.py: FD5
    entry/test_wiring_boundaries.py: FD5
    entry/test_wiring_constants.py: FD5
    entry/test_wiring_container_extra.py: FD5
    entry/test_wiring_container_extras.py: FD5
    entry/test_wiring_copy_snapshots.py: FD5
    entry/test_wiring_environment.py: FD5
    entry/test_wiring_extras.py: FD5
    entry/test_wiring_handlers.py: FD5
    entry/test_wiring_human_handlers.py: FD5
    entry/test_wiring_idle_shutdown.py: FD5
    entry/test_wiring_idle_shutdown_action.py: FD5
    entry/test_wiring_image_path.py: FD5
    entry/test_wiring_known_results.py: FD5
    entry/test_wiring_login.py: FD5
    entry/test_wiring_metadata_block.py: FD5
    entry/test_wiring_one_preflight.py: FD5
    entry/test_wiring_opencode.py: FD5
    entry/test_wiring_opencode_provider.py: FD5
    entry/test_wiring_preflight.py: FD5
    entry/test_wiring_project_image.py: FD5
    entry/test_wiring_provider_limit.py: FD5
    entry/test_wiring_record_logs.py: FD5
    entry/test_wiring_recovery.py: FD5
    entry/test_wiring_recovery_expired.py: FD5
    entry/test_wiring_run.py: FD5
    entry/test_wiring_stage_environment.py: FD5
    entry/test_wiring_stage_image_sizes.py: FD5
    entry/test_wiring_stop_records.py: FD5
    entry/test_wiring_without_agent_user.py: FD5
    hosting/adapters/test_pygithub_hosting.py: FD5
    application/test_agent_run_probe_environment.py -> hosting/application/test_agent_run_probe_environment.py: FD5
    application/test_checkout_preparer.py -> hosting/application/test_checkout_preparer.py: FD5
    application/test_costs.py -> hosting/application/test_costs.py: FD5
    application/test_hosting_failure_releases_claim.py -> hosting/application/test_hosting_failure_releases_claim.py: FD5
    application/test_opening.py -> hosting/application/test_opening.py: FD5
    application/test_preflight_stale_main_stop.py -> hosting/application/test_preflight_stale_main_stop.py: FD5
    application/test_recording_project_commands.py -> hosting/application/test_recording_project_commands.py: FD5
    application/test_watcher.py -> hosting/application/test_watcher.py: FD5
    domain/test_times.py -> hosting/domain/test_times.py: FD5
    machine/adapters/test_agent_launch_container.py: FD5
    machine/adapters/test_agent_launch_extra.py: FD5
    machine/adapters/test_claude_runtime_container.py: FD5
    adapters/test_make_commands.py -> machine/adapters/test_make_commands.py: FD5
    adapters/test_make_commands_container.py -> machine/adapters/test_make_commands_container.py: FD5
    machine/adapters/test_opencode_runtime_container.py: FD5
    machine/adapters/test_opencode_runtime_lockdown.py: FD5
    machine/adapters/test_runtime_podman_timeout_status.py: FD5
    application/test_acceptance_facts_disk.py -> machine/application/test_acceptance_facts_disk.py: FD5
    application/test_container_environment.py -> machine/application/test_container_environment.py: FD5
    application/test_disk_recorder.py -> machine/application/test_disk_recorder.py: FD5
    application/test_machine_checks_container.py -> machine/application/test_machine_checks_container.py: FD5
    application/test_preflight_login_line.py -> machine/application/test_preflight_login_line.py: FD5
    application/test_preflight_metadata_block.py -> machine/application/test_preflight_metadata_block.py: FD5
    application/test_preflight_run.py -> machine/application/test_preflight_run.py: FD5
    application/test_preflight_run_environment.py -> machine/application/test_preflight_run_environment.py: FD5
    adapters/test_make_last_line_shared.py -> pipeline/adapters/test_make_last_line_shared.py: FD5
    adapters/test_pipeline_rules.py -> pipeline/adapters/test_pipeline_rules.py: FD5
    adapters/test_pipeline_strict_values.py -> pipeline/adapters/test_pipeline_strict_values.py: FD5
    adapters/test_pipeline_yaml.py -> pipeline/adapters/test_pipeline_yaml.py: FD5
    adapters/test_pipeline_yaml_one_line_fault.py -> pipeline/adapters/test_pipeline_yaml_one_line_fault.py: FD5
    adapters/test_record_log_jsonl.py -> pipeline/adapters/test_record_log_jsonl.py: FD5
    adapters/test_record_log_jsonl_torn.py -> pipeline/adapters/test_record_log_jsonl_torn.py: FD5
    application/handlers/conftest.py -> pipeline/application/handlers/conftest.py: FD5
    application/handlers/test_closed.py -> pipeline/application/handlers/test_closed.py: FD5
    application/handlers/test_closed_send_back.py -> pipeline/application/handlers/test_closed_send_back.py: FD5
    application/handlers/test_comment_handler.py -> pipeline/application/handlers/test_comment_handler.py: FD5
    application/handlers/test_comments.py -> pipeline/application/handlers/test_comments.py: FD5
    application/handlers/test_comments_crash_cap.py -> pipeline/application/handlers/test_comments_crash_cap.py: FD5
    application/handlers/test_hand_over.py -> pipeline/application/handlers/test_hand_over.py: FD5
    application/handlers/test_handler_subjects.py -> pipeline/application/handlers/test_handler_subjects.py: FD5
    application/handlers/test_handlers_raise.py -> pipeline/application/handlers/test_handlers_raise.py: FD5
    application/handlers/test_lookups.py -> pipeline/application/handlers/test_lookups.py: FD5
    application/handlers/test_merged.py -> pipeline/application/handlers/test_merged.py: FD5
    application/handlers/test_questions.py -> pipeline/application/handlers/test_questions.py: FD5
    application/handlers/test_recording.py -> pipeline/application/handlers/test_recording.py: FD5
    application/handlers/test_reject.py -> pipeline/application/handlers/test_reject.py: FD5
    application/handlers/test_run.py -> pipeline/application/handlers/test_run.py: FD5
    application/handlers/test_run_gate.py -> pipeline/application/handlers/test_run_gate.py: FD5
    application/test_acceptance_due_handler.py -> pipeline/application/test_acceptance_due_handler.py: FD5
    application/test_acceptance_hand_over.py -> pipeline/application/test_acceptance_hand_over.py: FD5
    application/test_acceptance_merged.py -> pipeline/application/test_acceptance_merged.py: FD5
    application/test_acceptance_no_state_refusals.py -> pipeline/application/test_acceptance_no_state_refusals.py: FD5
    application/test_after_agent.py -> pipeline/application/test_after_agent.py: FD5
    application/test_boundaries.py -> pipeline/application/test_boundaries.py: FD5
    application/test_boundaries_required.py -> pipeline/application/test_boundaries_required.py: FD5
    application/test_boundaries_settings.py -> pipeline/application/test_boundaries_settings.py: FD5
    application/test_claims.py -> pipeline/application/test_claims.py: FD5
    application/test_claims_observed.py -> pipeline/application/test_claims_observed.py: FD5
    application/test_claims_refusals.py -> pipeline/application/test_claims_refusals.py: FD5
    application/test_container_environment_take.py -> pipeline/application/test_container_environment_take.py: FD5
    application/test_container_stage_checks.py -> pipeline/application/test_container_stage_checks.py: FD5
    application/test_container_sync_origin.py -> pipeline/application/test_container_sync_origin.py: FD5
    application/test_cost_image.py -> pipeline/application/test_cost_image.py: FD5
    application/test_cost_instance.py -> pipeline/application/test_cost_instance.py: FD5
    application/test_dispatcher.py -> pipeline/application/test_dispatcher.py: FD5
    application/test_dispatcher_counts_every_error.py -> pipeline/application/test_dispatcher_counts_every_error.py: FD5
    application/test_dispatcher_error_lines.py -> pipeline/application/test_dispatcher_error_lines.py: FD5
    application/test_dispatcher_without_state.py -> pipeline/application/test_dispatcher_without_state.py: FD5
    application/test_human_line_posts.py -> pipeline/application/test_human_line_posts.py: FD5
    application/test_idle_shutdown.py -> pipeline/application/test_idle_shutdown.py: FD5
    application/test_known_results.py -> pipeline/application/test_known_results.py: FD5
    application/test_known_results_torn.py -> pipeline/application/test_known_results_torn.py: FD5
    application/test_left_out_stage.py -> pipeline/application/test_left_out_stage.py: FD5
    application/test_machine_checks_runtime.py -> pipeline/application/test_machine_checks_runtime.py: FD5
    application/test_no_branch_check.py -> pipeline/application/test_no_branch_check.py: FD5
    application/test_no_state_refusals.py -> pipeline/application/test_no_state_refusals.py: FD5
    application/test_opencode_item.py -> pipeline/application/test_opencode_item.py: FD5
    application/test_opening_journal_edges.py -> pipeline/application/test_opening_journal_edges.py: FD5
    application/test_pipeline_definition_reader.py -> pipeline/application/test_pipeline_definition_reader.py: FD5
    application/test_pipeline_loading.py -> pipeline/application/test_pipeline_loading.py: FD5
    application/test_pipeline_loading_agents.py -> pipeline/application/test_pipeline_loading_agents.py: FD5
    application/test_pipeline_loading_project_agents.py -> pipeline/application/test_pipeline_loading_project_agents.py: FD5
    application/test_pipeline_loading_rules.py -> pipeline/application/test_pipeline_loading_rules.py: FD5
    application/test_pipeline_loading_stage_moves.py -> pipeline/application/test_pipeline_loading_stage_moves.py: FD5
    application/test_pipeline_loading_strict_values.py -> pipeline/application/test_pipeline_loading_strict_values.py: FD5
    application/test_pipeline_loading_yaml_fault.py -> pipeline/application/test_pipeline_loading_yaml_fault.py: FD5
    application/test_preflight_stop_detail.py -> pipeline/application/test_preflight_stop_detail.py: FD5
    application/test_preflight_stops_commit.py -> pipeline/application/test_preflight_stops_commit.py: FD5
    application/test_probe_nested_repository.py -> pipeline/application/test_probe_nested_repository.py: FD5
    application/test_question_causes_recorded.py -> pipeline/application/test_question_causes_recorded.py: FD5
    application/test_recovery_cap.py -> pipeline/application/test_recovery_cap.py: FD5
    application/test_recovery_crash.py -> pipeline/application/test_recovery_crash.py: FD5
    application/test_recovery_expiry.py -> pipeline/application/test_recovery_expiry.py: FD5
    application/test_recovery_expiry_key.py -> pipeline/application/test_recovery_expiry_key.py: FD5
    application/test_recovery_subjects.py -> pipeline/application/test_recovery_subjects.py: FD5
    application/test_repository_waiter.py -> pipeline/application/test_repository_waiter.py: FD5
    application/test_request_working_directory.py -> pipeline/application/test_request_working_directory.py: FD5
    application/test_scheduler.py -> pipeline/application/test_scheduler.py: FD5
    application/test_split_by_work_item_kind.py -> pipeline/application/test_split_by_work_item_kind.py: FD5
    application/test_stage_changes.py -> pipeline/application/test_stage_changes.py: FD5
    application/test_stage_died_line.py -> pipeline/application/test_stage_died_line.py: FD5
    application/test_stage_environment_calls.py -> pipeline/application/test_stage_environment_calls.py: FD5
    application/test_stage_environment_of.py -> pipeline/application/test_stage_environment_of.py: FD5
    application/test_stage_finish.py -> pipeline/application/test_stage_finish.py: FD5
    application/test_stage_finish_causes.py -> pipeline/application/test_stage_finish_causes.py: FD5
    application/test_stage_known_results.py -> pipeline/application/test_stage_known_results.py: FD5
    application/test_stage_launch.py -> pipeline/application/test_stage_launch.py: FD5
    application/test_stage_nested_repository.py -> pipeline/application/test_stage_nested_repository.py: FD5
    application/test_stage_on_container_fakes.py -> pipeline/application/test_stage_on_container_fakes.py: FD5
    application/test_stage_provider_limit.py -> pipeline/application/test_stage_provider_limit.py: FD5
    application/test_stage_run.py -> pipeline/application/test_stage_run.py: FD5
    application/test_stage_run_acceptance.py -> pipeline/application/test_stage_run_acceptance.py: FD5
    application/test_stage_time_limited_report.py -> pipeline/application/test_stage_time_limited_report.py: FD5
    application/test_stage_tool_uses.py -> pipeline/application/test_stage_tool_uses.py: FD5
    application/test_stage_transcripts.py -> pipeline/application/test_stage_transcripts.py: FD5
    application/test_stale_branches.py -> pipeline/application/test_stale_branches.py: FD5
    application/test_stall_container.py -> pipeline/application/test_stall_container.py: FD5
    application/test_stall_edges.py -> pipeline/application/test_stall_edges.py: FD5
    application/test_stall_environment.py -> pipeline/application/test_stall_environment.py: FD5
    application/test_stall_labels.py -> pipeline/application/test_stall_labels.py: FD5
    application/test_stall_reasons_recorded.py -> pipeline/application/test_stall_reasons_recorded.py: FD5
    application/test_stalls.py -> pipeline/application/test_stalls.py: FD5
    application/test_stop_log_once.py -> pipeline/application/test_stop_log_once.py: FD5
    application/test_stop_posting.py -> pipeline/application/test_stop_posting.py: FD5
    application/test_stop_publisher.py -> pipeline/application/test_stop_publisher.py: FD5
    application/test_stop_records_service.py -> pipeline/application/test_stop_records_service.py: FD5
    application/test_stops.py -> pipeline/application/test_stops.py: FD5
    application/test_take.py -> pipeline/application/test_take.py: FD5
    application/test_take_edges.py -> pipeline/application/test_take_edges.py: FD5
    application/test_take_rule.py -> pipeline/application/test_take_rule.py: FD5
    application/test_task.py -> pipeline/application/test_task.py: FD5
    application/test_task_acceptance.py -> pipeline/application/test_task_acceptance.py: FD5
    application/test_tick_disk.py -> pipeline/application/test_tick_disk.py: FD5
    application/test_tick_docstrings.py -> pipeline/application/test_tick_docstrings.py: FD5
    application/test_tick_own_fetch.py -> pipeline/application/test_tick_own_fetch.py: FD5
    application/test_tick_preflight.py -> pipeline/application/test_tick_preflight.py: FD5
    application/test_tick_restore_ignored.py -> pipeline/application/test_tick_restore_ignored.py: FD5
    application/test_tick_stale_branch.py -> pipeline/application/test_tick_stale_branch.py: FD5
    application/test_tick_stop_details.py -> pipeline/application/test_tick_stop_details.py: FD5
    application/test_tick_stop_records.py -> pipeline/application/test_tick_stop_records.py: FD5
    application/test_watcher_acceptance.py -> pipeline/application/test_watcher_acceptance.py: FD5
    application/test_watcher_observer.py -> pipeline/application/test_watcher_observer.py: FD5
    application/test_write_paths.py -> pipeline/application/test_write_paths.py: FD5
    domain/test_checks.py -> pipeline/domain/test_checks.py: FD5
    domain/test_checks_last_line.py -> pipeline/domain/test_checks_last_line.py: FD5
    domain/test_command_ending.py -> pipeline/domain/test_command_ending.py: FD5
    domain/test_command_line.py -> pipeline/domain/test_command_line.py: FD5
    domain/test_command_line_time_limit.py -> pipeline/domain/test_command_line_time_limit.py: FD5
    domain/test_contract.py -> pipeline/domain/test_contract.py: FD5
    domain/test_documents.py -> pipeline/domain/test_documents.py: FD5
    domain/test_evaluation.py -> pipeline/domain/test_evaluation.py: FD5
    domain/test_evaluation_details.py -> pipeline/domain/test_evaluation_details.py: FD5
    domain/test_evaluation_due.py -> pipeline/domain/test_evaluation_due.py: FD5
    domain/test_evaluation_reject.py -> pipeline/domain/test_evaluation_reject.py: FD5
    domain/test_events.py -> pipeline/domain/test_events.py: FD5
    domain/test_fault_paths.py -> pipeline/domain/test_fault_paths.py: FD5
    domain/test_fault_paths_all_rows.py -> pipeline/domain/test_fault_paths_all_rows.py: FD5
    domain/test_known_results.py -> pipeline/domain/test_known_results.py: FD5
    domain/test_lease.py -> pipeline/domain/test_lease.py: FD5
    domain/test_lease_observed.py -> pipeline/domain/test_lease_observed.py: FD5
    domain/test_move_rule.py -> pipeline/domain/test_move_rule.py: FD5
    domain/test_pipeline_definition.py -> pipeline/domain/test_pipeline_definition.py: FD5
    domain/test_pipeline_not_read.py -> pipeline/domain/test_pipeline_not_read.py: FD5
    domain/test_recovery.py -> pipeline/domain/test_recovery.py: FD5
    domain/test_recovery_cap.py -> pipeline/domain/test_recovery_cap.py: FD5
    domain/test_recovery_expiry_text.py -> pipeline/domain/test_recovery_expiry_text.py: FD5
    domain/test_stop_records.py -> pipeline/domain/test_stop_records.py: FD5
    domain/test_stop_table.py -> pipeline/domain/test_stop_table.py: FD5
    domain/test_stops.py -> pipeline/domain/test_stops.py: FD5
    domain/test_target_times.py -> pipeline/domain/test_target_times.py: FD5
    domain/test_tick_status.py -> pipeline/domain/test_tick_status.py: FD5
    domain/test_tick_status_mark.py -> pipeline/domain/test_tick_status_mark.py: FD5
    domain/test_work_item_stop.py -> pipeline/domain/test_work_item_stop.py: FD5
    adapters/test_health_file.py -> watching/adapters/test_health_file.py: FD5
    adapters/test_opencode_events.py -> watching/adapters/test_opencode_events.py: FD5
    watching/adapters/test_runtime_tool_uses.py: FD5
    application/test_board_in_progress.py -> watching/application/test_board_in_progress.py: FD5
    application/test_cost_record_machine_measures.py -> watching/application/test_cost_record_machine_measures.py: FD5
    application/test_costs_denials.py -> watching/application/test_costs_denials.py: FD5
    application/test_costs_died_text.py -> watching/application/test_costs_died_text.py: FD5
    application/test_costs_login.py -> watching/application/test_costs_login.py: FD5
    application/test_costs_model_seconds.py -> watching/application/test_costs_model_seconds.py: FD5
    application/test_costs_provider_limit.py -> watching/application/test_costs_provider_limit.py: FD5
    application/test_acceptance_closed.py -> work/application/test_acceptance_closed.py: FD5
    application/test_acceptance_facts_human.py -> work/application/test_acceptance_facts_human.py: FD5
    application/test_acceptance_merged_before_approval.py -> work/application/test_acceptance_merged_before_approval.py: FD5
    application/test_acceptance_reading.py -> work/application/test_acceptance_reading.py: FD5
    application/test_acceptance_refusals.py -> work/application/test_acceptance_refusals.py: FD5
    application/test_acceptance_repeated.py -> work/application/test_acceptance_repeated.py: FD5
    application/test_acceptance_service.py -> work/application/test_acceptance_service.py: FD5
    application/test_acceptance_snapshots.py -> work/application/test_acceptance_snapshots.py: FD5
    application/test_board_reader.py -> work/application/test_board_reader.py: FD5
    application/test_watcher_move_rule.py -> work/application/test_watcher_move_rule.py: FD5
    application/test_work_items.py -> work/application/test_work_items.py: FD5
    application/test_work_items_duplicate.py -> work/application/test_work_items_duplicate.py: FD5
    domain/test_acceptance_before_approval.py -> work/domain/test_acceptance_before_approval.py: FD5
    domain/test_decide_docs_slip.py -> work/domain/test_decide_docs_slip.py: FD5
    domain/test_decision_rules.py -> work/domain/test_decision_rules.py: FD5
    domain/test_send_back.py -> work/domain/test_send_back.py: FD5
17. 2026-11-05 human: Answer of the human:

    **(a)**, with your wording. Extend criterion 7: every place in `README.md`, `docs/operator-guide.md` or `docs/project-guide/` that names `factory.domain`, `factory.application` or `factory.adapters` as a package names the area package or layer that holds it now. For the `make mutants` examples, use an existing area package, for example `MODULES='factory.machine.domain.disk factory.pipeline.application'`. Then pass the story to `docs`.

    The baseline lines and the mutmut deselect are mine; they follow after the merge.
18. factory: started review as vm.
19. reviewer: Review rerun, round 0, after the human's answer in entry 17.

    Work item change (the human's answer (a), entry 17): I extended criterion 7 with: "Every place in `README.md`, `docs/operator-guide.md` or `docs/project-guide/` that names `factory.domain`, `factory.application` or `factory.adapters` as a package names the area package or layer that holds it now; the `make mutants` examples use an existing area package, for example `MODULES='factory.machine.domain.disk factory.pipeline.application'`." Nothing else in the work item changed. For the documenter: a grep finds these old paths in docs/operator-guide.md:148 and :1701 and many lines of docs/project-guide/stages.md and watching.md (plus the lines named in entry 16: processes-and-checks.md:120 and :174, watching.md:274, work-items.md:190).

    No findings.

    I checked again myself rather than relying on entry 16, on the head after the merge of `main`:
    - Group 1: criteria 1 to 3 are tests/test_areas.py, with `AREAS["pipeline"]` holding exactly the 27 modules of the table. Criteria 4 and 5 are tests/test_old_layer_packages_removed.py: one parametrized row per layer, plus the exact listing of `src/factory`. Each test checks its criterion. The coder's `make check` was green (entry 14).
    - Group 2: the src/ diff is the 27 modules (handlers with its `__init__.py`) moved, the four new `__init__.py` files with exactly the Interface's docstrings, the three old layer `__init__.py` files deleted, and import lines rewritten in 37 other modules. Filtering out import lines leaves no other changed src/ line. `src/factory/` holds exactly `__init__.py`, the seven areas, `entry`, `contract`. No src/ file names an old layer path.
    - Group 3: no new marker. `shared/domain/contract.py` changes only its import lines, so no contract model changes and no schema needs to be regenerated.
    - Group 4: `module_exists` in tests/module_names.py is one shared helper, not a copy. The `make duplicates` new entries are the old baseline entries under their new paths (entry 16). The stale baseline lines and the mutmut deselect belong to the human (entry 17).
    - Group 5: the Description matches what was built (it was corrected in entry 16). Criterion 7 is now extended as above.

    Earlier tests (paths under tests/; FD5 = feature decision 5's leave: import lines and module paths of moved modules rewritten, a test module moved with `git mv`, a test package created, or a guard of the old layout changed). This is 377 entries, the same set as entry 16. I re-read every non-import changed line. The only changes beyond import and path rewrites are the three that entry 8 allows, plus the parents depth fixes and the path constants.
    module_names.py: human's leave, entry 8 (`module_exists` added)
    test_checkout_hygiene_removed.py: human's leave, entry 8
    test_docker_path_removed.py: human's leave, entry 8
    test_home_reset_removed.py: human's leave, entry 8
    test_hook_removed.py: human's leave, entry 8
    test_kernel_guard_removed.py: human's leave, entry 8, plus FD5
    test_leftovers_program_removed.py: human's leave, entry 8
    test_undo_removed.py: human's leave, entry 8, plus FD5 (module path of take)
    entry/test_mutation_report_removed.py: human's leave, entry 8
    application/test_tick.py -> pipeline/application/test_tick.py: FD5 (move), human's leave, entry 8 (`pipeline/` prefix)
    test_areas.py: the story's Interface (`AREAS` row), human's leave, entry 8 (bare `import factory`)
    adapters/claude_stand_in.py -> claude_stand_in.py: standing leave to move a shared test helper
    adapters/container_runtime_support.py -> container_runtime_support.py: standing leave to move a shared test helper
    adapters/opencode_stand_in.py -> opencode_stand_in.py: standing leave to move a shared test helper
    adapters/pygithub_stand_ins.py -> pygithub_stand_ins.py: standing leave to move a shared test helper
    adapters/__init__.py, application/__init__.py, application/handlers/__init__.py, domain/__init__.py -> the pipeline test package `__init__.py` files: FD5
    test_layers.py: FD5 (guard)
    domain/test_hosting.py -> hosting/domain/test_hosting.py: FD5 (guard)
    test_agent_run_request_search.py: FD5 (guard)
    entry/test_wiring.py: FD5 (guard)
    shared/domain/test_duplicates.py: FD5 (module path inside its sample text)
    test_stop_table.py, test_opencode_shared_steps.py, test_suite_held_once.py, test_suite_leftovers.py, test_suite_old_names.py, test_make_search.py: FD5 (paths)
    application/test_interfaces.py -> machine/application/test_interfaces.py: FD5 (depth)
    adapters/test_pipeline_yaml_tool_paths.py -> pipeline/adapters/test_pipeline_yaml_tool_paths.py: FD5 (depth)
    The support modules, one line each: FD5 (imports only): acceptance_walk.py, branch_reading.py, claude_resume_support.py, conftest.py, container_extra_support.py, container_support.py, cost_image_support.py, crash_support.py, definition_support.py, document_texts.py, evaluation_support.py, git_support.py, known_results_support.py, power_support.py, preflight_support.py, project_command_support.py, proof_support.py, push_retry_support.py, remote_outage_support.py, scripted_tick_support.py, shipped_agents.py, stage_run_support.py, stall_support.py, take_support.py, template_make_support.py, tick_support.py, torn_record_support.py, undo_support.py, watch_support.py, wiring_support.py, work_item_support.py, write_path_support.py
    Root test modules: FD5 (imports only): test_claim_ownership.py, test_claude_files.py, test_fault_paths_table.py, test_model_configuration.py, test_no_journal_reading.py, test_one_stage_environment.py, test_shared_branch_helpers.py, test_shared_definition.py, test_shared_imports.py, test_suite_fixtures.py, test_template_makefile.py, test_template_sync.py, test_time_limits.py
    Modified in place under an area folder or entry/: FD5 (imports only): every agents/adapters/test_*.py, entry/test_*.py, hosting/adapters/test_pygithub_hosting.py, machine/adapters/test_*.py and watching/adapters/test_runtime_tool_uses.py that the diff modifies (the M list of `git diff -M --name-status main...HEAD -- tests`)
    Moved from tests/{domain,application,adapters}/ with `git mv` to tests/pipeline/, agents/, hosting/, machine/, watching/, work/, shared/, entry/ or the tests/ root, as entry 16 lists them by name: FD5 (move plus import rewrite)
20. factory: started docs as vm.
21. documenter: Documents only; no code, tests or comments changed. `make documents` passes ("documents ok"). I did not run `make check`, since only documents changed.

    Files changed:
    - `docs/project-guide/README.md`: the layout section now says `src/factory/` holds the seven areas, `entry` and `contract`, and each area has three layers. A new sentence names the area `pipeline` and what it holds. The module paths in the file index are rewritten. The handlers' conftest path is now under `tests/pipeline/application/handlers/`. Test paths are updated.
    - `docs/project-guide/stages.md`, `watching.md`, `stage-environment.md`, `processes-and-checks.md`, `costs.md`, `write-paths.md`, `work-items.md`, `agents.md`, `git-and-hosting.md`: module paths of the 27 moved modules rewritten to `factory.pipeline.<layer>.<name>`, handlers submodules included. Test-file paths rewritten from the old `tests/{domain,application,adapters}/` to where `git` moved each file in this branch, including the stand-in support modules, which are now at the `tests/` root.
    - `docs/project-guide/processes-and-checks.md`: the `make mutants` example uses `factory.pipeline.application`. The baseline sentence about fakes now names each fake's real module in place of `factory.adapters`.
    - `docs/project-guide/work-items.md`: "in `factory.adapters`… in `factory.application`" now says "the `adapters` layer of its area… the `application` layer", and the check_story sentence says "an `adapters` layer".
    - `docs/project-guide/watching.md`: `run_agent` lives in `factory.machine.application`, so that is what the sentence now says.
    - `docs/operator-guide.md`: `make mutants MODULES=factory.pipeline.application`, and `STOP_TABLE` is located in `factory.pipeline.domain.stop_table`.

    Cross-read and found current: `README.md` (no moved path or old layer package named), the rest of the operator guide, and `operator.md`.

    Stale text I left alone:
    - `docs/project-guide/write-paths.md` lines 71 and 73 name `factory.adapters.landlock` and `factory.domain.leftovers`. These are in the "Replaced in v1.2" list as modules that were removed long ago, so the old names are history.
    - `docs/decisions.md` keeps the old paths, as criterion 7 says.

    No findings for the coder. I set aside no skill. `make check` and `pyproject.toml` (the layers contract and the mutmut deselect) are the coder's open items from journal entry 7, not documentation.

    `check`: check: green (not run again: passed on tree 4b9a4e02e3e2 at 2026-11-05T04:03:28Z)
    `secrets`: secrets: green (7.7 s)
    `documents`: documents ok
22. factory: started smoke-test as vm.
23. smoke-tester: Smoke test, round 0. I ran the three commands under `## Smoke test` from the repository root, as written and in order. All three met their `Expect:` lines.

    Command 1: `uv run python -c "import factory.pipeline.domain.checks as m; print(m.__name__)"`
    ```
    Bytecode compiled 4164 files in 51ms
    factory.pipeline.domain.checks
    ```
    Met `Expect: factory.pipeline.domain.checks`. The first line is uv's own message on stderr, not the program's output.

    Command 2: `test -e src/factory/domain/checks.py && echo still there || echo moved`
    ```
    moved
    ```
    Met `Expect: moved`.

    Command 3: `uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed`
    ```
    1
    ```
    Met `Expect: 1`. The line it counted was `759 passed in 32.60s`.

    Checking the acceptance criteria against the tree, beyond the commands:
    - Criterion 4: `tests/domain/`, `tests/application/` and `tests/adapters/` do not exist (`ls`: "No such file or directory" for each).
    - Criterion 5: `src/factory/` holds exactly `__init__.py`, `agents`, `contract`, `entry`, `hosting`, `machine`, `pipeline`, `shared` and `watching`. Importing `factory.domain`, `factory.application` or `factory.adapters` raises ImportError.
    - Criterion 7 (docs): `docs/project-guide/README.md` line 9 has the sentence on the area `pipeline`. The `make mutants` example in `docs/project-guide/processes-and-checks.md:174` is `MODULES='factory.machine.domain.disk factory.pipeline.application'`, and the one in `docs/operator-guide.md:148` uses `factory.pipeline.application`.
    - No criterion is contradicted.

    Findings: none.

    Note (not a finding): `docs/project-guide/write-paths.md:71` and `:73`, in the "Replaced in v1.2" section, still name `factory.adapters.landlock` and `factory.domain.leftovers`. Both are modules that were removed earlier (F0044) and are not in this story's table. No area holds them now, so I read these as history rather than as a package to rename under criterion 7.

    I did not run `make check`, because the factory runs it as this stage's check. I fixed nothing, as the stage requires.
