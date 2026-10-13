---
stage: demo
pr: 46
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Load-time rules of the pipeline definition

## Assignment (as of log entry 1)

Add the rules that look across the keys of the pipeline definition, so that a definition that is well formed but cannot work is refused when it loads and not when a stage first reaches the fault (R30, R21): an unknown major contract version (ST8.4), a `next` naming a stage that does not exist (ST8.2), a role without write paths (the write-path half of ST8.3), and a role whose agent run `time_limit` plus the `time_limit`s of a stage's checks and reports do not fit inside the role's `lease_duration` (ST8.5, GH1.4). They are validators of `PipelineDefinition`, so every reader and every ref gets them; a refusal is the `PipelineDefinitionInvalid` that S0004's reader already raises, and S0006's loader already turns into a `pipeline_definition_invalid` stop, so each refusal here is a reported stop that names the fault. The other rules of the definition (a `done` stage, approval and reserved names, the project commands that checks and reports name, the acceptance stage) are in the same validator because they are the same kind of fault. Covers ST8.2, ST8.3 (write paths), ST8.4, ST8.5, GH1.4, R21 (validation of the lease) and R30; keeps kept things 7 and 12.

## Interface

`src/factory/domain/pipeline_definition.py` (adds to S0004's module)

```python
CONTRACT_MAJOR = 1
DONE_STAGE = "done"
RESERVED_NAMES = ("human", "factory", "question")

class PipelineDefinition(BaseModel):
    ...
    # a model validator (mode "after") applies the nine rules below. It collects every fault of every
    # rule and raises one ValueError whose message is the faults joined by "; ", in the order of the rules
    # and, inside a rule, in the order of stages or roles in the text.
```

`src/factory/adapters/pipeline_yaml.py` (changes `RuamelPipelineDefinitionReader.parse`): the rules run only when every field is valid, so the field faults of S0004 (from `all_faults`) come first and alone. When the validation error is the model validator's (its location is empty), the `fault` is the message of the `ValueError` as written, without pydantic's prefix `Value error, ` and without the `invalid <whole>:` form that `all_faults` would give an error with no location; the message is found in the error's `ctx["error"]`.

Rules and the fault each one gives (`<s>` is a stage, `<t>` a stage name, `<r>` a role, `<c>` a project command):

1. The contract has the form `<digits>.<digits>`, else `contract must look like <major>.<minor>, got '<contract>'`.
2. When the form holds, the major (compared as an integer) is `CONTRACT_MAJOR`, else `contract major <major> is not supported (this factory reads major 1)` (ST8.4), where `<major>` is the text before the dot as written (`02` stays `02`). Any minor version is accepted.
3. `stages` holds a stage named `DONE_STAGE`, else `stages must hold a stage named done`; that stage has no role and an empty `next`, else `stage done must have no role and no next`.
4. Every name in the `next` of a stage is a stage, else `stage <s>: next names unknown stage <t>` (ST8.2), once for each unknown name, in the order of the stages and, inside a `next`, of the names.
5. Three checks, whose faults come in this order: first every stage's role is a key of `roles`, else `stage <s>: role <r> is not defined in roles` (in the order of the stages); then every role has at least one write path, else `role <r>: write_paths is empty` (ST8.3; in the order of the roles); then a stage with `approval: true` has no role, else `stage <s>: an approval stage has no role` (in the order of the stages).
6. No stage name and no role name is one of `RESERVED_NAMES`, else `stage name <n> is reserved` or `role name <n> is reserved`.
7. Every name in `checks` and in `reports` of a stage is a key of `project_commands`, else `stage <s>: check <c> is not a project command` or `stage <s>: report <c> is not a project command`.
8. For each stage with a role that is a key of `roles`: the role's `time_limit` plus the `time_limit` of each command listed in the stage's `checks` and each listed in its `reports` (a command listed twice counts twice; a name that is not a key of `project_commands` counts nothing) is at most the role's `lease_duration`, else `role <r> at stage <s>: <total> min exceed lease_duration <lease> min` (ST8.5, GH1.4). The total may equal the lease. `lease_duration` is the role's own; stages without a role (an approval, `done`) are not measured, whatever commands they list.
9. When `acceptance_stage` is set it names a stage that has a role, else `acceptance_stage <t> is not a stage with a role`.

Tests: `tests/adapters/test_pipeline_rules.py`, `tests/application/test_pipeline_loading_rules.py`. `PIPELINE_YAML` from `tests/git_support.py` (nine stages, project commands `check` 10, `lint` 5 and `test` 10 minutes, default role limits 40 and 60) is the base of every case, changed by text replacement. The rules are tested through `RuamelPipelineDefinitionReader` and compare `PipelineDefinitionInvalid.fault`, so the tests sit with the adapter. The loader tests use the fixtures of S0006 and push each changed text to `main`. No test of S0004 changes: its accepting cases were written to satisfy these rules.

## Acceptance criteria

1. `PIPELINE_YAML` passes every rule: parsing it raises nothing.
2. A contract whose major is not 1 (`"2.0"`, `"0.9"`, `"10.0"`, `"02.0"`) is refused with the fault `contract major <major> is not supported (this factory reads major 1)`, `<major>` as written (`02` for `"02.0"`) (ST8.4).
3. A contract whose major is 1 is accepted for any minor (`"1.0"`, `"1.7"`, `"1.10"`), and `"01.0"` is accepted too: the major is compared as an integer.
4. A contract that does not have the form `<digits>.<digits>` (`"1"`, `"1.0.0"`, `"v1.0"`, `"1.x"`) is refused with the fault `contract must look like <major>.<minor>, got '<contract>'`, naming the text written.
5. A definition without a stage named `done` is refused with the fault `stages must hold a stage named done`.
6. A `done` stage that has a role, or a `next`, is refused with the fault `stage done must have no role and no next`.
7. A stage whose `next` names a stage that does not exist is refused with the fault `stage <s>: next names unknown stage <t>`; with `next: [review, ship]` in the stage `doing` the fault is `stage doing: next names unknown stage ship` (ST8.2).
8. Every unknown name is a fault of its own, in the order of the text: with `next: [doing, nowhere]` in the stage `tests` and `next: [ship, review, harbour]` in the stage `doing`, the fault is `stage tests: next names unknown stage nowhere; stage doing: next names unknown stage ship; stage doing: next names unknown stage harbour`.
9. A stage whose role is not a key of `roles` is refused with the fault `stage <s>: role <r> is not defined in roles`.
10. A role whose `write_paths` is empty is refused with the fault `role <r>: write_paths is empty`; a role with one write path is accepted (ST8.3).
11. A stage with `approval: true` that also has a role is refused with the fault `stage <s>: an approval stage has no role`.
12. The three checks of rule 5 report in the order written: with a new stage `x: {role: ghost, next: [done]}`, the role `documenter` with `write_paths: []` and the role `coder` on the stage `approval`, the fault is `stage x: role ghost is not defined in roles; role documenter: write_paths is empty; stage approval: an approval stage has no role`.
13. A stage named `human`, `factory` or `question`, and a role with one of these names, are each refused with the fault `stage name <n> is reserved` or `role name <n> is reserved`.
14. A stage whose `checks` names a command that is not a key of `project_commands` is refused with the fault `stage <s>: check <c> is not a project command`; the same for `reports` with `report`.
15. The `time_limit` limit has two sides: with the coder's `time_limit` at 50, its stage `doing` (checks `check`, 10 minutes) totals 60 and the definition is accepted, the total equal to the `lease_duration` of 60; at 51 it totals 61 and is refused with the fault `role coder at stage doing: 61 min exceed lease_duration 60 min` (ST8.5, GH1.4, R21).
16. The `time_limit`s of checks and of reports both count: with the tester's `time_limit` at 45 its stage `tests` (checks `lint` 5, reports `test` 10) totals 60 and is accepted; at 46 it totals 61 and is refused with the fault `role tester at stage tests: 61 min exceed lease_duration 60 min`.
17. The lease is the role's own: with the coder's `lease_duration` at 90 and `time_limit` at 70 (stage `doing` totals 80) and the tester's `time_limit` at 70 under the default lease of 60 (stage `tests` totals 85), only the tester is refused, with the fault `role tester at stage tests: 85 min exceed lease_duration 60 min`.
18. A role used by two stages is measured at each stage: with a second stage that also has the coder's role and no checks, and the coder's `time_limit` at 55, the fault names only the stage with the check, `role coder at stage doing: 65 min exceed lease_duration 60 min`, and not the other stage.
19. A command listed twice counts twice: with `checks: [check, check]` in the stage `doing` and the coder's `time_limit` at 41, the stage totals 61 and the fault is `role coder at stage doing: 61 min exceed lease_duration 60 min`.
20. A name that is not a project command counts nothing, and a stage without a role is not measured (one test, two cases): with `checks: [ghost]` in the stage `doing` and the coder's `time_limit` at 60, the only fault is `stage doing: check ghost is not a project command`; with `checks: [check]` added to the stage `approval`, the definition is accepted.
21. An `acceptance_stage` that is not a stage, or names a stage without a role (`approval`), is refused with the fault `acceptance_stage <t> is not a stage with a role`; `acceptance` is accepted.
22. A definition that breaks two rules is refused once, and its `fault` is the two faults in the order of the rules joined by `; ` (for example a `next` naming `ship` in `doing`, and the coder's `time_limit` at 51, give `stage doing: next names unknown stage ship; role coder at stage doing: 61 min exceed lease_duration 60 min`).
23. The rules run only when every field is valid: a text with `lease_duration: 0` for the coder and a `next` naming `ship` is refused with a `fault` that starts with `invalid roles.coder.lease_duration:` and does not contain `ship`.
24. Loaded through `PipelineLoader.load`, each of these refusals is a reported stop that names the fault: a `next` naming an unknown stage (ST8.2), a role without write paths (ST8.3), a contract with major 2 (ST8.4) and a role whose limits exceed its lease (ST8.5, GH1.4) each make `load` raise `PipelineDefinitionInvalid` and leave exactly one stop in the health status, with `reason` `pipeline_definition_invalid` and `detail` equal to the fault (one parametrised test, four cases).
25. `make check` stays green.
26. docs: `docs/project-guide.md` explains the contract version (the major must be 1, any minor is read), the rule that a role's `time_limit` plus the `time_limit`s of a stage's checks and reports must not exceed the role's `lease_duration` (with the defaults 40 + 10 + 10 fits 60, a stage with two checks and a report does not), and lists the faults a refused definition reports; `docs/operator-guide.md` points from the stop `pipeline_definition_invalid` to that list; `docs/decisions.md` records that the rules refuse at load and that the faults of one text are reported together.

## Demo

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
  tester: {write_paths: ['tests/*']}
stages:
  tests: {role: tester, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
'''
reader = RuamelPipelineDefinitionReader()
cases = {
    'next': TEXT.replace('next: [done]', 'next: [ship]'),
    'contract': TEXT.replace('1.0', '2.0'),
    'write paths': TEXT.replace('[\'src/*\']', '[]'),
    'time limit': TEXT.replace('coder: {write_paths', 'coder: {time_limit: 61, write_paths'),
    'fits': TEXT.replace('coder: {write_paths', 'coder: {time_limit: 60, write_paths'),
}
for name, text in cases.items():
    try:
        reader.parse(text)
        print(name, 'accepted')
    except PipelineDefinitionInvalid as error:
        print(name, '->', error.fault)
"
```
Expect: five lines of output: `next -> stage doing: next names unknown stage ship`, then `contract -> contract major 2 is not supported (this factory reads major 1)`, then `write paths -> role coder: write_paths is empty`, then `time limit -> role coder at stage doing: 61 min exceed lease_duration 60 min`, then `fits accepted`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete module (`src/factory/domain/pipeline_definition.py`, the `PipelineDefinition` after-validator, `CONTRACT_MAJOR`, `DONE_STAGE`, `RESERVED_NAMES`) and the reader change in `src/factory/adapters/pipeline_yaml.py` (fault taken from `ctx["error"]`, prefix dropped). Every rule has its exact fault text and ordering.
   - Criteria: each is testable by one test function. Every rule has a refused and an accepted side: contract major (2, 3), contract form (4), done (5, 6), next (7, 8), role/write paths/approval (9, 10, 11, 12), reserved names (13), commands (14), time limit equal/over (15, 16), lease per role and per stage, doubles, unknown names and role-less stages (17 to 20), acceptance stage (21), multiple faults (22), field faults first (23), loader stops (24). The Interface comments (ordering, joining with "; ", integer major, `02` kept as written) are each covered.
   - Demo: runnable as written. Each Expect line gives the exact output. It is consistent with the rules, assuming `checks` and `reports` default to empty, so 61 + 0 = 61 in the time limit case.
   - Architecture: the rules are pure domain validation; the reader only translates the error to a fault; the loader is unchanged. This fits the four layers and the one-reader-per-format rule.
   - Scope: within F0003's "load-time validation" scope and kept decisions 18 and 19. The installed-agent rule belongs to S0006, and nothing here is in "Out of scope".
   - Note for the tester, not a question: criterion 5 needs a text where `done` is absent without leaving other stages' `next: [done]` unknown, or else rule 4 adds faults. Rename `done` consistently in the text.
3. tester: Wrote red tests for the load-time rules of the pipeline definition. Every case starts from `PIPELINE_YAML` and changes it by text replacement. The adapter tests check that each changed line occurs exactly once before they replace it.

   Criterion → test:
   - criterion 1: tests/adapters/test_pipeline_rules.py::test_the_test_pipeline_definition_passes_every_rule
   - criterion 2: tests/adapters/test_pipeline_rules.py::test_a_contract_major_other_than_one_is_refused (2.0, 0.9, 10.0, 02.0)
   - criterion 3: tests/adapters/test_pipeline_rules.py::test_a_contract_of_major_one_is_accepted_for_any_minor (1.0, 1.7, 1.10, 01.0)
   - criterion 4: tests/adapters/test_pipeline_rules.py::test_a_contract_without_major_and_minor_is_refused (1, 1.0.0, v1.0, 1.x)
   - criterion 5: tests/adapters/test_pipeline_rules.py::test_a_definition_without_a_done_stage_is_refused (renames `done` to `finished` everywhere, as intake suggested, so no `next` becomes unknown)
   - criterion 6: tests/adapters/test_pipeline_rules.py::test_a_done_stage_with_a_role_or_a_next_is_refused
   - criterion 7: tests/adapters/test_pipeline_rules.py::test_a_next_naming_an_unknown_stage_is_refused
   - criterion 8: tests/adapters/test_pipeline_rules.py::test_every_unknown_next_is_a_fault_of_its_own_in_the_order_of_the_text
   - criterion 9: tests/adapters/test_pipeline_rules.py::test_a_stage_with_an_undefined_role_is_refused
   - criterion 10: tests/adapters/test_pipeline_rules.py::test_a_role_needs_at_least_one_write_path (0 and 1 paths)
   - criterion 11: tests/adapters/test_pipeline_rules.py::test_an_approval_stage_with_a_role_is_refused
   - criterion 12: tests/adapters/test_pipeline_rules.py::test_the_role_checks_report_undefined_roles_then_empty_paths_then_approval_roles
   - criterion 13: tests/adapters/test_pipeline_rules.py::test_a_reserved_stage_name_is_refused and ::test_a_reserved_role_name_is_refused (human, factory, question each)
   - criterion 14: tests/adapters/test_pipeline_rules.py::test_checks_and_reports_must_name_project_commands
   - criterion 15: tests/adapters/test_pipeline_rules.py::test_a_role_time_limit_and_its_stage_checks_must_fit_the_lease (50 accepted, 51 refused)
   - criterion 16: tests/adapters/test_pipeline_rules.py::test_the_time_limits_of_checks_and_reports_both_count (45 accepted, 46 refused)
   - criterion 17: tests/adapters/test_pipeline_rules.py::test_each_role_is_measured_against_its_own_lease
   - criterion 18: tests/adapters/test_pipeline_rules.py::test_a_role_used_by_two_stages_is_measured_at_each_stage (adds stage `extra: {role: coder, next: [done]}`)
   - criterion 19: tests/adapters/test_pipeline_rules.py::test_a_command_listed_twice_counts_twice
   - criterion 20: tests/adapters/test_pipeline_rules.py::test_unknown_commands_and_stages_without_a_role_add_no_minutes (two cases)
   - criterion 21: tests/adapters/test_pipeline_rules.py::test_the_acceptance_stage_must_be_a_stage_with_a_role (nowhere, approval, acceptance)
   - criterion 22: tests/adapters/test_pipeline_rules.py::test_faults_of_two_rules_are_reported_together_in_the_order_of_the_rules
   - criterion 23: tests/adapters/test_pipeline_rules.py::test_the_rules_run_only_when_every_field_is_valid
   - criterion 24: tests/application/test_pipeline_loading_rules.py::test_a_definition_the_rules_refuse_is_one_reported_stop (four cases: unknown next, empty write paths, major 2, time limit over the lease). It checks the raised fault and that the health status holds exactly one stop with (`pipeline_definition_invalid`, fault).
   - criteria 25 and 26: not tests (`make check`, docs).

   Files created: tests/adapters/test_pipeline_rules.py, tests/application/test_pipeline_loading_rules.py.

   The test runner imported every module; nothing failed to import. The tests fail on wrong results: the rules don't exist yet, so the refusing cases raise nothing or give a different fault. The accepting cases pass already.

   `make lint` is green. I didn't run the type check, as this stage skips it.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_pipeline_loading_rules.py::test_a_definition_the_rules_refuse_is_one_reported_stop[  coder: {write_paths: ["src/*"]}-  coder: {time_limit: 51, write_paths: ["src/*"]}-role coder at stage doing: 61 min exceed lease_duration 60 min]
4. coder: Added the load-time rules of the pipeline definition. `make check` is green, all tests pass without any test change, and the Demo prints its five expected lines.

   What I built:
   - `src/factory/domain/pipeline_definition.py`
     - Adds `CONTRACT_MAJOR`, `DONE_STAGE` and `RESERVED_NAMES`.
     - Adds an after-mode `model_validator` on `PipelineDefinition`. It runs a tuple `_RULES` of eight private rule functions, each returning a list of faults. Rules 1 and 2 share `_contract_faults`, because the major is checked only when the form holds.
     - It joins every fault with "; " and raises one `ValueError`.
     - The order follows the Interface: by rule, then by stage or role in the text. Rule 5 lists its three checks in the order given.
     - The lease rule counts the minutes of a role's run plus its stage's checks and reports in `_minutes_at_stage`. Repeated names count again and unknown names count nothing. It skips stages with no role and stages whose role is undefined.
   - `src/factory/adapters/pipeline_yaml.py`: the new `_fault_of` returns `ctx["error"]` as written when the validation error is the single model-level error (empty location). Otherwise it falls back to `all_faults` as before. Field faults therefore still come first and alone, because pydantic does not run the after-validator when a field is invalid.

   Main decision: each rule is a small module-level function and the validator only collects their results. I rejected one large validator method because its ordering and branching would be hard to review against the nine rules. I also rejected raising pydantic's `PydanticCustomError` with a custom type. The reader would then have to know that type, while `ctx["error"]` is what the Interface names.

   Refactor (commit ede5c91): checks and reports now share one loop in `_command_faults`, and the role lookup in `_lease_faults` is plainer. Behaviour is unchanged.

   Noticed, not touched: the `_FAULT_SEPARATOR = "; "` constant is now defined both in the domain module and in the reader. The two join different things (rule faults and field faults), so I left them separate.

   `make check`: check: green
5. reviewer: no findings.

   What I checked:
   - `src/factory/domain/pipeline_definition.py`: I read the after-validator and its eight rule functions against the nine rules in the Interface. One function, `_contract_faults`, covers rules 1 and 2, so the major is checked only when the form holds. I confirmed the fault texts match the Interface exactly. Faults are ordered by rule, then by stage or role in the text. Inside rule 5 they come as undefined role, then empty write paths, then an approval stage with a role. Rule 8 skips stages with no role or an undefined role, counts a command listed twice twice and counts an unknown command as nothing. The total may equal the lease.
   - `src/factory/adapters/pipeline_yaml.py` (`_fault_of`): it returns `ctx["error"]` only for a single error with an empty location, and otherwise falls back to `all_faults` as before. Pydantic skips after-validators when a field is invalid, so field faults come first and alone (criterion 23).
   - Criteria 1–24 each map to one test in `tests/adapters/test_pipeline_rules.py` or `tests/application/test_pipeline_loading_rules.py`, and each test asserts what its criterion names. Each limit in the Interface is tested on both sides:
     - contract major refused (2, 0, 10, 02) and accepted (1.x, 01.0)
     - contract form refused and accepted
     - done stage missing, with a role, with a `next`
     - write paths 0 and 1
     - lease totals 60 and 61, for checks alone and for checks plus reports
     - acceptance stage: unknown, a stage without a role, and a valid one
   - Criterion 5: `PIPELINE_YAML.replace("done", "finished")` touches only the `done` stage and the `next` entries that name it (I checked `tests/git_support.py`), so no other rule adds a fault.
   - The coder's entry reports the factory's `make check` green.
   - Architecture: the rules are pure domain code (using `re` only), and the adapter only translates the error into a fault. No new dependency and no suppression markers.

   Considered, not raised: the `"; "` separator constant now exists in both the domain module and the reader. They join different things (rule faults in the domain, field faults in the reader), and the domain constant is private, so the reader cannot import it.

   Ticket hygiene: the log explains the main decision (small rule functions collected by one validator) and what was rejected. The Assignment matches what was built. Criterion 26 still says what the documenter must write.
6. documenter: wrote the documentation for the load-time rules of the pipeline definition. `make check` is green.

   Files changed:
   - `docs/project-guide.md`
     - New section "The rules of the definition". It covers the contract version (major must be 1, any minor is read, `01.0` is read), the lease rule with the 40+10+10=60 default example and a two-checks-plus-report counter-example, and a table of every fault in rule order.
     - Replaced the stale "Not checked here, by later stories" bullet in "The pipeline definition". Added a note in "Faults" that the rules run only after the field faults are clear.
   - `docs/operator-guide.md`: a row in the `pipeline_definition_invalid` faults table for the cross-key faults. It gives examples and points to the project guide's "The rules of the definition".
   - `docs/decisions.md`: new entry. The rules refuse at load, the faults of one text are reported together, field faults come first, and the alternatives I rejected.

   Cross-read and found current: the README, and the loader, agent and work item sections of the project guide.

   Stale but not touched: none.

   Findings: none. The code matches the Interface and the criteria.

   I did not run the project-guide example code. I added no new example, and the existing one is unchanged and still valid.

   `make check`: check: green
