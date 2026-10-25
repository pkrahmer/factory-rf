---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 445
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T12:27:43.087257Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T12:27:43.093855Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T12:27:59.382204Z'
  stage: intake
  run: d73a35f803884a909a94dbd615be2b97
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T12:28:19.647509Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T12:34:58.503968Z'
  stage: tests
  run: d8a3a6bff5794a9d82be2781dd205308
---

# The wrapper, the kernel's rules and the tool paths are removed

## Description

After S0001 (no agent call starts through the write guard's wrapper) the kernel's guard is code that nothing starts: the wrapper `factory-confine` (`factory.entry.confine`), the Landlock calls through ctypes (`factory.adapters.landlock`), the kernel's targets and rules (`factory.domain.confinement`), the process module's `replace_process` with its `os.execvpe` (the wrapper replaced itself with the runtime), and the input they were built from: the pipeline definition's `tool_paths`, `GuardSettings.tool_paths`, and the guard settings an agent run request and a task context carry. This story removes them. The pipeline definition's schema forbids unknown keys, so a definition that still holds `tool_paths` is refused at load from now on; the human's change 1 of `feature.md` takes the key out of `factory/pipeline.yml` and the demo's definition before this story starts, and the coder takes it out of `template/factory/pipeline.yml`. Removing a field of a contract model is a change that can break a reader, so the records contract's major version rises to 2.0 and the five schemas are generated again (decision 5 of `feature.md`); the definition's own `contract` stays `1.0`, as the decision log keeps the two apart. What stays: the write paths and their refusal rule (`refusal`, `PROTECTED_PATHS`, `WritePathService.at`, which still returns `GuardSettings` with the root, the expanded write paths and the protected paths), which the take and the undo read; the process module's one `Popen`.

## Interface

Removed whole: `src/factory/entry/confine.py`, `src/factory/adapters/landlock.py`, `src/factory/domain/confinement.py`.

`factory.adapters.process` (`adapters`): `replace_process` goes, with its `os.execvpe` call and that line's two markers.

`factory.domain.agent_runs` (`domain`): `CONFINE_COMMAND` goes; `GuardSettings` loses `tool_paths`; `AgentRunRequest` loses `guard`:

```python
class GuardSettings(BaseModel):
    root: AbsolutePath
    write_paths: list[str]
    protected_paths: list[str]
```

`factory.domain.pipeline_definition` (`domain`): `PipelineDefinition.tool_paths`, `tool_path_folder`, `HOME_PREFIX` and the rule `_tool_path_faults` go, with what only `tool_path_folder` and `factory.domain.confinement` used (`_is_plain_segment`, `_FOLDER_SUFFIX`, `has_wildcard`, `_WILDCARDS`, `CURRENT_SEGMENT`); a definition text with the key `tool_paths` is refused as an unknown key, as any other unknown key is.

`factory.domain.contract` (`domain`): `RECORDS_CONTRACT = "2.0"`; `src/factory/contract/*.schema.json` regenerated with `uv run python -m factory.entry.contract` (the pipeline definition's schema loses `tool_paths`; every file's `x-records-contract` is `2.0`).

`factory.application.write_paths.WritePathService.at` (`application`) returns `GuardSettings(root=..., write_paths=..., protected_paths=...)`; `factory.application.task`: `TaskContext.guard` goes and the request carries no guard; `factory.application.stage`: the launcher builds the context without a guard; `factory.application.preflight._probe_request`: no guard.

`template/factory/pipeline.yml`: its two lines `# What every agent run may write for the project's tools, besides its write paths.` and `tool_paths: [...]` go; the file loads as before.

Tests (the leave is decision 18 of `feature.md`):

- Deleted whole: `tests/adapters/test_landlock.py`, `tests/adapters/test_landlock_checks.py`, `tests/adapters/test_process_replace.py`, `tests/adapters/test_process_replace_faults.py`, `tests/application/test_write_paths_tool_paths.py`, `tests/domain/test_confinement_abi.py`, `tests/domain/test_confinement_model.py`, `tests/domain/test_confinement_of.py`, `tests/domain/test_tool_paths.py`, `tests/domain/test_write_targets.py`, `tests/entry/test_confine.py`, `tests/entry/test_confine_defaults.py`, `tests/entry/test_confine_steps.py`.
- `tests/test_process_search.py`: `test_no_module_uses_another_route_to_a_process` expects no module to use `os.execvpe` (`users == {}`); `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` expects the four markers on the `subprocess` import and the `Popen` line of `adapters/process.py` and the `noqa: PLR0913` of `entry/leftovers.py`, which S0003 removes (the `exec_line` and `confinement.py` entries go); both keep their names.
- `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: the set loses `factory.entry.confine`.
- `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`: the set loses `factory.entry.confine`; it keeps its name.
- `tests/domain/test_pipeline_not_read.py`: the row that adds `tool_paths: ["x"]` goes.
- `tests/application/test_stage_launch.py::test_the_runtime_receives_the_request_with_the_guard_and_the_draft_number`, `tests/application/test_task.py::test_the_request_carries_the_agent_checkout_and_guard_without_os_user` and its helpers `_guard`, `_context` and `_context_values`, the `_context` helpers of `tests/application/test_task_acceptance.py` and `tests/application/test_task_os_user.py`, `tests/application/test_no_state_refusals.py::test_composing_a_task_for_a_document_without_a_state_is_refused_with_its_path`, `tests/domain/test_agent_runs.py::test_minimal_request_has_empty_defaults_not_shared`, `tests/adapters/test_claude_runtime.py::test_call_without_effort_guard_or_tools_leaves_those_flags_out` and the module's helpers `_guard` and `_request`, the helper `_request` of `tests/adapters/test_claude_runtime_resume.py`, `tests/adapters/test_claude_runtime_file_modes.py::test_the_files_of_a_run_are_0640_when_the_agent_starts` (its helper `_request` loses `guard`, its two rows become one), `tests/application/test_agent_run_probe.py::test_the_probe_runs_the_coder_on_a_small_budget_with_the_question_alone` and `::test_the_probe_calls_claude_with_the_flags_of_a_stage` with the module's import of `GuardSettings`, `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs`: no guard in the request or the context; each keeps its name and its other assertions.
- `tests/test_hook_removed.py::test_the_guard_settings_have_no_temporary_folder` reads `GuardSettings.model_fields` (`root`, `write_paths`, `protected_paths`) and keeps its name; in `::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept` the row `confine-command` expects `None` (no `CONFINE_COMMAND`).
- `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2` read the version `2.0`; each keeps its name.
- `tests/confine_support.py` keeps `Layout`, `build_layout`, `read_records`, `write_script` and `run_request` (other modules import them; `run_request` builds no guard and loses its parameters `write_paths` and `tool_paths`) and loses everything else that names the wrapper, `GuardSettings`, `CONFINE` or `STAND_IN_TOOL_PATH`.

## Acceptance criteria

1. The removed modules (rows of one parametrized test): `importlib.util.find_spec` is `None` for `factory.entry.confine`, `factory.adapters.landlock` and `factory.domain.confinement`.
2. The removed names (rows of one parametrized test): `replace_process` is no attribute of `factory.adapters.process`; `CONFINE_COMMAND` none of `factory.domain.agent_runs`; `tool_path_folder`, `HOME_PREFIX`, `has_wildcard` and `CURRENT_SEGMENT` none of `factory.domain.pipeline_definition`; `GuardSettings.model_fields` is exactly `root`, `write_paths`, `protected_paths`; `AgentRunRequest.model_fields` holds no `guard`; `PipelineDefinition.model_fields` holds no `tool_paths`; `TaskContext.model_fields` holds no `guard`.
3. The key is refused (rows of one parametrized test through `RuamelPipelineDefinitionReader().parse`): the definition of `tests/git_support.py` (`PIPELINE_YAML`) is accepted; the same text with the line `tool_paths: [".venv/*"]` added raises `PipelineDefinitionInvalid` whose text names `tool_paths`.
4. `WritePathService.at` (one test on the `boundaries` fixture with a definition committed at the stage start): a tester's stage gives `GuardSettings(root=<checkout>, write_paths=["tests/*"], protected_paths=list(PROTECTED_PATHS))`; and the take still leaves out a changed path outside the write paths (the existing `tests/application/test_take.py` stays green unchanged).
5. The contract (rows of one parametrized test): `RECORDS_CONTRACT == "2.0"`; each of the five files under `src/factory/contract/` holds `"x-records-contract": "2.0"` and equals `contract_schema` of its entry; `pipeline-definition.schema.json` names no `tool_paths`.
6. `template/factory/pipeline.yml` holds no `tool_paths` and is accepted by the reader; `factory/pipeline.yml` (after the human's change 1) is accepted too.
7. The markers and routes (the two tests of `tests/test_process_search.py` as the Interface says): the only suppression markers under `src/factory` are `noqa: S404`, `nosec B404` on the `subprocess` import and `noqa: S603`, `nosec B603` on the `Popen` line of `adapters/process.py`, besides the `noqa: PLR0913` of `entry/leftovers.py` that S0003 removes, and no module uses `os.execvpe`, `os.system` or another route to a process.
8. `make check` stays green.
9. docs: `docs/project-guide/write-guard.md`: the sections *The kernel's targets*, *The kernel's write guard* and *The start wrapper* go, each replaced by one line in a section *Replaced in v1.2* at the end of the file that says what replaced it (the dataset's rollback and the take); *The write paths* no longer names tool paths; `docs/project-guide/stages.md`, *The pipeline definition*: `tool_paths` goes from the keys, rule 12 (`tool path <path>: ...`) and its paragraph go from the rules, and an unknown key is refused; `docs/project-guide/agents.md`, the bullet on `template/factory/pipeline.yml`: it names no `tool_paths`; `docs/project-guide/processes-and-checks.md`, *Starting a process*: no `replace_process`; `docs/project-guide/README.md`, *The files*: the line of `write-guard.md` follows its sections, and *Shared test helpers*: the line of `confine_support.py` names only the helpers it keeps; `docs/operator-guide.md`, *The pipeline definition*: `tool_paths` goes and a definition that still holds it is refused with `pipeline_definition_invalid` (what to do: remove the key), *The records contract*: the version `2.0` and why it rose, and *The kernel refuses every other write*: removed, with one sentence in *The agent runtime* that the take keeps the write paths. `docs/decisions.md`: the entries "The write guard by the kernel: Landlock through ctypes", "factory-confine replaces itself with the runtime", "The kernel's targets of the write paths and the tool paths" and "The one module that starts processes may carry four markers" each gain one closing line ("Replaced by the dataset's rollback and the take, v1.2 F0044-S0002"; the last: "The `os.execvpe` call and its markers went with the wrapper, v1.2 F0044-S0002; the two on `subprocess` and `Popen` stay"); and the entry on the records contract gains the line that `2.0` removed `tool_paths`. `README.md`: the row `factory-confine` of the commands goes, and the sentence after the table counts five console commands.

## Smoke test

```bash
for module in factory.adapters.landlock factory.domain.confinement factory.entry.confine; do uv run python -c "import $module" 2>/dev/null && echo "$module present" || echo "$module gone"; done
```
Expect: three lines: `factory.adapters.landlock gone`; `factory.domain.confinement gone`; `factory.entry.confine gone`

```bash
uv run python -c 'from factory.domain.agent_runs import GuardSettings as g; from factory.domain.contract import RECORDS_CONTRACT as v; from factory.domain.pipeline_definition import PipelineDefinition as p; print(v, "tool_paths" in p.model_fields, sorted(g.model_fields))'; grep -c tool_paths template/factory/pipeline.yml || true
```
Expect: two lines: `2.0 False ['protected_paths', 'root', 'write_paths']`; `0`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete modules and signatures are named. The removals are by path and name, and the new `GuardSettings` is spelled out. `RECORDS_CONTRACT` is "2.0". The retained `WritePathService.at` is given with its return value. The test changes are listed per test with the leave (decision 18, widened by decision 31a).
   Criteria: each can be tested by one function or one parametrized test. The behaviours the Interface states have a criterion. Removed modules are criterion 1 and removed names criterion 2. The unknown-key refusal is criterion 3, which has both the accepted `PIPELINE_YAML` and the refused `tool_paths` line. The `at` return value and the take are criterion 4, the contract version and schemas criterion 5, the template and `factory/pipeline.yml` criterion 6, and the markers and routes criterion 7. The one rule with a failing side, the unknown key, has a criterion for that side.
   Smoke test: both commands are runnable. They run no pytest, so the `-q` check does not apply. `grep -c ... || true` prints `0` and exits cleanly. Each Expect line gives exact output that can be compared.
   Architecture: the removals follow the layering in CLAUDE.md. Only `adapters/process.py` keeps a process call (one `Popen`). `WritePathService.at` stays in `application`, and the models stay in `domain`. Nothing is added.
   Scope: the story matches feature.md's S0002 line. The refusal rule, the take and the other layers' stories are untouched. Changes to `factory/pipeline.yml` and the demo's definition are the human's change 1, and the docs criterion lists the documents it changes. No finding from the format check.
4. factory: started tests as self.
5. tester: I wrote tests for criteria 1–7 and made the test changes the Interface lists, under the leave in decision 18. The branch's tests are now red on purpose.

   Criterion → test:
   - criterion 1: tests/test_kernel_guard_removed.py::test_the_wrapper_and_the_kernel_s_modules_are_gone (3 rows)
   - criterion 2: tests/test_kernel_guard_removed.py::test_the_names_of_the_kernel_s_guard_and_the_tool_paths_are_gone (one row per removed name or field)
   - criterion 3: tests/adapters/test_pipeline_yaml_tool_paths.py::test_a_definition_with_tool_paths_is_refused (rows `without-tool-paths` accepted and `with-tool-paths` refused with a fault naming `tool_paths`, through `pipeline_outcome` from git_support)
   - criterion 4: tests/application/test_write_paths_guard.py::test_a_tester_s_stage_gives_the_root_the_write_paths_and_the_protected_paths (checks equality and that `model_dump` holds exactly root, write_paths, protected_paths). tests/application/test_take.py is unchanged.
   - criterion 5: tests/domain/test_contract_version_2.py::test_the_records_contract_is_at_version_2_without_tool_paths (rows: version, one per schema file for `"x-records-contract": "2.0"` and equality with `contract_schema`, no-tool-paths)
   - criterion 6: tests/adapters/test_pipeline_yaml_tool_paths.py::test_the_shipped_definitions_hold_no_tool_paths_and_load (rows: template/factory/pipeline.yml and factory/pipeline.yml)
   - criterion 7: tests/test_process_search.py::test_no_module_uses_another_route_to_a_process (`users == {}`) and ::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper (the `exec_line` and `confinement.py` entries are gone)
   - criteria 8 and 9: no test (they are `make check` and docs).

   Files created: tests/test_kernel_guard_removed.py, tests/adapters/test_pipeline_yaml_tool_paths.py, tests/application/test_write_paths_guard.py, tests/domain/test_contract_version_2.py.

   Deleted: the 13 test files the Interface lists.

   Earlier test files changed as the Interface lists, each test keeping its name:
   - tests/test_process_search.py, tests/test_wrapper_search.py, tests/entry/test_wiring.py
   - tests/domain/test_pipeline_not_read.py: the row `after-tool-paths` is gone.
   - tests/test_hook_removed.py: the `confine-command` row now expects `None`; the fields are three and the row id is now `three-fields`.
   - tests/domain/test_contract.py, tests/domain/test_contract_provider_limit.py: version 2.0.
   - tests/confine_support.py: now holds only Layout (without `confine_bin`, which nothing used), build_layout, read_records, write_script, LIMIT and run_request (no guard, no `write_paths`/`tool_paths` parameters).
   - No guard in the request or the context any more: tests/application/test_stage_launch.py, test_task.py, test_task_acceptance.py, test_task_os_user.py, test_no_state_refusals.py, test_agent_run_probe.py; tests/domain/test_agent_runs.py; tests/adapters/test_claude_runtime.py, test_claude_runtime_resume.py, test_claude_runtime_file_modes.py (one row, id `run`); tests/entry/test_wiring_boundaries.py.

   Follow-on edits for lint in those same files: the helpers `_context`, `_context_values` and `_prompt_lines` and the tests that called them lost their now-unused `tmp_path` parameters, and the unused imports of `CHECKOUT`, `Path` and `WritePathService` went.

   Test run: I ran `make test` once. It failed for the right reasons: the modules and names still exist, `TaskContext` still requires `guard`, and `GuardSettings` still has `tool_paths`. That run also showed a bug of my own: tests/domain/test_contract_version_2.py failed at collection on `pytest.ParameterSet`. I fixed it and confirmed with `pytest --collect-only` on that file only (7 tests), not with a second test run. No module failed to import in the test run; the removal tests use `find_spec`/`hasattr`. `make lint` is green. I skipped the type check, as the stage says.

   Open for the coder: three tests outside the Interface's list still add a guard through `model_copy(update={"guard": ...})`: tests/adapters/test_claude_runtime_login.py (`_guarded_request`), test_claude_runtime_api_login.py and test_claude_runtime_no_hook.py. `model_copy` does not validate, so they should stay green. If one turns red, it is a question for the human, not a fix for the coder.

   `lint`: lint: green (0.6 s)
   `test`: FAILED tests/test_hook_removed.py::test_the_hook_s_code_is_gone_and_the_kernel_s_guard_is_kept[confine-command] - AssertionError: assert 'factory-confine' == None
