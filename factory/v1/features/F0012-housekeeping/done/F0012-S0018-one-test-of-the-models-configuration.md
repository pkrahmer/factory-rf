---
stage: done
pr: 169
blocked: null
comments_seen: 2
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

1. The rule returns `None` for a stand-in model (defined in the test) with `frozen=True, extra="forbid"`, and a fault for stand-ins with `frozen=True` only, with `extra="forbid"` only, with `frozen=True, extra="ignore"`, with `frozen=False, extra="forbid"` and with no `model_config`. Six rows of one parametrized test. Each failing row also checks that the fault contains the stand-in's name and the missing setting (`frozen`, `extra`, or both for the stand-in with no `model_config`).
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
2. intake: 1. The Interface says the rule's function "returns a fault naming the model and the missing setting" for a model that is not closed. Criterion 1 only requires "a fault" for the five failing stand-ins. Nothing tests what the fault says, so two coders could read it two ways and both pass. Options: (a) reword criterion 1 so each failing row also checks that the fault contains the stand-in's name and the missing setting (`frozen`, `extra`, or both for a stand-in with no `model_config`); (b) drop "naming the model and the missing setting" from the Interface and keep "a fault". I would choose (a), since the fault is what tells a reader which model to fix. The rest of the story is fine: the criteria are testable, the Demo is runnable and its counts add up (6 + 90 + 1 + 6 = 103, at least 100), the architecture and scope check out, and the six exceptions match FEATURE decision 25.
3. human (pull request comment, 2026-10-17): (a). Each failing row of criterion 1 also checks that the fault contains the stand-in's name and the missing setting (`frozen`, `extra`, or both for a stand-in with no `model_config`).
4. intake: accepted. Carried in from log entry 3 (the human's answer (a)): criterion 1 now also says each failing row checks that the fault contains the stand-in's name and the missing setting (`frozen`, `extra`, or both for the stand-in with no `model_config`). That is the human's edit, not mine. The Assignment's meaning did not change, so I left it as it was.
   - Interface: names the new module `tests/test_model_configuration.py`, how models are collected (`pkgutil.walk_packages` over `factory.__path__`, defined in the module, private ones included), the rule's function and its return value, the six exceptions by dotted name, and the 25 tests to remove by module and function name. The fault wording is now covered by criterion 1.
   - Criteria: each one fits one test function, or one parametrized test with a row per case, with no further decisions. Criterion 1 covers the passing side and all five failing sides. Criterion 2 covers every collected model, and criterion 4 covers each exception with `extra == "ignore"`. Criterion 3 gives a count above 90 and names three models, plus `Boundaries` as excluded. Criterion 5 is a search for the removed function names plus the other tests of those modules still passing.
   - Demo: both commands run as written. The first expects at least 100 passed, and 6 + 90 + 1 + 6 = 103 meets that. The second is a grep that should exit 1 and print `status 1`. Both `Expect:` lines can be checked against the output.
   - Architecture: this is a test-only change under `tests/` at the root, which is where CLAUDE.md puts a module outside the layers. Pydantic models and `Boundaries` (a dataclass) are separated correctly.
   - Scope: it is inside FEATURE 1.5 and decisions 25 and 39. The six exceptions match decision 25. Only the tests of `tests/adapters` and `tests/application` are removed here, and S0019 handles `tests/domain`.
5. tester: Wrote `tests/test_model_configuration.py` and removed the 25 per-model tests listed in the Interface.

   Criteria → tests:
   - criterion 1: tests/test_model_configuration.py::test_the_rule_names_the_model_and_each_missing_setting (6 rows: closed, frozen-only, forbid-only, frozen-ignore, not-frozen-forbid, no-config). Each failing row checks that the fault contains the stand-in's `__name__` and every missing setting.
   - criterion 2: tests/test_model_configuration.py::test_every_model_is_frozen_and_forbids_unknown_keys (one row per collected model outside the exceptions, id = dotted name)
   - criterion 3: tests/test_model_configuration.py::test_the_collection_finds_every_model_and_nothing_else
   - criterion 4: tests/test_model_configuration.py::test_each_exception_is_a_model_that_ignores_unknown_keys (6 rows)
   - criterion 5: done by removal. The 25 functions are gone from the 17 modules. A grep for the Demo's three names finds nothing (`status 1`). The rest of those modules passed in `make test`.
   - criteria 6 and 7: not tests. Criterion 6 is the coder's `make check`; criterion 7 is for the docs stage.

   Module contents: the module holds the rule `closed_fault(model) -> str | None` and the `EXCEPTIONS` list (the six dotted names). `MODELS` is collected through `pkgutil.walk_packages(factory.__path__, prefix="factory.")`. It keeps every `BaseModel` subclass whose `__module__` is the module being walked, private ones included.

   Removal and cleanup:
   - The functions were removed with their decorators.
   - The imports that only they used were removed with `ruff --select F401 --fix`, and `ruff format` was run on the changed files.
   - `tests/application/test_bill_service.py` got its import block re-sorted.
   - The helper `_prepared` in `tests/application/test_opening.py` was used only by the removed tests, so it went too.
   - No other helpers, fixtures or constants were left without a use by this change. `_agents` in `tests/application/test_tick.py` is a fixture that was already not referenced by name before this change, so I left it alone.

   Files:
   - created: tests/test_model_configuration.py
   - changed: tests/adapters/{test_claude_guard,test_fake_agent_runtime}.py, tests/application/handlers/{test_comments,test_recording}.py, tests/application/{test_acceptance_service,test_after_agent,test_bill_service,test_board_reader,test_claims,test_costs,test_opening,test_stage_finish,test_stage_launch,test_stalls,test_task,test_tick,test_undo}.py

   Test run: as the Assignment expected, `make test` was green (`test: green`, coverage 99.51%) and there are no red tests. All the modules imported. After that run I made two lint-only edits: `ids=str` in place of a lambda, and the import sort. `make lint` is green.

   For the coder: no production code is needed. Run `make check` and say so.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (25.4 s)
6. coder: I built nothing, because there was nothing to build. As the Assignment and the tester's entry say, all models outside the six exceptions already declare `frozen=True` and `extra="forbid"`, so `tests/test_model_configuration.py` passes against today's code without any change under `src/`. I ran `make check` on the branch as committed (tester's tests included) and it ended `check: green` (`test: green (25.4 s)`, coverage 99.51%). I made no commits. The refactor step had nothing to do: my own diff (`git diff main...HEAD -- . ':!factory' ':!tests'`) is empty. The rejected alternative was editing the tester's module (for example its lint-only shape), which is not mine to touch. Not touched, as the tester already noted: the `_agents` fixture in `tests/application/test_tick.py` was unreferenced before this change too. Open for the docs stage: criterion 7 (a *The models' configuration* section in the project guide after *Errors*, and a decision log entry recording the rule and its six exceptions).

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
7. reviewer: No findings.

   What I checked in `git diff main...HEAD -- . ':!factory'` (18 test files, nothing under `src/`):
   - Criterion 1: `tests/test_model_configuration.py::test_the_rule_names_the_model_and_each_missing_setting` has the six rows the criterion names. Each failing row checks that the fault contains the stand-in's `__name__` and every missing setting. The no-config row expects both `frozen` and `extra`. `closed_fault` returns `None` only when `frozen == True` and `extra == "forbid"`.
   - Criterion 2: `test_every_model_is_frozen_and_forbids_unknown_keys` is parametrized over `MODELS` minus `EXCEPTIONS`, with the dotted name as each row's id. Models are collected with `pkgutil.walk_packages(factory.__path__, prefix="factory.")` and filtered by `__module__`, private ones included, as the Interface says. No `src/factory` module nests a `BaseModel` inside a class, so walking module-level classes misses none.
   - Criterion 3: `test_the_collection_finds_every_model_and_nothing_else` checks a count above 90, the three named models and that `Boundaries` is absent.
   - Criterion 4: `test_each_exception_is_a_model_that_ignores_unknown_keys` has one row for each of the six dotted names, and checks that each is collected and has `extra == "ignore"`.
   - Criterion 5: exactly 25 `def test_` lines are removed, and a search for all 25 names under `tests/` finds none (status 1). No other test was removed. Each import, constant, helper and fixture the removed tests used is still used elsewhere in its module (`_context_values`, `_result`, `_launch_new`, `_aftermath`, `QUESTION`, `COMPLETED`, `SIDECAR`, `snapshot_of`/`state_with`, `CopyResult`, `GuardVerdict` and others). `_prepared` in `test_opening.py` was used only by the removed tests and is gone.
   - Criterion 6: the coder's entry reports `make check` green (coverage 99.51 %), and `make duplicates` reports 0 new findings.
   - Architecture and security: a test-only change, with the new module at the `tests/` root as `CLAUDE.md` says for a module outside the layers. No silencing markers, no secrets, no strings run as shell commands.
   - Ticket hygiene: the Assignment matches what was built. Criterion 7 (project guide section *The models' configuration* after *Errors*, and a decision log entry for the rule and its six exceptions) is still open for the documenter.
8. documenter: wrote the criterion-7 documentation.
   - `docs/project-guide.md`: new section *The models' configuration* after *Errors*. It says every model is frozen and forbids unknown keys, that `tests/test_model_configuration.py` checks all of them at once (so a new model needs no test of its own for that), and that a tool-output model declares `extra="ignore"` and joins the test's `EXCEPTIONS` by dotted name. It names the six.
   - `docs/decisions.md`: new entry recording the rule, the six exceptions and the rejected alternatives (a test per model, a base class).

   `python -m factory.entry.check_documents` prints `documents ok`. I ran no `make check`, since I changed only documents.

   Cross-read and found current: README, `docs/operator-guide.md`, and the other statements in the project guide that say a model is frozen and forbids unknown keys. The diff is tests only, so no name or behaviour in the docs changed.

   No findings for the coder. Nothing stale seen.

   `make check`: check: green
   `make documents`: documents ok
9. demo: I ran both Demo commands from the repository root, exactly as written. Both met their `Expect:` lines, and nothing in the output contradicts an acceptance criterion. No findings.

   1. `uv run pytest --no-header -p no:cacheprovider tests/test_model_configuration.py`
   ```
   ........................................................................ [ 66%]
   .....................................                                    [100%]
   109 passed in 0.05s
   ```
   Met: the last line is `109 passed`, at least 100, with no `failed`, `error` or `skipped` count. The 109 breaks down as 6 rule rows (criterion 1), 1 collection test (criterion 3), 6 exception rows (criterion 4) and 96 rows for criterion 2. 96 + 6 = 102 collected models, so the collection's model count is above 90, as criterion 3 requires. The ticket says there are 96 models in all, not 102; it doesn't change the result.

   2. `grep -rn "def test_a_verdict_is_frozen\|def test_stage_start_is_frozen\|def test_tick_outcome_refuses_an_assignment" tests; echo "status $?"`
   ```
   status 1
   ```
   Met: the single line `status 1`. Three of the removed tests are gone, which matches criterion 5.

   Criteria cross-read: the demo contradicts none of them. I did not re-run criteria 6 (`make check`) and 7 (docs). They rest on the coder's, reviewer's and documenter's entries, and the factory runs `make check` itself after this stage.
10. done (pull request merged); cost: 7 runs, 4.5 min, 44 turns, 198k tokens in (636k more from cache), 16k out, $1.17
