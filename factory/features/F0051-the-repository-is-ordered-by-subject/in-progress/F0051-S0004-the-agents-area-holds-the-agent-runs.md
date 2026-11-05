---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 559
comments_read: [6648033321]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-05T02:39:33.488281Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T02:13:20.633087Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T02:13:20.639563Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T02:13:39.485040Z'
  stage: intake
  run: 642d092507c9489ab4a4e99520322e98
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T02:13:44.797849Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T02:14:39.046659Z'
  stage: tests
  run: 4132ed73d1ae4447964fec777cb9f15d
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T02:14:44.201148Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-11-05T02:22:19.525254Z'
  stage: doing
  run: c4d3e9343e9b4cfaacd33e3a251682fc
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-11-05T02:30:18.231959Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T02:30:20.655034Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T02:30:48.313312Z'
  stage: doing
  run: 144fd8d0fe30450f91c1c8983f314181
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-05T02:30:53.327119Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-05T02:34:06.421781Z'
  stage: tests
  run: 6c888f24a35c484092cf37a031d63260
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-05T02:34:11.882358Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-05T02:39:26.374559Z'
  stage: doing
  run: 176ec0a247384616881c3723d756971f
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T02:39:33.488281Z'
  stage: review
---

# The agents area holds the agent runs

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `agents` area: agent runs, the two runtimes, prompts, write paths, tool uses, provider limits and tokens. Each of its 19 modules moves from its layer package to the same layer inside `factory.agents`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/agents/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`; and the same folders under `tests/agents/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.agent_runs` → `factory.agents.domain.agent_runs`
- `factory.domain.died_runs` → `factory.agents.domain.died_runs`
- `factory.domain.opencode_provider` → `factory.agents.domain.opencode_provider`
- `factory.domain.prompts` → `factory.agents.domain.prompts`
- `factory.domain.provider_limits` → `factory.agents.domain.provider_limits`
- `factory.domain.tokens` → `factory.agents.domain.tokens`
- `factory.domain.tool_uses` → `factory.agents.domain.tool_uses`
- `factory.domain.write_paths` → `factory.agents.domain.write_paths`
- `factory.application.agent_runtime` → `factory.agents.application.agent_runtime`
- `factory.application.project_agents` → `factory.agents.application.project_agents`
- `factory.application.provider_limits` → `factory.agents.application.provider_limits`
- `factory.application.tokens` → `factory.agents.application.tokens`
- `factory.application.write_paths` → `factory.agents.application.write_paths`
- `factory.adapters.agent_files` → `factory.agents.adapters.agent_files`
- `factory.adapters.agent_launch` → `factory.agents.adapters.agent_launch`
- `factory.adapters.claude_runtime` → `factory.agents.adapters.claude_runtime`
- `factory.adapters.opencode_runtime` → `factory.agents.adapters.opencode_runtime`
- `factory.adapters.fake_agent_runtime` → `factory.agents.adapters.fake_agent_runtime`
- `factory.adapters.oauth_token` → `factory.agents.adapters.oauth_token`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `agents` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/agents/<its layer>/` when every one of its imports from `factory` is a module of the `agents` area or of an area already moved before it and at least one is of `agents`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.agents.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `agents` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `agents` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.agents.domain.agent_runs as m; print(m.__name__)"
```
Expect: `factory.agents.domain.agent_runs`

```bash
test -e src/factory/domain/agent_runs.py && echo still there || echo moved
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
   - Interface: the four new packages and the 19 moves are listed old to new with concrete module paths. The rules (no old path, no re-export, which test modules move) are stated and each has a criterion.
   - Criteria: 1 (AREAS row, import of each new path, old file gone, one row per module), 2 (packages import and have a docstring), 3 (no old import, one row per module, in the three forms of feature decision 8) and 4 (no test module left that takes all its imports from agents and earlier areas) are each testable by one test function. 5 and 6 are the closing criteria. Both sides of every rule are covered: the new path exists and the old one does not, and an old import is absent. Feature decision 8 supplies the standing answers on the AREAS key, the untested `__init__.py` files and docstring form, which areas count as "moved before", and the import forms.
   - Smoke test: the three commands are runnable and each Expect line can be checked against the output. The pytest command passes no `-q`, and `pyproject.toml`'s `addopts` already sets one, so `tail -1` shows the "N passed" summary line.
   - Architecture: the move keeps each module in its own layer inside `factory.agents`, so the layer rule holds. It matches feature decisions 1 to 4 and 7.
   - Scope: this is the agents area of S0004 in the feature's stories list, and it changes no behaviour. `docs/decisions.md` is untouched, as the feature's out-of-scope list requires. No test that another story wrote is changed beyond the leave in feature decision 5.
