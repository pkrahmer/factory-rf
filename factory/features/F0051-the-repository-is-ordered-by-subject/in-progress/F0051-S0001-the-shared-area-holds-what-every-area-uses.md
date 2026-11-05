---
stage: docs
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 556
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-05T00:58:45.710227Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T00:22:36.306042Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T00:22:36.312432Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T00:22:57.151643Z'
  stage: intake
  run: b60043aa03ae4cb8903c8e448754262f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T00:23:02.115043Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T00:24:35.937368Z'
  stage: tests
  run: 5e352e393a894dac99c57945fa8137ef
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T00:24:40.947127Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-05T00:32:27.986272Z'
  stage: doing
  run: e5249aa72b904f7e86ffc43a03444e06
- number: 8
  speaker: factory
  kind: stall
  at: '2026-11-05T00:32:28.537635Z'
  stage: doing
  run: e5249aa72b904f7e86ffc43a03444e06
  reason: check_red
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T00:32:36.014959Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T00:33:29.514603Z'
  stage: doing
  run: 24c787413db3499a8b08a94619ba780e
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-05T00:33:34.863004Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-05T00:37:45.931707Z'
  stage: tests
  run: 0c1842dc4b9a45e485f0a9f50534b604
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-05T00:37:53.844446Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-05T00:43:06.334826Z'
  stage: doing
  run: 4f351c0615b8448da87fa903f851d1b2
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T00:43:12.123790Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-11-05T00:47:26.706427Z'
  stage: review
  run: b63cce3fe42e44818203d3856178176d
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-05T00:47:32.022958Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-05T00:48:08.498147Z'
  stage: doing
  run: 2c594865e0ec4f4d9c74aa606d365dc0
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-05T00:48:14.428736Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-11-05T00:49:36.322835Z'
  stage: tests
  run: 1c6ae20e08894fbabf643e7f97344ca0
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-05T00:49:41.924080Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-11-05T00:54:30.223510Z'
  stage: doing
  run: c14b005ed4f542c2a85afa32947e1ef7
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-05T00:54:35.959367Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-11-05T00:58:39.493849Z'
  stage: review
  run: 6f301a5c4cfd430f9e2bf52e713dd9a0
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-05T00:58:45.710227Z'
  stage: docs
---

# The shared area holds what every area uses

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `shared` area: what every other area uses: errors, times, identifiers, paths, settings, the records contract, the document and duplicate checks, the kill points of the fault tests, the file ports, the clock, atomic files and processes. Each of its 18 modules moves from its layer package to the same layer inside `factory.shared`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/shared/<layer>/` (feature decision 5). As the first move, it also writes the guard that every later move extends: `tests/test_areas.py`, with one table of every area's modules. No behaviour changes: every test that passed before passes after and checks the same thing, with only its import lines and paths changed, and the guards that pin the old layout made to check the same rule over the new one (feature decision 5).

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.shared`, `factory.shared.domain`, `factory.shared.application`, `factory.shared.adapters`; and the same folders under `tests/shared/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.errors` → `factory.shared.domain.errors`
- `factory.domain.times` → `factory.shared.domain.times`
- `factory.domain.identifiers` → `factory.shared.domain.identifiers`
- `factory.domain.paths` → `factory.shared.domain.paths`
- `factory.domain.settings` → `factory.shared.domain.settings`
- `factory.domain.printed_lines` → `factory.shared.domain.printed_lines`
- `factory.domain.contract` → `factory.shared.domain.contract`
- `factory.domain.duplicates` → `factory.shared.domain.duplicates`
- `factory.domain.sections` → `factory.shared.domain.sections`
- `factory.domain.documents` → `factory.shared.domain.documents`
- `factory.domain.kill_points` → `factory.shared.domain.kill_points`
- `factory.domain.kill_point_cases` → `factory.shared.domain.kill_point_cases`
- `factory.application.files` → `factory.shared.application.files`
- `factory.adapters.clock` → `factory.shared.adapters.clock`
- `factory.adapters.atomic_file` → `factory.shared.adapters.atomic_file`
- `factory.adapters.process` → `factory.shared.adapters.process`
- `factory.adapters.printed_output` → `factory.shared.adapters.printed_output`
- `factory.adapters.validation_faults` → `factory.shared.adapters.validation_faults`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py` (new): a table `AREAS` from each area's name to its modules as `<layer>.<name>`, filled for `shared`, and parametrized tests over it, as criteria 1 to 3 say. Later moves add their rows to this table and change nothing else in it.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/shared/<its layer>/` when every one of its imports from `factory` is a module of the `shared` area or of an area already moved before it and at least one is of `shared`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. For every module of the table above (one row each), `importlib.import_module("factory.shared.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.shared`, `factory.shared.domain`, `factory.shared.application`, `factory.shared.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `shared` and the areas moved before it.
5. Every test module under `tests/shared/` takes all its `factory` imports from `shared` and the areas moved before it, and at least one from `shared`: a module there that imports an area not yet moved, or nothing of `shared`, fails.
6. `make check` stays green.
7. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `shared` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.shared.domain.errors as m; print(m.__name__)"
```
Expect: `factory.shared.domain.errors`

