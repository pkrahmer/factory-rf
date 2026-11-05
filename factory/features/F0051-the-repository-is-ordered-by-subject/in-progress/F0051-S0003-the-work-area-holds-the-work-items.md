---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 558
comments_read: [6647217933]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T01:30:42.907085Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T01:30:42.914340Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T01:31:01.535266Z'
  stage: intake
  run: 383f628a60eb4660ab6a3731e3c3b398
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T01:38:56.739185Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T01:38:59.126382Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T01:39:17.476226Z'
  stage: intake
  run: d2f740c301a64b8ba5bf665f4dacc5e0
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T01:39:22.530581Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T01:40:31.695373Z'
  stage: tests
  run: e27f1848590449218b893d5f81600b43
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T01:40:37.024813Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T01:45:47.998402Z'
  stage: doing
  run: 940de3a8374c4d2d88462ab2d153e424
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-05T01:45:53.679034Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-05T01:49:09.274320Z'
  stage: tests
  run: 16e4c8a0b90a451f852384fe61930919
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-05T01:49:14.849032Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-05T01:54:18.713204Z'
  stage: doing
  run: 308cabdb8428490bb36c3a77cfd54091
---

# The work area holds the work items

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `work` area: work items, their journal, the story form, answers, decisions, send-backs, the archive and the feature acceptance. Each of its 14 modules moves from its layer package to the same layer inside `factory.work`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/work/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`; and the same folders under `tests/work/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.acceptance` → `factory.work.domain.acceptance`
- `factory.domain.answers` → `factory.work.domain.answers`
- `factory.domain.archive` → `factory.work.domain.archive`
- `factory.domain.decisions` → `factory.work.domain.decisions`
- `factory.domain.journal` → `factory.work.domain.journal`
- `factory.domain.labels` → `factory.work.domain.labels`
- `factory.domain.move_rule` → `factory.work.domain.move_rule`
- `factory.domain.send_back` → `factory.work.domain.send_back`
- `factory.domain.story_form` → `factory.work.domain.story_form`
- `factory.domain.work_item` → `factory.work.domain.work_item`
- `factory.application.acceptance` → `factory.work.application.acceptance`
- `factory.application.acceptance_reading` → `factory.work.application.acceptance_reading`
- `factory.application.work_items` → `factory.work.application.work_items`
- `factory.adapters.work_item_markdown` → `factory.work.adapters.work_item_markdown`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `work` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/work/<its layer>/` when every one of its imports from `factory` is a module of the `work` area or of an area already moved before it and at least one is of `work`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. For every module of the table above (one row each), `importlib.import_module("factory.work.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist. `AREAS` of `tests/test_areas.py` has a `work` key whose modules are exactly the 14 of the table.
2. Every package of the Interface (`factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module), in each form `imports()` of `tests/source_search.py` reads: `import factory.x.y`, `from factory.x.y import z` and `from factory.x import y`.
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `work` and the areas moved before it (`shared` and `hosting`).
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `work` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.work.domain.acceptance as m; print(m.__name__)"
```
Expect: `factory.work.domain.acceptance`

```bash
test -e src/factory/domain/acceptance.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface rule without a criterion: "`tests/test_areas.py`: the table `AREAS` gains the row of `work` with the modules above". No criterion tests it. The smoke test only counts a passing run, which passes without the row. Suggest a criterion such as "`AREAS` has a `work` key whose modules are exactly the 14 of the table".
   2. Interface rule without a criterion: the folders `tests/work/`, `tests/work/domain/`, `tests/work/application/` and `tests/work/adapters/` each get an `__init__.py`. Criterion 2 covers only the four `src` packages. Suggest adding the four test packages to criterion 2, or a separate criterion.
   3. Interface rule without a criterion: the new `src` packages' `__init__.py` holds a one-line docstring. Criterion 2 only says "has a docstring", not one line. Say whether one line is to be tested.
   4. Criterion 1 says "for `handlers`, the folder", but the table has no `handlers` module. This looks like a leftover from another story. Please remove it or say what it means.
   5. Criterion 4 and the Interface rule on test moves depend on "areas moved before it". Say which areas those are when this story runs: S0001 (`shared`) and S0002 (`hosting`) only, or also S0013's nothing. Name them, so the test can compute the set.
   6. Criterion 3 should say that it covers both `import factory.x.y` and `from factory.x import y` forms. As written, "an import line that names `factory.<layer>.<name>`" misses `from factory.domain import journal`.
   Format check passed. The architecture and scope fit F0051 (decisions 1 to 5, and the map to `work`). With these answered I would accept.