4. factory: started tests as vm.
5. tester: Added the `agents` row to `AREAS` in `tests/test_areas.py`, holding the 19 modules of the Interface's table. That was the only change. The test functions already in that module are parametrized over `AREAS`, so they now cover the new area and I wrote no new functions. This matches the Interface's rule that nothing else in that module changes.

   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (one row per module, ids `agents.<layer>.<name>`). The key and its module list are the new `AREAS["agents"]` entry.
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.agents`, `factory.agents.adapters`, `factory.agents.application`, `factory.agents.domain`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module; `source_search.imports` covers the three import forms)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own checks the moved test modules under `tests/agents/` once they exist.
   - criteria 5 and 6: the closing ones (`make check` stays green, docs), not tested here.

   Files: I created none. I changed tests/test_areas.py, which an earlier story of this feature wrote; feature decision 5 covers that change, and the Interface names it.

   Run of `uv run pytest -q tests/test_areas.py`: the new rows fail for the right reason. The `factory.agents.*` modules cannot be imported yet (ModuleNotFoundError), and the old paths are still imported from `src/` and `tests/`. The runner could not import `factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`, or any of the 19 modules under them. `make lint` is green.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Round 0. I stopped at a question: three lint exemptions in `pyproject.toml` name old paths. That file is outside the write paths of both the coder and the tester. Everything else is done and checked. With all the changes below in my working tree, plus a local `pyproject.toml` edit, `make check` was green (`test: green (126.0 s)`, `check: green`). The factory keeps only my `src/` changes.

   **Question.** `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` has three keys for modules this story moves:
   - `"src/factory/adapters/claude_runtime.py"` (PLR0913)
   - `"src/factory/adapters/opencode_runtime.py"` (PLR0913)
   - `"src/factory/adapters/oauth_token.py"` (PLR0913, S310)

   At the new paths, ruff reports PLR0913 three times and S310 once. So `make lint` is red, and with it the tests stage's check and `make check`. The options I see:
   - (a) You change the three keys to `src/factory/agents/adapters/<name>.py` and keep their comments. This is the same kind of follow-up you made for S0001 in 159f946a2.
   - (b) You give me leave to change `pyproject.toml` for exactly those three keys.
   - (c) Put `# noqa` in the source. I reject this: the keys' own comments say "no noqa in the source".

   I would choose (a). Once it is on the branch, the next doing run ends with `tests` and hands the tester the changes below.

   **What I built (in my write paths), now in the tree:**
   - `src/factory/agents/__init__.py`, `src/factory/agents/domain/__init__.py`, `src/factory/agents/application/__init__.py` and `src/factory/agents/adapters/__init__.py`, each with a one-line docstring.
   - The 19 modules of the Interface, moved with `git mv` to `src/factory/agents/<layer>/<name>.py`.
   - Every reference to an old path under `src/` now names `factory.agents.<layer>.<name>`: 31 files, re-sorted by `ruff check --fix` and `ruff format`. I checked the diff: only import lines changed. `uv run python -m factory.entry.contract` left the schemas unchanged, and `make layers` is green.

   **Main choice:** I followed S0003's split: the coder moves `src/`, the tester moves and rewrites `tests/`. I rejected ending with `review` with the test edits in the tree, because the factory drops them. I rejected ending with `tests` now, because the tester's `make lint` stays red until `pyproject.toml` changes.

   **Test changes for the tester, after the answer** (Interface leave, feature decision 5; every test keeps its name and checks the same thing):
   1. Under `tests/`, except `tests/test_areas.py`: run sed over the regex `\bfactory\.((domain\.(agent_runs|died_runs|opencode_provider|prompts|provider_limits|tokens|tool_uses|write_paths)|application\.(agent_runtime|project_agents|provider_limits|tokens|write_paths)|adapters\.(agent_files|agent_launch|claude_runtime|opencode_runtime|fake_agent_runtime|oauth_token))\b)` → `factory.agents.\1`.
      - Then split the `from factory.<layer> import ...` lines, so that the moved names come from `factory.agents.<layer>` and the rest stay. Those lines are in: `tests/adapters/test_calls_as_the_factory_user.py`, `test_opencode_runtime_container.py`, `test_runtime_podman_timeout_status.py`, `test_runtimes_without_wrapper.py`, `tests/conftest.py` (`claude_runtime` moves, `podman_runs` stays), `tests/test_home_reset_removed.py`, `tests/test_leftovers_program_removed.py`, `tests/test_removed_layer_names.py` and `tests/test_second_user_removed.py` (`make_commands` stays).
      - Then run `ruff check --fix tests` and `ruff format tests`. Format wraps the long `has_name(...)` rows in `test_hook_removed.py` and `test_removed_layer_names.py`.
   2. Three path references to moved test files:
      - `tests/test_no_agent_login.py:11`: `/ "adapters" /` → `/ "agents" / "adapters" /`
      - `tests/test_suite_held_once.py:123`: `"adapters/test_claude_runtime_no_hook.py"` → `"agents/adapters/test_claude_runtime_no_hook.py"`
      - `tests/test_tests_run_under_the_starting_umask.py:7`: `EXEMPT_FILE` → `"agents/adapters/test_calls_as_the_factory_user.py"`
   3. Create empty `tests/agents/__init__.py` and `tests/agents/{domain,application,adapters}/__init__.py`. Then move these 55 modules, which criterion 4 selects after step 1, to the same layer under `tests/agents/`:
      - From `tests/domain/` (18): test_agent_entry, test_agent_environment, test_agent_runs, test_agent_runs_session, test_decisions, test_died_runs, test_nested_claude_paths, test_opencode_provider, test_project_agent_paths, test_prompts, test_provider_limit_wait, test_provider_limits, test_provider_limits_one_second, test_resumed_result, test_resumed_result_time_limit, test_tokens, test_tokens_masked, test_write_paths.
      - From `tests/application/` (1): test_tokens.
      - From `tests/adapters/` (36): test_agent_file_keys, test_agent_files, test_agent_files_parse, test_agent_launch, test_agent_launch_call_end, test_agent_launch_container_kill, test_agent_launch_login, test_agent_launch_state_directory, test_calls_as_the_factory_user, test_claude_runtime, test_claude_runtime_api_login, test_claude_runtime_denial_paths, test_claude_runtime_environment, test_claude_runtime_login, test_claude_runtime_no_hook, test_claude_runtime_provider_limit, test_claude_runtime_resume, test_claude_runtime_resume_session, test_claude_runtime_transcript, test_died_text, test_fake_agent_runtime, test_kill_at_the_limit_stays, test_oauth_token, test_opencode_budget, test_opencode_left_out_tools, test_opencode_measures, test_opencode_provider_limit, test_opencode_result_block, test_opencode_resumed_words, test_opencode_runtime, test_opencode_runtime_launch, test_opencode_runtime_provider, test_opencode_runtime_runs_folder, test_runtime_died_text, test_runtime_state_directory_write, test_shipped_agents_effect.
      - Their only `__file__` uses are inside the stand-in scripts they write, so the move does not change them.

   **Refactor:** the diff is mechanical (moves and import lines), so nothing needed changing.

   **Noticed, not touched:**
   - `security/duplicates-baseline.txt` lines 4–6, 21, 31, 34, 36 and 42 name old paths. They need the `factory.agents.*` / `src/factory/agents/...` paths, as you did for the earlier stories.
   - `CLAUDE.md` line 19 names `factory.adapters.agent_launch`.
   - The docs that name old paths are for the docs stage (criterion 6).

   The factory left out changes outside the write paths: pyproject.toml, tests/adapters/claude_stand_in.py, tests/adapters/container_runtime_support.py, tests/adapters/opencode_stand_in.py, tests/adapters/test_agent_file_keys.py, tests/adapters/test_agent_files.py, tests/adapters/test_agent_files_parse.py, tests/adapters/test_agent_launch.py, tests/adapters/test_agent_launch_call_end.py, tests/adapters/test_agent_launch_container.py, tests/adapters/test_agent_launch_container_kill.py, tests/adapters/test_agent_launch_extra.py, tests/adapters/test_agent_launch_login.py, tests/adapters/test_agent_launch_state_directory.py, tests/adapters/test_calls_as_the_factory_user.py, tests/adapters/test_claude_runtime.py, tests/adapters/test_claude_runtime_api_login.py, tests/adapters/test_claude_runtime_container.py, tests/adapters/test_claude_runtime_denial_paths.py, tests/adapters/test_claude_runtime_environment.py, tests/adapters/test_claude_runtime_login.py, tests/adapters/test_claude_runtime_no_hook.py, tests/adapters/test_claude_runtime_provider_limit.py, tests/adapters/test_claude_runtime_resume.py, tests/adapters/test_claude_runtime_resume_session.py, tests/adapters/test_claude_runtime_transcript.py, tests/adapters/test_died_text.py, tests/adapters/test_fake_agent_runtime.py, tests/adapters/test_kill_at_the_limit_stays.py, tests/adapters/test_oauth_token.py, tests/adapters/test_opencode_budget.py, tests/adapters/test_opencode_events.py, tests/adapters/test_opencode_left_out_tools.py, tests/adapters/test_opencode_measures.py, tests/adapters/test_opencode_provider_limit.py, tests/adapters/test_opencode_result_block.py, tests/adapters/test_opencode_resumed_words.py, tests/adapters/test_opencode_runtime.py, tests/adapters/test_opencode_runtime_container.py, tests/adapters/test_opencode_runtime_launch.py, tests/adapters/test_opencode_runtime_lockdown.py, tests/adapters/test_opencode_runtime_provider.py, tests/adapters/test_opencode_runtime_runs_folder.py, tests/adapters/test_runtime_died_text.py, tests/adapters/test_runtime_podman_timeout_status.py, tests/adapters/test_runtime_state_directory_write.py, tests/adapters/test_runtime_tool_uses.py, tests/adapters/test_runtimes_without_wrapper.py, tests/adapters/test_shipped_agents_effect.py, tests/agent_definition_support.py, tests/agent_run_support.py, tests/agents/__init__.py, tests/agents/adapters/__init__.py, tests/agents/adapters/test_agent_file_keys.py, tests/agents/adapters/test_agent_files.py, tests/agents/adapters/test_agent_files_parse.py, tests/agents/adapters/test_agent_launch.py, tests/agents/adapters/test_agent_launch_call_end.py, tests/agents/adapters/test_agent_launch_container_kill.py, tests/agents/adapters/test_agent_launch_login.py, tests/agents/adapters/test_agent_launch_state_directory.py, tests/agents/adapters/test_calls_as_the_factory_user.py, tests/agents/adapters/test_claude_runtime.py, tests/agents/adapters/test_claude_runtime_api_login.py, tests/agents/adapters/test_claude_runtime_denial_paths.py, tests/agents/adapters/test_claude_runtime_environment.py, tests/agents/adapters/test_claude_runtime_login.py, tests/agents/adapters/test_claude_runtime_no_hook.py, tests/agents/adapters/test_claude_runtime_provider_limit.py, tests/agents/adapters/test_claude_runtime_resume.py, tests/agents/adapters/test_claude_runtime_resume_session.py, tests/agents/adapters/test_claude_runtime_transcript.py, tests/agents/adapters/test_died_text.py, tests/agents/adapters/test_fake_agent_runtime.py, tests/agents/adapters/test_kill_at_the_limit_stays.py, tests/agents/adapters/test_oauth_token.py, tests/agents/adapters/test_opencode_budget.py, tests/agents/adapters/test_opencode_left_out_tools.py, tests/agents/adapters/test_opencode_measures.py, tests/agents/adapters/test_opencode_provider_limit.py, tests/agents/adapters/test_opencode_result_block.py, tests/agents/adapters/test_opencode_resumed_words.py, tests/agents/adapters/test_opencode_runtime.py, tests/agents/adapters/test_opencode_runtime_launch.py, tests/agents/adapters/test_opencode_runtime_provider.py, tests/agents/adapters/test_opencode_runtime_runs_folder.py, tests/agents/adapters/test_runtime_died_text.py, tests/agents/adapters/test_runtime_state_directory_write.py, tests/agents/adapters/test_shipped_agents_effect.py, tests/agents/application/__init__.py, tests/agents/application/test_tokens.py, tests/agents/domain/__init__.py, tests/agents/domain/test_agent_entry.py, tests/agents/domain/test_agent_environment.py, tests/agents/domain/test_agent_runs.py, tests/agents/domain/test_agent_runs_session.py, tests/agents/domain/test_decisions.py, tests/agents/domain/test_died_runs.py, tests/agents/domain/test_nested_claude_paths.py, tests/agents/domain/test_opencode_provider.py, tests/agents/domain/test_project_agent_paths.py, tests/agents/domain/test_prompts.py, tests/agents/domain/test_provider_limit_wait.py, tests/agents/domain/test_provider_limits.py, tests/agents/domain/test_provider_limits_one_second.py, tests/agents/domain/test_resumed_result.py, tests/agents/domain/test_resumed_result_time_limit.py, tests/agents/domain/test_tokens.py, tests/agents/domain/test_tokens_masked.py, tests/agents/domain/test_write_paths.py, tests/application/handlers/test_run.py, tests/application/test_acceptance_service.py, tests/application/test_acceptance_ticks_closed.py, tests/application/test_acceptance_ticks_merged.py, tests/application/test_after_agent.py, tests/application/test_after_agent_edges.py, tests/application/test_agent_definition_reader.py, tests/application/test_agent_run_probe.py, tests/application/test_agent_run_probe_api_login.py, tests/application/test_agent_run_probe_environment.py, tests/application/test_agent_run_probe_factory_user.py, tests/application/test_agent_run_probe_login.py, tests/application/test_agent_run_probe_opencode.py, tests/application/test_agent_run_probe_project_agent.py, tests/application/test_container_environment.py, tests/application/test_container_environment_extra.py, tests/application/test_container_environment_take.py, tests/application/test_container_stage_checks.py, tests/application/test_cost_image.py, tests/application/test_cost_instance.py, tests/application/test_cost_record_machine_measures.py, tests/application/test_costs.py, tests/application/test_costs_denials.py, tests/application/test_costs_died_text.py, tests/application/test_costs_login.py, tests/application/test_costs_model_seconds.py, tests/application/test_costs_provider_limit.py, tests/application/test_interfaces.py, tests/application/test_left_out_stage.py, tests/application/test_machine_checks_runtime.py, tests/application/test_no_branch_check.py, tests/application/test_no_state_refusals.py, tests/application/test_patient_runs.py, tests/application/test_pipeline_loading_project_agents.py, tests/application/test_preflight.py, tests/application/test_preflight_stop_detail.py, tests/application/test_probe_nested_repository.py, tests/application/test_project_agents.py, tests/application/test_push_retry.py, tests/application/test_request_working_directory.py, tests/application/test_sealed_runs_runner.py, tests/application/test_stage_died_line.py, tests/application/test_stage_environment_calls.py, tests/application/test_stage_finish.py, tests/application/test_stage_finish_causes.py, tests/application/test_stage_known_results.py, tests/application/test_stage_launch.py, tests/application/test_stage_nested_repository.py, tests/application/test_stage_on_container_fakes.py, tests/application/test_stage_provider_limit.py, tests/application/test_stage_run.py, tests/application/test_stage_run_acceptance.py, tests/application/test_stage_time_limited_report.py, tests/application/test_stage_tool_uses.py, tests/application/test_stage_transcripts.py, tests/application/test_stall_container.py, tests/application/test_stall_edges.py, tests/application/test_stall_environment.py, tests/application/test_stall_labels.py, tests/application/test_stall_reasons_recorded.py, tests/application/test_stalls.py, tests/application/test_task.py, tests/application/test_task_acceptance.py, tests/application/test_tick_agent_definition.py, tests/application/test_tick_preflight.py, tests/application/test_tick_project_agent.py, tests/application/test_tokens.py, tests/application/test_write_paths.py, tests/application/test_write_paths_guard.py, tests/bill_support.py, tests/claude_resume_support.py, tests/conftest.py, tests/container_extra_support.py, tests/container_support.py, tests/cost_image_support.py, tests/cost_records_support.py, tests/domain/test_agent_entry.py, tests/domain/test_agent_environment.py, tests/domain/test_agent_runs.py, tests/domain/test_agent_runs_session.py, tests/domain/test_bills.py, tests/domain/test_cost_records.py, tests/domain/test_decisions.py, tests/domain/test_died_runs.py, tests/domain/test_nested_claude_paths.py, tests/domain/test_opencode_provider.py, tests/domain/test_project_agent_paths.py, tests/domain/test_prompts.py, tests/domain/test_provider_limit_wait.py, tests/domain/test_provider_limits.py, tests/domain/test_provider_limits_one_second.py, tests/domain/test_resumed_result.py, tests/domain/test_resumed_result_time_limit.py, tests/domain/test_tokens.py, tests/domain/test_tokens_masked.py, tests/domain/test_tool_uses.py, tests/domain/test_tool_uses_replayed_lines.py, tests/domain/test_write_paths.py, tests/entry/test_refresh_token.py, tests/entry/test_refresh_token_signals.py, tests/entry/test_run.py, tests/entry/test_wiring_acceptance.py, tests/entry/test_wiring_api_login.py, tests/entry/test_wiring_boundaries.py, tests/entry/test_wiring_container_extra.py, tests/entry/test_wiring_environment.py, tests/entry/test_wiring_extras.py, tests/entry/test_wiring_handlers.py, tests/entry/test_wiring_human_handlers.py, tests/entry/test_wiring_image_path.py, tests/entry/test_wiring_login.py, tests/entry/test_wiring_one_environment.py, tests/entry/test_wiring_opencode.py, tests/entry/test_wiring_opencode_provider.py, tests/entry/test_wiring_project_agents.py, tests/entry/test_wiring_provider_limit.py, tests/entry/test_wiring_run.py, tests/entry/test_wiring_stage_environment.py, tests/entry/test_wiring_without_agent_user.py, tests/observing_runtime.py, tests/probe_support.py, tests/proof_support.py, tests/push_retry_support.py, tests/run_layout_support.py, tests/stage_run_support.py, tests/stall_support.py, tests/test_agent_launch_search.py, tests/test_agent_run_request_search.py, tests/test_claude_files.py, tests/test_home_reset_removed.py, tests/test_hook_removed.py, tests/test_hosting_search.py, tests/test_kernel_guard_removed.py, tests/test_leftovers_program_removed.py, tests/test_model_configuration.py, tests/test_no_agent_login.py, tests/test_opencode_runtime_search.py, tests/test_operator_job.py, tests/test_operator_site_example.py, tests/test_removed_layer_names.py, tests/test_second_user_removed.py, tests/test_suite_held_once.py, tests/test_tests_run_under_the_starting_umask.py, tests/test_wrapper_search.py, tests/token_support.py.
