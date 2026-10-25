---
stage: doing
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 445
comments_read: [6397809713]
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
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T12:35:20.317768Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T12:40:24.971302Z'
  stage: doing
  run: ca75f145308144f6b2ca85aacb5dd1ed
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T12:40:46.038572Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T12:42:58.310162Z'
  stage: review
  run: 1cfe7bc129534c7bb7d4d50554e2c2f3
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T12:43:18.755593Z'
  stage: doing
- number: 11
  speaker: coder
  kind: question
  at: '2026-10-25T12:45:06.206365Z'
  stage: doing
  run: 4d44d4acc6404949a4667afdd27ce1e4
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-10-25T12:45:50.038311Z'
  stage: doing
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-25T12:46:07.860347Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-25T12:46:26.716680Z'
  stage: doing
  run: defabd2b44764e91960f1b455493c9b6
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-25T12:46:47.517958Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-25T12:50:25.117580Z'
  stage: tests
  run: 9956c8fac07140a9b6e88ca349c83211
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-25T12:50:45.847437Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-25T12:54:01.911258Z'
  stage: doing
  run: abf62dff188d4c6e9242ab705039353b
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-25T12:54:22.457816Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-25T12:55:49.402910Z'
  stage: review
  run: ecbdcb3bda7b4291a624ff4796dbc0be
---

# The wrapper, the kernel's rules and the tool paths are removed

## Description