4. 2026-11-05 human: Answers of the human:

   1. Yes, as you suggest: criterion 1 also says that `AREAS` has a `work` key whose modules are exactly the 14 of the table.
   2. No criterion. The four test packages are structure; pytest's collection of same-named test modules already fails without them.
   3. "Has a docstring" is enough; one line is not tested.
   4. A leftover: remove "for `handlers`, the folder" from criterion 1. Only S0007 moves `handlers`.
   5. The areas moved before this story are `shared` (S0001) and `hosting` (S0002). S0013 moved nothing.
   6. Yes, both forms: `import factory.x.y`, `from factory.x.y import z` and `from factory.x import y`, as S0001's test already reads them with `imports()` from `tests/source_search.py`.

   These answers hold for S0004 to S0007 as well; feature decision 8 records them.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: names 4 new packages and 14 concrete old → new module moves, each a `git mv`. The `AREAS` row rule now has a criterion (see below).
   - Criteria: each is testable by one test function. I carried in the human's answers from journal entry 4. Criterion 1 now also says `AREAS` has a `work` key whose modules are exactly the 14 of the table (answer 1). I removed the "for `handlers`, the folder" leftover (answer 4). Criterion 3 now names the three import forms that `imports()` of `tests/source_search.py` reads (answer 6). Criterion 4 names the earlier areas as `shared` and `hosting` (answer 5). I added no criterion for the test packages' `__init__.py` files (answer 2) and none for a one-line docstring (answer 3). Each rule has its failing side: criteria 1 and 3 check that the old path is gone, and criterion 4 checks that no test module is left behind.
   - Smoke test: the three commands are runnable. Each `Expect:` line is checkable. The pytest command passes no `-q`, and I did not check the pytest configuration's `addopts`. The `tail -1 | grep -c passed` expectation needs a summary line, so the tester should confirm `addopts` doesn't set `-qq`.
   - Architecture: each module moves to the same layer inside `factory.work`, which fits the areas-with-layers design (feature decisions 1, 2 and 4). No re-export is left.
   - Scope: within F0051 and not in its "Out of scope". The tester's leave is feature decision 5, and the standing answers are decision 8.
