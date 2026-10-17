---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One test of the models' configuration, and the per-model tests of adapters and application removed

## Assignment (as of log entry 1)

Nearly every story wrote, for each Pydantic model it added, a test that an assignment is refused and a test that an unknown key is refused. Those tests test Pydantic, not the factory: what the factory decides is that its models are frozen and refuse unknown keys, and that is one rule over all of them. The human's word (2026-10-14, "Tests of the DTOs' own configuration") is one test that walks every Pydantic model under `src/factory` and checks the configuration, replacing the per-model tests. This story writes that test and removes the per-model tests of `tests/adapters` and `tests/application`; F0012-S0019 removes those of `tests/domain`. A test that also checks something of the factory's own (a pattern, a `Literal`, a limit, a rule across fields) stays (FEATURE decision 25). The models that read a tool's own output keep `extra="ignore"` on purpose and are the rule's named exceptions. It is a change of tests only, by the human's leave (FEATURE decision 39). On 2026-10-17 all 96 models but the six exceptions declare `frozen=True` and `extra="forbid"`, and the human re-ran that check on `main` before starting this story: so every test this story writes passes on today's code, the tester's one `make test` is green, which is right here, and the coder has nothing to build and says so after its `make check`.

## Interface

A new test module `tests/test_model_configuration.py`:

- It imports every module of the package `factory` (`pkgutil.walk_packages` over `factory.__path__`) and collects every class that is a subclass of `pydantic.BaseModel` and is defined in that module (its `__module__` is the module's name), private ones included.
- The rule, a function of the module: a model is closed when its `model_config` has `frozen` equal to `True` and `extra` equal to `"forbid"`; the function returns `None` for a closed model and otherwise a fault naming the model and the missing setting.
- The exceptions, by dotted name, each a model that reads a tool's output and declares `extra="ignore"`: `factory.adapters.claude_guard._ToolInput`, `factory.adapters.claude_guard._Payload`, `factory.adapters.claude_runtime._Usage`, `factory.adapters.claude_runtime._Denial`, `factory.adapters.claude_runtime._StructuredOutput`, `factory.adapters.claude_runtime._Reply`.

The tests removed, by the human's leave (FEATURE decision 39), with the helpers, fixtures and imports that only they used and nothing else:

- `tests/adapters/test_claude_guard.py`: `test_a_verdict_is_frozen`, `test_a_verdict_forbids_an_unknown_field`
- `tests/adapters/test_fake_agent_runtime.py`: `test_scripted_run_forbids_unknown_keys_and_is_frozen`
- `tests/application/handlers/test_comments.py`: `test_a_copy_result_is_frozen_and_forbids_unknown_keys`
- `tests/application/handlers/test_recording.py`: `test_a_target_is_frozen_and_forbids_unknown_keys`
- `tests/application/test_acceptance_service.py`: `test_the_opened_acceptance_refuses_an_assignment` (its `test_the_opened_acceptance_is_closed_and_typed` stays: it checks the id and the commit)
- `tests/application/test_after_agent.py`: `test_the_aftermath_is_frozen_and_forbids_unknown_keys`
- `tests/application/test_bill_service.py`: `test_a_work_item_bill_is_frozen`, `test_a_work_item_bill_refuses_an_unknown_key`
- `tests/application/test_board_reader.py`: `test_a_board_view_refuses_an_unknown_key`, `test_a_board_view_refuses_an_assignment`
- `tests/application/test_claims.py`: `test_stage_start_is_frozen`, `test_stage_start_forbids_an_unknown_field`
- `tests/application/test_costs.py`: `test_cost_runs_and_stall_contexts_are_frozen_and_forbid_unknown_keys`
- `tests/application/test_opening.py`: `test_prepared_work_item_is_frozen`, `test_prepared_work_item_forbids_unknown_keys`
- `tests/application/test_stage_finish.py`: `test_a_stage_report_is_frozen`
- `tests/application/test_stage_launch.py`: `test_started_and_launched_stages_are_frozen_and_forbid_unknown_keys`
- `tests/application/test_stalls.py`: `test_stall_results_and_contexts_are_frozen_and_forbid_unknown_keys`
- `tests/application/test_task.py`: `test_task_context_is_frozen`, `test_task_context_refuses_an_unknown_key`
- `tests/application/test_tick.py`: `test_tick_outcome_refuses_an_unknown_key`, `test_tick_outcome_refuses_an_assignment`
- `tests/application/test_undo.py`: `test_the_undo_report_is_frozen`, `test_the_undo_report_forbids_unknown_fields`

Twenty-five tests. `tests/application/test_boundaries.py::test_boundaries_refuse_assignment_to_a_field` stays: `Boundaries` is a dataclass, not a Pydantic model.

## Acceptance criteria

1. The rule returns `None` for a stand-in model (defined in the test) with `frozen=True, extra="forbid"`, and a fault for stand-ins with `frozen=True` only, with `extra="forbid"` only, with `frozen=True, extra="ignore"`, with `frozen=False, extra="forbid"` and with no `model_config`. Six rows of one parametrized test.
2. Every model collected from `src/factory`, outside the exceptions, is closed: one parametrized test over the collected models, each row's id its dotted name.
3. The collection finds more than 90 models, among them `factory.domain.work_item.WorkItemState`, `factory.application.stage.StartedStage` and `factory.adapters.claude_runtime._Reply`, and no class that is not a `BaseModel` (`factory.application.boundaries.Boundaries` is not among them).
4. Each name of the exceptions is a collected model whose `model_config` has `extra == "ignore"`. One row per exception.
5. None of the twenty-five tests of the Interface exists any more (a search of the named modules for those function names finds none), and every other test of those modules still passes.
6. `make check` stays green.
7. docs: the project guide gets a section *The models' configuration* after *Errors*: every Pydantic model under `src/factory` is frozen and refuses unknown keys; `tests/test_model_configuration.py` checks that for all of them at once, so a new model needs no test of its own for an assignment or an unknown key (a test of a pattern, a `Literal`, a limit or a rule across fields is still the story's); a model that reads a tool's own output declares `extra="ignore"` and joins that test's exceptions by name. The decision log records the rule and its six exceptions. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_model_configuration.py
```
Expect: the last line reads `<n> passed in <t>s` with `<n>` at least 100, and no `failed`, `error` or `skipped` count.

```bash
grep -rn "def test_a_verdict_is_frozen\|def test_stage_start_is_frozen\|def test_tick_outcome_refuses_an_assignment" tests; echo "status $?"
```
Expect: the single line `status 1`.

## Log (append only)

1. 2026-10-17 human: created.
