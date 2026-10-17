# The per-model configuration tests of the domain removed, part two

## Assignment (as of log entry 1)

F0012-S0018 added `tests/test_model_configuration.py`, which checks for every Pydantic model under `src/factory` that it is frozen and refuses unknown keys, and removed the per-model tests of `tests/adapters` and `tests/application` that tested only that. This story removes those of `tests/domain`, the modules from journal to work item stop in alphabetical order (F0012-S0019 takes the rest), so that each tester's run stays small (FEATURE decision 25). A test that also checks something of the factory's own (a pattern, a `Literal`, a limit, a rule across fields) stays. It is a change of tests only, by the human's leave (FEATURE decision 39); the coder expects to change nothing under `src/`.

## Interface

No name under `src/` changes. The tests removed, with the helpers, fixtures and imports that only they used and nothing else:

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

1. None of the 22 tests of the Interface exists any more: a search of the named modules for those function names finds none.
2. Every other test of the named modules still passes, and `tests/test_model_configuration.py` still passes.
3. No helper, fixture or import is left in a named module that no remaining test of that module uses (ruff's unused-import check is clean, and a search of the module finds each remaining private helper used).
4. `make check` stays green.
5. docs: none. F0012-S0018's documentation already says that `tests/test_model_configuration.py` checks every model's configuration and that a model needs no test of its own for an assignment or an unknown key; this story only removes tests that the rule replaced.

## Demo

```bash
grep -rn "def test_a_new_entry_is_frozen\|def test_the_settings_model_is_closed\|def test_an_unknown_key_is_refused" tests/domain; echo "status $?"
```
Expect: the single line `status 1`.

```bash
uv run pytest --no-header -p no:cacheprovider -q tests/domain tests/test_model_configuration.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