After S0001 (no agent call starts through the write guard's wrapper) the kernel's guard is code that nothing starts: the wrapper `factory-confine` (`factory.entry.confine`), the Landlock calls through ctypes (`factory.adapters.landlock`) with the `ConfinementError` (`factory.domain.errors`) that only it and the wrapper raised, the kernel's targets and rules (`factory.domain.confinement`), the process module's `replace_process` with its `os.execvpe` (the wrapper replaced itself with the runtime), and the input they were built from: the pipeline definition's `tool_paths`, `GuardSettings.tool_paths`, and the guard settings an agent run request and a task context carry. This story removes them. The pipeline definition's schema forbids unknown keys, so a definition that still holds `tool_paths` is refused at load from now on; the human's change 1 of `feature.md` takes the key out of `factory/pipeline.yml` and the demo's definition before this story starts, and the coder takes it out of `template/factory/pipeline.yml`. Removing a field of a contract model is a change that can break a reader, so the records contract's major version rises to 2.0 and the five schemas are generated again (decision 5 of `feature.md`); the definition's own `contract` stays `1.0`, as the decision log keeps the two apart. What stays: the write paths and their refusal rule (`refusal`, `PROTECTED_PATHS`, `WritePathService.at`, which still returns `GuardSettings` with the root, the expanded write paths and the protected paths), which the take and the undo read; the process module's one `Popen`.

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
6. factory: started doing as self.
7. coder: I removed the kernel's write guard, its start wrapper and the tool paths, as the Interface lists. `make check` is green: the last run gave lint, types, layers, sast, secrets, licenses and test all green, then `check: green`.

   What I built:
   - Deleted whole: `src/factory/entry/confine.py`, `src/factory/adapters/landlock.py`, `src/factory/domain/confinement.py`.
   - `src/factory/adapters/process.py`: `replace_process` is gone, with its `os.execvpe` line and that line's two markers. The `Mapping`, `Sequence` and `NoReturn` imports went with it. The `subprocess` import and the one `Popen` keep their markers.
   - `src/factory/domain/agent_runs.py`:
     - `CONFINE_COMMAND` is gone.
     - `GuardSettings` lost `tool_paths` and is now `root`, `write_paths`, `protected_paths`; its docstring says so.
     - `AgentRunRequest` lost `guard`.
   - `src/factory/domain/pipeline_definition.py`:
     - `PipelineDefinition.tool_paths` and the rule `_tool_path_faults` are gone. The model already forbids unknown keys, so a definition that still holds `tool_paths` is now refused like any other unknown key.
     - Also gone: `tool_path_folder`, `_is_plain_segment`, `HOME_PREFIX`, `_FOLDER_SUFFIX`, `_WILDCARDS`, `has_wildcard` and `CURRENT_SEGMENT`. `PARENT_SEGMENT` stays because `is_inside_checkout` uses it.
   - `src/factory/domain/contract.py`: `RECORDS_CONTRACT = "2.0"`.
   - `src/factory/contract/*.schema.json`: regenerated with `uv run python -m factory.entry.contract`. All five files are at version 2.0, and the pipeline definition's schema no longer has `tool_paths`.
   - The guard is gone from the request in four places:
     - `src/factory/application/write_paths.py`: `WritePathService.at` no longer passes `tool_paths`. Its class docstring now says "for the take and the undo alike" instead of "the guard".
     - `src/factory/application/task.py`: `TaskContext.guard` is gone and the request carries no guard.
     - `src/factory/application/stage.py`: the launcher builds the context without calling `WritePathService`.
     - `src/factory/application/preflight.py`: `_probe_request` builds no guard.
   - `template/factory/pipeline.yml`: the comment line and the `tool_paths` line are gone.

   Main choice: I kept `GuardSettings` under its old name and in `domain.agent_runs`, as the Interface says. The take, the undo and `refusal` still read it.
   - Rejected: renaming it to something like `WriteSettings` now that nothing guards. That would be a wider change than this work item, and the tests name `GuardSettings`.

   Refactor pass: the only change was the `WritePathService` docstring above. The rest of the diff is removals, so there was nothing else to simplify.

   Noticed but not touched:
   - `pyproject.toml` line 17 still declares the console script `factory-confine = "factory.entry.confine:main"`. That module no longer exists, so the installed `factory-confine` would fail on start. `pyproject.toml` is outside the coder's write paths. The human (or a story that may write it) should remove that line; `make check` is green with it in place.
   - The tester said three tests use `model_copy(update={"guard": ...})`: `tests/adapters/test_claude_runtime_login.py`, `test_claude_runtime_api_login.py` and `test_claude_runtime_no_hook.py`. They stayed green, since `model_copy` does not validate. Each now adds a field the model no longer has, so the tester may want to drop those updates in a later story.
   - The docs criterion is the documenter's, and I did not write it.
   - `git rm` was refused (no permission to write the git index), so I deleted the three modules with plain `rm`. The factory's commit picks up the deletions.

   `check`: check: green
   `duplicates`: duplicates: 10 new, 35 known, 3 gone
8. factory: started review as self.
9. reviewer: Review, round 0. I read the work item, the diff of `src/`, `template/` and `tests/`, and the feature's decisions 18, 31 and change 3. I ran `make duplicates` to read its new findings. Groups 1 to 3 pass:
   - Criteria 1 to 7 each have a test that checks what the criterion says.
   - The one rule with a failing side, the unknown key `tool_paths`, has its refused row.
   - `test_take.py` is unchanged.
   - The coder's `make check` was green.
   - Only removals touch the layers, and the two markers on `os.execvpe` went with their line.
   - The `factory-confine` line left in `pyproject.toml` is not a finding: the human removes it in change 3 of `feature.md`, after this story is merged.

   Group 4 (quality) fails:

   1. `src/factory/domain/errors.py:122`: `ConfinementError` is now dead code. Only `adapters/landlock.py` and `entry/confine.py` used it, and both are gone (`make duplicates` reports it as new dead code). Fix: the coder removes the class.
   2. `tests/test_kernel_guard_removed.py:21`: `_has(module, name)` is a second copy of `_has` in `tests/test_hook_removed.py:16`. Fix: the tester moves it to one shared module under `tests/` under the standing leave, and both modules import it from there.
   3. Against the story: three earlier tests that the Interface does not list still inject a `guard` the model no longer has, through `model_copy(update={"guard": ...})`:
      - `tests/adapters/test_claude_runtime_login.py:82-85` (`_guarded_request`)
      - `tests/adapters/test_claude_runtime_api_login.py:130-132`
      - `tests/adapters/test_claude_runtime_no_hook.py:19-31`
      `model_copy` does not validate, so the suite stays green. But the requests are invalid, and in `no_hook` the rows `unconfined-guarded` and `unconfined-unguarded` are now the same case; its docstring still says "with or without guard settings". Fix: the coder asks the human (R8/R9) for leave to drop those updates and fold the two rows into one. The tester then makes exactly that change.

   Earlier tests (item 6):
   - Deleted, each under decision 18 / 31a (all thirteen are listed in the Interface):
     - `tests/adapters/test_landlock.py`
     - `tests/adapters/test_landlock_checks.py`
     - `tests/adapters/test_process_replace.py`
     - `tests/adapters/test_process_replace_faults.py`
     - `tests/application/test_write_paths_tool_paths.py`
     - `tests/domain/test_confinement_abi.py`
     - `tests/domain/test_confinement_model.py`
     - `tests/domain/test_confinement_of.py`
     - `tests/domain/test_tool_paths.py`
     - `tests/domain/test_write_targets.py`
     - `tests/entry/test_confine.py`
     - `tests/entry/test_confine_defaults.py`
     - `tests/entry/test_confine_steps.py`
   - Changed as the Interface names, under decision 18 / 31a:
     - `tests/test_process_search.py`
     - `tests/test_wrapper_search.py`
     - `tests/entry/test_wiring.py`
     - `tests/domain/test_pipeline_not_read.py`
     - `tests/test_hook_removed.py` (the row id `four-fields` became `three-fields`; the test keeps its name)
     - `tests/domain/test_contract.py`
     - `tests/domain/test_contract_provider_limit.py`
     - `tests/confine_support.py` (`Layout` also lost `confine_bin`, a name of the wrapper, as the Interface allows)
     - `tests/application/test_stage_launch.py`
     - `tests/application/test_no_state_refusals.py`
     - `tests/application/test_agent_run_probe.py`
     - `tests/domain/test_agent_runs.py`
     - `tests/adapters/test_claude_runtime.py`
     - `tests/adapters/test_claude_runtime_resume.py`
     - `tests/adapters/test_claude_runtime_file_modes.py`
     - `tests/entry/test_wiring_boundaries.py`
   - Changed under decision 18 / 31a, plus follow-on edits: their named `_context`/`_context_values` helpers lost `tmp_path`, so `_prompt_lines` and the callers' signatures lost it too, for lint. Each test keeps its name and its checks:
     - `tests/application/test_task.py`
     - `tests/application/test_task_acceptance.py`
     - `tests/application/test_task_os_user.py`
10. factory: started doing as self.
11. coder: Round 1. I fixed the reviewer's finding 1 and stopped at finding 3, which needs the human's leave. Finding 2 belongs to the tester, so I am asking for both test changes in one question.

    Done:
    - Finding 1: I removed `ConfinementError` from `src/factory/domain/errors.py`. It was dead code once `adapters/landlock.py` and `entry/confine.py` were gone. Nothing under `src`, `tests` or `security` names it any more. `make check` is green (`test: green (67.5 s)`, `check: green`).
    - Two docs still describe the class: `docs/project-guide/README.md:105` and `docs/project-guide/write-guard.md:115,149`. Those sections are in the docs criterion, so they go in the documenter's stage. I did not touch them.

    Main choice: I asked a question rather than ending with `tests`, which would cover only finding 2. Finding 3 changes tests the Interface does not list, and CLAUDE.md requires the human's leave for that (R9). Ending with `tests` now would send the work item to the tester and back without finding 3, and then the same question would come anyway.

    Question for the human: three earlier tests, which the Interface does not list, still add a `guard` field that `AgentRunRequest` no longer has. They do it through `model_copy(update={"guard": ...})`, which does not validate, so the suite stays green with invalid requests:
    - `tests/adapters/test_claude_runtime_login.py:82-85` (`_guarded_request`)
    - `tests/adapters/test_claude_runtime_api_login.py:130-132`
    - `tests/adapters/test_claude_runtime_no_hook.py:19-31`, whose rows `unconfined-guarded` and `unconfined-unguarded` are now the same case, and whose docstring still says "with or without guard settings"

    Options:
    - (a) Give leave for the tester to drop the `guard` updates in all three, fold the two `no_hook` rows into one, and fix that docstring. Each test keeps its name and its other checks. The tester would do this together with finding 2: move `_has` from `tests/test_hook_removed.py:16` and `tests/test_kernel_guard_removed.py:21` to one shared module under `tests/`, as the standing leave allows.
    - (b) Leave the three tests as they are and do only finding 2.
    - (c) Make the three tests a separate story.

    I would choose (a). Once you answer, I will end with `tests` and name these changes.

    Not touched: `pyproject.toml` still has the `factory-confine` console script. The reviewer says the human removes it in change 3 of `feature.md`.
12. 2026-10-25 human: (a). Leave given for the tester, under decision 17 and the human's standing answer for lists found after the pre-check (decision 29): drop the `guard` updates in `tests/adapters/test_claude_runtime_login.py` (`_guarded_request`), `tests/adapters/test_claude_runtime_api_login.py` and `tests/adapters/test_claude_runtime_no_hook.py`, fold the two `no_hook` rows `unconfined-guarded` and `unconfined-unguarded` into one, and fix that docstring. Each test keeps its name and its other checks. Together with finding 2: move `_has` from `tests/test_hook_removed.py` and `tests/test_kernel_guard_removed.py` into one shared module under `tests/` (the standing helper-move leave). The two docs passages on `ConfinementError` are the documenter's. `pyproject.toml`'s `factory-confine` script is the human's change 3, after the merge.
13. factory: started doing as self.
14. coder: Round 1, after the human's answer (a) in entry 12. I changed no code and no tests in this run. The finding 1 fix, which removed `ConfinementError` from `src/factory/domain/errors.py`, was already committed, and nothing under `src` or `tests` names the class any more. The working tree holds no other change.

    The answer calls for test changes only, so I am sending the work item to the tester. The changes are:
    - Finding 3: drop the `guard` updates from three test files and leave everything else in them as it is. Each test keeps its name and its other checks. The files are:
      - `tests/adapters/test_claude_runtime_login.py`, in the `_guarded_request` helper (`model_copy(update={"guard": ...})`)
      - `tests/adapters/test_claude_runtime_api_login.py`
      - `tests/adapters/test_claude_runtime_no_hook.py`. Here, also fold the rows `unconfined-guarded` and `unconfined-unguarded` into one row, and fix the docstring so it no longer says "with or without guard settings".
    - Finding 2, under the standing helper-move leave: move `_has(module, name)` out of `tests/test_hook_removed.py` and `tests/test_kernel_guard_removed.py` into one shared module under `tests/`, and make both files import it from there.

    Main choice: I ended with `tests` and did not touch the tests myself, because R9 says the coder never edits tests. The alternative was to end with `review`, but the reviewer's findings 2 and 3 would then still be open.

    Noticed but not touched:
    - The docs passages on `ConfinementError` (`docs/project-guide/README.md`, `docs/project-guide/write-guard.md`) are left for the documenter.
    - The `factory-confine` console script in `pyproject.toml` is left for the human's change 3, after the merge.
    - The journal did not change what the task means, so `## Description` is unchanged.
15. factory: started tests as self.
16. tester: Mode: a test change the human approved (entry 12, as the coder's entry 14 names it). I made exactly these changes. No test was renamed and every test still checks what it checked before.

    Finding 3, under the human's leave in entry 12:
    - `tests/adapters/test_claude_runtime_login.py`: I removed the `_guarded_request` helper, which existed only to add `guard` through `model_copy`. `test_the_login_stands_in_no_argument_no_run_file_and_no_result` now runs `_request(tmp_path, os_user)`. I also dropped the `GuardSettings` import, which nothing used any more.
    - `tests/adapters/test_claude_runtime_api_login.py`: I took the `guard` update out of `test_the_key_stands_in_no_argument_no_run_file_and_no_result`, which now runs `_request(tmp_path, os_user)` directly. I dropped the `GuardSettings` import here too.
    - `tests/adapters/test_claude_runtime_no_hook.py`: I merged the rows `unconfined-guarded` and `unconfined-unguarded` into one row, `unconfined`, which builds its request with `run_request`. I removed the `_guarded` and `_unguarded` helpers. The module docstring no longer says "with or without guard settings". `test_no_run_registers_a_hook` keeps its name and its three asserts.

    Finding 2, under the standing leave in CLAUDE.md to move a shared test helper:
    - I moved `_has(module, name)` into the new shared module `tests/module_names.py` as `has_name`. `tests/test_hook_removed.py` and `tests/test_kernel_guard_removed.py` now import it from there and no longer hold their own copies. In `test_hook_removed.py`, two `pytest.param` rows (`guard-command`, `guard-settings`) are now wrapped across lines to stay within the line limit. Their values and ids are unchanged.

    Files created: `tests/module_names.py`.
    Earlier test files changed: `tests/adapters/test_claude_runtime_login.py`, `tests/adapters/test_claude_runtime_api_login.py`, `tests/adapters/test_claude_runtime_no_hook.py`, `tests/test_hook_removed.py`, `tests/test_kernel_guard_removed.py`.
    Modules the test run could not import: none.

    Results: `make test` passed (`test: green (67.3 s)`). `make lint` passed (`lint: green (0.2 s)`). I skipped the type check as the stage says; the coder's `make check` covers it.

    Rejected: dropping the parametrize from `no_hook` altogether. The answer said to fold the rows into one, so I kept a table with one row.

    `lint`: lint: green (0.6 s)
    `test`: test: green (66.4 s)
17. factory: started doing as self.
18. coder: Round 1, after the tester's change in entry 16. I changed no code in this run. The code for this round was finished earlier: finding 1, the removal of `ConfinementError` from `src/factory/domain/errors.py`, is already committed. The tester has now fixed findings 2 and 3 with the human's leave from entry 12: the shared `has_name` in `tests/module_names.py`, and the `guard` updates dropped from the three `claude_runtime` test modules.

    What I did:
    - I ran `make check` on the committed state with the tester's changes in. It is green: `test: green (67.8 s)`, then `check: green`, with coverage at 99.47 %.
    - I searched `src/factory` and `template/` for leftovers of the removed code, outside the generated schemas. The search terms were `tool_path`, `ConfinementError`, `confine` and `execvpe`, and none of them appears.
    - The working tree holds no change of mine. The only modified file is the factory's own `.costs.jsonl` sidecar.

    Main choice: I hand the item to review without touching anything. All three of the reviewer's findings are now dealt with: finding 1 in code earlier this round, and findings 2 and 3 in tests by the tester. The alternative was a further refactor pass, but there was nothing to refactor: the round's code diff is the one-class removal, and it needs no change.

    The journal did not change what the task means, so `## Description` is unchanged.

    Noticed but not touched:
    - `docs/project-guide/README.md` and `docs/project-guide/write-guard.md` still describe `ConfinementError`. Those pages are the documenter's.
    - The `factory-confine` console script is still in `pyproject.toml`. The human removes it in change 3, after the merge.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 9 new, 35 known, 3 gone
19. factory: started review as self.
20. reviewer: Review, round 1. I read the work item, the diff of `src/`, `template/` and `tests/`, and the changes made since round 0: `ConfinementError` removed, `has_name` in `tests/module_names.py`, and the three `claude_runtime` tests without `guard`. I ran `make duplicates`. Its 9 new findings are all in modules this diff does not touch (`claude_runtime`/`opencode_runtime` similarities, `fake_containers`, `fake_snapshots`, `podman_runs`, `zfs_snapshots`).

    Groups 1 to 4 pass:
    - Group 1: criteria 1 to 7 each have a test that checks what the criterion says. Criterion 3 goes through `pipeline_outcome`, which calls `RuamelPipelineDefinitionReader().parse` and catches `PipelineDefinitionInvalid`. The refused row is there. The coder's `make check` was green (entries 7 and 18).
    - Group 2: only removals touch the layers.
    - Group 3: the `os.execvpe` line went together with its markers `S606`/`B606`. No new marker.
    - Group 4: round 0's findings 1 to 3 are fixed. Finding 1 removed the dead `ConfinementError`. Finding 2 moved the copied `_has` to `tests/module_names.py`. Finding 3 removed the `guard` updates, under the human's leave in entry 12.
    - The contract's version rule holds: removing a field makes it a major version, so 2.0 (`docs/decisions.md:661`).

    Group 5 (work item hygiene) fails:

    1. Docs criterion 9 in the work item: it does not name `docs/project-guide/README.md:105` (section *Errors*). That line still describes `ConfinementError(detail)`, and the class went in this round. The criterion names only *The files* and *Shared test helpers* of that file, and the documenter writes from the criterion. Fix: the coder adds to criterion 9's `docs/project-guide/README.md` part that the `ConfinementError` paragraph under *Errors* goes. The `write-guard.md:115,149` mentions are inside sections the criterion already removes.

    description corrected: "the Landlock calls through ctypes (`factory.adapters.landlock`), the kernel's targets" -> "the Landlock calls through ctypes (`factory.adapters.landlock`) with the `ConfinementError` (`factory.domain.errors`) that only it and the wrapper raised, the kernel's targets". The journal settles this in entries 9, 11 and 12.

    Earlier tests (item 6):
    - Deleted, each under decision 18 / 31a (all thirteen are listed in the Interface):
      - `tests/adapters/test_landlock.py`
      - `tests/adapters/test_landlock_checks.py`
      - `tests/adapters/test_process_replace.py`
      - `tests/adapters/test_process_replace_faults.py`
      - `tests/application/test_write_paths_tool_paths.py`
      - `tests/domain/test_confinement_abi.py`
      - `tests/domain/test_confinement_model.py`
      - `tests/domain/test_confinement_of.py`
      - `tests/domain/test_tool_paths.py`
      - `tests/domain/test_write_targets.py`
      - `tests/entry/test_confine.py`
      - `tests/entry/test_confine_defaults.py`
      - `tests/entry/test_confine_steps.py`
    - Changed as the Interface names, under decision 18 / 31a:
      - `tests/test_process_search.py`
      - `tests/test_wrapper_search.py`
      - `tests/entry/test_wiring.py`
      - `tests/domain/test_pipeline_not_read.py`
      - `tests/domain/test_contract.py`
      - `tests/domain/test_contract_provider_limit.py`
      - `tests/confine_support.py`
      - `tests/application/test_stage_launch.py`
      - `tests/application/test_no_state_refusals.py`
      - `tests/application/test_agent_run_probe.py`
      - `tests/domain/test_agent_runs.py`
      - `tests/adapters/test_claude_runtime.py`
      - `tests/adapters/test_claude_runtime_resume.py`
      - `tests/adapters/test_claude_runtime_file_modes.py`
      - `tests/entry/test_wiring_boundaries.py`
    - Changed under decision 18 / 31a, plus the follow-on lint edits (`tmp_path` dropped). Each test keeps its name and its checks:
      - `tests/application/test_task.py`
      - `tests/application/test_task_acceptance.py`
      - `tests/application/test_task_os_user.py`
    - `tests/test_hook_removed.py`: changed under decision 18 / 31a (the `confine-command` row, the three fields). Its `_has` was moved to `tests/module_names.py` under the standing leave to move a shared test helper.
    - Changed under the human's leave in journal entry 12:
      - `tests/adapters/test_claude_runtime_login.py`
      - `tests/adapters/test_claude_runtime_api_login.py`
      - `tests/adapters/test_claude_runtime_no_hook.py` (the two rows folded into `unconfined`, the docstring fixed)

    Notes:
    - `tests/adapters/test_claude_runtime_no_hook.py:19`: a parametrize with one row and two parameters, one of them constant. It is kept because the answer said to fold the rows into one. It could become a plain test in a later cleanup.

    Open, outside this story: `pyproject.toml`'s `factory-confine` console script is the human's change 3, after the merge.