8. 2026-11-05 human: Answer of the human:

   **(a).** `pyproject.toml` on `main` now has the three keys at the new paths, `src/factory/agents/adapters/claude_runtime.py`, `opencode_runtime.py` and `oauth_token.py`, with the same rules and comments, beside the old ones (the old keys go after this story's merge). The next stage merges `main` into the branch, so the keys reach it there. The baseline and `CLAUDE.md`'s line follow after the merge, as for the earlier moves.

   End with `tests`, and the tester makes the test changes you listed.
9. factory: started doing as vm.
10. coder: Round 0, after the human's answer (a). The source moves are already on the branch: the four `factory.agents` packages and the 19 modules at `src/factory/agents/<layer>/<name>.py`, with every import under `src/` switched to the new paths. `pyproject.toml` now has the three per-file-ignores keys at the new paths (merged from `main`), and `make lint` is green on the branch. I changed no code in this run.

    As the human asked, I end with `tests`. The tester should make the test changes listed in entry 7, under the leave of feature decision 5:
    1. Rewrite the old `factory.<layer>.<name>` paths of the 19 modules under `tests/`, leaving out `tests/test_areas.py`, to `factory.agents.<layer>.<name>`. Split the mixed `from factory.<layer> import ...` lines that entry 7 names. Then run `ruff check --fix tests` and `ruff format tests`.
    2. Change the three path references to moved test files: `tests/test_no_agent_login.py:11`, `tests/test_suite_held_once.py:123` and `EXEMPT_FILE` in `tests/test_tests_run_under_the_starting_umask.py`.
    3. Create `tests/agents/__init__.py` and `tests/agents/{domain,application,adapters}/__init__.py`. Then move the 55 test modules that entry 7 lists into the same layer folder under `tests/agents/`.

    I have not run `make check` in this run because the test changes are still missing. Entry 7 records it green with those changes in the tree.

    What remains open, as entry 7 and the human's answer say: the old-path lines in `security/duplicates-baseline.txt`, `CLAUDE.md` line 19, and the old `pyproject.toml` keys all wait for the merge. The docs belong to the docs stage.
11. factory: started tests as vm.
12. tester: Mode: the test change the human approved (answer (a) in entry 8; the change list is in the coder's entries 7 and 10, under the leave of feature decision 5). I made exactly the three changes listed. Every test keeps its name and checks the same thing. `tests/test_areas.py` is untouched.

    1. **Import paths.** I ran sed over `tests/`, leaving out `tests/test_areas.py`, with the coder's regex: `factory.<layer>.<name>` for the 19 moved modules became `factory.agents.<layer>.<name>`. That changed 192 files.
       - I rewrote or split the `from factory.<layer> import ...` lines in nine files:
         - `tests/conftest.py`: `podman_runs` stays in `factory.adapters`, `claude_runtime` now comes from `factory.agents.adapters`.
         - `tests/test_second_user_removed.py`: `make_commands` stays, `agent_launch` moves.
         - `tests/test_removed_layer_names.py`: now `from factory.agents.domain import agent_runs, write_paths`.
         - `tests/test_home_reset_removed.py`, `tests/test_leftovers_program_removed.py`, `tests/adapters/test_runtimes_without_wrapper.py`, `tests/adapters/test_opencode_runtime_container.py` and `tests/adapters/test_runtime_podman_timeout_status.py`: now import from `factory.agents.adapters`.
         - `tests/adapters/test_calls_as_the_factory_user.py`: the same, before step 3 moved it to `tests/agents/adapters/`.
       - Then I ran `ruff check --fix tests` and `ruff format tests` (2 files reformatted).
    2. **Path references to moved test files:**
       - `tests/test_no_agent_login.py:11` now reads `/ "agents" / "adapters" /`.
       - `tests/test_suite_held_once.py:123` now names `agents/adapters/test_claude_runtime_no_hook.py`.
       - `EXEMPT_FILE` in `tests/test_tests_run_under_the_starting_umask.py` is now `agents/adapters/test_calls_as_the_factory_user.py`.
       - A grep found no other reference to the old paths of the moved test modules in `tests/`, `src/` or `pyproject.toml`.
    3. **Moved test modules.** I created empty `tests/agents/__init__.py`, `tests/agents/domain/__init__.py`, `tests/agents/application/__init__.py` and `tests/agents/adapters/__init__.py`. Then I moved the 55 test modules of entry 7 with `git mv`: 18 from `tests/domain/`, 1 from `tests/application/` and 36 from `tests/adapters/`, each into the same layer folder under `tests/agents/`.

    Criterion → test mapping is unchanged from entry 5:
    - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer
    - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring
    - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path
    - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved, and tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own
    - criteria 5 and 6: the closing ones, not tested here.

    **Files.**
    - Created: the four `__init__.py` files under `tests/agents/`.
    - Moved: the 55 modules above.
    - Changed, all written by earlier stories (the leave of feature decision 5, which the human's answer confirms): the moved modules, plus the 192 files of step 1, including `tests/conftest.py`, the support modules and the three files of step 2.

    **Run.** One run of `uv run pytest -q` over `tests/test_areas.py`, `tests/agents` and the changed top-level and adapter files:
    - The tail showed only progress dots up to `[100%]`, with no failures shown.
    - No module failed to import.
    - `make lint`: lint: green (0.1 s).
    - I did not run the whole `make test`; the coder's `make check` covers it.

    **Open, as entries 7, 8 and 10 say:**
    - The old paths in `security/duplicates-baseline.txt` and `CLAUDE.md` line 19, and the old `pyproject.toml` keys, wait for the merge.
    - The docs belong to the docs stage.

    `lint`: lint: green (0.1 s)
13. factory: started doing as vm.
14. coder: Round 0, after the tester's test changes (entry 12). I changed no code in this run. The branch already has everything this story needs, and `make check` is green on it as it is: `test: green (125.5 s)`, total coverage 99.26 %, `check: green`. My working tree is clean.

    What was built (committed in the earlier doing runs, entries 7 and 10):
    - `src/factory/agents/__init__.py`, `src/factory/agents/domain/__init__.py`, `src/factory/agents/application/__init__.py` and `src/factory/agents/adapters/__init__.py`, each with a one-line docstring.
    - The 19 modules of the Interface, moved with `git mv` to `src/factory/agents/<layer>/<name>.py`. None remains at its old path under `src/factory/{domain,application,adapters}/`; I checked the folder listings.
    - Every import under `src/` now uses the new paths. The diff against `main` under `src` is 41 files, +77/−68, and only import lines changed.
    - The tester moved 55 test modules to `tests/agents/<layer>/` and rewrote the test imports (entry 12).

    Main choice: I kept S0003's split. The coder moves `src/`, the tester moves and rewrites `tests/`, and `pyproject.toml` came through the human's change on `main` (answer (a), entry 8). I rejected putting `# noqa` in the moved sources, because the per-file-ignores comments forbid it.

    Refactor: the diff is mechanical (moves and import lines), so nothing needed changing.

    Noticed, not touched (open, as entries 7, 8 and 10 say):
    - The old-path lines in `security/duplicates-baseline.txt`.
    - `CLAUDE.md` line 19 still names `factory.adapters.agent_launch`.
    - The old `pyproject.toml` per-file-ignores keys. The human said all three of these wait for the merge.
    - The docs that name old paths belong to the docs stage (criterion 6).

    `check`: check: green
    `duplicates`: duplicates: 12 new, 33 known, 10 gone
15. factory: started review as vm.