7. factory: started tests as vm.
8. tester: I added the `work` row to the table `AREAS` in `tests/test_areas.py`. It holds the 14 modules of the Interface's table, in that order. Nothing else in the module changed, as the Interface asks. The tests S0001 and S0002 wrote are generic over `AREAS`, so the new row gives each criterion its cases for `work`:

   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer, one row per module, ids `work.<layer>.<name>`. The "exactly the 14" part is the `work` row of `AREAS` itself. I wrote no separate test that compares the table with a copy of itself.
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring, rows `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`.
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path, one row per module. It uses `imports()` of `tests/source_search.py`, which covers all three import forms.
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. `_in_a_moved_area` now counts the `work` modules, under their new and old paths, beside `shared` and `hosting`. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own also checks the test modules that move to `tests/work/`.
   - criterion 5: `make check`, run by the coder and the factory; no test function.
   - criterion 6: docs stage; no test function.

   Files created: none. Changed: tests/test_areas.py, the row only. This module was written by S0001 and S0002 of this feature; the Interface orders this change and feature decision 5 covers it.

   Run: `uv run pytest -q tests/test_areas.py` fails on the `work` rows. Only the last five lines were printed: all five are `work` rows of the old-path test, which fails because files still import the old paths. The test runner could not import these modules: `factory.work.domain.acceptance`, `factory.work.domain.answers`, `factory.work.domain.archive`, `factory.work.domain.decisions`, `factory.work.domain.journal`, `factory.work.domain.labels`, `factory.work.domain.move_rule`, `factory.work.domain.send_back`, `factory.work.domain.story_form`, `factory.work.domain.work_item`, `factory.work.application.acceptance`, `factory.work.application.acceptance_reading`, `factory.work.application.work_items`, `factory.work.adapters.work_item_markdown`, and the packages `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`. `make lint`: green.

   Open: on the intake's note about `addopts` and `-qq` in the smoke test's pytest command: following the stage's rule against reading tool configuration, I did not check it.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Round 0. The source side of the move is done. The rest is test work, which only the tester may write, so I am sending it to the tester with the exact changes below, the way S0002 did (its entries 7 and 9). With all of them in my working tree, `make check` was green (`test: green (123.7 s)`, `check: green`). The factory drops my edits under `tests/`, so the tester has to make them again.

    What I built (in my write paths):
    - `src/factory/work/__init__.py`, `src/factory/work/domain/__init__.py`, `src/factory/work/application/__init__.py`, `src/factory/work/adapters/__init__.py`, each with a one-line docstring.
    - The 14 modules of the Interface, moved with `git mv` to `src/factory/work/<layer>/<name>.py`. Only their import lines changed.
    - Every import under `src/` of an old path now names `factory.work.<layer>.<name>`: 45 files, all of them import lines, re-sorted by `ruff check --fix` and `ruff format`. That includes the two `from factory.domain import journal` lines in `work/domain/work_item.py` and `work/domain/decisions.py`.
    - `uv run python -m factory.entry.contract` leaves the schemas unchanged. `lint-imports`: 4 kept, 0 broken.

    Main choice: I followed S0002's split (the coder moves `src/`, the tester moves and rewrites `tests/`). I rejected ending with `review` and leaving the test edits in the tree, because the factory would drop them and `make check` would be red.

    Test changes for the tester. The Interface's leave (feature decision 5) covers them, and every test keeps its name and checks the same thing:
    1. Under `tests/`, rewrite every word-bounded dotted reference to the 14 modules, `factory.<layer>.<name>` → `factory.work.<layer>.<name>`, with sed over the regex `\bfactory\.(domain\.(acceptance|answers|archive|decisions|journal|labels|move_rule|send_back|story_form|work_item)|application\.(acceptance|acceptance_reading|work_items)|adapters\.work_item_markdown)\b` → `factory.work.\1`. That covers 168 files. Leave `tests/test_areas.py` unchanged. Three spots need a hand edit:
       - `tests/domain/test_provider_limit_stall_text.py`: `from factory.domain import decisions, journal` → `from factory.work.domain import decisions, journal`
       - `tests/domain/test_journal_causes.py`: `from factory.domain import decisions, journal, work_item` → `from factory.work.domain import decisions, journal, work_item`
       - `tests/application/test_tick.py`, the parametrize row of `test_the_tick_knows_no_run_record_and_no_lock`: `"application/work_items.py"` → `"work/application/work_items.py"`

       Then run `ruff check --fix tests` and `ruff format tests`.
    2. Create empty `tests/work/__init__.py`, `tests/work/domain/__init__.py`, `tests/work/application/__init__.py` and `tests/work/adapters/__init__.py`. Then `git mv` these 34 modules to the same layer under `tests/work/`. They are exactly the modules that criterion 4's rule selects after step 1:
       - from `tests/domain/` (29): test_acceptance, test_acceptance_description, test_acceptance_facts, test_acceptance_facts_disk, test_acceptance_facts_human, test_acceptance_facts_limit, test_acceptance_status, test_answers, test_answers_round_cap, test_archive, test_hand_over, test_journal, test_journal_acceptance, test_journal_causes, test_journal_records, test_labels, test_post_texts_notes, test_provider_limit_stall_text, test_question_texts, test_section_edges, test_send_back_records, test_stall_reason_removed, test_stall_texts, test_story_form, test_story_form_edges, test_story_place, test_work_item, test_work_item_require_state, test_work_item_snapshot
       - from `tests/adapters/` (5): test_journal_as_data, test_journal_causes_file, test_journal_stamps_file, test_work_item_markdown, test_work_item_markdown_acceptance
       - none from `tests/application/`

       None of them reads a path relative to its own file. No other test, Makefile or pyproject entry names their old paths.

    Refactor: the diff is mechanical (moves and import lines), so nothing needed changing.

    Noticed, not touched:
    - `make duplicates` reports `11 new, 34 known, 8 gone`. The new findings are the known findings of `work_item_markdown.py`, `move_rule.py` and the similar-code pairs under their new `factory.work.*` paths. `security/duplicates-baseline.txt` needs those paths, as the human did for S0002 in 63bd1e18b; it is outside my write paths.
    - Two of the "gone" findings are unrelated to this story: the `claude_runtime`/`opencode_runtime` similar-code pair and `fake_containers.calls`.
    - The docs that name the old paths (`docs/project-guide/*.md`) are for the docs stage (criterion 6).

    The factory left out changes outside the write paths: tests/acceptance_support.py, tests/acceptance_walk.py, tests/adapters/test_journal_as_data.py, tests/adapters/test_journal_causes_file.py, tests/adapters/test_journal_stamps_file.py, tests/adapters/test_work_item_markdown.py, tests/adapters/test_work_item_markdown_acceptance.py, tests/application/handlers/conftest.py, tests/application/handlers/test_closed.py, tests/application/handlers/test_closed_send_back.py, tests/application/handlers/test_comment_handler.py, tests/application/handlers/test_comments.py, tests/application/handlers/test_hand_over.py, tests/application/handlers/test_handler_subjects.py, tests/application/handlers/test_lookups.py, tests/application/handlers/test_merged.py, tests/application/handlers/test_questions.py, tests/application/handlers/test_recording.py, tests/application/handlers/test_reject.py, tests/application/handlers/test_run_gate.py, tests/application/test_acceptance_closed.py, tests/application/test_acceptance_due_handler.py, tests/application/test_acceptance_facts_disk.py, tests/application/test_acceptance_facts_human.py, tests/application/test_acceptance_hand_over.py, tests/application/test_acceptance_merged.py, tests/application/test_acceptance_merged_before_approval.py, tests/application/test_acceptance_no_state_refusals.py, tests/application/test_acceptance_reading.py, tests/application/test_acceptance_refusals.py, tests/application/test_acceptance_repeated.py, tests/application/test_acceptance_reviewer_role.py, tests/application/test_acceptance_service.py, tests/application/test_acceptance_snapshots.py, tests/application/test_acceptance_ticks_closed.py, tests/application/test_acceptance_ticks_merged.py, tests/application/test_after_agent.py, tests/application/test_after_agent_edges.py, tests/application/test_board_reader.py, tests/application/test_board_reader_acceptance.py, tests/application/test_claims.py, tests/application/test_claims_observed.py, tests/application/test_claims_refusals.py, tests/application/test_costs.py, tests/application/test_dispatcher.py, tests/application/test_dispatcher_without_state.py, tests/application/test_hosting_failure_releases_claim.py, tests/application/test_human_line_posts.py, tests/application/test_left_out_stage.py, tests/application/test_no_branch_check.py, tests/application/test_no_state_refusals.py, tests/application/test_opening.py, tests/application/test_question_causes_recorded.py, tests/application/test_recovery_cap.py, tests/application/test_recovery_crash.py, tests/application/test_recovery_expiry.py, tests/application/test_request_working_directory.py, tests/application/test_split_by_work_item_kind.py, tests/application/test_stage_changes.py, tests/application/test_stage_finish.py, tests/application/test_stage_finish_causes.py, tests/application/test_stage_known_results.py, tests/application/test_stage_launch.py, tests/application/test_stage_nested_repository.py, tests/application/test_stage_on_container_fakes.py, tests/application/test_stage_run_acceptance.py, tests/application/test_stage_time_limited_report.py, tests/application/test_stall_edges.py, tests/application/test_stall_environment.py, tests/application/test_stall_labels.py, tests/application/test_stall_reasons_recorded.py, tests/application/test_stalls.py, tests/application/test_task.py, tests/application/test_task_acceptance.py, tests/application/test_tick.py, tests/application/test_tick_stale_branch.py, tests/application/test_watcher.py, tests/application/test_watcher_acceptance.py, tests/application/test_watcher_move_rule.py, tests/application/test_work_items.py, tests/application/test_work_items_duplicate.py, tests/branch_reading.py, tests/conftest.py, tests/cost_image_support.py, tests/crash_support.py, tests/domain/test_acceptance.py, tests/domain/test_acceptance_before_approval.py, tests/domain/test_acceptance_booking.py, tests/domain/test_acceptance_description.py, tests/domain/test_acceptance_facts.py, tests/domain/test_acceptance_facts_disk.py, tests/domain/test_acceptance_facts_human.py, tests/domain/test_acceptance_facts_limit.py, tests/domain/test_acceptance_refusal_edges.py, tests/domain/test_acceptance_status.py, tests/domain/test_agent_entry.py, tests/domain/test_answers.py, tests/domain/test_answers_round_cap.py, tests/domain/test_archive.py, tests/domain/test_board.py, tests/domain/test_board_absent_values.py, tests/domain/test_contract.py, tests/domain/test_decide_docs_slip.py, tests/domain/test_decision_rules.py, tests/domain/test_decisions.py, tests/domain/test_evaluation.py, tests/domain/test_evaluation_details.py, tests/domain/test_evaluation_due.py, tests/domain/test_evaluation_reject.py, tests/domain/test_events.py, tests/domain/test_hand_over.py, tests/domain/test_human_waits.py, tests/domain/test_journal.py, tests/domain/test_journal_acceptance.py, tests/domain/test_journal_causes.py, tests/domain/test_journal_records.py, tests/domain/test_journal_stamps.py, tests/domain/test_labels.py, tests/domain/test_lease.py, tests/domain/test_lease_observed.py, tests/domain/test_move_rule.py, tests/domain/test_post_texts_notes.py, tests/domain/test_prompts.py, tests/domain/test_provider_limit_stall_text.py, tests/domain/test_question_texts.py, tests/domain/test_recovery.py, tests/domain/test_recovery_cap.py, tests/domain/test_section_edges.py, tests/domain/test_send_back.py, tests/domain/test_send_back_records.py, tests/domain/test_stall_reason_removed.py, tests/domain/test_stall_texts.py, tests/domain/test_story_form.py, tests/domain/test_story_form_edges.py, tests/domain/test_story_place.py, tests/domain/test_times.py, tests/domain/test_work_item.py, tests/domain/test_work_item_require_state.py, tests/domain/test_work_item_snapshot.py, tests/entry/test_run.py, tests/entry/test_watch.py, tests/entry/test_wiring.py, tests/entry/test_wiring_acceptance.py, tests/entry/test_wiring_boundaries.py, tests/entry/test_wiring_handlers.py, tests/entry/test_wiring_human_handlers.py, tests/evaluation_support.py, tests/proof_support.py, tests/push_retry_support.py, tests/shipped_agents.py, tests/stage_run_support.py, tests/stall_support.py, tests/story_form_support.py, tests/test_approval_description.py, tests/test_checkout_hygiene_removed.py, tests/test_claude_files.py, tests/test_fault_paths.py, tests/test_fault_paths_7_to_13.py, tests/test_model_configuration.py, tests/test_no_journal_reading.py, tests/test_no_state_copies.py, tests/test_proof_support.py, tests/test_shared_branch_helpers.py, tests/test_stop_table.py, tests/undo_support.py, tests/watch_support.py, tests/work/__init__.py, tests/work/adapters/__init__.py, tests/work/adapters/test_journal_as_data.py, tests/work/adapters/test_journal_causes_file.py, tests/work/adapters/test_journal_stamps_file.py, tests/work/adapters/test_work_item_markdown.py, tests/work/adapters/test_work_item_markdown_acceptance.py, tests/work/application/__init__.py, tests/work/domain/__init__.py, tests/work/domain/test_acceptance.py, tests/work/domain/test_acceptance_description.py, tests/work/domain/test_acceptance_facts.py, tests/work/domain/test_acceptance_facts_disk.py, tests/work/domain/test_acceptance_facts_human.py, tests/work/domain/test_acceptance_facts_limit.py, tests/work/domain/test_acceptance_status.py, tests/work/domain/test_answers.py, tests/work/domain/test_answers_round_cap.py, tests/work/domain/test_archive.py, tests/work/domain/test_hand_over.py, tests/work/domain/test_journal.py, tests/work/domain/test_journal_acceptance.py, tests/work/domain/test_journal_causes.py, tests/work/domain/test_journal_records.py, tests/work/domain/test_labels.py, tests/work/domain/test_post_texts_notes.py, tests/work/domain/test_provider_limit_stall_text.py, tests/work/domain/test_question_texts.py, tests/work/domain/test_section_edges.py, tests/work/domain/test_send_back_records.py, tests/work/domain/test_stall_reason_removed.py, tests/work/domain/test_stall_texts.py, tests/work/domain/test_story_form.py, tests/work/domain/test_story_form_edges.py, tests/work/domain/test_story_place.py, tests/work/domain/test_work_item.py, tests/work/domain/test_work_item_require_state.py, tests/work/domain/test_work_item_snapshot.py, tests/work_item_support.py, tests/write_path_support.py.
