---
stage: tests
pr: 170
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The per-model configuration tests of the domain removed

## Assignment (as of log entry 1)

F0012-S0018 added `tests/test_model_configuration.py`, which checks for every Pydantic model under `src/factory` that it is frozen and refuses unknown keys, and removed the per-model tests of `tests/adapters` and `tests/application` that tested only that. This story removes those of `tests/domain`, the modules from acceptance to identifiers in alphabetical order, and the modules from journal to work item stop in alphabetical order, so that each tester's run stays small (FEATURE decision 25). A test that also checks something of the factory's own (a pattern, a `Literal`, a limit, a rule across fields) stays. It is a change of tests only, by the human's leave (FEATURE decision 39); the coder expects to change nothing under `src/`.

## Interface

No name under `src/` changes. The tests removed, with the helpers, fixtures and imports that only they used and nothing else:

The modules from acceptance to identifiers:

- `tests/domain/test_acceptance.py`: `test_acceptance_state_refuses_an_assignment` (its `test_acceptance_state_is_closed_and_typed` stays: it checks the story ids and the outcome)
- `tests/domain/test_acceptance_facts.py`: `test_the_facts_refuse_an_assignment`
- `tests/domain/test_acceptance_status.py`: `test_the_models_refuse_an_unknown_key`, `test_the_models_refuse_an_assignment`
- `tests/domain/test_agent_runs.py`: `test_models_forbid_unknown_keys_and_are_frozen`
- `tests/domain/test_bills.py`: `test_a_bill_is_frozen`, `test_a_stage_bill_is_frozen`, `test_a_bill_refuses_an_unknown_key`, `test_a_stage_bill_refuses_an_unknown_key`
- `tests/domain/test_board.py`: `test_a_row_refuses_an_unknown_key`, `test_a_row_refuses_an_assignment`
- `tests/domain/test_checks.py`: `test_unknown_keys_and_assignment_are_rejected`
- `tests/domain/test_cost_records.py`: `test_a_record_is_frozen_and_refuses_unknown_fields`
- `tests/domain/test_decision_rules.py`: `test_a_stage_move_is_frozen`
- `tests/domain/test_documents.py`: `test_a_finding_is_a_closed_model`
- `tests/domain/test_evaluation.py`: `test_closed_models_refuse_an_unknown_key`, `test_closed_models_refuse_an_assignment`
- `tests/domain/test_evaluation_reject.py`: `test_evaluation_input_refuses_an_unknown_key_and_an_assignment` (`tests/domain/test_evaluation_due.py::test_evaluation_input_refuses_a_malformed_due_and_an_unknown_key` stays: it checks the feature id)
- `tests/domain/test_events.py`: `test_event_refuses_an_unknown_key`, `test_event_refuses_an_assignment`
- `tests/domain/test_fault_paths.py`: `test_a_built_path_refuses_the_assignment_of_a_field`, `test_a_path_refuses_an_unknown_key_and_a_wrong_type` (a plain integer field given a word)
- `tests/domain/test_git.py`: `test_remote_branch_refuses_assignment`, `test_remote_branch_refuses_an_unknown_field` (its `test_identity_needs_a_name_and_an_email_and_is_frozen` stays: it checks the blank name and email)
- `tests/domain/test_git_history.py`: `test_history_models_forbid_unknown_keys_and_assignment`
- `tests/domain/test_hosting.py`: `test_models_forbid_unknown_keys_and_are_frozen`
- `tests/domain/test_identifiers.py`: `test_name_models_are_frozen_and_refuse_an_unknown_field`

27 tests. Every other test of these modules stays as it is.

The modules from journal to work item stop:

