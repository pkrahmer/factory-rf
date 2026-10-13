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