11. factory: started tests as vm.
12. tester: Mode: a test change the human approved. I made the changes the coder's entry 10 names, and nothing else. The leave for them is the Interface's last rule (feature decision 5). Every test keeps its name and checks the same thing.

    1. Import rewrite under `tests/`: I ran the coder's sed over the 168 files that match its regex, which rewrites `factory.<layer>.<name>` to `factory.work.<layer>.<name>` for the 14 modules. `tests/test_areas.py` stayed unchanged. I also made the three hand edits:
       - `tests/domain/test_provider_limit_stall_text.py` now has `from factory.work.domain import decisions, journal`.
       - `tests/domain/test_journal_causes.py` now has `from factory.work.domain import decisions, journal, work_item`.
       - In `tests/application/test_tick.py`, the parametrize row `"application/work_items.py"` is now `"work/application/work_items.py"`.

       Then I ran `ruff check --fix tests` and `ruff format tests`. A grep afterwards found no `from factory.<layer> import <moved module>` line left under `src/` or `tests/`.
    2. Created: `tests/work/__init__.py`, `tests/work/domain/__init__.py`, `tests/work/application/__init__.py` and `tests/work/adapters/__init__.py`, all empty.
    3. Moved: the 34 modules the coder listed, 29 from `tests/domain/` to `tests/work/domain/` and 5 from `tests/adapters/` to `tests/work/adapters/`. None came from `tests/application/`.
       - The permission layer refused `git mv` and `git add -N`, so I moved the files with plain `mv`. That leaves the moves in the working tree as a deletion plus a new file; git's rename detection pairs them in the factory's commit.

    Criterion → test mapping, unchanged from entry 8:
    - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer
    - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring
    - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path
    - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved and tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own
    - criterion 5: `make check`; no test function.
    - criterion 6: docs stage; no test function.

    Run:
    - I ran the whole `make test` once instead of only the changed files, because the changes cover almost the whole suite: `test: green (124.3 s)`, coverage 99.26 %.
    - `make lint`: `lint: green (0.1 s)`.
    - Every module now imports, so there is no module the test runner could not import.

    Earlier test files changed: the 168 rewritten files and the 34 moved modules, all listed in entry 10.

    Open for others:
    - `security/duplicates-baseline.txt` needs the new `factory.work.*` paths. It is outside my write paths and the coder's; the coder noted it in entry 10.

    `lint`: lint: green (0.2 s)