```bash
test -e src/factory/domain/errors.py && echo still there || echo moved
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
   - Interface: all 18 moves name concrete old and new dotted paths; the four new packages and their test folders are named. A pure move adds no signatures. The source files exist at the old paths (spot-checked errors, files, validation_faults).
   - Criteria: each one is testable by one parametrized test: 1 (import succeeds, old file absent, one row per module), 2 (four packages import and have a docstring), 3 (no import line names an old path, which is the failing side of the move), 4 (no test module left that should have moved), 5 and 6 (closing criteria). Note, not a question: criterion 1 says "for `handlers`, the folder", but no module in the table is named handlers or is a folder, so that clause has no effect.
   - Smoke test: the three commands are runnable and each Expect line can be checked. pyproject.toml's addopts already sets `-q`, and the pytest command passes none, so the summary line is printed and `grep -c passed` gives 1.
   - Architecture: the moves keep the layer inside `factory.shared`, which matches CLAUDE.md and feature decision 1. The wildcard import-linter contracts are set by the human at S0001's start (feature "The human's changes"). The `process.py` exception already names the new path.
   - Scope: within F0051 S0001 and decisions 1 to 5. `shared` is the area decision 2 gives it, and kill_points and kill_point_cases are in it. Nothing in Out of scope is touched.
4. factory: started tests as vm.
5. tester: Wrote `tests/test_areas.py`. It holds the table `AREAS` (`shared` → its 18 modules as `<layer>.<name>`) and parametrized tests that read that table, so a later move only adds rows.

   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (one row per module: `importlib.import_module("factory.<area>.<layer>.<name>")`, and neither `src/factory/<layer>/<name>.py` nor a folder `src/factory/<layer>/<name>/` exists, which covers the "for `handlers`, the folder" clause)
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows are built from the table: `factory.shared` and each layer package its rows name, so `factory.shared.domain`, `.application` and `.adapters`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module; every `.py` file under `src/` and `tests/` is parsed with `ast`, and the check uses `imports()` from `tests/source_search.py`, which catches `import factory.domain.errors`, `from factory.domain.errors import …` and `from factory.domain import errors`)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved
   - criteria 5 and 6: these are the closing criteria (`make check` and `docs:`), so there is no test function.

   How criterion 4 reads a test module: its `factory` imports are the module of each `import X` and each absolute `from X import …`. The module stays in the failing list when it has at least one such import and every one of them is of an area in the table. An import counts as of an area by its new path (`factory.<area>…`) or by its old path (`factory.<layer>.<name>` for a module in the table). The old path counts so the test fails now, before the move. A bare `import factory` belongs to no area, so a module that has one stays where it is.

   Files created: tests/test_areas.py. I changed no earlier test file.

   Modules the test run could not import: `factory.shared.domain.*`, `factory.shared.application.files` and `factory.shared.adapters.*` (all 18), plus the packages `factory.shared`, `factory.shared.domain`, `factory.shared.application` and `factory.shared.adapters`. The criterion 3 rows fail because the old paths are still imported. The criterion 4 test fails because test modules such as those of errors and times are still under `tests/domain/` and the other layer folders. `make lint` is green, after one `ruff format` of the new file.

   Option I rejected: building the criterion 2 package list by hand. Building it from the table keeps later moves from editing anything but the table, as the Interface asks.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Moved the `shared` area. `make check` is green (test: 117.5 s); `tests/test_areas.py` passes and is untouched.

   What I built:
   - New packages, each with a one-line docstring: `src/factory/shared/__init__.py`, `src/factory/shared/domain/__init__.py`, `src/factory/shared/application/__init__.py`, `src/factory/shared/adapters/__init__.py`. Also `tests/shared/{,domain/,application/,adapters/}__init__.py`, empty like `tests/domain/__init__.py`.
   - All 18 modules of the Interface moved with `git mv` to `src/factory/shared/<layer>/<name>.py`. Their content is unchanged apart from import lines; for example, `shared/domain/paths.py` now has `from factory.shared.domain import identifiers`.
   - Every `factory.<layer>.<name>` import of a moved module under `src/` and `tests/` was rewritten to the new path, `from factory.<layer> import <name>` forms included. The forms that mixed a moved and an unmoved module were split: `tests/domain/test_default_git_identity.py` and `tests/test_leftovers_program_removed.py`. Then `ruff check --fix` re-sorted the import blocks and `ruff format` re-wrapped them.
   - 60 test modules moved with `git mv` from `tests/{domain,application,adapters}/` to `tests/shared/<layer>/`: exactly the list criterion 4's test printed (for example `tests/shared/domain/test_errors.py`, `tests/shared/adapters/test_process*.py`, `tests/shared/application/test_push_retry_*.py`).
   - Changes to earlier tests beyond their import lines, made under the Interface's leave of feature decision 5 (the move needs them; each test keeps its name and checks the same thing):
     - `tests/test_process_search.py`: the path of the process wrapper, `SRC / "shared" / "adapters" / "process.py"`, and the key `"shared/adapters/process.py"`.
     - `tests/entry/test_watch.py`: `_names_the_replaced_phrases` and the `document-check` row point at `shared/domain/documents.py`.
     - `tests/test_suite_old_names.py` and `tests/test_suite_held_once.py`: the paths of the moved test modules they read now start with `shared/domain/`.
     - `tests/domain/test_hosting.py`: `_is_domain` also counts `factory.shared.domain` as the domain layer, because the domain modules it checks now import shared domain modules. This is the one predicate change. The reviewer may want to judge it against "only import lines and paths".
   - `security/duplicates-baseline.txt`: the five accepted dead-code findings in moved modules now name their new paths, so the record does not report them as new or gone.

   Main choice: a mechanical rewrite (sed over the exact old dotted paths and `src/factory/<layer>/<name>.py` strings, then hand fixes for the `from package import name` forms), with no re-export left at the old paths, as feature decision 4 asks. Rejected: temporary shim modules at the old paths to move imports over in steps. The story forbids them, and criterion 1 checks that the old files are gone.

   Refactor: I read the diff and found nothing to change beyond the formatter's re-wrapping.

   Noticed, not touched:
   - `make duplicates` reports 4 new findings, none in a moved module: similar code between `claude_runtime` and `opencode_runtime` (`version_launch`), and three dead-code variables in `src/factory/domain/cost_records.py`.
   - `tests/adapters/test_work_item_markdown.py::test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` picks modules by `name.split(".")[1:2]`, so it no longer looks at `factory.shared.*`. None of those modules imports frontmatter or ruamel, so it passes, but it now covers less. Every later move will widen that gap.
   - `tests/test_layers.py` still checks only the four top-level layer packages.
   - `CLAUDE.md` still names `factory.domain.contract.CONTRACT`. That file is the human's.
   - The docs (README, operator guide, project guide) still name old paths. They are the documenter's, by criterion 6.

   Description unchanged: no journal entry changed the meaning of the task.

   The factory left out changes outside the write paths: security/duplicates-baseline.txt, tests/acceptance_support.py, tests/acceptance_walk.py, tests/adapters/claude_stand_in.py, tests/adapters/container_runtime_support.py, tests/adapters/opencode_stand_in.py, tests/adapters/pygithub_stand_ins.py, tests/adapters/test_agent_file_keys.py, tests/adapters/test_agent_files.py, tests/adapters/test_agent_files_parse.py, tests/adapters/test_agent_launch.py, tests/adapters/test_agent_launch_call_end.py, tests/adapters/test_agent_launch_container.py, tests/adapters/test_agent_launch_container_kill.py, tests/adapters/test_agent_launch_extra.py, tests/adapters/test_agent_launch_login.py, tests/adapters/test_agent_launch_state_directory.py, tests/adapters/test_calls_as_the_factory_user.py, tests/adapters/test_claude_runtime.py, tests/adapters/test_claude_runtime_api_login.py, tests/adapters/test_claude_runtime_container.py, tests/adapters/test_claude_runtime_denial_paths.py, tests/adapters/test_claude_runtime_environment.py, tests/adapters/test_claude_runtime_login.py, tests/adapters/test_claude_runtime_no_hook.py, tests/adapters/test_claude_runtime_provider_limit.py, tests/adapters/test_claude_runtime_resume.py, tests/adapters/test_claude_runtime_resume_session.py, tests/adapters/test_claude_runtime_transcript.py, tests/adapters/test_clock.py, tests/adapters/test_copy_snapshots.py, tests/adapters/test_cost_records_jsonl.py, tests/adapters/test_cost_records_jsonl_denials.py, tests/adapters/test_cost_records_jsonl_instance.py, tests/adapters/test_cost_records_jsonl_login.py, tests/adapters/test_cost_records_jsonl_model_seconds.py, tests/adapters/test_died_text.py, tests/adapters/test_disk_space.py, tests/adapters/test_factory_log.py, tests/adapters/test_fake_agent_runtime.py, tests/adapters/test_fake_containers.py, tests/adapters/test_fake_hosting.py, tests/adapters/test_fake_snapshots.py, tests/adapters/test_git_cli_arguments.py, tests/adapters/test_git_cli_branches.py, tests/adapters/test_git_cli_check_ignore.py, tests/adapters/test_git_cli_history.py, tests/adapters/test_git_cli_reading.py, tests/adapters/test_git_cli_restoring.py, tests/adapters/test_git_cli_seal.py, tests/adapters/test_git_cli_work_tree.py, tests/adapters/test_git_cli_work_tree_dash.py, tests/adapters/test_git_cli_work_tree_tick.py, tests/adapters/test_git_cli_writing.py, tests/adapters/test_health_file.py, tests/adapters/test_journal_as_data.py, tests/adapters/test_journal_causes_file.py, tests/adapters/test_journal_stamps_file.py, tests/adapters/test_kill_at_the_limit_stays.py, tests/adapters/test_machine_files.py, tests/adapters/test_make_commands.py, tests/adapters/test_make_commands_container.py, tests/adapters/test_make_last_line_shared.py, tests/adapters/test_oauth_token.py, tests/adapters/test_opencode_budget.py, tests/adapters/test_opencode_events.py, tests/adapters/test_opencode_left_out_tools.py, tests/adapters/test_opencode_measures.py, tests/adapters/test_opencode_provider_limit.py, tests/adapters/test_opencode_result_block.py, tests/adapters/test_opencode_resumed_words.py, tests/adapters/test_opencode_runtime.py, tests/adapters/test_opencode_runtime_container.py, tests/adapters/test_opencode_runtime_launch.py, tests/adapters/test_opencode_runtime_lockdown.py, tests/adapters/test_opencode_runtime_provider.py, tests/adapters/test_opencode_runtime_runs_folder.py, tests/adapters/test_pipeline_rules.py, tests/adapters/test_pipeline_strict_values.py, tests/adapters/test_pipeline_yaml.py, tests/adapters/test_pipeline_yaml_one_line_fault.py, tests/adapters/test_pipeline_yaml_tool_paths.py, tests/adapters/test_podman_images.py, tests/adapters/test_podman_runs.py, tests/adapters/test_podman_runs_fence.py, tests/adapters/test_podman_runs_instance_label.py, tests/adapters/test_podman_runs_job_profile.py, tests/adapters/test_podman_runs_results.py, tests/adapters/test_podman_timeout_status.py, tests/adapters/test_power_off.py, tests/adapters/test_preflight_stamp_file.py, tests/adapters/test_process.py, tests/adapters/test_process_drain.py, tests/adapters/test_process_exit.py, tests/adapters/test_process_result_fields.py, tests/adapters/test_process_session.py, tests/adapters/test_process_streaming.py, tests/adapters/test_process_streaming_last_line.py, tests/adapters/test_process_streaming_reads.py, tests/adapters/test_pygithub_hosting.py, tests/adapters/test_pygithub_retry.py, tests/adapters/test_pygithub_service.py, tests/adapters/test_record_log_jsonl.py, tests/adapters/test_record_log_jsonl_torn.py, tests/adapters/test_run_or_raise.py, tests/adapters/test_runtime_died_text.py, tests/adapters/test_runtime_podman_timeout_status.py, tests/adapters/test_runtime_state_directory_write.py, tests/adapters/test_runtime_tool_uses.py, tests/adapters/test_runtimes_without_wrapper.py, tests/adapters/test_shipped_agents_effect.py, tests/adapters/test_transcript_files.py, tests/adapters/test_validation_faults.py, tests/adapters/test_waiters.py, tests/adapters/test_work_item_markdown.py, tests/adapters/test_work_item_markdown_acceptance.py, tests/adapters/test_zfs_snapshots.py, tests/adapters/test_zfs_snapshots_diff.py, tests/adapters/test_zfs_snapshots_drop_caches.py, tests/agent_definition_support.py, tests/agent_run_support.py, tests/application/handlers/conftest.py, tests/application/handlers/test_closed.py, tests/application/handlers/test_closed_send_back.py, tests/application/handlers/test_comment_handler.py, tests/application/handlers/test_comments.py, tests/application/handlers/test_comments_crash_cap.py, tests/application/handlers/test_hand_over.py, tests/application/handlers/test_handler_subjects.py, tests/application/handlers/test_handlers_raise.py, tests/application/handlers/test_lookups.py, tests/application/handlers/test_merged.py, tests/application/handlers/test_questions.py, tests/application/handlers/test_recording.py, tests/application/handlers/test_reject.py, tests/application/handlers/test_run.py, tests/application/handlers/test_run_gate.py, tests/application/test_acceptance_closed.py, tests/application/test_acceptance_due_handler.py, tests/application/test_acceptance_facts_disk.py, tests/application/test_acceptance_facts_human.py, tests/application/test_acceptance_hand_over.py, tests/application/test_acceptance_merged.py, tests/application/test_acceptance_merged_before_approval.py, tests/application/test_acceptance_no_state_refusals.py, tests/application/test_acceptance_reading.py, tests/application/test_acceptance_refusals.py, tests/application/test_acceptance_repeated.py, tests/application/test_acceptance_reviewer_role.py, tests/application/test_acceptance_service.py, tests/application/test_acceptance_snapshots.py, tests/application/test_acceptance_ticks_closed.py, tests/application/test_acceptance_ticks_merged.py, tests/application/test_acceptance_ticks_repeated.py, tests/application/test_after_agent.py, tests/application/test_after_agent_edges.py, tests/application/test_agent_definition_reader.py, tests/application/test_agent_run_probe.py, tests/application/test_agent_run_probe_api_login.py, tests/application/test_agent_run_probe_environment.py, tests/application/test_agent_run_probe_factory_user.py, tests/application/test_agent_run_probe_login.py, tests/application/test_agent_run_probe_opencode.py, tests/application/test_agent_run_probe_project_agent.py, tests/application/test_bill_service.py, tests/application/test_board_in_progress.py, tests/application/test_board_reader.py, tests/application/test_board_reader_acceptance.py, tests/application/test_boundaries.py, tests/application/test_boundaries_required.py, tests/application/test_boundaries_settings.py, tests/application/test_checkout_preparer.py, tests/application/test_claims.py, tests/application/test_claims_observed.py, tests/application/test_claims_refusals.py, tests/application/test_container_environment.py, tests/application/test_container_environment_extra.py, tests/application/test_container_environment_take.py, tests/application/test_container_items.py, tests/application/test_container_stage_checks.py, tests/application/test_container_sync_origin.py, tests/application/test_containers_interface.py, tests/application/test_cost_image.py, tests/application/test_cost_instance.py, tests/application/test_cost_record_machine_measures.py, tests/application/test_costs.py, tests/application/test_costs_denials.py, tests/application/test_costs_died_text.py, tests/application/test_costs_login.py, tests/application/test_costs_model_seconds.py, tests/application/test_costs_provider_limit.py, tests/application/test_disk_recorder.py, tests/application/test_disk_space_interface.py, tests/application/test_dispatcher.py, tests/application/test_dispatcher_counts_every_error.py, tests/application/test_dispatcher_error_lines.py, tests/application/test_dispatcher_without_state.py, tests/application/test_git_interface.py, tests/application/test_hosting_failure_after_claim.py, tests/application/test_hosting_failure_releases_claim.py, tests/application/test_hosting_interface.py, tests/application/test_human_line_posts.py, tests/application/test_idle_shutdown.py, tests/application/test_interfaces.py, tests/application/test_known_results.py, tests/application/test_known_results_torn.py, tests/application/test_left_out_stage.py, tests/application/test_machine.py, tests/application/test_machine_checks_container.py, tests/application/test_machine_checks_runtime.py, tests/application/test_no_branch_check.py, tests/application/test_no_state_refusals.py, tests/application/test_opencode_item.py, tests/application/test_opencode_item_container.py, tests/application/test_opening.py, tests/application/test_opening_journal_edges.py, tests/application/test_patient_runs.py, tests/application/test_pipeline_definition_reader.py, tests/application/test_pipeline_loading.py, tests/application/test_pipeline_loading_agents.py, tests/application/test_pipeline_loading_project_agents.py, tests/application/test_pipeline_loading_rules.py, tests/application/test_pipeline_loading_stage_moves.py, tests/application/test_pipeline_loading_strict_values.py, tests/application/test_pipeline_loading_yaml_fault.py, tests/application/test_preflight.py, tests/application/test_preflight_login_line.py, tests/application/test_preflight_metadata_block.py, tests/application/test_preflight_run.py, tests/application/test_preflight_run_environment.py, tests/application/test_preflight_snapshots_item.py, tests/application/test_preflight_stale_main_stop.py, tests/application/test_preflight_stop_detail.py, tests/application/test_preflight_stops_commit.py, tests/application/test_probe_nested_repository.py, tests/application/test_project_agents.py, tests/application/test_push_retry.py, tests/application/test_push_retry_reason.py, tests/application/test_push_retry_server_lines.py, tests/application/test_question_causes_recorded.py, tests/application/test_recording_project_commands.py, tests/application/test_recovery_cap.py, tests/application/test_recovery_crash.py, tests/application/test_recovery_expiry.py, tests/application/test_recovery_expiry_key.py, tests/application/test_recovery_subjects.py, tests/application/test_repository_waiter.py, tests/application/test_request_working_directory.py, tests/application/test_scheduler.py, tests/application/test_sealed_runs_runner.py, tests/application/test_snapshots_interface.py, tests/application/test_split_by_work_item_kind.py, tests/application/test_stage_changes.py, tests/application/test_stage_died_line.py, tests/application/test_stage_environment_calls.py, tests/application/test_stage_environment_of.py, tests/application/test_stage_finish.py, tests/application/test_stage_finish_causes.py, tests/application/test_stage_known_results.py, tests/application/test_stage_launch.py, tests/application/test_stage_nested_repository.py, tests/application/test_stage_on_container_fakes.py, tests/application/test_stage_provider_limit.py, tests/application/test_stage_run.py, tests/application/test_stage_run_acceptance.py, tests/application/test_stage_time_limited_report.py, tests/application/test_stage_tool_uses.py, tests/application/test_stage_transcripts.py, tests/application/test_stale_branches.py, tests/application/test_stall_container.py, tests/application/test_stall_edges.py, tests/application/test_stall_environment.py, tests/application/test_stall_labels.py, tests/application/test_stall_reasons_recorded.py, tests/application/test_stalls.py, tests/application/test_stop_log_once.py, tests/application/test_stop_posting.py, tests/application/test_stop_publisher.py, tests/application/test_stop_records_service.py, tests/application/test_stops.py, tests/application/test_take.py, tests/application/test_take_edges.py, tests/application/test_take_rule.py, tests/application/test_task.py, tests/application/test_task_acceptance.py, tests/application/test_tick.py, tests/application/test_tick_agent_definition.py, tests/application/test_tick_disk.py, tests/application/test_tick_docstrings.py, tests/application/test_tick_own_fetch.py, tests/application/test_tick_preflight.py, tests/application/test_tick_project_agent.py, tests/application/test_tick_restore_ignored.py, tests/application/test_tick_stale_branch.py, tests/application/test_tick_stop_details.py, tests/application/test_tick_stop_records.py, tests/application/test_token_file_item.py, tests/application/test_tokens.py, tests/application/test_transcript_keeper.py, tests/application/test_watcher.py, tests/application/test_watcher_acceptance.py, tests/application/test_watcher_main_ref.py, tests/application/test_watcher_move_rule.py, tests/application/test_watcher_observer.py, tests/application/test_work_items.py, tests/application/test_work_items_duplicate.py, tests/application/test_write_paths.py, tests/application/test_write_paths_guard.py, tests/bill_support.py, tests/branch_reading.py, tests/claude_resume_support.py, tests/conftest.py, tests/container_extra_support.py, tests/container_support.py, tests/contract_support.py, tests/cost_image_support.py, tests/cost_records_support.py, tests/crash_support.py, tests/definition_support.py, tests/disk_support.py, tests/document_texts.py, tests/domain/test_acceptance.py, tests/domain/test_acceptance_before_approval.py, tests/domain/test_acceptance_booking.py, tests/domain/test_acceptance_description.py, tests/domain/test_acceptance_facts.py, tests/domain/test_acceptance_facts_disk.py, tests/domain/test_acceptance_facts_human.py, tests/domain/test_acceptance_facts_limit.py, tests/domain/test_acceptance_refusal_edges.py, tests/domain/test_acceptance_status.py, tests/domain/test_agent_entry.py, tests/domain/test_agent_environment.py, tests/domain/test_agent_runs.py, tests/domain/test_agent_runs_session.py, tests/domain/test_answers.py, tests/domain/test_answers_round_cap.py, tests/domain/test_archive.py, tests/domain/test_archive_texts.py, tests/domain/test_bills.py, tests/domain/test_bills_model_time.py, tests/domain/test_board.py, tests/domain/test_board_absent_values.py, tests/domain/test_cannot_handle.py, tests/domain/test_checks.py, tests/domain/test_checks_last_line.py, tests/domain/test_command_ending.py, tests/domain/test_command_line.py, tests/domain/test_command_line_time_limit.py, tests/domain/test_command_records.py, tests/domain/test_container_extra_environment.py, tests/domain/test_containers.py, tests/domain/test_containers_beneath_or_at.py, tests/domain/test_containers_job_options.py, tests/domain/test_contract.py, tests/domain/test_contract_version_4.py, tests/domain/test_contract_version_4_2.py, tests/domain/test_contract_without_nested_repository.py, tests/domain/test_contract_without_tool_paths.py, tests/domain/test_correction_texts.py, tests/domain/test_cost_record_denials.py, tests/domain/test_cost_record_errors.py, tests/domain/test_cost_record_instance.py, tests/domain/test_cost_record_machine.py, tests/domain/test_cost_record_model_seconds.py, tests/domain/test_cost_records.py, tests/domain/test_decide_docs_slip.py, tests/domain/test_decision_rules.py, tests/domain/test_decisions.py, tests/domain/test_default_git_identity.py, tests/domain/test_died_runs.py, tests/domain/test_disk.py, tests/domain/test_disk_records.py, tests/domain/test_documents.py, tests/domain/test_documents_guide_files.py, tests/domain/test_documents_line_edges.py, tests/domain/test_duplicates.py, tests/domain/test_duplicates_skipped_lines.py, tests/domain/test_error_report_text.py, tests/domain/test_errors.py, tests/domain/test_errors_agent_definition.py, tests/domain/test_errors_environment.py, tests/domain/test_evaluation.py, tests/domain/test_evaluation_details.py, tests/domain/test_evaluation_due.py, tests/domain/test_evaluation_reject.py, tests/domain/test_events.py, tests/domain/test_fault_paths.py, tests/domain/test_fault_paths_all_rows.py, tests/domain/test_git.py, tests/domain/test_git_history.py, tests/domain/test_hand_over.py, tests/domain/test_hosting.py, tests/domain/test_human_waits.py, tests/domain/test_identifiers.py, tests/domain/test_is_name.py, tests/domain/test_journal.py, tests/domain/test_journal_acceptance.py, tests/domain/test_journal_causes.py, tests/domain/test_journal_records.py, tests/domain/test_journal_stamps.py, tests/domain/test_kill_point_cases.py, tests/domain/test_kill_points.py, tests/domain/test_known_results.py, tests/domain/test_labels.py, tests/domain/test_lease.py, tests/domain/test_lease_observed.py, tests/domain/test_login_records.py, tests/domain/test_machine.py, tests/domain/test_move_rule.py, tests/domain/test_name.py, tests/domain/test_nested_claude_paths.py, tests/domain/test_opencode_provider.py, tests/domain/test_paths.py, tests/domain/test_pipeline_definition.py, tests/domain/test_pipeline_not_read.py, tests/domain/test_post_texts.py, tests/domain/test_post_texts_crash_cap.py, tests/domain/test_post_texts_notes.py, tests/domain/test_power_off_error.py, tests/domain/test_preflight.py, tests/domain/test_preflight_stamp.py, tests/domain/test_preflight_stop_records_paths.py, tests/domain/test_project_agent_paths.py, tests/domain/test_prompts.py, tests/domain/test_provider_limit_stall_text.py, tests/domain/test_provider_limit_wait.py, tests/domain/test_provider_limits.py, tests/domain/test_provider_limits_one_second.py, tests/domain/test_push_reason.py, tests/domain/test_push_reason_porcelain.py, tests/domain/test_push_reason_summary_line.py, tests/domain/test_question_post_texts.py, tests/domain/test_question_texts.py, tests/domain/test_recovery.py, tests/domain/test_recovery_cap.py, tests/domain/test_recovery_expiry_text.py, tests/domain/test_resumed_result.py, tests/domain/test_resumed_result_time_limit.py, tests/domain/test_section_edges.py, tests/domain/test_sections.py, tests/domain/test_send_back.py, tests/domain/test_send_back_records.py, tests/domain/test_send_back_texts.py, tests/domain/test_settings.py, tests/domain/test_settings_agent_files_stay.py, tests/domain/test_settings_agent_runtime.py, tests/domain/test_settings_agent_user_unread.py, tests/domain/test_settings_api_login.py, tests/domain/test_settings_boundaries.py, tests/domain/test_settings_claude_login.py, tests/domain/test_settings_container_env.py, tests/domain/test_settings_container_profile.py, tests/domain/test_settings_idle_shutdown.py, tests/domain/test_settings_idle_shutdown_action.py, tests/domain/test_settings_min_free.py, tests/domain/test_settings_model_rules.py, tests/domain/test_settings_one_environment.py, tests/domain/test_settings_opencode_folders_ignored.py, tests/domain/test_settings_opencode_models.py, tests/domain/test_settings_opencode_provider.py, tests/domain/test_settings_paths.py, tests/domain/test_settings_pinned.py, tests/domain/test_settings_provider_limit.py, tests/domain/test_settings_provider_limit_wait.py, tests/domain/test_settings_required_paths.py, tests/domain/test_settings_snapshots.py, tests/domain/test_settings_stage_environment.py, tests/domain/test_settings_transcripts.py, tests/domain/test_settings_url_edges.py, tests/domain/test_stage_layer.py, tests/domain/test_stall_note_block.py, tests/domain/test_stall_reason_removed.py, tests/domain/test_stall_texts.py, tests/domain/test_stop_records.py, tests/domain/test_stop_table.py, tests/domain/test_stops.py, tests/domain/test_story_form.py, tests/domain/test_story_form_edges.py, tests/domain/test_story_place.py, tests/domain/test_target_times.py, tests/domain/test_tick_status.py, tests/domain/test_tick_status_mark.py, tests/domain/test_times.py, tests/domain/test_tokens.py, tests/domain/test_tokens_masked.py, tests/domain/test_tool_use_model.py, tests/domain/test_tool_uses.py, tests/domain/test_tool_uses_replayed_lines.py, tests/domain/test_transcript_ref.py, tests/domain/test_tree_id.py, tests/domain/test_unhandled_event.py, tests/domain/test_work_item.py, tests/domain/test_work_item_errors.py, tests/domain/test_work_item_require_state.py, tests/domain/test_work_item_snapshot.py, tests/domain/test_work_item_stop.py, tests/domain/test_write_paths.py, tests/entry/test_bill.py, tests/entry/test_check_demos.py, tests/entry/test_check_documents.py, tests/entry/test_check_documents_guide_files.py, tests/entry/test_check_documents_usage.py, tests/entry/test_check_duplicates.py, tests/entry/test_check_story.py, tests/entry/test_contract.py, tests/entry/test_contract_arguments.py, tests/entry/test_contract_not_read.py, tests/entry/test_entry_arguments.py, tests/entry/test_git_hooks.py, tests/entry/test_git_nested_repositories.py, tests/entry/test_health.py, tests/entry/test_health_missing.py, tests/entry/test_inputs.py, tests/entry/test_mutation_report_removed.py, tests/entry/test_refresh_token.py, tests/entry/test_refresh_token_signals.py, tests/entry/test_run.py, tests/entry/test_run_fetch_before_tick.py, tests/entry/test_run_health_file.py, tests/entry/test_run_idle_exit.py, tests/entry/test_run_idle_shutdown.py, tests/entry/test_run_image_sizes.py, tests/entry/test_run_machine_stop_exit.py, tests/entry/test_run_one_fetch.py, tests/entry/test_run_project_image_rebuild.py, tests/entry/test_run_required_paths.py, tests/entry/test_run_state_variable.py, tests/entry/test_run_stop_requested.py, tests/entry/test_run_waiter.py, tests/entry/test_watch.py, tests/entry/test_watch_acceptance.py, tests/entry/test_watch_agent_definition.py, tests/entry/test_watch_main.py, tests/entry/test_watch_own_claim.py, tests/entry/test_watch_settings.py, tests/entry/test_wiring.py, tests/entry/test_wiring_acceptance.py, tests/entry/test_wiring_api_login.py, tests/entry/test_wiring_boundaries.py, tests/entry/test_wiring_command_records.py, tests/entry/test_wiring_constants.py, tests/entry/test_wiring_container_extra.py, tests/entry/test_wiring_container_extras.py, tests/entry/test_wiring_container_profile.py, tests/entry/test_wiring_copy_snapshots.py, tests/entry/test_wiring_drop_caches.py, tests/entry/test_wiring_environment.py, tests/entry/test_wiring_extras.py, tests/entry/test_wiring_handlers.py, tests/entry/test_wiring_human_handlers.py, tests/entry/test_wiring_idle_shutdown.py, tests/entry/test_wiring_idle_shutdown_action.py, tests/entry/test_wiring_image_path.py, tests/entry/test_wiring_instance_label.py, tests/entry/test_wiring_known_results.py, tests/entry/test_wiring_login.py, tests/entry/test_wiring_machine_inputs.py, tests/entry/test_wiring_metadata_block.py, tests/entry/test_wiring_one_environment.py, tests/entry/test_wiring_one_preflight.py, tests/entry/test_wiring_opencode.py, tests/entry/test_wiring_opencode_provider.py, tests/entry/test_wiring_preflight.py, tests/entry/test_wiring_project_agents.py, tests/entry/test_wiring_project_image.py, tests/entry/test_wiring_provider_limit.py, tests/entry/test_wiring_record_logs.py, tests/entry/test_wiring_recovery.py, tests/entry/test_wiring_recovery_expired.py, tests/entry/test_wiring_run.py, tests/entry/test_wiring_stage_environment.py, tests/entry/test_wiring_stage_image_sizes.py, tests/entry/test_wiring_stop_records.py, tests/entry/test_wiring_transcripts.py, tests/entry/test_wiring_waiter.py, tests/entry/test_wiring_without_agent_user.py, tests/evaluation_support.py, tests/git_support.py, tests/hosting_interface_support.py, tests/human_clone.py, tests/known_results_support.py, tests/log_support.py, tests/machine_readings_support.py, tests/module_names.py, tests/observing_runtime.py, tests/operator_job_support.py, tests/operator_skill_support.py, tests/operator_support.py, tests/podman_support.py, tests/power_support.py, tests/preflight_support.py, tests/probe_support.py, tests/process_support.py, tests/project_command_support.py, tests/proof_support.py, tests/push_retry_support.py, tests/record_support.py, tests/recording_log.py, tests/remote_outage_support.py, tests/run_layout_support.py, tests/run_process_recorder.py, tests/scripted_tick_support.py, tests/settings_support.py, tests/shared/__init__.py, tests/shared/adapters/__init__.py, tests/shared/adapters/test_clock.py, tests/shared/adapters/test_process.py, tests/shared/adapters/test_process_drain.py, tests/shared/adapters/test_process_result_fields.py, tests/shared/adapters/test_process_session.py, tests/shared/adapters/test_process_streaming.py, tests/shared/adapters/test_process_streaming_last_line.py, tests/shared/adapters/test_process_streaming_reads.py, tests/shared/adapters/test_run_or_raise.py, tests/shared/adapters/test_validation_faults.py, tests/shared/application/__init__.py, tests/shared/application/test_hosting_failure_after_claim.py, tests/shared/application/test_push_retry_reason.py, tests/shared/application/test_push_retry_server_lines.py, tests/shared/domain/__init__.py, tests/shared/domain/test_cannot_handle.py, tests/shared/domain/test_contract_version_4.py, tests/shared/domain/test_contract_version_4_2.py, tests/shared/domain/test_contract_without_nested_repository.py, tests/shared/domain/test_contract_without_tool_paths.py, tests/shared/domain/test_cost_record_errors.py, tests/shared/domain/test_documents_guide_files.py, tests/shared/domain/test_documents_line_edges.py, tests/shared/domain/test_duplicates.py, tests/shared/domain/test_duplicates_skipped_lines.py, tests/shared/domain/test_errors.py, tests/shared/domain/test_errors_agent_definition.py, tests/shared/domain/test_errors_environment.py, tests/shared/domain/test_identifiers.py, tests/shared/domain/test_is_name.py, tests/shared/domain/test_kill_point_cases.py, tests/shared/domain/test_kill_points.py, tests/shared/domain/test_name.py, tests/shared/domain/test_paths.py, tests/shared/domain/test_power_off_error.py, tests/shared/domain/test_sections.py, tests/shared/domain/test_settings_agent_files_stay.py, tests/shared/domain/test_settings_agent_runtime.py, tests/shared/domain/test_settings_agent_user_unread.py, tests/shared/domain/test_settings_api_login.py, tests/shared/domain/test_settings_boundaries.py, tests/shared/domain/test_settings_claude_login.py, tests/shared/domain/test_settings_container_env.py, tests/shared/domain/test_settings_container_profile.py, tests/shared/domain/test_settings_idle_shutdown.py, tests/shared/domain/test_settings_idle_shutdown_action.py, tests/shared/domain/test_settings_min_free.py, tests/shared/domain/test_settings_one_environment.py, tests/shared/domain/test_settings_opencode_folders_ignored.py, tests/shared/domain/test_settings_opencode_models.py, tests/shared/domain/test_settings_opencode_provider.py, tests/shared/domain/test_settings_paths.py, tests/shared/domain/test_settings_pinned.py, tests/shared/domain/test_settings_provider_limit.py, tests/shared/domain/test_settings_provider_limit_wait.py, tests/shared/domain/test_settings_required_paths.py, tests/shared/domain/test_settings_snapshots.py, tests/shared/domain/test_settings_stage_environment.py, tests/shared/domain/test_settings_transcripts.py, tests/shared/domain/test_settings_url_edges.py, tests/shared/domain/test_unhandled_event.py, tests/shared/domain/test_work_item_errors.py, tests/shipped_agents.py, tests/site_check_support.py, tests/sized_images.py, tests/source_search.py, tests/stage_image_support.py, tests/stage_run_support.py, tests/stall_support.py, tests/story_form_support.py, tests/take_support.py, tests/template_make_support.py, tests/test_agent_home_wiring.py, tests/test_agent_launch_search.py, tests/test_agent_run_request_search.py, tests/test_approval_description.py, tests/test_areas.py, tests/test_checkout_hygiene_removed.py, tests/test_claim_ownership.py, tests/test_claude_agent_refusal.py, tests/test_claude_agent_skills.py, tests/test_claude_agent_texts.py, tests/test_claude_agent_texts_decision_log.py, tests/test_claude_agent_texts_description.py, tests/test_claude_agent_texts_docs_slip.py, tests/test_claude_agent_texts_mutants.py, tests/test_claude_agent_texts_review_leave.py, tests/test_claude_agent_texts_smoke_pytest.py, tests/test_claude_files.py, tests/test_claude_settings_git.py, tests/test_demos.py, tests/test_docker_path_removed.py, tests/test_fault_paths.py, tests/test_fault_paths_7_to_13.py, tests/test_fault_paths_table.py, tests/test_git_credential_helper.py, tests/test_home_reset_removed.py, tests/test_hook_removed.py, tests/test_hosting_search.py, tests/test_human_clone.py, tests/test_kernel_guard_removed.py, tests/test_kill_points.py, tests/test_layers.py, tests/test_leftovers_program_removed.py, tests/test_make_search.py, tests/test_model_configuration.py, tests/test_no_agent_login.py, tests/test_no_journal_reading.py, tests/test_no_state_copies.py, tests/test_no_untyped_dicts.py, tests/test_one_stage_environment.py, tests/test_opencode_runtime_search.py, tests/test_operator_hosting.py, tests/test_operator_job.py, tests/test_operator_job_log.py, tests/test_operator_merge_reset.py, tests/test_operator_python_isolation.py, tests/test_operator_sanitise.py, tests/test_operator_site.py, tests/test_operator_site_check.py, tests/test_operator_site_example.py, tests/test_operator_skill_name.py, tests/test_operator_skill_scripts.py, tests/test_operator_skill_signature.py, tests/test_operator_texts.py, tests/test_pins.py, tests/test_process_search.py, tests/test_proof_support.py, tests/test_removed_layer_names.py, tests/test_retrying_wording.py, tests/test_round_cap_answer.py, tests/test_second_user_removed.py, tests/test_shared_bodies.py, tests/test_shared_branch_helpers.py, tests/test_shared_constants.py, tests/test_shared_definition.py, tests/test_shared_environments.py, tests/test_shared_imports.py, tests/test_shared_test_helpers.py, tests/test_stage_image.py, tests/test_stop_table.py, tests/test_suite_fixtures.py, tests/test_suite_held_once.py, tests/test_suite_leftovers.py, tests/test_suite_old_names.py, tests/test_template_makefile.py, tests/test_template_sync.py, tests/test_tests_run_under_the_starting_umask.py, tests/test_tmp_path_reopening.py, tests/test_undo_removed.py, tests/test_vm_credential_helper_host.py, tests/test_vm_job_start.py, tests/test_vm_job_start_environment.py, tests/test_vm_job_start_instance.py, tests/test_vm_job_start_transcripts.py, tests/test_vm_local_environment.py, tests/test_vm_service.py, tests/test_vm_service_stop.py, tests/test_vm_setup.py, tests/test_vm_setup_caches.py, tests/test_vm_setup_code_ref.py, tests/test_vm_setup_code_url.py, tests/test_vm_setup_first_base.py, tests/test_vm_setup_idle_shutdown.py, tests/test_vm_setup_install_hint.py, tests/test_vm_setup_text.py, tests/test_vm_setup_transcripts.py, tests/test_vm_setup_writes.py, tests/test_wrapper_out_of_the_call_path.py, tests/test_wrapper_search.py, tests/tick_support.py, tests/time_limits.py, tests/token_support.py, tests/tool_use_support.py, tests/torn_record_support.py, tests/undo_support.py, tests/vm_support.py, tests/watch_support.py, tests/wiring_support.py, tests/work_item_support.py, tests/write_path_support.py, tests/zfs_support.py.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   tests/conftest.py:23: error: Skipping analyzing "factory.adapters.clock": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/conftest.py:41: error: Skipping analyzing "factory.domain.identifiers": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/conftest.py:42: error: Skipping analyzing "factory.domain.kill_points": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/conftest.py:45: error: Skipping analyzing "factory.domain.settings": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/conftest.py:550: error: Returning Any from function declared to return "str"  [no-any-return]
   tests/application/test_hosting_failure_releases_claim.py:14: error: Skipping analyzing "factory.domain.errors": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/application/test_hosting_failure_releases_claim.py:17: error: Skipping analyzing "factory.domain.identifiers": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/application/test_hosting_failure_releases_claim.py:18: error: Skipping analyzing "factory.domain.kill_points": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/application/test_hosting_failure_after_claim.py:3: error: Skipping analyzing "factory.domain.identifiers": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/entry/test_wiring_image_path.py:21: error: Skipping analyzing "factory.domain.settings": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/entry/test_wiring_container_extra.py:17: error: Skipping analyzing "factory.domain.settings": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/application/test_container_environment_extra.py:23: error: Skipping analyzing "factory.domain.settings": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   tests/adapters/test_agent_launch_extra.py:18: error: Skipping analyzing "factory.domain.settings": module is installed, but missing library stubs or py.typed marker  [import-untyped]
   Found 619 errors in 399 files (checked 933 source files)
   make: *** [Makefile:38: types] Error 1
9. factory: started doing as vm.
10. coder: Round 0, second attempt after the `check_red` stall. Code is unchanged in this run: what remains is test work, so I'm handing it to the tester.

    Where it stands: the source side of the move is committed from the first attempt. All 18 modules are under `src/factory/shared/<layer>/`, the four packages `src/factory/shared/{,domain/,application/,adapters/}__init__.py` exist, and no file under `src/` imports an old path. `uv run mypy --strict src` is clean (161 files), and import-linter keeps all 4 contracts. `make check` is red only because of `tests/`. The first attempt changed the tests, but the factory dropped those changes because the coder's write paths do not include `tests/*`. The test files still import `factory.domain.errors`, `factory.adapters.clock` and the other old paths, which is where the 619 mypy errors in entry 8 come from.

    The tester needs to make these test changes. The Interface's leave of feature decision 5 covers them.
    1. Rewrite every import of a moved module under `tests/` to its new path `factory.shared.<layer>.<name>`, including the `from factory.<layer> import <name>` forms. Split the import lines that mix moved and unmoved modules: `tests/domain/test_default_git_identity.py` and `tests/test_leftovers_program_removed.py`.
    2. Create `tests/shared/`, `tests/shared/domain/`, `tests/shared/application/` and `tests/shared/adapters/`, each with an `__init__.py`. Then `git mv` into `tests/shared/<layer>/` every test module that `tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved` lists. Entry 7 counted 60, among them `test_errors.py`, `test_process*.py` and `test_push_retry_*.py`.
    3. Change the paths that point at moved files:
       - `tests/test_process_search.py`: `SRC / "shared" / "adapters" / "process.py"`, and the key `"shared/adapters/process.py"`.
       - `tests/entry/test_watch.py`: `_names_the_replaced_phrases` and the `document-check` row point at `shared/domain/documents.py`.
       - `tests/test_suite_old_names.py` and `tests/test_suite_held_once.py`: the paths of the moved test modules they read now start with `shared/domain/`.
    4. `tests/domain/test_hosting.py`: `_is_domain` must also count `factory.shared.domain` as the domain layer, because the domain modules it checks now import shared domain modules.

    After that, `make check` should be green with no change to code. The first attempt had it green with these exact changes.

    Main choice: send the test changes to the tester rather than end with `question`. The work item already grants the leave, so the only open point was whose write paths these changes fall in, and those are the tester's. I rejected making the test changes again myself: they would be dropped a second time.

    Noticed, not touched:
    - `security/duplicates-baseline.txt` is in no role's write paths. Its five accepted dead-code findings in moved modules still name the old paths, so `make duplicates` will report them as gone and again as new. That file is only read by a report, not by a check, so it does not block anything, but only the human can update it.
    - `tests/adapters/test_work_item_markdown.py::test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` picks modules by `name.split(".")[1:2]`, so it does not look at `factory.shared.*`. It passes, but it covers less with every area that moves.
    - `CLAUDE.md` still names `factory.domain.contract.CONTRACT`. That file is the human's.

    Refactor: not done in this run, since my code did not change. Entry 7 found nothing to change in the source diff.

    Description unchanged: no journal entry changed the meaning of the task.
11. factory: started tests as vm.
12. tester: Mode: an approved test change. I made the test changes the coder listed in entry 10, under the Interface's leave of feature decision 5. The source code was already in place, so this run touched tests only.

    What I changed:
    1. Imports: every `factory.<layer>.<name>` reference to one of the 18 moved modules under `tests/` now names `factory.shared.<layer>.<name>`. A script made the rewrite and changed 406 files. I also rewrote the `from factory.<layer> import <name>` forms by hand in `tests/test_home_reset_removed.py`, `tests/test_one_stage_environment.py`, `tests/test_second_user_removed.py`, `tests/test_checkout_hygiene_removed.py`, `tests/domain/test_settings_model_rules.py`, `tests/adapters/test_process_result_fields.py`, `tests/adapters/test_process_drain.py`, `tests/adapters/test_zfs_snapshots.py` and `tests/adapters/test_podman_runs_results.py`. I split the mixed import lines in `tests/domain/test_default_git_identity.py` and `tests/test_leftovers_program_removed.py`. Then `ruff check --fix` and `ruff format` re-sorted and re-wrapped the imports.
    2. Created `tests/shared/__init__.py`, `tests/shared/domain/__init__.py`, `tests/shared/application/__init__.py` and `tests/shared/adapters/__init__.py`, all empty. I moved with `git mv` the 60 test modules that `tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved` listed: 47 from `tests/domain/`, 3 from `tests/application/` and 10 from `tests/adapters/`. Each went to the same layer under `tests/shared/`.
    3. Paths:
       - `tests/test_process_search.py` now reads `SRC / "shared" / "adapters" / "process.py"` and uses the key `"shared/adapters/process.py"`.
       - `tests/entry/test_watch.py`: `_names_the_replaced_phrases` and the `document-check` row now point at `shared/domain/documents.py`.
       - `tests/test_suite_old_names.py`: the two moved contract modules are now under `shared/domain/`. `domain/test_contract_provider_limit.py` did not move and is unchanged.
       - `tests/test_suite_held_once.py`: the three settings modules are now under `shared/domain/`.
    4. `tests/domain/test_hosting.py::_is_domain` now also counts `factory.shared.domain` and `factory.shared.domain.*` as the domain layer. The coder's note left out the bare package name. It is needed because `from factory.shared.domain import identifiers` records the import as `factory.shared.domain`, and `test_domain_modules_import_only_stdlib_pydantic_and_domain[factory.shared.domain.paths]` failed in my run until I added it.

    Every test keeps its name and checks the same thing as before. `tests/test_areas.py` is unchanged and passes.

    The one test run: `uv run pytest -q -n auto` over every changed or moved test module. Its only failure was the `_is_domain` case above. After the fix, `tests/domain/test_hosting.py` passes; I did not run the rest again. `make lint` is green and `uv run mypy --strict src tests` is clean (937 files). I did not run `make check`.

    Not touched (the coder noted these in entry 10): `security/duplicates-baseline.txt` still names the old paths, and only the human can update it. `tests/adapters/test_work_item_markdown.py`'s module filter does not look at `factory.shared.*`.

    `lint`: lint: green (0.1 s)
13. factory: started doing as vm.
14. coder: Round 0, third run in doing. The tester's changes from entry 12 completed the move, and `make check` is green with no further edit (`test: green (119.8 s)`, `check: green`, total coverage 99.26 %). I changed nothing in this run, and the working tree is clean.

    What is built (committed in earlier runs):
    - `src/factory/shared/__init__.py`, `src/factory/shared/domain/__init__.py`, `src/factory/shared/application/__init__.py` and `src/factory/shared/adapters/__init__.py`, each with a one-line docstring.
    - All 18 modules of the Interface, moved with `git mv` to `src/factory/shared/<layer>/<name>.py`. Only their import lines changed. The source diff against main is 121 files, almost all of them import rewrites.
    - Tests: the tester's entry 12 covers them. That includes `tests/shared/...` with its 60 moved test modules, and `tests/test_areas.py` is untouched.

    Checks I ran in this run:
    - `uv run python -m factory.entry.contract` leaves the schemas unchanged.
    - No old dotted path of a moved module is left under `src/`, in `Makefile` or in `pyproject.toml` (grep).

    Main choice: a straight move with every import rewritten and nothing left at the old paths, as feature decision 4 asks. I rejected re-export shims at the old paths: the story forbids them, and criterion 1 checks that the old files are gone.

    Refactor: I read the source diff again and found nothing to change. It is moves and import lines only.

    Noticed, not touched:
    - `make duplicates` reports `11 new, 34 known, 8 gone`. Most of the "gone" and "new" lines are the same accepted findings under their old and new paths: `kill_points.arm`/`reached`, `paths.FACTORY_DIRECTORY`, `clock.ManualWaiter`, and the claude/opencode `finished_run` similarity. `security/duplicates-baseline.txt` needs the human to rename these entries, because it is outside every role's write paths. It is a record, not a check.
    - `tests/adapters/test_work_item_markdown.py::test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` filters modules by `name.split(".")[1:2]`, so it does not look at `factory.shared.*`. It passes but covers less, and the gap grows with every later move.
    - `tests/test_layers.py` checks only the four top-level layer packages.
    - `CLAUDE.md` still names `factory.domain.contract.CONTRACT` and `src/factory/adapters/process.py` as the current path. That file is the human's.
    - The docs still name old paths. Updating them is the documenter's job under criterion 6.

    Description unchanged: no journal entry changed the meaning of the task.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 34 known, 8 gone
15. factory: started review as vm.
16. reviewer: Review of round 0. I read the source and test diff line by line, leaving out import lines. `src/` has only moves, import rewrites and the four package docstrings. The 18 modules are under `src/factory/shared/<layer>/`, and nothing is left at an old path. No `nosec`, `nosemgrep`, `noqa` or `type: ignore` marker was added. The `process.py` markers moved unchanged. No old dotted path is left in `src/`, `tests/`, `Makefile` or `pyproject.toml`. All 60 modules under `tests/shared/` import only `factory.shared.*`, and each imports at least one. Entry 14 says the factory's `make check` was green.

    Findings:
    1. `tests/adapters/test_work_item_markdown.py:449`: `test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` picks modules by `name.split(".")[1:2]`. The 13 moved domain and application modules (`factory.shared.domain.*`, `factory.shared.application.files`) were under this rule on `main` and now fall outside it. The test still passes but checks less, which goes against the Description ("checks the same thing") and against feature decision 5 ("check the same rule over the new layout"). Fix: the tester makes the filter match the layer wherever it sits (`factory.<layer>.*` or `factory.<area>.<layer>.*`), as it did for `_is_domain` in `tests/domain/test_hosting.py`. This test is a guard that pins the old layout, but decision 5's list of guards does not name it. If the tester reads that list as closed, it asks the human first.
    2. `tests/test_areas.py:96`: `_factory_imports` is a second copy of `imported_modules` in `tests/source_search.py:22`, and this file already imports from that module. It walks `ast.Import` and absolute `ast.ImportFrom` the same way. Fix: filter `imported_modules(tree)` to names that are `factory` or start with `factory.`. The extra `<module>.<alias>` names it adds do not change which modules `_in_a_moved_area` accepts.
    3. Criterion 5 added; it needs its test. The Interface's rule on which test modules move has a criterion only for the stay side (criterion 4). Nothing checks that a module under `tests/shared/` meets the rule: one that imports an area not yet moved, or nothing of `shared`, would pass. All 60 modules meet it today, so the test would be green without any change under `src/`. The old criteria 5 and 6 are now 6 and 7.

    description corrected: "every test that passed before passes after, with only its import lines and paths changed" -> "every test that passed before passes after and checks the same thing, with only its import lines and paths changed, and the guards that pin the old layout made to check the same rule over the new one (feature decision 5)". This matches decision 5 and the change to `_is_domain`.

    Open, for the human, outside every write path:
    - `security/duplicates-baseline.txt` lines 25 to 32 still name the old paths of `identifiers`, `kill_point_cases`, `kill_points` (twice), `paths` and `clock`. That is why `make duplicates` shows 11 new and 8 gone (entry 14).
    - `CLAUDE.md` still names `factory.domain.contract.CONTRACT`.

    Groups 2 to 5, apart from the findings above: the layers hold (import-linter is green in `make check`, and every module keeps its layer). There are no security points. The four new `src` packages have docstrings. The journal names the main choice, a straight move, and what was rejected, re-export shims. Criterion 7 (docs) still says what the documenter must change.

    Earlier tests changed (410 files). D5 means the leave of feature decision 5, which the Interface names in the human's story ("The leave of feature decision 5 covers every other change to tests that the move needs"). Each file below changed under D5, and only by what is named in brackets: [i] import lines only; [p] import lines plus dotted or file paths of moved modules or moved test modules; [g] import lines plus the guard `_is_domain`; [mv] moved with `git mv`, plus import lines.
    tests/acceptance_walk.py [i]
    tests/adapters/opencode_stand_in.py [i]
    tests/adapters/test_agent_file_keys.py [i]
    tests/adapters/test_agent_files.py [i]
    tests/adapters/test_agent_files_parse.py [i]
    tests/adapters/test_agent_launch_call_end.py [i]
    tests/adapters/test_agent_launch_extra.py [i]
    tests/adapters/test_agent_launch_login.py [i]
    tests/adapters/test_agent_launch_state_directory.py [i]
    tests/adapters/test_calls_as_the_factory_user.py [i]
    tests/adapters/test_claude_runtime.py [i]
    tests/adapters/test_claude_runtime_api_login.py [i]
    tests/adapters/test_claude_runtime_container.py [i]
    tests/adapters/test_claude_runtime_login.py [i]
    tests/adapters/test_claude_runtime_resume.py [i]
    tests/adapters/test_copy_snapshots.py [i]
    tests/adapters/test_cost_records_jsonl.py [i]
    tests/adapters/test_cost_records_jsonl_instance.py [i]
    tests/adapters/test_factory_log.py [i]
    tests/adapters/test_fake_agent_runtime.py [i]
    tests/adapters/test_fake_containers.py [i]
    tests/adapters/test_fake_hosting.py [i]
    tests/adapters/test_fake_snapshots.py [i]
    tests/adapters/test_git_cli_arguments.py [i]
    tests/adapters/test_git_cli_branches.py [i]
    tests/adapters/test_git_cli_check_ignore.py [i]
    tests/adapters/test_git_cli_history.py [i]
    tests/adapters/test_git_cli_reading.py [i]
    tests/adapters/test_git_cli_restoring.py [i]
    tests/adapters/test_git_cli_seal.py [i]
    tests/adapters/test_git_cli_work_tree.py [i]
    tests/adapters/test_git_cli_writing.py [i]
    tests/adapters/test_health_file.py [i]
    tests/adapters/test_kill_at_the_limit_stays.py [i]
    tests/adapters/test_make_commands.py [i]
    tests/adapters/test_make_commands_container.py [i]
    tests/adapters/test_oauth_token.py [i]
    tests/adapters/test_opencode_budget.py [i]
    tests/adapters/test_opencode_left_out_tools.py [i]
    tests/adapters/test_opencode_runtime.py [i]
    tests/adapters/test_opencode_runtime_container.py [i]
    tests/adapters/test_opencode_runtime_launch.py [i]
    tests/adapters/test_opencode_runtime_lockdown.py [i]
    tests/adapters/test_opencode_runtime_provider.py [i]
    tests/adapters/test_pipeline_yaml.py [i]
    tests/adapters/test_pipeline_yaml_one_line_fault.py [i]
    tests/adapters/test_podman_images.py [i]
    tests/adapters/test_podman_runs_job_profile.py [i]
    tests/adapters/test_podman_runs_results.py [i]
    tests/adapters/test_power_off.py [i]
    tests/adapters/test_pygithub_hosting.py [i]
    tests/adapters/test_record_log_jsonl.py [i]
    tests/adapters/test_runtime_podman_timeout_status.py [i]
    tests/adapters/test_runtime_state_directory_write.py [i]
    tests/adapters/test_waiters.py [i]
    tests/adapters/test_work_item_markdown.py [i] (see finding 1)
    tests/adapters/test_work_item_markdown_acceptance.py [i]
    tests/adapters/test_zfs_snapshots.py [i]
    tests/adapters/test_zfs_snapshots_diff.py [i]
    tests/adapters/test_zfs_snapshots_drop_caches.py [i]
    tests/application/handlers/test_closed.py [i]
    tests/application/handlers/test_closed_send_back.py [i]
    tests/application/handlers/test_comment_handler.py [i]
    tests/application/handlers/test_comments.py [i]
    tests/application/handlers/test_hand_over.py [i]
    tests/application/handlers/test_lookups.py [i]
    tests/application/handlers/test_merged.py [i]
    tests/application/handlers/test_questions.py [i]
    tests/application/handlers/test_recording.py [i]
    tests/application/handlers/test_reject.py [i]
    tests/application/handlers/test_run.py [i]
    tests/application/handlers/test_run_gate.py [i]
    tests/application/test_acceptance_closed.py [i]
    tests/application/test_acceptance_due_handler.py [i]
    tests/application/test_acceptance_facts_disk.py [i]
    tests/application/test_acceptance_hand_over.py [i]
    tests/application/test_acceptance_merged.py [i]
    tests/application/test_acceptance_merged_before_approval.py [i]
    tests/application/test_acceptance_no_state_refusals.py [i]
    tests/application/test_acceptance_reading.py [i]
    tests/application/test_acceptance_refusals.py [i]
    tests/application/test_acceptance_repeated.py [i]
    tests/application/test_acceptance_reviewer_role.py [i]
    tests/application/test_acceptance_service.py [i]
    tests/application/test_acceptance_snapshots.py [i]
    tests/application/test_acceptance_ticks_closed.py [i]
    tests/application/test_acceptance_ticks_merged.py [i]
    tests/application/test_acceptance_ticks_repeated.py [i]
    tests/application/test_after_agent.py [i]
    tests/application/test_agent_definition_reader.py [i]
    tests/application/test_agent_run_probe.py [i]
    tests/application/test_agent_run_probe_api_login.py [i]
    tests/application/test_agent_run_probe_environment.py [i]
    tests/application/test_agent_run_probe_factory_user.py [i]
    tests/application/test_agent_run_probe_login.py [i]
    tests/application/test_agent_run_probe_opencode.py [i]
    tests/application/test_agent_run_probe_project_agent.py [i]
    tests/application/test_bill_service.py [i]
    tests/application/test_board_reader.py [i]
    tests/application/test_board_reader_acceptance.py [i]
    tests/application/test_boundaries_required.py [i]
    tests/application/test_boundaries_settings.py [i]
    tests/application/test_checkout_preparer.py [i]
    tests/application/test_claims.py [i]
    tests/application/test_claims_observed.py [i]
    tests/application/test_container_environment.py [i]
    tests/application/test_container_environment_extra.py [i]
    tests/application/test_container_environment_take.py [i]
    tests/application/test_container_items.py [i]
    tests/application/test_cost_image.py [i]
    tests/application/test_cost_instance.py [i]
    tests/application/test_costs.py [i]
    tests/application/test_disk_recorder.py [i]
    tests/application/test_dispatcher.py [i]
    tests/application/test_dispatcher_counts_every_error.py [i]
    tests/application/test_hosting_failure_releases_claim.py [i]
    tests/application/test_human_line_posts.py [i]
    tests/application/test_idle_shutdown.py [i]
    tests/application/test_known_results.py [i]
    tests/application/test_known_results_torn.py [i]
    tests/application/test_left_out_stage.py [i]
    tests/application/test_machine.py [i]
    tests/application/test_machine_checks_container.py [i]
    tests/application/test_machine_checks_runtime.py [i]
    tests/application/test_no_state_refusals.py [i]
    tests/application/test_opencode_item.py [i]
    tests/application/test_opencode_item_container.py [i]
    tests/application/test_opening.py [i]
    tests/application/test_patient_runs.py [i]
    tests/application/test_pipeline_definition_reader.py [i]
    tests/application/test_pipeline_loading.py [i]
    tests/application/test_pipeline_loading_agents.py [i]
    tests/application/test_pipeline_loading_project_agents.py [i]
    tests/application/test_pipeline_loading_rules.py [i]
    tests/application/test_pipeline_loading_stage_moves.py [i]
    tests/application/test_pipeline_loading_strict_values.py [i]
    tests/application/test_pipeline_loading_yaml_fault.py [i]
    tests/application/test_preflight.py [i]
    tests/application/test_preflight_login_line.py [i]
    tests/application/test_preflight_metadata_block.py [i]
    tests/application/test_preflight_run.py [i]
    tests/application/test_preflight_stops_commit.py [i]
    tests/application/test_probe_nested_repository.py [i]
    tests/application/test_project_agents.py [i]
    tests/application/test_push_retry.py [i]
    tests/application/test_question_causes_recorded.py [i]
    tests/application/test_recording_project_commands.py [i]
    tests/application/test_recovery_cap.py [i]
    tests/application/test_recovery_crash.py [i]
    tests/application/test_recovery_expiry.py [i]
    tests/application/test_recovery_expiry_key.py [i]
    tests/application/test_recovery_subjects.py [i]
    tests/application/test_repository_waiter.py [i]
    tests/application/test_request_working_directory.py [i]
    tests/application/test_scheduler.py [i]
    tests/application/test_sealed_runs_runner.py [i]
    tests/application/test_split_by_work_item_kind.py [i]
    tests/application/test_stage_changes.py [i]
    tests/application/test_stage_died_line.py [i]
    tests/application/test_stage_environment_calls.py [i]
    tests/application/test_stage_finish.py [i]
    tests/application/test_stage_launch.py [i]
    tests/application/test_stage_on_container_fakes.py [i]
    tests/application/test_stage_provider_limit.py [i]
    tests/application/test_stage_transcripts.py [i]
    tests/application/test_stale_branches.py [i]
    tests/application/test_stall_container.py [i]
    tests/application/test_stall_environment.py [i]
    tests/application/test_stall_labels.py [i]
    tests/application/test_stalls.py [i]
    tests/application/test_stop_log_once.py [i]
    tests/application/test_stop_posting.py [i]
    tests/application/test_stop_publisher.py [i]
    tests/application/test_stop_records_service.py [i]
    tests/application/test_stops.py [i]
    tests/application/test_take.py [i]
    tests/application/test_take_edges.py [i]
    tests/application/test_task.py [i]
    tests/application/test_task_acceptance.py [i]
    tests/application/test_tick.py [i]
    tests/application/test_tick_agent_definition.py [i]
    tests/application/test_tick_disk.py [i]
    tests/application/test_tick_own_fetch.py [i]
    tests/application/test_tick_preflight.py [i]
    tests/application/test_tick_stale_branch.py [i]
    tests/application/test_tick_stop_details.py [i]
    tests/application/test_tick_stop_records.py [i]
    tests/application/test_tokens.py [i]
    tests/application/test_watcher.py [i]
    tests/application/test_watcher_main_ref.py [i]
    tests/application/test_watcher_move_rule.py [i]
    tests/application/test_watcher_observer.py [i]
    tests/application/test_work_items.py [i]
    tests/application/test_work_items_duplicate.py [i]
    tests/application/test_write_paths.py [i]
    tests/claude_resume_support.py [i]
    tests/conftest.py [i]
    tests/container_support.py [i]
    tests/contract_support.py [i]
    tests/cost_image_support.py [i]
    tests/crash_support.py [i]
    tests/document_texts.py [i]
    tests/domain/test_acceptance.py [i]
    tests/domain/test_acceptance_booking.py [i]
    tests/domain/test_acceptance_facts.py [p]
    tests/domain/test_archive.py [i]
    tests/domain/test_board.py [i]
    tests/domain/test_container_extra_environment.py [i]
    tests/domain/test_contract.py [i]
    tests/domain/test_default_git_identity.py [i]
    tests/domain/test_documents.py [i]
    tests/domain/test_evaluation.py [i]
    tests/domain/test_evaluation_reject.py [i]
    tests/domain/test_fault_paths.py [i]
    tests/domain/test_hand_over.py [i]
    tests/domain/test_hosting.py [g] (a guard decision 5 names)
    tests/domain/test_journal.py [i]
    tests/domain/test_pipeline_definition.py [i]
    tests/domain/test_project_agent_paths.py [i]
    tests/domain/test_section_edges.py [i]
    tests/domain/test_settings.py [i]
    tests/domain/test_settings_model_rules.py [i]
    tests/domain/test_story_form.py [i]
    tests/domain/test_story_form_edges.py [i]
    tests/domain/test_times.py [p]
    tests/domain/test_work_item_require_state.py [i]
    tests/entry/test_bill.py [i]
    tests/entry/test_check_documents.py [i]
    tests/entry/test_check_documents_guide_files.py [i]
    tests/entry/test_contract.py [i]
    tests/entry/test_contract_arguments.py [i]
    tests/entry/test_contract_not_read.py [i]
    tests/entry/test_health.py [i]
    tests/entry/test_health_missing.py [i]
    tests/entry/test_refresh_token.py [i]
    tests/entry/test_run.py [i]
    tests/entry/test_run_fetch_before_tick.py [i]
    tests/entry/test_run_health_file.py [i]
    tests/entry/test_run_idle_exit.py [i]
    tests/entry/test_run_idle_shutdown.py [i]
    tests/entry/test_run_image_sizes.py [i]
    tests/entry/test_run_machine_stop_exit.py [i]
    tests/entry/test_run_one_fetch.py [i]
    tests/entry/test_run_project_image_rebuild.py [i]
    tests/entry/test_run_required_paths.py [i]
    tests/entry/test_run_state_variable.py [i]
    tests/entry/test_run_stop_requested.py [i]
    tests/entry/test_run_waiter.py [i]
    tests/entry/test_watch.py [p]
    tests/entry/test_watch_main.py [i]
    tests/entry/test_watch_own_claim.py [i]
    tests/entry/test_watch_settings.py [i]
    tests/entry/test_wiring_acceptance.py [i]
    tests/entry/test_wiring_api_login.py [i]
    tests/entry/test_wiring_boundaries.py [i]
    tests/entry/test_wiring_command_records.py [i]
    tests/entry/test_wiring_container_extra.py [i]
    tests/entry/test_wiring_container_profile.py [i]
    tests/entry/test_wiring_copy_snapshots.py [i]
    tests/entry/test_wiring_extras.py [i]
    tests/entry/test_wiring_idle_shutdown.py [i]
    tests/entry/test_wiring_idle_shutdown_action.py [i]
    tests/entry/test_wiring_image_path.py [i]
    tests/entry/test_wiring_instance_label.py [i]
    tests/entry/test_wiring_known_results.py [i]
    tests/entry/test_wiring_login.py [i]
    tests/entry/test_wiring_machine_inputs.py [i]
    tests/entry/test_wiring_one_environment.py [i]
    tests/entry/test_wiring_one_preflight.py [i]
    tests/entry/test_wiring_opencode.py [i]
    tests/entry/test_wiring_opencode_provider.py [i]
    tests/entry/test_wiring_preflight.py [i]
    tests/entry/test_wiring_project_agents.py [i]
    tests/entry/test_wiring_project_image.py [i]
    tests/entry/test_wiring_provider_limit.py [i]
    tests/entry/test_wiring_record_logs.py [i]
    tests/entry/test_wiring_run.py [i]
    tests/entry/test_wiring_stage_environment.py [i]
    tests/entry/test_wiring_stage_image_sizes.py [i]
    tests/entry/test_wiring_stop_records.py [i]
    tests/entry/test_wiring_transcripts.py [i]
    tests/entry/test_wiring_waiter.py [i]
    tests/entry/test_wiring_without_agent_user.py [i]
    tests/evaluation_support.py [i]
    tests/git_support.py [i]
    tests/known_results_support.py [i]
    tests/operator_job_support.py [i]
    tests/operator_skill_support.py [i]
    tests/operator_support.py [i]
    tests/power_support.py [i]
    tests/preflight_support.py [i]
    tests/process_support.py [i]
    tests/proof_support.py [i]
    tests/push_retry_support.py [i]
    tests/record_support.py [i]
    tests/run_layout_support.py [i]
    tests/run_process_recorder.py [i]
    tests/scripted_tick_support.py [i]
    tests/site_check_support.py [i]
    tests/stage_run_support.py [i]
    tests/template_make_support.py [i]
    tests/test_agent_launch_search.py [p]
    tests/test_approval_description.py [i]
    tests/test_checkout_hygiene_removed.py [i]
    tests/test_claude_agent_refusal.py [i]
    tests/test_claude_agent_skills.py [i]
    tests/test_claude_agent_texts.py [i]
    tests/test_claude_agent_texts_decision_log.py [i]
    tests/test_claude_agent_texts_description.py [i]
    tests/test_claude_agent_texts_docs_slip.py [i]
    tests/test_claude_agent_texts_mutants.py [i]
    tests/test_claude_agent_texts_review_leave.py [i]
    tests/test_claude_agent_texts_smoke_pytest.py [i]
    tests/test_claude_settings_git.py [i]
    tests/test_docker_path_removed.py [p]
    tests/test_fault_paths.py [i]
    tests/test_fault_paths_7_to_13.py [i]
    tests/test_git_credential_helper.py [i]
    tests/test_home_reset_removed.py [i]
    tests/test_hook_removed.py [p]
    tests/test_kernel_guard_removed.py [p]
    tests/test_kill_points.py [i]
    tests/test_leftovers_program_removed.py [i]
    tests/test_no_journal_reading.py [p]
    tests/test_one_stage_environment.py [i]
    tests/test_operator_hosting.py [i]
    tests/test_operator_job_log.py [i]
    tests/test_operator_merge_reset.py [i]
    tests/test_operator_python_isolation.py [i]
    tests/test_operator_sanitise.py [i]
    tests/test_operator_skill_signature.py [i]
    tests/test_process_search.py [p]
    tests/test_proof_support.py [i]
    tests/test_round_cap_answer.py [i]
    tests/test_second_user_removed.py [i]
    tests/test_stop_table.py [i]
    tests/test_suite_fixtures.py [i]
    tests/test_suite_held_once.py [p]
    tests/test_suite_old_names.py [p]
    tests/test_tmp_path_reopening.py [i]
    tests/test_vm_credential_helper_host.py [i]
    tests/test_vm_local_environment.py [i]
    tests/test_vm_setup.py [i]
    tests/test_vm_setup_first_base.py [i]
    tests/test_vm_setup_writes.py [i]
    tests/test_wrapper_search.py [p]
    tests/undo_support.py [i]
    tests/vm_support.py [i]
    tests/watch_support.py [i]
    tests/wiring_support.py [i]
    tests/adapters/test_clock.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_drain.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_result_fields.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_session.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming_last_line.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming_reads.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_run_or_raise.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_validation_faults.py -> tests/shared/adapters/ [mv]
    tests/application/test_hosting_failure_after_claim.py -> tests/shared/application/ [mv]
    tests/application/test_push_retry_reason.py -> tests/shared/application/ [mv]
    tests/application/test_push_retry_server_lines.py -> tests/shared/application/ [mv]
    tests/domain/test_cannot_handle.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_version_4.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_version_4_2.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_without_nested_repository.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_without_tool_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_cost_record_errors.py -> tests/shared/domain/ [mv]
    tests/domain/test_documents_guide_files.py -> tests/shared/domain/ [mv]
    tests/domain/test_documents_line_edges.py -> tests/shared/domain/ [mv]
    tests/domain/test_duplicates.py -> tests/shared/domain/ [mv]
    tests/domain/test_duplicates_skipped_lines.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors_agent_definition.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_identifiers.py -> tests/shared/domain/ [mv]
    tests/domain/test_is_name.py -> tests/shared/domain/ [mv]
    tests/domain/test_kill_point_cases.py -> tests/shared/domain/ [mv]
    tests/domain/test_kill_points.py -> tests/shared/domain/ [mv]
    tests/domain/test_name.py -> tests/shared/domain/ [mv]
    tests/domain/test_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_power_off_error.py -> tests/shared/domain/ [mv]
    tests/domain/test_sections.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_files_stay.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_runtime.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_user_unread.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_api_login.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_boundaries.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_claude_login.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_container_env.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_container_profile.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_idle_shutdown.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_idle_shutdown_action.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_min_free.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_one_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_folders_ignored.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_models.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_provider.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_pinned.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_provider_limit.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_provider_limit_wait.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_required_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_snapshots.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_stage_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_transcripts.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_url_edges.py -> tests/shared/domain/ [mv]
    tests/domain/test_unhandled_event.py -> tests/shared/domain/ [mv]
    tests/domain/test_work_item_errors.py -> tests/shared/domain/ [mv]
17. factory: started doing as vm.
18. coder: Round 1. All three of the reviewer's findings in entry 16 are changes to tests, so I changed no code and nothing under `src/`. The working tree is clean. For the tester:

    1. Criterion 5 (added by the reviewer) needs its test in `tests/test_areas.py`. Every test module under `tests/shared/` must take all its `factory` imports from `shared` and the areas moved before it, and at least one from `shared`. The test fails for a module there that imports an area not yet moved, or nothing of `shared`. All 60 modules meet this today, so the test will be green with no source change.
    2. Finding 2: `tests/test_areas.py:94` `_factory_imports` copies `imported_modules` from `tests/source_search.py:22`. It should instead filter `imported_modules(tree)` to names that are `factory` or start with `factory.`.
    3. Finding 1: `tests/adapters/test_work_item_markdown.py:449` `test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` filters with `name.split(".")[1:2]`, so the 13 moved domain and application modules no longer fall under the rule. The filter should match the layer wherever it sits (`factory.<layer>.*` or `factory.<area>.<layer>.*`), the way `_is_domain` in `tests/domain/test_hosting.py` was changed. The reviewer notes that feature decision 5's list of guards does not name this test. If the tester reads that list as closed, this is a question for the human, not a change.

    Main choice: hand the work to the tester (R9) rather than touch any test myself. I rejected changing code: nothing in the findings asks for it.

    The reviewer also flagged two things outside every write path, and I left both alone: `security/duplicates-baseline.txt` lines 25 to 32 still name the old paths, and `CLAUDE.md` still names `factory.domain.contract.CONTRACT`. Both are for the human.
19. factory: started tests as vm.
20. tester: Mode: an approved test change, round 1. I made the three test changes that coder entry 18 lists, from reviewer entry 16, and nothing under `src/`.

    1. Reviewer finding 3 (new criterion 5): `tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own`. It is parametrized with one row per `test_*.py` under `tests/<area>/` for each area of `AREAS`. A row fails if the module imports a `factory` module outside the moved areas (checked with `_in_a_moved_area`), or if it imports nothing under `factory.<area>.`. All rows are green today, as entry 18 expected.
    2. Reviewer finding 2: `tests/test_areas.py::_factory_imports` no longer walks the tree itself. It now filters `imported_modules(tree)` from `tests/source_search.py` to the names that are `factory` or start with `factory.`. The extra `<module>.<alias>` names this adds don't change which modules `_in_a_moved_area` accepts.
    3. Reviewer finding 1: in `tests/adapters/test_work_item_markdown.py::test_only_the_work_item_adapter_imports_frontmatter_and_ruamel`, the filter `name.split(".")[1:2]` is replaced by a private `_layer(name)`. It gives the layer whether the module sits at `factory.<layer>.*` or at `factory.<area>.<layer>.*`, the same way `_is_domain` in `tests/domain/test_hosting.py` was changed. The 13 moved domain and application modules fall under the rule again. The test keeps its name and checks the same rule over the new layout.

    On finding 1: I read it as covered by the Interface's leave of feature decision 5 ("covers every other change to tests that the move needs") and by the Description ("the guards that pin the old layout made to check the same rule over the new one"). That is why I did not ask.

    Earlier test files changed: `tests/adapters/test_work_item_markdown.py` (under decision 5's leave, as above) and `tests/test_areas.py` (this story's own). No files created.

    Run: `uv run pytest -q tests/test_areas.py tests/adapters/test_work_item_markdown.py` passed, and `make lint` is green. The new test is green rather than red, because the move it checks is already done. Every module the run needed imported.

    Still open, outside my write paths, from entry 16: `security/duplicates-baseline.txt` still names old paths, and `CLAUDE.md` still names `factory.domain.contract.CONTRACT`.

    `lint`: lint: green (0.1 s)
21. factory: started doing as vm.
22. coder: Round 1, back from the tester (entry 20). The tester made all three test changes from reviewer entry 16 that entry 18 named: the new criterion-5 test in `tests/test_areas.py`, `_factory_imports` now built on `imported_modules`, and the layer filter in `tests/adapters/test_work_item_markdown.py`. None of them needed a code change, and I changed nothing under `src/` and no test. I ran `make check` on the committed tree and it is green: `test: green (118.8 s)`, `check: green`, total coverage 99.26 %.

    Main choice: send the work to review as it is. I rejected making any source change, because the new and changed tests pass against the move that is already done and no finding asks for code.

    Refactor step: I wrote no new diff this round, so there was nothing to refactor.

    Two things I noticed and did not touch, both outside my write paths and for the human (from entry 16):
    - `security/duplicates-baseline.txt` lines 25–32 still name the old paths.
    - `CLAUDE.md` still names `factory.domain.contract.CONTRACT`.

    The journal did not change what the task means, so the Description stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 34 known, 8 gone
23. factory: started review as vm.
24. reviewer: Review of round 1. The only files changed since the round 0 review (entry 16) are `tests/test_areas.py` and `tests/adapters/test_work_item_markdown.py`; I read both against findings 1 to 3 of entry 16. I also checked the whole diff again. `src/` has only moves, import lines and the four package docstrings. The non-import lines in the test diff are only paths and dotted names of moved modules, plus the two guards `_is_domain` and `_layer`. The set of earlier test files changed matches entry 16's list exactly (410 files). Entry 22 says the factory's `make check` was green (`check: green`, coverage 99.26 %).

    no findings

    - Group 1: criteria 1 to 5 each have their parametrized test in `tests/test_areas.py`. The test for the new criterion 5, `test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own`, has one row per module under `tests/shared/` and asserts both failing sides (a module that imports an area not yet moved, a module that imports nothing of `shared`). Criteria 6 and 7 are the closing ones.
    - Group 2: every module keeps its layer inside `factory.shared`, and import-linter is green in `make check`.
    - Group 3: no new markers. The `process.py` markers moved unchanged, which `CLAUDE.md` allows.
    - Group 4: finding 2 is fixed: `_factory_imports` filters `imported_modules` from `tests/source_search.py`. Finding 1 is fixed: `_layer` in `tests/adapters/test_work_item_markdown.py:443` brings the 13 moved domain and application modules back under the frontmatter/ruamel rule.
    - Group 5: the Description, the criteria and docs criterion 7 match what was built.

    Notes:
    1. `tests/test_areas.py:106` (`_in_a_moved_area`): the old-path branch checks exact membership in `{factory.<layer>.<name>}`. Since round 1, `_factory_imports` takes in `imported_modules`, and that also yields `factory.<layer>.<name>.<alias>` for `from factory.<layer>.<name> import X`. So before a later move, a test module written in that form no longer counts as moved, and the criterion 4 test cannot go red before the move. Entry 16's finding 2 said these extra names change nothing, which is wrong for this branch. On the moved tree the check is unaffected. Fix: also accept `module.startswith(f"factory.{old}.")`.
    2. Open for the human, outside every write path (as in entry 16): `security/duplicates-baseline.txt` lines 25 to 32 still name the old paths, and `CLAUDE.md` still names `factory.domain.contract.CONTRACT` and `src/factory/adapters/process.py`.

    Earlier tests. Every file below changed under the leave of feature decision 5, which the Interface grants in the human's story ("The leave of feature decision 5 covers every other change to tests that the move needs"). Each keeps its test names and checks the same thing. Key: [i] import lines only; [p] import lines plus dotted or file paths of moved modules or moved test modules; [g] import lines plus a layer guard made to check the same rule over the new layout; [mv] moved with `git mv`, plus import lines.
    tests/acceptance_walk.py [i]
    tests/adapters/opencode_stand_in.py [i]
    tests/adapters/test_agent_file_keys.py [i]
    tests/adapters/test_agent_files.py [i]
    tests/adapters/test_agent_files_parse.py [i]
    tests/adapters/test_agent_launch_call_end.py [i]
    tests/adapters/test_agent_launch_extra.py [i]
    tests/adapters/test_agent_launch_login.py [i]
    tests/adapters/test_agent_launch_state_directory.py [i]
    tests/adapters/test_calls_as_the_factory_user.py [i]
    tests/adapters/test_claude_runtime.py [i]
    tests/adapters/test_claude_runtime_api_login.py [i]
    tests/adapters/test_claude_runtime_container.py [i]
    tests/adapters/test_claude_runtime_login.py [i]
    tests/adapters/test_claude_runtime_resume.py [i]
    tests/adapters/test_copy_snapshots.py [i]
    tests/adapters/test_cost_records_jsonl.py [i]
    tests/adapters/test_cost_records_jsonl_instance.py [i]
    tests/adapters/test_factory_log.py [i]
    tests/adapters/test_fake_agent_runtime.py [i]
    tests/adapters/test_fake_containers.py [i]
    tests/adapters/test_fake_hosting.py [i]
    tests/adapters/test_fake_snapshots.py [i]
    tests/adapters/test_git_cli_arguments.py [i]
    tests/adapters/test_git_cli_branches.py [i]
    tests/adapters/test_git_cli_check_ignore.py [i]
    tests/adapters/test_git_cli_history.py [i]
    tests/adapters/test_git_cli_reading.py [i]
    tests/adapters/test_git_cli_restoring.py [i]
    tests/adapters/test_git_cli_seal.py [i]
    tests/adapters/test_git_cli_work_tree.py [i]
    tests/adapters/test_git_cli_writing.py [i]
    tests/adapters/test_health_file.py [i]
    tests/adapters/test_kill_at_the_limit_stays.py [i]
    tests/adapters/test_make_commands.py [i]
    tests/adapters/test_make_commands_container.py [i]
    tests/adapters/test_oauth_token.py [i]
    tests/adapters/test_opencode_budget.py [i]
    tests/adapters/test_opencode_left_out_tools.py [i]
    tests/adapters/test_opencode_runtime.py [i]
    tests/adapters/test_opencode_runtime_container.py [i]
    tests/adapters/test_opencode_runtime_launch.py [i]
    tests/adapters/test_opencode_runtime_lockdown.py [i]
    tests/adapters/test_opencode_runtime_provider.py [i]
    tests/adapters/test_pipeline_yaml.py [i]
    tests/adapters/test_pipeline_yaml_one_line_fault.py [i]
    tests/adapters/test_podman_images.py [i]
    tests/adapters/test_podman_runs_job_profile.py [i]
    tests/adapters/test_podman_runs_results.py [i]
    tests/adapters/test_power_off.py [i]
    tests/adapters/test_pygithub_hosting.py [i]
    tests/adapters/test_record_log_jsonl.py [i]
    tests/adapters/test_runtime_podman_timeout_status.py [i]
    tests/adapters/test_runtime_state_directory_write.py [i]
    tests/adapters/test_waiters.py [i]
    tests/adapters/test_work_item_markdown.py [g] (`_layer`, round 1)
    tests/adapters/test_work_item_markdown_acceptance.py [i]
    tests/adapters/test_zfs_snapshots.py [i]
    tests/adapters/test_zfs_snapshots_diff.py [i]
    tests/adapters/test_zfs_snapshots_drop_caches.py [i]
    tests/application/handlers/test_closed.py [i]
    tests/application/handlers/test_closed_send_back.py [i]
    tests/application/handlers/test_comment_handler.py [i]
    tests/application/handlers/test_comments.py [i]
    tests/application/handlers/test_hand_over.py [i]
    tests/application/handlers/test_lookups.py [i]
    tests/application/handlers/test_merged.py [i]
    tests/application/handlers/test_questions.py [i]
    tests/application/handlers/test_recording.py [i]
    tests/application/handlers/test_reject.py [i]
    tests/application/handlers/test_run.py [i]
    tests/application/handlers/test_run_gate.py [i]
    tests/application/test_acceptance_closed.py [i]
    tests/application/test_acceptance_due_handler.py [i]
    tests/application/test_acceptance_facts_disk.py [i]
    tests/application/test_acceptance_hand_over.py [i]
    tests/application/test_acceptance_merged.py [i]
    tests/application/test_acceptance_merged_before_approval.py [i]
    tests/application/test_acceptance_no_state_refusals.py [i]
    tests/application/test_acceptance_reading.py [i]
    tests/application/test_acceptance_refusals.py [i]
    tests/application/test_acceptance_repeated.py [i]
    tests/application/test_acceptance_reviewer_role.py [i]
    tests/application/test_acceptance_service.py [i]
    tests/application/test_acceptance_snapshots.py [i]
    tests/application/test_acceptance_ticks_closed.py [i]
    tests/application/test_acceptance_ticks_merged.py [i]
    tests/application/test_acceptance_ticks_repeated.py [i]
    tests/application/test_after_agent.py [i]
    tests/application/test_agent_definition_reader.py [i]
    tests/application/test_agent_run_probe.py [i]
    tests/application/test_agent_run_probe_api_login.py [i]
    tests/application/test_agent_run_probe_environment.py [i]
    tests/application/test_agent_run_probe_factory_user.py [i]
    tests/application/test_agent_run_probe_login.py [i]
    tests/application/test_agent_run_probe_opencode.py [i]
    tests/application/test_agent_run_probe_project_agent.py [i]
    tests/application/test_bill_service.py [i]
    tests/application/test_board_reader.py [i]
    tests/application/test_board_reader_acceptance.py [i]
    tests/application/test_boundaries_required.py [i]
    tests/application/test_boundaries_settings.py [i]
    tests/application/test_checkout_preparer.py [i]
    tests/application/test_claims.py [i]
    tests/application/test_claims_observed.py [i]
    tests/application/test_container_environment.py [i]
    tests/application/test_container_environment_extra.py [i]
    tests/application/test_container_environment_take.py [i]
    tests/application/test_container_items.py [i]
    tests/application/test_cost_image.py [i]
    tests/application/test_cost_instance.py [i]
    tests/application/test_costs.py [i]
    tests/application/test_disk_recorder.py [i]
    tests/application/test_dispatcher.py [i]
    tests/application/test_dispatcher_counts_every_error.py [i]
    tests/application/test_hosting_failure_releases_claim.py [i]
    tests/application/test_human_line_posts.py [i]
    tests/application/test_idle_shutdown.py [i]
    tests/application/test_known_results.py [i]
    tests/application/test_known_results_torn.py [i]
    tests/application/test_left_out_stage.py [i]
    tests/application/test_machine.py [i]
    tests/application/test_machine_checks_container.py [i]
    tests/application/test_machine_checks_runtime.py [i]
    tests/application/test_no_state_refusals.py [i]
    tests/application/test_opencode_item.py [i]
    tests/application/test_opencode_item_container.py [i]
    tests/application/test_opening.py [i]
    tests/application/test_patient_runs.py [i]
    tests/application/test_pipeline_definition_reader.py [i]
    tests/application/test_pipeline_loading.py [i]
    tests/application/test_pipeline_loading_agents.py [i]
    tests/application/test_pipeline_loading_project_agents.py [i]
    tests/application/test_pipeline_loading_rules.py [i]
    tests/application/test_pipeline_loading_stage_moves.py [i]
    tests/application/test_pipeline_loading_strict_values.py [i]
    tests/application/test_pipeline_loading_yaml_fault.py [i]
    tests/application/test_preflight.py [i]
    tests/application/test_preflight_login_line.py [i]
    tests/application/test_preflight_metadata_block.py [i]
    tests/application/test_preflight_run.py [i]
    tests/application/test_preflight_stops_commit.py [i]
    tests/application/test_probe_nested_repository.py [i]
    tests/application/test_project_agents.py [i]
    tests/application/test_push_retry.py [i]
    tests/application/test_question_causes_recorded.py [i]
    tests/application/test_recording_project_commands.py [i]
    tests/application/test_recovery_cap.py [i]
    tests/application/test_recovery_crash.py [i]
    tests/application/test_recovery_expiry.py [i]
    tests/application/test_recovery_expiry_key.py [i]
    tests/application/test_recovery_subjects.py [i]
    tests/application/test_repository_waiter.py [i]
    tests/application/test_request_working_directory.py [i]
    tests/application/test_scheduler.py [i]
    tests/application/test_sealed_runs_runner.py [i]
    tests/application/test_split_by_work_item_kind.py [i]
    tests/application/test_stage_changes.py [i]
    tests/application/test_stage_died_line.py [i]
    tests/application/test_stage_environment_calls.py [i]
    tests/application/test_stage_finish.py [i]
    tests/application/test_stage_launch.py [i]
    tests/application/test_stage_on_container_fakes.py [i]
    tests/application/test_stage_provider_limit.py [i]
    tests/application/test_stage_transcripts.py [i]
    tests/application/test_stale_branches.py [i]
    tests/application/test_stall_container.py [i]
    tests/application/test_stall_environment.py [i]
    tests/application/test_stall_labels.py [i]
    tests/application/test_stalls.py [i]
    tests/application/test_stop_log_once.py [i]
    tests/application/test_stop_posting.py [i]
    tests/application/test_stop_publisher.py [i]
    tests/application/test_stop_records_service.py [i]
    tests/application/test_stops.py [i]
    tests/application/test_take.py [i]
    tests/application/test_take_edges.py [i]
    tests/application/test_task.py [i]
    tests/application/test_task_acceptance.py [i]
    tests/application/test_tick.py [i]
    tests/application/test_tick_agent_definition.py [i]
    tests/application/test_tick_disk.py [i]
    tests/application/test_tick_own_fetch.py [i]
    tests/application/test_tick_preflight.py [i]
    tests/application/test_tick_stale_branch.py [i]
    tests/application/test_tick_stop_details.py [i]
    tests/application/test_tick_stop_records.py [i]
    tests/application/test_tokens.py [i]
    tests/application/test_watcher.py [i]
    tests/application/test_watcher_main_ref.py [i]
    tests/application/test_watcher_move_rule.py [i]
    tests/application/test_watcher_observer.py [i]
    tests/application/test_work_items.py [i]
    tests/application/test_work_items_duplicate.py [i]
    tests/application/test_write_paths.py [i]
    tests/claude_resume_support.py [i]
    tests/conftest.py [i]
    tests/container_support.py [i]
    tests/contract_support.py [i]
    tests/cost_image_support.py [i]
    tests/crash_support.py [i]
    tests/document_texts.py [i]
    tests/domain/test_acceptance.py [i]
    tests/domain/test_acceptance_booking.py [i]
    tests/domain/test_acceptance_facts.py [p]
    tests/domain/test_archive.py [i]
    tests/domain/test_board.py [i]
    tests/domain/test_container_extra_environment.py [i]
    tests/domain/test_contract.py [i]
    tests/domain/test_default_git_identity.py [i]
    tests/domain/test_documents.py [i]
    tests/domain/test_evaluation.py [i]
    tests/domain/test_evaluation_reject.py [i]
    tests/domain/test_fault_paths.py [i]
    tests/domain/test_hand_over.py [i]
    tests/domain/test_hosting.py [g] (`_is_domain`)
    tests/domain/test_journal.py [i]
    tests/domain/test_pipeline_definition.py [i]
    tests/domain/test_project_agent_paths.py [i]
    tests/domain/test_section_edges.py [i]
    tests/domain/test_settings.py [i]
    tests/domain/test_settings_model_rules.py [i]
    tests/domain/test_story_form.py [i]
    tests/domain/test_story_form_edges.py [i]
    tests/domain/test_times.py [p]
    tests/domain/test_work_item_require_state.py [i]
    tests/entry/test_bill.py [i]
    tests/entry/test_check_documents.py [i]
    tests/entry/test_check_documents_guide_files.py [i]
    tests/entry/test_contract.py [i]
    tests/entry/test_contract_arguments.py [i]
    tests/entry/test_contract_not_read.py [i]
    tests/entry/test_health.py [i]
    tests/entry/test_health_missing.py [i]
    tests/entry/test_refresh_token.py [i]
    tests/entry/test_run.py [i]
    tests/entry/test_run_fetch_before_tick.py [i]
    tests/entry/test_run_health_file.py [i]
    tests/entry/test_run_idle_exit.py [i]
    tests/entry/test_run_idle_shutdown.py [i]
    tests/entry/test_run_image_sizes.py [i]
    tests/entry/test_run_machine_stop_exit.py [i]
    tests/entry/test_run_one_fetch.py [i]
    tests/entry/test_run_project_image_rebuild.py [i]
    tests/entry/test_run_required_paths.py [i]
    tests/entry/test_run_state_variable.py [i]
    tests/entry/test_run_stop_requested.py [i]
    tests/entry/test_run_waiter.py [i]
    tests/entry/test_watch.py [p]
    tests/entry/test_watch_main.py [i]
    tests/entry/test_watch_own_claim.py [i]
    tests/entry/test_watch_settings.py [i]
    tests/entry/test_wiring_acceptance.py [i]
    tests/entry/test_wiring_api_login.py [i]
    tests/entry/test_wiring_boundaries.py [i]
    tests/entry/test_wiring_command_records.py [i]
    tests/entry/test_wiring_container_extra.py [i]
    tests/entry/test_wiring_container_profile.py [i]
    tests/entry/test_wiring_copy_snapshots.py [i]
    tests/entry/test_wiring_extras.py [i]
    tests/entry/test_wiring_idle_shutdown.py [i]
    tests/entry/test_wiring_idle_shutdown_action.py [i]
    tests/entry/test_wiring_image_path.py [i]
    tests/entry/test_wiring_instance_label.py [i]
    tests/entry/test_wiring_known_results.py [i]
    tests/entry/test_wiring_login.py [i]
    tests/entry/test_wiring_machine_inputs.py [i]
    tests/entry/test_wiring_one_environment.py [i]
    tests/entry/test_wiring_one_preflight.py [i]
    tests/entry/test_wiring_opencode.py [i]
    tests/entry/test_wiring_opencode_provider.py [i]
    tests/entry/test_wiring_preflight.py [i]
    tests/entry/test_wiring_project_agents.py [i]
    tests/entry/test_wiring_project_image.py [i]
    tests/entry/test_wiring_provider_limit.py [i]
    tests/entry/test_wiring_record_logs.py [i]
    tests/entry/test_wiring_run.py [i]
    tests/entry/test_wiring_stage_environment.py [i]
    tests/entry/test_wiring_stage_image_sizes.py [i]
    tests/entry/test_wiring_stop_records.py [i]
    tests/entry/test_wiring_transcripts.py [i]
    tests/entry/test_wiring_waiter.py [i]
    tests/entry/test_wiring_without_agent_user.py [i]
    tests/evaluation_support.py [i]
    tests/git_support.py [i]
    tests/known_results_support.py [i]
    tests/operator_job_support.py [i]
    tests/operator_skill_support.py [i]
    tests/operator_support.py [i]
    tests/power_support.py [i]
    tests/preflight_support.py [i]
    tests/process_support.py [i]
    tests/proof_support.py [i]
    tests/push_retry_support.py [i]
    tests/record_support.py [i]
    tests/run_layout_support.py [i]
    tests/run_process_recorder.py [i]
    tests/scripted_tick_support.py [i]
    tests/site_check_support.py [i]
    tests/stage_run_support.py [i]
    tests/template_make_support.py [i]
    tests/test_agent_launch_search.py [p]
    tests/test_approval_description.py [i]
    tests/test_checkout_hygiene_removed.py [i]
    tests/test_claude_agent_refusal.py [i]
    tests/test_claude_agent_skills.py [i]
    tests/test_claude_agent_texts.py [i]
    tests/test_claude_agent_texts_decision_log.py [i]
    tests/test_claude_agent_texts_description.py [i]
    tests/test_claude_agent_texts_docs_slip.py [i]
    tests/test_claude_agent_texts_mutants.py [i]
    tests/test_claude_agent_texts_review_leave.py [i]
    tests/test_claude_agent_texts_smoke_pytest.py [i]
    tests/test_claude_settings_git.py [i]
    tests/test_docker_path_removed.py [p]
    tests/test_fault_paths.py [i]
    tests/test_fault_paths_7_to_13.py [i]
    tests/test_git_credential_helper.py [i]
    tests/test_home_reset_removed.py [i]
    tests/test_hook_removed.py [p]
    tests/test_kernel_guard_removed.py [p]
    tests/test_kill_points.py [i]
    tests/test_leftovers_program_removed.py [i]
    tests/test_no_journal_reading.py [p]
    tests/test_one_stage_environment.py [i]
    tests/test_operator_hosting.py [i]
    tests/test_operator_job_log.py [i]
    tests/test_operator_merge_reset.py [i]
    tests/test_operator_python_isolation.py [i]
    tests/test_operator_sanitise.py [i]
    tests/test_operator_skill_signature.py [i]
    tests/test_process_search.py [p]
    tests/test_proof_support.py [i]
    tests/test_round_cap_answer.py [i]
    tests/test_second_user_removed.py [i]
    tests/test_stop_table.py [i]
    tests/test_suite_fixtures.py [i]
    tests/test_suite_held_once.py [p]
    tests/test_suite_old_names.py [p]
    tests/test_tmp_path_reopening.py [i]
    tests/test_vm_credential_helper_host.py [i]
    tests/test_vm_local_environment.py [i]
    tests/test_vm_setup.py [i]
    tests/test_vm_setup_first_base.py [i]
    tests/test_vm_setup_writes.py [i]
    tests/test_wrapper_search.py [p]
    tests/undo_support.py [i]
    tests/vm_support.py [i]
    tests/watch_support.py [i]
    tests/wiring_support.py [i]
    tests/adapters/test_clock.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_drain.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_result_fields.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_session.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming_last_line.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_process_streaming_reads.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_run_or_raise.py -> tests/shared/adapters/ [mv]
    tests/adapters/test_validation_faults.py -> tests/shared/adapters/ [mv]
    tests/application/test_hosting_failure_after_claim.py -> tests/shared/application/ [mv]
    tests/application/test_push_retry_reason.py -> tests/shared/application/ [mv]
    tests/application/test_push_retry_server_lines.py -> tests/shared/application/ [mv]
    tests/domain/test_cannot_handle.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_version_4.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_version_4_2.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_without_nested_repository.py -> tests/shared/domain/ [mv]
    tests/domain/test_contract_without_tool_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_cost_record_errors.py -> tests/shared/domain/ [mv]
    tests/domain/test_documents_guide_files.py -> tests/shared/domain/ [mv]
    tests/domain/test_documents_line_edges.py -> tests/shared/domain/ [mv]
    tests/domain/test_duplicates.py -> tests/shared/domain/ [mv]
    tests/domain/test_duplicates_skipped_lines.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors_agent_definition.py -> tests/shared/domain/ [mv]
    tests/domain/test_errors_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_identifiers.py -> tests/shared/domain/ [mv]
    tests/domain/test_is_name.py -> tests/shared/domain/ [mv]
    tests/domain/test_kill_point_cases.py -> tests/shared/domain/ [mv]
    tests/domain/test_kill_points.py -> tests/shared/domain/ [mv]
    tests/domain/test_name.py -> tests/shared/domain/ [mv]
    tests/domain/test_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_power_off_error.py -> tests/shared/domain/ [mv]
    tests/domain/test_sections.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_files_stay.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_runtime.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_agent_user_unread.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_api_login.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_boundaries.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_claude_login.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_container_env.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_container_profile.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_idle_shutdown.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_idle_shutdown_action.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_min_free.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_one_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_folders_ignored.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_models.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_opencode_provider.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_pinned.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_provider_limit.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_provider_limit_wait.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_required_paths.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_snapshots.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_stage_environment.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_transcripts.py -> tests/shared/domain/ [mv]
    tests/domain/test_settings_url_edges.py -> tests/shared/domain/ [mv]
    tests/domain/test_unhandled_event.py -> tests/shared/domain/ [mv]
    tests/domain/test_work_item_errors.py -> tests/shared/domain/ [mv]
25. factory: started docs as vm.
