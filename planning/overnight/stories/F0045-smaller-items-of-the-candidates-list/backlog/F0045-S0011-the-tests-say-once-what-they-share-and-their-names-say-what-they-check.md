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
2. The source of the scheduler (one test reading `factory.application.scheduler` with `ast`): the class `CheckoutPreparer` assigns no attribute `_log`.
3. Each item is held once (rows of one parametrized test over the test files, read with `ast`, one row per item 1 to 7): `tests/adapters/test_runtimes_without_wrapper.py` defines neither `_claude_end` nor `_opencode_end`, and `test_no_constructor_takes_the_wrapper_or_its_folders` calls no `hasattr`; the three settings modules of item 2 assign no `CONTAINER` of their own; exactly one module under `tests/` defines `_record_get_repo`, and it is `tests/wiring_support.py`; `tests/entry/test_wiring_container_extra.py` and `tests/entry/test_wiring_stage_environment.py` define no function `_recording`, `_recording_stand_in` or `_calls`; `tests/container_extra_support.py` assigns no `CA_NAMES`; `tests/test_suite_fixtures.py` holds no string constant `"stage environment: reset"`, and `tests/application/test_stage_on_container_fakes.py` assigns no `RESET_PREFIX`; `test_no_run_registers_a_hook` carries no `pytest.mark.parametrize`.
4. The old names are gone (rows of one parametrized test over the test files' text, one row per old name): no file under `tests/` defines `test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user`, `test_the_opencode_login_hint_names_the_agent_user_or_the_factory_user`, `test_an_existing_checkout_is_kept_without_a_log_line`, `test_the_committed_schemas_list_provider_limit_at_version_1_2`, `test_the_records_contract_is_at_version_2_without_tool_paths` or `test_the_records_contract_is_at_version_3_without_nested_repository`; no file under `tests/` is named `test_checkout_preparer_seal.py`.
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