13. factory: started doing as vm.
14. coder: Round 0, second doing run. The work was already done when this run started: my source move (entry 10) and the tester's test move (entry 12) are both committed. All I did was check it, and I changed nothing.

    What was built (entry 10): `src/factory/work/__init__.py`, `src/factory/work/{domain,application,adapters}/__init__.py`, and the 14 modules moved to `src/factory/work/<layer>/<name>.py`. Every import of them under `src/` now uses the new path. The tester's entry 12 did the same for `tests/` and moved 34 test modules to `tests/work/`.

    Checks this run:
    - `git status` is clean.
    - No old path of the 14 modules is left anywhere under `src/` or `tests/` (I searched outside `tests/test_areas.py`, which keeps the old paths on purpose).
    - `make check` is green: `test: green (123.7 s)`, coverage 99.26 %, `check: green`.

    Main choice (unchanged from entry 10): the coder moves `src/` and the tester moves and rewrites `tests/`, the same split S0002 used. I rejected leaving test edits in my working tree, because the factory drops them.

    Refactor: nothing to change. The diff is only file moves and import lines.

    Noticed, not touched:
    - `security/duplicates-baseline.txt` still lists the old paths, so `make duplicates` reports the known findings of `work_item_markdown.py`, `move_rule.py` and the similar-code pairs as new under `factory.work.*`. That file is outside my write paths and needs the human, as it did for S0002.
    - The docs that name old module paths are left for the docs stage (criterion 6).
    - Three modules left in `tests/domain/` have names that sound like the work area: `test_archive_texts`, `test_journal_stamps` and `test_work_item_stop`. Criterion 4's test passes, so each of them imports from an area not yet moved.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 34 known, 8 gone
