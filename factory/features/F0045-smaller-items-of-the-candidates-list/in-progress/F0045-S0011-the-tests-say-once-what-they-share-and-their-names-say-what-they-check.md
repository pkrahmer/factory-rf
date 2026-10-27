---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 476
comments_read: [6432211115]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-27T02:24:46.700130Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-27T02:24:46.705795Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-27T02:25:10.085056Z'
  stage: intake
  run: f6030e814949414c842f2a16f9c779b2
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-27T02:26:27.870937Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-27T02:26:45.670984Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-27T02:27:17.503978Z'
  stage: intake
  run: 24c2a4c4cdef4b8da11e935dac0b948e
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-27T02:27:37.778240Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-27T02:37:30.345542Z'
  stage: tests
  run: 2ae614b8d1cc4c779b8f12f3aa2ef7e5
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-27T02:37:50.924935Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-27T02:44:11.120877Z'
  stage: doing
  run: 8234eccee72c424798e7c1f8dd039f62
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-27T02:44:31.526878Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-27T02:46:02.887766Z'
  stage: review
  run: b76a2ddfdc474a15aa3fd0bdbc1421e3
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-27T02:46:23.521350Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-27T02:46:40.869477Z'
  stage: doing
  run: ffc0882c26fd42998216456a168b6327
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-27T02:47:00.865853Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-27T02:53:03.410590Z'
  stage: tests
  run: 2758a8f71da14fa2a07e71bfd87a34d4
---

# The tests say once what they share, and their names say what they check

## Description