- `tests/domain/test_journal.py`: `test_a_new_entry_is_frozen`
- `tests/domain/test_kill_point_cases.py`: `test_an_assignment_to_a_built_case_is_refused` (its `test_a_case_outside_the_closed_model_is_refused` stays: it checks the three `Literal` fields)
- `tests/domain/test_move_rule.py`: `test_move_rule_models_refuse_an_unknown_key`, `test_move_rule_models_refuse_an_assignment`
- `tests/domain/test_preflight.py`: `test_both_models_reject_an_unknown_field`, `test_a_field_cannot_be_assigned`
- `tests/domain/test_preflight_stamp.py`: `test_the_stamp_refuses_an_unknown_key`, `test_the_stamp_refuses_an_assignment_to_a_field`
- `tests/domain/test_prompts.py`: `test_prompt_facts_are_frozen`, `test_prompt_facts_refuse_an_unknown_key`
- `tests/domain/test_sections.py`: `test_section_and_block_are_frozen_and_refuse_unknown_fields`
- `tests/domain/test_settings.py`: `test_the_settings_model_is_closed`
- `tests/domain/test_stop_table.py`: `test_a_built_row_refuses_the_assignment_of_a_field` (its `test_a_row_with_an_unknown_key_or_value_is_rejected` stays: it checks the destination and the reason)
- `tests/domain/test_stops.py`: `test_both_models_reject_an_unknown_field`, `test_a_field_cannot_be_assigned`
- `tests/domain/test_story_form.py`: `test_a_finding_is_frozen_and_refuses_an_unknown_field`
- `tests/domain/test_tick_status.py`: `test_an_error_count_refuses_an_unknown_key_and_an_assignment`, `test_a_tick_status_refuses_an_unknown_key_and_an_assignment`
- `tests/domain/test_work_item.py`: `test_work_item_models_are_frozen_and_refuse_an_unknown_field`
- `tests/domain/test_work_item_snapshot.py`: `test_an_unknown_key_is_refused`, `test_a_field_cannot_be_assigned`
- `tests/domain/test_work_item_stop.py`: `test_both_models_reject_an_unknown_field_and_an_assignment`

22 tests. Every other test of these modules stays as it is.

## Acceptance criteria

1. None of the 49 tests of the Interface (27 of the modules from acceptance to identifiers, 22 of the modules from journal to work item stop) exists any more: a search of the named modules for those function names finds none (the Demo's first two commands; no test function checks it).
2. Every other test of the named modules still passes, and `tests/test_model_configuration.py` still passes.
3. No helper, fixture or import is left in a named module that no remaining test of that module uses: `make lint` finds no unused import, and a search of the module finds each remaining private helper used (no test function checks it).
4. `make check` stays green.
5. docs: none. F0012-S0018's documentation already says that `tests/test_model_configuration.py` checks every model's configuration and that a model needs no test of its own for an assignment or an unknown key; this story only removes tests that the rule replaced.

## Demo

```bash
grep -rn "def test_a_bill_is_frozen\|def test_event_refuses_an_assignment\|def test_remote_branch_refuses_assignment" tests/domain; echo "status $?"
```
Expect: the single line `status 1`.

```bash
grep -rn "def test_a_new_entry_is_frozen\|def test_the_settings_model_is_closed\|def test_an_unknown_key_is_refused" tests/domain; echo "status $?"
```
Expect: the single line `status 1`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain tests/test_model_configuration.py 2>&1 | tail -1
```
Expect: one line `<n> passed in <t>s`, with neither `failed` nor `error` (`addopts` already holds `-q`; a second `-q` would hide this line).

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted. The factory's format check passed, so I did not repeat it.
   - Interface: the story names no `src/` change. It lists 27 and 22 test functions by module and function name, and says what stays when a test checks more than Pydantic's configuration. I spot-checked 8 of the names across both groups and each exists in the named module under `tests/domain`. I did not check the other 41.
   - Criteria: each is checkable. Criterion 1 is a search for the function names. Criterion 2 is the pytest run. Criterion 3 is `make lint` plus a search for unused helpers. Criterion 4 is `make check`. The story states no rule with a failing side. It only removes tests that `tests/test_model_configuration.py` replaces.
   - Demo: the three commands run as written. Each has an `Expect:` line that the output can be checked against: `status 1` twice, and a `<n> passed` line.
   - Architecture: nothing under `src/` changes. The story removes only tests and the helpers and imports that only those tests used.
   - Scope: it is housekeeping story 1.5 of F0012, and FEATURE decisions 25 and 39 grant it. It is not in the feature's "Out of scope".
