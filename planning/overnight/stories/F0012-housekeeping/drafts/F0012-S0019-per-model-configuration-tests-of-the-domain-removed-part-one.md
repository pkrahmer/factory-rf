# The per-model configuration tests of the domain removed, part one

## Assignment (as of log entry 1)

F0012-S0018 added `tests/test_model_configuration.py`, which checks for every Pydantic model under `src/factory` that it is frozen and refuses unknown keys, and removed the per-model tests of `tests/adapters` and `tests/application` that tested only that. This story removes those of `tests/domain`, the modules from acceptance to identifiers in alphabetical order (F0012-S0020 takes the rest), so that each tester's run stays small (FEATURE decision 25). A test that also checks something of the factory's own (a pattern, a `Literal`, a limit, a rule across fields) stays. It is a change of tests only, by the human's leave (FEATURE decision 39); the coder expects to change nothing under `src/`.

## Interface

No name under `src/` changes. The tests removed, with the helpers, fixtures and imports that only they used and nothing else:

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

## Acceptance criteria

1. None of the 27 tests of the Interface exists any more: a search of the named modules for those function names finds none.
2. Every other test of the named modules still passes, and `tests/test_model_configuration.py` still passes.
3. No helper, fixture or import is left in a named module that no remaining test of that module uses (ruff's unused-import check is clean, and a search of the module finds each remaining private helper used).
4. `make check` stays green.
5. docs: none. F0012-S0018's documentation already says that `tests/test_model_configuration.py` checks every model's configuration and that a model needs no test of its own for an assignment or an unknown key; this story only removes tests that the rule replaced.

## Demo

```bash
grep -rn "def test_a_bill_is_frozen\|def test_event_refuses_an_assignment\|def test_remote_branch_refuses_assignment" tests/domain; echo "status $?"
```
Expect: the single line `status 1`.

```bash
uv run pytest --no-header -p no:cacheprovider -q tests/domain tests/test_model_configuration.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