F0044 adapted hundreds of earlier tests story by story under leaves, and its reviewers, and F0046-S0002's, noted under `Notes:` what that left behind: helpers that are copies of others, a constant a module repeats instead of importing it, a one-row table, test names that still speak of a removed layer or of an older contract version, and in the source one parameter nothing reads, `CheckoutPreparer`'s `log` (`planning/v1.2-candidates.md`, "For F0045", the tests' tidy-up, and "From F0046-S0002's review"). This story clears that list, which decision 19 of `feature.md` fixes; it is the one story of this feature whose work is mostly the tester's. Every test keeps what it checks; where the list renames a test, it keeps its rows and its assertions. What stays: every behaviour of the factory; every shared helper that is not on the list; the guards `tests/test_shared_*.py`. The imports from test modules are S0010's (no test module imports another test module), which comes before this story.

## Interface

`factory.application.scheduler` (`application`): `CheckoutPreparer(git: Git, settings: InstanceSettings)`; the parameter `log` and the attribute it set go, and the docstring no longer names a log. `factory.entry.run.run_instance` builds it without the log. Nothing else under `src/factory/` changes.

The list (the tester changes `tests/`; the leave is decision 31 of `feature.md`):

1. `tests/adapters/test_runtimes_without_wrapper.py`: `_claude_end` and `_opencode_end` repeat the try and except that turns a run into `(detail, end_reason)`; one helper that takes the runtime serves both. In `test_no_constructor_takes_the_wrapper_or_its_folders`, the assertion `assert not hasattr(ClaudeCodeRuntime, "confine_executable")` that every row repeats becomes one row of `test_the_wrapper_s_names_are_gone`.
2. `CONTAINER`, the same three-key environment in `tests/domain/test_settings_agent_user_unread.py`, `tests/domain/test_settings_one_environment.py` and `tests/domain/test_settings_stage_environment.py`, is one constant in `tests/settings_support.py`.
3. `_record_get_repo` of `tests/entry/test_wiring_one_environment.py`, a copy of the one in `tests/entry/test_wiring_boundaries.py`, is one helper in `tests/wiring_support.py`.
4. `_recording` and `_calls` of `tests/entry/test_wiring_container_extra.py`, copies of `_recording_stand_in` and `_calls` of `tests/entry/test_wiring_stage_environment.py`, are one pair of helpers in a support module.
5. `CA_NAMES` of `tests/container_extra_support.py` repeats `factory.domain.containers.CA_BUNDLE_NAMES`; the tests use `CA_BUNDLE_NAMES`.
6. The literal `"stage environment: reset"` in `tests/test_suite_fixtures.py` and `RESET_PREFIX` of `tests/application/test_stage_on_container_fakes.py` are one shared constant.
7. `tests/adapters/test_claude_runtime_no_hook.py::test_no_run_registers_a_hook`: a parametrize with one row whose two parameters are constant becomes a plain test of the same name.
8. Names that speak of a removed layer: `tests/entry/test_wiring_extras.py::test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user` and `tests/application/test_agent_run_probe_factory_user.py::test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user` get names that say what their one row checks; the module `tests/application/test_checkout_preparer_seal.py` gets a name without `seal`.
9. `CheckoutPreparer` without `log`: the tests of `tests/application/test_checkout_preparer_seal.py` (under its new name) lose the argument `log=` and their assertions `log.lines == []`; `test_an_existing_checkout_is_kept_without_a_log_line` gets a name without the log; every other assertion stays.
10. Names that speak of an older contract version: `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2`, `tests/domain/test_contract_version_2.py::test_the_records_contract_is_at_version_2_without_tool_paths` and `tests/domain/test_contract_version_3.py::test_the_records_contract_is_at_version_3_without_nested_repository` lose the version in their names and their assertions on the version (S0004's test of `4.0` and `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` hold it), and keep what they check of the values and of the generated schemas; the modules `test_contract_version_2.py` and `test_contract_version_3.py` may get names without the version.

The tester's entry names each changed module and, for every renamed test or module, its old and its new name.

## Acceptance criteria

1. The preparer without a log (rows of one parametrized test): `"log"` is not a parameter of `inspect.signature(CheckoutPreparer.__init__)`; a `CheckoutPreparer(git, settings)` on a missing checkout clones it (`origin/main` resolves afterwards); one on a checkout that holds a `.git` keeps a file the test put in its work tree.
2. The source (rows of one parametrized test reading with `ast`): in `factory.application.scheduler` the class `CheckoutPreparer` assigns no attribute `_log`; the docstring of `CheckoutPreparer` and of its `__init__` (if any) does not contain the word `log` (case-insensitive); no call to `CheckoutPreparer` in `src/factory/entry/run.py` passes a `log` keyword.
3. Each item is held once (rows of one parametrized test over the test files, read with `ast`, one row per item 1 to 7): `tests/adapters/test_runtimes_without_wrapper.py` defines neither `_claude_end` nor `_opencode_end`, and `test_no_constructor_takes_the_wrapper_or_its_folders` calls no `hasattr`; the three settings modules of item 2 assign no `CONTAINER` of their own; exactly one module under `tests/` defines `_record_get_repo`, and it is `tests/wiring_support.py`; `tests/entry/test_wiring_container_extra.py` and `tests/entry/test_wiring_stage_environment.py` define no function `_recording`, `_recording_stand_in` or `_calls`; `tests/container_extra_support.py` assigns no `CA_NAMES`; `tests/test_suite_fixtures.py` holds no string constant `"stage environment: reset"`, and `tests/application/test_stage_on_container_fakes.py` assigns no `RESET_PREFIX`; `test_no_run_registers_a_hook` carries no `pytest.mark.parametrize`; and one more row: the shared helper of item 1, the shared helper of item 4 and the shared constant of item 6 are each defined once, in a support module under `tests/`, and the test modules that used the copies import them from there.
4. The old names are gone (rows of one parametrized test over the test files' text, one row per old name): no file under `tests/` defines `test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user`, `test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user`, `test_an_existing_checkout_is_kept_without_a_log_line`, `test_the_committed_schemas_list_provider_limit_at_version_1_2`, `test_the_records_contract_is_at_version_2_without_tool_paths` or `test_the_records_contract_is_at_version_3_without_nested_repository`; no file under `tests/` is named `test_checkout_preparer_seal.py`; and one more row: no function in `tests/domain/test_contract_provider_limit.py`, `tests/domain/test_contract_version_2.py` and `tests/domain/test_contract_version_3.py` has a name matching `version_[0-9]` or `at_version`, and none of them asserts the contract version string.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *The files* and *Shared test helpers*: the support modules and constants this story added or moved, one line each, and the renamed test modules; `docs/project-guide/watching.md`, where it describes `CheckoutPreparer`: its constructor without the log. `docs/operator-guide.md`, `docs/decisions.md`, `README.md`: none.

## Smoke test

```bash
uv run python -c 'import inspect; from factory.application.scheduler import CheckoutPreparer; print(list(inspect.signature(CheckoutPreparer.__init__).parameters))'
ls tests/application/test_checkout_preparer_seal.py 2>/dev/null || echo gone
grep -rlE 'def (test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user|test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user|test_the_committed_schemas_list_provider_limit_at_version_1_2|test_the_records_contract_is_at_version_2_without_tool_paths|test_the_records_contract_is_at_version_3_without_nested_repository)\(' tests --include='*.py' | wc -l
```
Expect: three lines: `['self', 'git', 'settings']`; `gone`; `0`

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed; the Interface, smoke test, architecture and scope otherwise read fine):

   1. The Interface says "the docstring no longer names a log" for `CheckoutPreparer`, but no criterion tests it. Two coders could read it two ways and both pass. I would add a criterion to criterion 2's `ast` test: the docstring of `CheckoutPreparer` and of its `__init__` (if any) does not contain the word `log` (case-insensitive). Or the clause could be dropped from the Interface. Which one? I would choose the added criterion.

   2. The Interface says "`factory.entry.run.run_instance` builds it without the log", with no criterion. A call that still passes `log=` would only show up at runtime. I would add it to criterion 2's `ast` test: no call to `CheckoutPreparer` in `src/factory/entry/run.py` passes a `log` keyword. Or the clause could be dropped. Which one? I would choose the added criterion.

   3. Item 10 says the three contract tests lose the version in their names and in their assertions "on the version". Criterion 4 checks only the old names. Nothing checks that the version assertions are gone, or that the new names carry no version. Please add a row, or confirm that criterion 4 together with review is enough. I would add one: no function in the three modules has a name matching `version_[0-9]` or `at_version`, and none of them asserts the contract version string. Which one?

   4. Items 8 and 10 leave the new names to the tester ("names that say what their one row checks"). Criterion 4 only shows that the old names are gone. Please confirm that this is intended, with the reviewer judging the new names. If you want fixed names, state them.

   5. Item 1 asks for one helper serving `_claude_end` and `_opencode_end`, and item 6 asks for one shared constant. Criterion 3 only checks that the old definitions are gone. It does not check that the shared helper or constant exists. Is "absent plus a green `make check`" enough, or should a row check that the helper or constant is defined once in a support module?
4. 2026-10-27 human: 1. Add it to criterion 2's `ast` test, as you propose.
   2. Add it to criterion 2's `ast` test, as you propose.
   3. Add the row: no function in the three modules has a name matching `version_[0-9]` or `at_version`, and none asserts the contract version string.
   4. Intended: the tester chooses the new names, the reviewer judges them; no fixed names.
   5. Add a row: the shared helper and the shared constant are each defined once, in a support module under `tests/`, and the test modules import them from there.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `CheckoutPreparer(git: Git, settings: InstanceSettings)` in `factory.application.scheduler` and the `run_instance` call are concrete. The list of ten items names modules, tests and constants. The docstring and `run_instance` clauses now have criteria (see below).
   - Criteria: each is testable by one parametrized test. Criterion 2 now covers `_log`, the docstring without "log", and no `log` keyword in `src/factory/entry/run.py`. Criterion 3 gains the row that the shared helpers of items 1 and 4 and the constant of item 6 are each defined once in a support module under `tests/` and imported from there. Criterion 4 gains the row for the three contract modules: no function name matching `version_[0-9]` or `at_version`, and no assertion of the version string. Both sides of the preparer rule are covered (clones when missing, keeps an existing checkout). All of this was written in from the human's answers, journal entry 4, points 1, 2, 3 and 5.
   - Smoke test: the three commands are runnable. Each `Expect:` line is checkable: the parameter list, `gone`, `0`. The block runs no pytest.
   - Architecture: the only source change is in the application layer's `CheckoutPreparer` and its wiring in `entry`, which goes the right way. The rest is under `tests/` and keeps the support-module rules of `CLAUDE.md`.
   - Scope: within feature decisions 19 and 31, which give the leave for the ten items. Journal entry 4, point 4: the tester chooses the new names and the reviewer judges them. No fixed names were added.
7. factory: started tests as vm.
8. tester: Tests written for criteria 1 to 4, and the ten items of the list carried out in `tests/` under the leave the Interface names (decision 31 of `feature.md`).

   Criterion → test:
   - criterion 1: tests/application/test_checkout_preparer.py::test_the_preparer_takes_only_the_git_and_the_settings (rows no-log-parameter, missing-is-cloned, existing-is-kept)
   - criterion 2: tests/application/test_checkout_preparer.py::test_the_preparer_s_source_holds_no_log (rows no-log-attribute, docstrings, run-instance)
   - criterion 3: tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once (one row for each of items 1 to 7, plus shared-from-support)
   - criterion 4: tests/test_suite_old_names.py::test_no_test_keeps_an_old_name_or_a_contract_version (one row for each of the six old names, plus seal-module and contract-version)
   - criteria 5 and 6: not tests (make check, docs).

   Files created: tests/test_suite_held_once.py, tests/test_suite_old_names.py, tests/recording_stand_in_support.py (`recording_stand_in`, `recorded_calls`).

   Modules changed, by item:
   1. tests/adapters/test_runtimes_without_wrapper.py: `_claude_end` and `_opencode_end` are replaced by `run_end(runtime, layout)` in tests/run_layout_support.py. Two private builders, `_claude` and `_opencode`, make the runtimes. The `hasattr(ClaudeCodeRuntime, "confine_executable")` check is now the row `claude-runtime-confine` of `test_the_wrapper_s_names_are_gone`.
   2. `CONTAINER` now lives in tests/settings_support.py. It is imported by tests/domain/test_settings_agent_user_unread.py, test_settings_one_environment.py and test_settings_stage_environment.py.
   3. `_record_get_repo` now lives in tests/wiring_support.py. It is imported by tests/entry/test_wiring_boundaries.py and test_wiring_one_environment.py.
   4. tests/entry/test_wiring_container_extra.py and test_wiring_stage_environment.py now use `recording_stand_in` and `recorded_calls` from tests/recording_stand_in_support.py. `recorded_calls` returns [] when the stand-in never ran, as the stage-environment copy did.
   5. `CA_NAMES` is removed from tests/container_extra_support.py. tests/entry/test_wiring_container_extra.py, tests/application/test_container_environment_extra.py and tests/adapters/test_agent_launch_extra.py now use `factory.domain.containers.CA_BUNDLE_NAMES`.
   6. `RESET_PREFIX = f"{TIMING_PREFIX} reset"` is now in tests/container_support.py. tests/test_suite_fixtures.py and tests/application/test_stage_on_container_fakes.py import it.
   7. tests/adapters/test_claude_runtime_no_hook.py::test_no_run_registers_a_hook is now a plain test.
   8. Renames:
      - tests/entry/test_wiring_extras.py: test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user → test_the_extras_are_the_container_items_then_the_agent_run_probe
      - tests/application/test_agent_run_probe_factory_user.py: test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user → test_the_opencode_login_hint_names_the_factory_user
      - Both keep their one row.
   9. Module renamed: tests/application/test_checkout_preparer_seal.py → tests/application/test_checkout_preparer.py. The `log=` arguments, the `RecordingLog`s and the `log.lines == []` assertions are gone. test_an_existing_checkout_is_kept_without_a_log_line → test_an_existing_checkout_is_kept_with_its_files_and_modes. Every other assertion stays. The tests of criteria 1 and 2 are in this module too.
   10. Contract tests:
      - tests/domain/test_contract_provider_limit.py: test_the_committed_schemas_list_provider_limit_at_version_1_2 → test_the_committed_schemas_list_provider_limit. It loses the `RECORDS_CONTRACT == "4.0"` and `x-records-contract` assertions.
      - tests/domain/test_contract_version_2.py → tests/domain/test_contract_without_tool_paths.py, with test_the_records_contract_is_at_version_2_without_tool_paths → test_the_committed_schemas_are_generated_and_the_pipeline_definition_has_no_tool_paths.
      - tests/domain/test_contract_version_3.py → tests/domain/test_contract_without_nested_repository.py, with test_the_records_contract_is_at_version_3_without_nested_repository → test_the_committed_schemas_are_generated_and_name_no_nested_repository.
      - Both renamed modules drop the `_version` row. Their generated-schema rows call `committed_is_generated(entry)` without a version. For that, `version` in tests/contract_support.py::committed_is_generated is now optional (`str | None = None`). S0004's test_contract_version_4.py still passes "4.0" and is unchanged.

   Interpretations the reviewer should judge:
   - Criterion 4's contract row checks the three modules at their current paths, after the renames item 10 allows.
   - In that row, "asserts the contract version string" is read as: no string literal of the form `<n>.<n>` and no name `RECORDS_CONTRACT` in the module.
   - The new test and module names are my choice, as journal entry 4, point 4 allows.

   `make test` (one run): 4 failed, the rest passed, coverage 99.57 %. The failures are the four rows that need the coder: no-log-parameter, no-log-attribute, docstrings and run-instance. They fail on assertions against the current `CheckoutPreparer(…, log=…)` and on `run.py` passing `log=`. Every module imported; nothing failed to import. Every moved helper and renamed test passed. `make lint`: green. No type check run in this stage.

   For the coder: `src/factory/application/scheduler.py` (`CheckoutPreparer` without `log`, its `_log` and the log in its docstrings) and `src/factory/entry/run.py:116` (no `log=`).

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/application/test_checkout_preparer.py::test_the_preparer_takes_only_the_git_and_the_settings[no-log-parameter] - assert 'log' not in mappingproxy(OrderedDict({'self': <Parameter "self"...
9. factory: started doing as vm.
10. coder: `CheckoutPreparer` no longer takes a log. `make check` is green (coverage 99.57 %), and the four tester rows that were failing now pass.

    What I built:
    - `src/factory/application/scheduler.py`: `CheckoutPreparer.__init__(self, git, settings)`. The `log` parameter and the `_log` attribute are gone, and the `__init__` docstring no longer mentions a log. The class docstring never did. The `FactoryLog` import stays because `Scheduler` still uses it.
    - `src/factory/entry/run.py:116`: `run_instance` builds `CheckoutPreparer(boundaries.git, settings)` without `log=`.

    Main choice: I deleted the parameter outright. The alternative was to keep it as an ignored keyword so older callers still work. I rejected that because nothing in the code passed it except `run.py`, and an ignored parameter is exactly the dead parameter this story removes.

    Refactor pass: I read the diff (two files, a few lines). Nothing needed changing.

    The journal did not change the meaning of the task after intake, so the Description stays as it is.

    Noticed but not touched: `docs/project-guide/watching.md` still describes the constructor with a log, and `docs/project-guide/README.md` needs the new support module and the renamed test modules. Both are for the docs stage under criterion 6. The tests are as the tester left them; I did not change any.

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Findings:

    1. `tests/application/test_checkout_preparer.py:301` `_keeps_without_a_log`: this is a second copy of the existing `_group_writable` (line 72) without the mode assertion, and of `test_an_existing_checkout_is_kept_with_its_files_and_modes` without the chmods. Both already clone through `_existing`, prepare, and check that the test's file is kept. Also, `test_the_preparer_takes_only_the_git_and_the_settings` runs `_missing` as row `missing-is-cloned`, the same row with the same id as in `test_the_preparer_clones_only_a_missing_checkout_and_checks_none`. So the module now checks the same thing three times: `test_a_missing_checkout_is_cloned` plus those two rows. This story exists to remove exactly that kind of repetition. Fix (tester): delete `_keeps_without_a_log` and use `_group_writable` as the `existing-is-kept` row. Better still, put criterion 1's `no-log-parameter` row into `test_the_preparer_clones_only_a_missing_checkout_and_checks_none`, which already holds `missing-is-cloned` and a kept checkout, and drop the new test. That row is added to the earlier story's test, so it needs the human's leave unless decision 31's leave for this module (item 9) is read to cover it.

    Checked and found sound: Interface `src/factory/application/scheduler.py:78` (no `log`, no `_log`, the docstrings name no log) and `src/factory/entry/run.py:116`. Criteria 2 to 4 each have one parametrized test with one row per item or old name: `tests/application/test_checkout_preparer.py::test_the_preparer_s_source_holds_no_log`, `tests/test_suite_held_once.py`, `tests/test_suite_old_names.py`. Items 1 to 10 are carried out as listed. The new names describe their one row: `test_the_extras_are_the_container_items_then_the_agent_run_probe`, `test_the_opencode_login_hint_names_the_factory_user`, `test_an_existing_checkout_is_kept_with_its_files_and_modes`, and the two contract modules renamed `without_tool_paths` and `without_nested_repository`. `committed_is_generated` now takes `version` as an optional argument, so S0004's `4.0` check stays. The coder's entry 10 says `make check` is green. I ran `make duplicates` (`2 new, 42 known, 0 gone`): both new findings are in `power_off`, `zfs_snapshots` and `podman_runs`, outside this diff. Architecture and security: no findings. `_record_get_repo` keeps its leading underscore in `tests/wiring_support.py` because criterion 3 names it that way.

    Earlier tests changed (all under the human's leave, decision 31 of `feature.md`, which the Interface names):
    - tests/adapters/test_agent_launch_extra.py: decision 31, item 5
    - tests/adapters/test_claude_runtime_no_hook.py: decision 31, item 7
    - tests/adapters/test_runtimes_without_wrapper.py: decision 31, item 1
    - tests/application/test_agent_run_probe_factory_user.py: decision 31, item 8
    - tests/application/test_checkout_preparer_seal.py -> tests/application/test_checkout_preparer.py: decision 31, items 8 and 9 (the new criterion 1 and 2 tests in it are added tests)
    - tests/application/test_container_environment_extra.py: decision 31, item 5
    - tests/application/test_stage_on_container_fakes.py: decision 31, item 6
    - tests/domain/test_contract_provider_limit.py: decision 31, item 10
    - tests/domain/test_contract_version_2.py (deleted, now tests/domain/test_contract_without_tool_paths.py): decision 31, item 10
    - tests/domain/test_contract_version_3.py (deleted, now tests/domain/test_contract_without_nested_repository.py): decision 31, item 10
    - tests/domain/test_settings_agent_user_unread.py: decision 31, item 2
    - tests/domain/test_settings_one_environment.py: decision 31, item 2
    - tests/domain/test_settings_stage_environment.py: decision 31, item 2
    - tests/entry/test_wiring_boundaries.py: decision 31, item 3
    - tests/entry/test_wiring_container_extra.py: decision 31, items 4 and 5
    - tests/entry/test_wiring_extras.py: decision 31, item 8
    - tests/entry/test_wiring_one_environment.py: decision 31, item 3
    - tests/entry/test_wiring_stage_environment.py: decision 31, item 4
    - tests/test_suite_fixtures.py: decision 31, item 6
    - support modules tests/container_extra_support.py, tests/container_support.py, tests/contract_support.py, tests/run_layout_support.py, tests/settings_support.py, tests/wiring_support.py: decision 31, the moves of items 1 to 6 and item 10's optional version
13. factory: started doing as vm.
14. coder: Round 1: the reviewer's only finding (entry 12, finding 1) is a change to tests, so I changed no code. The source the reviewer checked and found sound stays as it is: `src/factory/application/scheduler.py` (`CheckoutPreparer(git, settings)`, no `_log`, no log in its docstrings) and `src/factory/entry/run.py:116`.

    Test change for the tester: in `tests/application/test_checkout_preparer.py`, delete `_keeps_without_a_log`. The `existing-is-kept` row of `test_the_preparer_takes_only_the_git_and_the_settings` then runs `_group_writable` instead. The test keeps its three rows (`no-log-parameter`, `missing-is-cloned`, `existing-is-kept`), so criterion 1 is still one parametrized test of this story's own.

    Main choice: the reviewer offered two fixes. I chose the first, swapping `_keeps_without_a_log` for the existing helper. I rejected the second, moving the `no-log-parameter` row into `test_the_preparer_clones_only_a_missing_checkout_and_checks_none` and dropping the new test. That test belongs to an earlier story, and adding a row to it needs the human's leave (the reviewer says so too). The first fix removes the second copy of a helper without that leave.

    Noticed but not touched: the `missing-is-cloned` row still appears both in the new test and in the earlier story's test. It also overlaps `test_a_missing_checkout_is_cloned`. Criterion 1 names that row, so it stays unless the human chooses the second fix. The journal did not change the meaning of the task, so the Description stays as it is. I did not run `make check` this round because I changed nothing.
15. factory: started tests as vm.
16. tester: Round 1, test change: the one the coder named in entry 14, which is the first fix the reviewer gave for finding 1 in entry 12.

    What I changed, in tests/application/test_checkout_preparer.py only:
    - Deleted `_keeps_without_a_log`. It was a second copy of `_group_writable`, minus the mode assertion.
    - The `existing-is-kept` row of `test_the_preparer_takes_only_the_git_and_the_settings` now runs the existing `_group_writable`. That helper clones through `_existing`, prepares with `CheckoutPreparer(git, settings)` and checks that the file the test added is still there. It also checks the mode of `.git`.
    - The test keeps its name and its three rows (`no-log-parameter`, `missing-is-cloned`, `existing-is-kept`). It is still criterion 1's one parametrized test.

    Why: it removes the second copy of a helper without touching the earlier story's test. I did not take the reviewer's second fix, which moves the `no-log-parameter` row into `test_the_preparer_clones_only_a_missing_checkout_and_checks_none`: that would add a row to another story's test without the human's leave.

    Criterion → test (unchanged since entry 8):
    - criterion 1: tests/application/test_checkout_preparer.py::test_the_preparer_takes_only_the_git_and_the_settings
    - criterion 2: tests/application/test_checkout_preparer.py::test_the_preparer_s_source_holds_no_log
    - criterion 3: tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once
    - criterion 4: tests/test_suite_old_names.py::test_no_test_keeps_an_old_name_or_a_contract_version

    Files created this round: none. Every module imported.

    Still open: the `missing-is-cloned` row also exists in the earlier story's test, and it overlaps `test_a_missing_checkout_is_cloned`. Criterion 1 names that row, so it stays unless the human chooses the second fix.

    `make test` (one run): test: green (166.9 s), coverage 99.57 %. `make lint`: green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (166.6 s)
