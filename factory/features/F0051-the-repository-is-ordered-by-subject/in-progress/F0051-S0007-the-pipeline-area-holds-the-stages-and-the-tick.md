---
stage: doing
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 562
comments_read: []
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
---

# The pipeline area holds the stages and the tick

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `pipeline` area: the pipeline definition, stages, checks, events, the tick, the scheduler and dispatcher, the handlers, claims, leases, stops, stalls, recovery and `Boundaries`. Each of its 27 modules moves from its layer package to the same layer inside `factory.pipeline`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/pipeline/<layer>/` (feature decision 5). It is the last move: afterwards `src/factory/` holds only the seven areas, `entry/` and `contract/`; the old layer packages `factory.domain`, `factory.application` and `factory.adapters` are gone, and every test module still left under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to the area of the module it imports most. No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

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
7. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `pipeline` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

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
