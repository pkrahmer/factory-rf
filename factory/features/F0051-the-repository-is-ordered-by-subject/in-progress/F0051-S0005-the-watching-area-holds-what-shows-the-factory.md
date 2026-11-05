---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 560
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T02:49:26.540948Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T02:49:26.547377Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T02:49:44.454039Z'
  stage: intake
  run: 32da5479f68a4b7ebcd4d64dac80909f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T02:49:49.337615Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T02:52:37.903702Z'
  stage: tests
  run: bb81af9547714623a9f183322ebe01db
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T02:52:43.319986Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-05T02:57:49.042852Z'
  stage: doing
  run: ba9d48b9a6704afc8c69459be6417919
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-05T02:57:54.414442Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-05T03:00:32.422734Z'
  stage: review
  run: 0992ce15260c4a1ea538a91824390e3f
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T03:00:37.573329Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-05T03:01:16.605763Z'
  stage: docs
  run: 29513458f9cd4fc3b91accc6c8fa8d47
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T03:01:22.304424Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-11-05T03:02:27.308497Z'
  stage: smoke-test
  run: 61dc22bdbd3a49f0b952002e6ca17507
---

# The watching area holds what shows the factory and what it costs

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `watching` area: everything that shows what the factory does and what it costs: cost records, bills, the machine measures, human waits, transcripts, the board, the watcher, the factory log and the health file (the human, 2026-11-04). Each of its 17 modules moves from its layer package to the same layer inside `factory.watching`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/watching/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.watching`, `factory.watching.domain`, `factory.watching.application`, `factory.watching.adapters`; and the same folders under `tests/watching/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.bills` → `factory.watching.domain.bills`
- `factory.domain.board` → `factory.watching.domain.board`
- `factory.domain.cost_records` → `factory.watching.domain.cost_records`
- `factory.domain.human_waits` → `factory.watching.domain.human_waits`
- `factory.domain.machine` → `factory.watching.domain.machine`
- `factory.domain.transcripts` → `factory.watching.domain.transcripts`
- `factory.application.board` → `factory.watching.application.board`
- `factory.application.costs` → `factory.watching.application.costs`
- `factory.application.machine` → `factory.watching.application.machine`
- `factory.application.transcripts` → `factory.watching.application.transcripts`
- `factory.application.watcher` → `factory.watching.application.watcher`
- `factory.adapters.cost_records_jsonl` → `factory.watching.adapters.cost_records_jsonl`
- `factory.adapters.machine_files` → `factory.watching.adapters.machine_files`
- `factory.adapters.transcript_files` → `factory.watching.adapters.transcript_files`
- `factory.adapters.record_log_jsonl` → `factory.watching.adapters.record_log_jsonl`
- `factory.adapters.factory_log` → `factory.watching.adapters.factory_log`
- `factory.adapters.health_file` → `factory.watching.adapters.health_file`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `watching` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/watching/<its layer>/` when every one of its imports from `factory` is a module of the `watching` area or of an area already moved before it and at least one is of `watching`.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The package docstrings are exactly: `factory.watching`: "The watching area: what shows the factory's work and what it costs."; each layer package: "The watching area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.watching.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.watching`, `factory.watching.domain`, `factory.watching.application`, `factory.watching.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `watching` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `watching` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.watching.domain.bills as m; print(m.__name__)"
```
Expect: `factory.watching.domain.bills`

```bash
test -e src/factory/domain/bills.py && echo still there || echo moved
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
   - Interface: The 17 moves are listed old → new, six in domain, five in application and six in adapters. The four new packages are named and their docstrings are given. The tester's and the coder's tasks are split by write paths. Nothing is missing.
   - Criteria: Each criterion is testable by one parametrized test. Criterion 1 has a row per module and checks the `AREAS` key, the import and the old path's absence, which is the standing answer 8 of the feature. Criterion 3 has a row per module and covers the three import forms, and criterion 4 is the test-move rule. The failing side is covered: the old path no longer exists and nothing imports it. The package docstring wording is not tested, as standing answer 8 says.
   - Smoke test: The three commands are runnable. Each `Expect:` line can be checked against the output. The pytest command passes no `-q`, and `addopts` in `pyproject.toml` sets a single `-q`, so the summary line is printed.
   - Architecture: Each module goes to the same layer inside `factory.watching`, so the layer rule is kept. The moves are made with `git mv`, nothing is re-exported, and the coder changes only `src/`.
   - Scope: The story is the watching area of feature decision 2, with decisions 4 and 5 applied. It changes no behaviour, and nothing in the feature's "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: Round 0. As the Interface asks, I made every test change the move needs in this run, before the code moves, under the leave of feature decision 5. Every earlier test keeps its name and checks the same thing.

   I added the `watching` row to `AREAS` in `tests/test_areas.py`, holding the 17 modules of the table. Nothing else in that module changed. Its test functions are already parametrized over `AREAS`, so I wrote no new functions:
   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (rows `watching.<layer>.<name>`). The key and its modules are the new `AREAS["watching"]` entry.
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.watching`, `factory.watching.adapters`, `factory.watching.application`, `factory.watching.domain`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module; `source_search.imports` covers the three import forms)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own checks the moved modules under `tests/watching/`.
   - criteria 5 and 6: these are the closing ones and are not tested.

   Test changes (feature decision 5):
   1. I rewrote every `factory.<layer>.<name>` path of the 17 modules under `tests/` (leaving out `tests/test_areas.py`) to `factory.watching.<layer>.<name>`, with sed. That touched 117 files, and then I ran `ruff check --fix tests` and `ruff format tests`. No `from factory.<layer> import <name>` form of a moved module existed, so no import line needed splitting.
   2. I changed one guard that pins the old layout: in `tests/application/test_tick.py::test_the_tick_knows_no_run_record_and_no_lock`, the row `"application/watcher.py"` is now `"watching/application/watcher.py"`. No other test names a path of a moved source or test module.
   3. I created empty `tests/watching/__init__.py` and `tests/watching/{domain,application,adapters}/__init__.py`.
   4. I moved 34 test modules with `git mv` to the same layer under `tests/watching/`. These are the ones criterion 4's rule selects once the imports are rewritten.
      - From `tests/domain/` (20): test_acceptance_booking, test_acceptance_refusal_edges, test_archive_texts, test_bills, test_bills_model_time, test_board, test_board_absent_values, test_cost_record_denials, test_cost_record_instance, test_cost_record_machine, test_cost_record_model_seconds, test_cost_records, test_human_waits, test_journal_stamps, test_login_records, test_machine, test_tool_use_model, test_tool_uses, test_tool_uses_replayed_lines, test_transcript_ref.
      - From `tests/application/` (4): test_acceptance_ticks_merged, test_bill_service, test_machine, test_transcript_keeper.
      - From `tests/adapters/` (10): test_cost_records_jsonl, test_cost_records_jsonl_denials, test_cost_records_jsonl_instance, test_cost_records_jsonl_login, test_cost_records_jsonl_model_seconds, test_factory_log, test_machine_files, test_runtime_tool_uses, test_transcript_files, test_waiters.
      - None of them uses `__file__` for a path, and no other file names them.

   Files I created: the four `tests/watching/**/__init__.py` files. Earlier test files I changed: `tests/test_areas.py`, `tests/application/test_tick.py`, and the import lines of the 117 files the sed touched, which include the support modules and `tests/conftest.py`. The 34 modules above were moved.

   Run: `uv run pytest -q` over the 105 changed or moved test files. It stops at collection with `ModuleNotFoundError: No module named 'factory.watching'` (first in `tests/bill_support.py:7`, reached through `tests/acceptance_walk.py`). That is the right reason. The runner could not import `factory.watching`, its three layer packages, or any of the 17 modules under them. `make lint`: `lint: green (0.1 s)`.

   A note for the coder: with the source moved, `pyproject.toml` may still have per-file-ignores under old `src/factory/<layer>/` paths for these modules. The coder may also need to check the `security/duplicates-baseline.txt` entries. I did not check either; both are outside my write paths.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Round 0. I changed only `src/`.

   What I built:
   - New packages, with the docstrings exactly as the Interface gives them: `src/factory/watching/__init__.py`, `src/factory/watching/domain/__init__.py`, `src/factory/watching/application/__init__.py` and `src/factory/watching/adapters/__init__.py`.
   - I moved the 17 modules of the table with `git mv` from `src/factory/<layer>/<name>.py` to `src/factory/watching/<layer>/<name>.py`. Their content is unchanged.
   - I rewrote every `factory.<layer>.<name>` import of a moved module under `src/` with sed, using a word boundary so that `machine_stop_exit` and `machine_files` stay untouched. After that I ran `ruff check --fix` and `ruff format` to re-sort the import blocks. 53 files in `src/` changed, by import lines only. No `from factory.<layer> import <name>` form and no relative import of a moved module existed. Nothing is re-exported at an old path.
   - Check: `make check` is green (`test: green (117.4 s)`, `check: green`, total coverage 99.26 %).

   Main choice: a mechanical rename of the import paths, with the module content unchanged. I rejected leaving re-export shims at the old paths: feature decision 4 forbids them.

   Refactor step: I read the diff. It holds only renamed import lines and re-sorted import blocks, so there was nothing to change.

   Description: the journal did not change the meaning of the task.

   Noticed, not touched:
   - `security/duplicates-baseline.txt` lines 22 and 23 still name `src/factory/domain/cost_records.py`, which now lives at `src/factory/watching/domain/cost_records.py`. The baseline is outside my write paths. `make duplicates` is a record, not a check, so these two known findings may show as "gone" and two as "new" until the file is updated.
   - `pyproject.toml` has no per-file ignore under an old path of a moved module, so it needs no change.

   `check`: check: green
   `duplicates`: duplicates: 7 new, 38 known, 5 gone
8. factory: started review as vm.
9. reviewer: Round 0 review of `git diff main...HEAD -- . ':!factory'` against the work item.

   no findings

   What I checked:
   - Group 1 (criteria): criteria 1 to 4 are rows of the parametrized tests in `tests/test_areas.py`, which run over `AREAS`. The new `watching` row holds exactly the 17 modules of the table, and nothing else in that module changed. Criterion 1's failing side (the old file still exists) and criterion 3's (an import from the old path) are covered by the same rows. The wording of the package docstrings is not tested, as the feature's standing answer 8 says. The coder's `make check` was green (entry 7: `check: green`, coverage 99.26 %).
   - Group 2 (architecture): each of the 17 files moved with a rename to the same layer inside `factory.watching`. 12 are identical (R100) or differ only in import lines. Outside them, the `src/` diff changes only import lines and the import blocks ruff re-sorted. No old path remains under `src/` or `tests/` (checked with grep), and nothing is re-exported. The four package docstrings match the Interface word for word.
   - Group 3 (security): no markers, no secrets, no new string-built commands.
   - Group 4 (quality): there is no new logic. `make duplicates` reports `7 new, 38 known, 5 gone`. Two of the new findings are the old dead-code entries for `cost_records.py` (`attempt`, `ok`), now under the new path. The other new ones (the `store_free_bytes`, `dataset_free_bytes` and `memory_peak_since_boot_bytes` fields of `cost_records.py`, which kept its content in the move, and two similar-code pairs that only changed key) were not caused by this diff's logic.
   - Group 5 (hygiene): the journal states the main choice (a mechanical rename, no shims) and what was rejected. The Description matches what was built. The docs criterion matches the pattern of S0001 to S0004.

   Open, not findings:
   - `security/duplicates-baseline.txt:22-23` still name `src/factory/domain/cost_records.py`. That file is outside every role's write path, so only the human can update it to `src/factory/watching/domain/cost_records.py`. `make duplicates` is a record, not a check.
   - For the documenter: two moved test modules are still named at their old paths in the project guide, `tests/adapters/test_waiters.py` (`docs/project-guide/stages.md:199`) and `tests/domain/test_archive_texts.py` (`docs/project-guide/watching.md:152`). They now live at `tests/watching/adapters/test_waiters.py` and `tests/watching/domain/test_archive_texts.py`. The documenters of S0003 and S0004 updated moved test paths under the same criterion wording.

   Earlier tests (item 6). Each of these was changed under the leave of feature decision 5, which the story's Interface names. Only import lines and the paths of moved modules changed, plus the `git mv` of the test modules criterion 4 selects. Every test keeps its name and what it checks.
   - tests/acceptance_walk.py: feature decision 5 (imports)
   - tests/adapters/test_health_file.py: feature decision 5 (imports)
   - tests/adapters/test_opencode_events.py: feature decision 5 (imports)
   - tests/adapters/test_record_log_jsonl.py: feature decision 5 (imports)
   - tests/adapters/test_record_log_jsonl_torn.py: feature decision 5 (imports)
   - tests/application/handlers/test_closed.py: feature decision 5 (imports)
   - tests/application/handlers/test_hand_over.py: feature decision 5 (imports)
   - tests/application/handlers/test_merged.py: feature decision 5 (imports)
   - tests/application/handlers/test_run.py: feature decision 5 (imports)
   - tests/application/test_acceptance_closed.py: feature decision 5 (imports)
   - tests/application/test_acceptance_facts_disk.py: feature decision 5 (imports)
   - tests/application/test_acceptance_hand_over.py: feature decision 5 (imports)
   - tests/application/test_acceptance_merged.py: feature decision 5 (imports)
   - tests/application/test_acceptance_merged_before_approval.py: feature decision 5 (imports)
   - tests/application/test_acceptance_reading.py: feature decision 5 (imports)
   - tests/application/test_acceptance_refusals.py: feature decision 5 (imports)
   - tests/application/test_acceptance_repeated.py: feature decision 5 (imports)
   - tests/application/test_acceptance_service.py: feature decision 5 (imports)
   - tests/application/test_agent_run_probe.py: feature decision 5 (imports)
   - tests/application/test_board_in_progress.py: feature decision 5 (imports)
   - tests/application/test_board_reader.py: feature decision 5 (imports)
   - tests/application/test_board_reader_acceptance.py: feature decision 5 (imports)
   - tests/application/test_cost_image.py: feature decision 5 (imports)
   - tests/application/test_cost_instance.py: feature decision 5 (imports)
   - tests/application/test_cost_record_machine_measures.py: feature decision 5 (imports)
   - tests/application/test_costs.py: feature decision 5 (imports)
   - tests/application/test_costs_denials.py: feature decision 5 (imports)
   - tests/application/test_costs_died_text.py: feature decision 5 (imports)
   - tests/application/test_costs_login.py: feature decision 5 (imports)
   - tests/application/test_costs_model_seconds.py: feature decision 5 (imports)
   - tests/application/test_costs_provider_limit.py: feature decision 5 (imports)
   - tests/application/test_disk_recorder.py: feature decision 5 (imports)
   - tests/application/test_disk_space_interface.py: feature decision 5 (imports)
   - tests/application/test_dispatcher.py: feature decision 5 (imports)
   - tests/application/test_human_line_posts.py: feature decision 5 (imports)
   - tests/application/test_pipeline_loading.py: feature decision 5 (imports)
   - tests/application/test_preflight_stops_commit.py: feature decision 5 (imports)
   - tests/application/test_recording_project_commands.py: feature decision 5 (imports)
   - tests/application/test_recovery_crash.py: feature decision 5 (imports)
   - tests/application/test_repository_waiter.py: feature decision 5 (imports)
   - tests/application/test_scheduler.py: feature decision 5 (imports)
   - tests/application/test_stage_known_results.py: feature decision 5 (imports)
   - tests/application/test_stage_run.py: feature decision 5 (imports)
   - tests/application/test_stage_tool_uses.py: feature decision 5 (imports)
   - tests/application/test_stage_transcripts.py: feature decision 5 (imports)
   - tests/application/test_stop_log_once.py: feature decision 5 (imports)
   - tests/application/test_stop_publisher.py: feature decision 5 (imports)
   - tests/application/test_stop_records_service.py: feature decision 5 (imports)
   - tests/application/test_stops.py: feature decision 5 (imports)
   - tests/application/test_tick.py: feature decision 5 (imports, and the moved module's file path `watching/application/watcher.py` in the guard's row)
   - tests/application/test_tick_stop_records.py: feature decision 5 (imports)
   - tests/application/test_watcher.py: feature decision 5 (imports)
   - tests/application/test_watcher_acceptance.py: feature decision 5 (imports)
   - tests/application/test_watcher_main_ref.py: feature decision 5 (imports)
   - tests/application/test_watcher_move_rule.py: feature decision 5 (imports)
   - tests/application/test_watcher_observer.py: feature decision 5 (imports)
   - tests/bill_support.py: feature decision 5 (imports)
   - tests/conftest.py: feature decision 5 (imports)
   - tests/container_support.py: feature decision 5 (imports)
   - tests/cost_records_support.py: feature decision 5 (imports)
   - tests/disk_support.py: feature decision 5 (imports)
   - tests/domain/test_acceptance_before_approval.py: feature decision 5 (imports)
   - tests/domain/test_contract.py: feature decision 5 (imports)
   - tests/domain/test_times.py: feature decision 5 (imports and the module path string `factory.watching.domain.cost_records`)
   - tests/entry/test_bill.py: feature decision 5 (imports)
   - tests/entry/test_health.py: feature decision 5 (imports)
   - tests/entry/test_health_missing.py: feature decision 5 (imports)
   - tests/entry/test_run.py: feature decision 5 (imports)
   - tests/entry/test_watch.py: feature decision 5 (imports)
   - tests/entry/test_watch_acceptance.py: feature decision 5 (imports)
   - tests/entry/test_wiring_boundaries.py: feature decision 5 (imports)
   - tests/entry/test_wiring_command_records.py: feature decision 5 (imports)
   - tests/entry/test_wiring_known_results.py: feature decision 5 (imports)
   - tests/entry/test_wiring_machine_inputs.py: feature decision 5 (imports)
   - tests/entry/test_wiring_stop_records.py: feature decision 5 (imports)
   - tests/entry/test_wiring_transcripts.py: feature decision 5 (imports)
   - tests/known_results_support.py: feature decision 5 (imports)
   - tests/machine_readings_support.py: feature decision 5 (imports)
   - tests/observing_runtime.py: feature decision 5 (imports)
   - tests/power_support.py: feature decision 5 (imports)
   - tests/proof_support.py: feature decision 5 (imports)
   - tests/recording_log.py: feature decision 5 (imports)
   - tests/stage_run_support.py: feature decision 5 (imports)
   - tests/test_areas.py: the story's Interface (the `watching` row of `AREAS`, nothing else)
   - tests/tool_use_support.py: feature decision 5 (imports)
   - tests/adapters/test_cost_records_jsonl.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_cost_records_jsonl_denials.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_cost_records_jsonl_instance.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_cost_records_jsonl_login.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_cost_records_jsonl_model_seconds.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_factory_log.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_machine_files.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_runtime_tool_uses.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_transcript_files.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/adapters/test_waiters.py -> tests/watching/adapters/: feature decision 5 (git mv, imports)
   - tests/application/test_acceptance_ticks_merged.py -> tests/watching/application/: feature decision 5 (git mv, imports)
   - tests/application/test_bill_service.py -> tests/watching/application/: feature decision 5 (git mv, imports)
   - tests/application/test_machine.py -> tests/watching/application/: feature decision 5 (git mv, imports)
   - tests/application/test_transcript_keeper.py -> tests/watching/application/: feature decision 5 (git mv, imports)
   - tests/domain/test_acceptance_booking.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_acceptance_refusal_edges.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_archive_texts.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_bills.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_bills_model_time.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_board.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_board_absent_values.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_cost_record_denials.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_cost_record_instance.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_cost_record_machine.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_cost_record_model_seconds.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_cost_records.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_human_waits.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_journal_stamps.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_login_records.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_machine.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_tool_use_model.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_tool_uses.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_tool_uses_replayed_lines.py -> tests/watching/domain/: feature decision 5 (git mv, imports)
   - tests/domain/test_transcript_ref.py -> tests/watching/domain/: feature decision 5 (git mv, imports)

   I compared each moved test module with its file on `main`: none differs in anything but import lines.
10. factory: started docs as vm.
11. documenter: Round 0. Only documents changed, so I ran no `make check`. The factory's checks after this stage decide.

    Files changed:
    - `docs/project-guide/README.md`: the layout section (line 9) now names the area `watching` and what it holds, in one sentence. The index lines for `costs.md`, `watching.md` and `processes-and-checks.md` now give the new module paths.
    - `docs/project-guide/costs.md`, `docs/project-guide/watching.md`, `docs/project-guide/agents.md`, `docs/project-guide/work-items.md`, `docs/project-guide/processes-and-checks.md`: each module path of the table (17 modules) is now `factory.watching.<layer>.<name>`. This includes the import line in the runnable example in `costs.md` (line 45). I ran a pattern replace that does not touch similar names such as `machine_stop_exit`, then grepped again: no old path of a moved module remains in the README, the operator guide or the project guide.
    - `docs/project-guide/stages.md` and `docs/project-guide/watching.md`: the reviewer's two moved test paths are now `tests/watching/adapters/test_waiters.py` and `tests/watching/domain/test_archive_texts.py`.

    Cross-read and found current: `README.md` and `docs/operator-guide.md` name no moved module path, so I left them unchanged. I did not touch `docs/decisions.md`, as the criterion says. I added no entry there, so no "Rejected" line is missing.

    I did not re-run the runnable example in `costs.md`. Its only change is the import path, and the module exists at the new path.

    Code findings: none. The code matches the Interface.

    Stale text I saw and did not touch (not mine to fix):
    - `security/duplicates-baseline.txt` lines 22 and 23 still name `src/factory/domain/cost_records.py`. The file is outside every role's write path, as the coder and reviewer noted.

    `check`: check: green (not run again: passed on tree 31bf5bf02204 at 2026-11-05T02:55:37Z)
    `secrets`: secrets: green (3.5 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
13. smoke-tester: Round 0 smoke test. I ran the three commands of `## Smoke test` from the repository root, in order. I fixed nothing.

    1. `uv run python -c "import factory.watching.domain.bills as m; print(m.__name__)"`
    ```
    Bytecode compiled 4164 files in 52ms
    factory.watching.domain.bills
    ```
    Met `Expect: factory.watching.domain.bills`. The first line is uv's own note on stderr, which shows because I captured stderr too. The command's stdout is just the expected name.

    2. `test -e src/factory/domain/bills.py && echo still there || echo moved`
    ```
    moved
    ```
    Met `Expect: moved`.

    3. `uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed`
    ```
    1
    ```
    Met `Expect: 1`. The summary line it counted was `396 passed in 20.23s`, from a second run without the `grep -c`.

    The acceptance criteria, read again:
    - Criteria 1 to 4: the `tests/test_areas.py` run covers them, with rows per module for the `watching` area, and all 396 tests passed. That agrees with commands 1 and 2.
    - Criterion 5 (`make check`): no command here touches it, and nothing in this run contradicts it.
    - Criterion 6 (docs): no command reads a document, so nothing contradicts it.

    Findings: none.

    Open, not a finding: `security/duplicates-baseline.txt:22-23` still names `src/factory/domain/cost_records.py`. The coder, the reviewer and the documenter all reported it. The file is outside every role's write path, and `make duplicates` is a record, not a check.
