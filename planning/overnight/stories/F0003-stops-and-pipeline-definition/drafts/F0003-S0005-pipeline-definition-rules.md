# Load-time rules of the pipeline definition

## Assignment (as of log entry 1)

Add the rules that look across the keys of the pipeline definition, so that a definition that is well formed but cannot work is refused when it loads and not when a stage first reaches the fault (R30, R21): an unknown major contract version (ST8.4), a `next` naming a stage that does not exist (ST8.2), a role without write paths (the write-path half of ST8.3), and a role whose agent run `time_limit` plus the `time_limit`s of a stage's checks and reports do not fit inside the role's `lease_duration` (ST8.5, GH1.4). They are validators of `PipelineDefinition`, so every reader and every ref gets them; a refusal is the `PipelineDefinitionInvalid` that S0003's reader already raises, and S0004's loader already turns into a `pipeline_definition_invalid` stop, so each refusal here is a reported stop that names the fault. The other rules of the definition (a `done` stage, approval and reserved names, the project commands that checks and reports name, the acceptance stage) are in the same validator because they are the same kind of fault. Covers ST8.2, ST8.3 (write paths), ST8.4, ST8.5, GH1.4, R21 (validation of the lease) and R30; keeps kept things 7 and 12.

## Interface

`src/factory/domain/pipeline_definition.py` (adds to S0003's module)

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

`src/factory/adapters/pipeline_yaml.py` (changes `RuamelPipelineDefinitionReader.parse`): a `ValueError` of the model validator is reported as its message, as written, without pydantic's prefix `Value error, `. The rules run only when every field is valid; the field faults of S0003 come first.

Rules and the fault each one gives (`<s>` is a stage, `<t>` a stage name, `<r>` a role, `<c>` a project command):

1. The contract has the form `<digits>.<digits>`, else `contract must look like <major>.<minor>, got '<contract>'`.
2. When the form holds, the major (compared as an integer) is `CONTRACT_MAJOR`, else `contract major <major> is not supported (this factory reads major 1)` (ST8.4). Any minor version is accepted.
3. `stages` holds a stage named `DONE_STAGE`, else `stages must hold a stage named done`; that stage has no role and an empty `next`, else `stage done must have no role and no next`.
4. Every name in the `next` of a stage is a stage, else `stage <s>: next names unknown stage <t>` (ST8.2), once for each unknown name.
5. A stage's role is a key of `roles`, else `stage <s>: role <r> is not defined in roles`; every role has at least one write path, else `role <r>: write_paths is empty` (ST8.3); a stage with `approval: true` has no role, else `stage <s>: an approval stage has no role`. The three checks of this rule are reported in the order written here.
6. No stage name and no role name is one of `RESERVED_NAMES`, else `stage name <n> is reserved` or `role name <n> is reserved`.
7. Every name in `checks` and in `reports` of a stage is a key of `project_commands`, else `stage <s>: check <c> is not a project command` or `stage <s>: report <c> is not a project command`.
8. For each stage with a role that is a key of `roles`: the role's `time_limit` plus the `time_limit` of each command listed in the stage's `checks` and each listed in its `reports` (a command listed twice counts twice; a name that is not a key of `project_commands` counts nothing) is at most the role's `lease_duration`, else `role <r> at stage <s>: <total> min exceed lease_duration <lease> min` (ST8.5, GH1.4). The total may equal the lease. `lease_duration` is the role's own; stages without a role are not measured.
9. When `acceptance_stage` is set it names a stage that has a role, else `acceptance_stage <t> is not a stage with a role`.

Tests: `tests/domain/test_pipeline_rules.py`, `tests/application/test_pipeline_loading_rules.py`. The domain tests parse text through `RuamelPipelineDefinitionReader` and compare `PipelineDefinitionInvalid.fault`; the example definition of S0003 (nine stages, project commands `check` 10, `lint` 5 and `test` 10 minutes, default role limits 40 and 60) is the base of every case, changed by text replacement. The loader tests use the fixtures of S0004.

## Acceptance criteria

1. The example definition of S0003 passes every rule: parsing it raises nothing.
2. A contract whose major is not 1 (`"2.0"`, `"0.9"`, `"10.0"`) is refused with the fault `contract major <major> is not supported (this factory reads major 1)` (ST8.4).
3. A contract whose major is 1 is accepted for any minor (`"1.0"`, `"1.7"`, `"1.10"`).
4. A contract that does not have the form `<digits>.<digits>` (`"1"`, `"1.0.0"`, `"v1.0"`, `"1.x"`) is refused with the fault `contract must look like <major>.<minor>, got '<contract>'`, naming the text written.
5. A definition without a stage named `done` is refused with the fault `stages must hold a stage named done`.
6. A `done` stage that has a role, or a `next`, is refused with the fault `stage done must have no role and no next`.
7. A stage whose `next` names a stage that does not exist is refused with the fault `stage <s>: next names unknown stage <t>`; with `next: [review, ship]` in the stage `doing` the fault is `stage doing: next names unknown stage ship` (ST8.2).
8. A stage whose role is not a key of `roles` is refused with the fault `stage <s>: role <r> is not defined in roles`.
9. A role whose `write_paths` is empty is refused with the fault `role <r>: write_paths is empty`; a role with one write path is accepted (ST8.3).
10. A stage with `approval: true` that also has a role is refused with the fault `stage <s>: an approval stage has no role`.
11. A stage named `human`, `factory` or `question`, and a role with one of these names, are each refused with the fault `stage name <n> is reserved` or `role name <n> is reserved`.
12. A stage whose `checks` names a command that is not a key of `project_commands` is refused with the fault `stage <s>: check <c> is not a project command`; the same for `reports` with `report`.
13. With the coder's `time_limit` at 50, its stage `doing` (checks `check`, 10 minutes) totals 60 and the definition is accepted: the total may equal the `lease_duration` of 60 (ST8.5, the limit's accepting side).
14. With the coder's `time_limit` at 51, the same definition is refused with the fault `role coder at stage doing: 61 min exceed lease_duration 60 min` (ST8.5, GH1.4, R21).
15. The `time_limit`s of checks and of reports both count: with the tester's `time_limit` at 45 its stage `tests` (checks `lint` 5, reports `test` 10) totals 60 and is accepted; at 46 it totals 61 and is refused with the fault `role tester at stage tests: 61 min exceed lease_duration 60 min`.
16. The lease is the role's own: with the coder's `lease_duration` at 90 and `time_limit` at 70 (stage `doing` totals 80) and the tester's `time_limit` at 70 under the default lease of 60 (stage `tests` totals 85), only the tester is refused, with the fault `role tester at stage tests: 85 min exceed lease_duration 60 min`.
17. A role used by two stages is measured at each stage: with a second stage that also has the coder's role and no checks, and the coder's `time_limit` at 55, the fault names only the stage with the check, `role coder at stage doing: 65 min exceed lease_duration 60 min`, and not the other stage.
18. An `acceptance_stage` that is not a stage, or names a stage without a role (`approval`), is refused with the fault `acceptance_stage <t> is not a stage with a role`; `acceptance` is accepted.
19. A definition that breaks two rules is refused once, and its `fault` is the two faults in the order of the rules joined by `; ` (for example a `next` naming `ship` in `doing`, and the coder's `time_limit` at 51, give `stage doing: next names unknown stage ship; role coder at stage doing: 61 min exceed lease_duration 60 min`).
20. Loaded through `PipelineLoader.load`, each of these refusals is a reported stop that names the fault: a `next` naming an unknown stage (ST8.2), a role without write paths (ST8.3), a contract with major 2 (ST8.4) and a role whose limits exceed its lease (ST8.5, GH1.4) each make `load` raise `PipelineDefinitionInvalid` and leave exactly one stop in the health status, with `reason` `pipeline_definition_invalid` and `detail` equal to the fault (one parametrised test, four cases).
21. `make check` stays green.
22. docs: `docs/project-guide.md` explains the contract version (the major must be 1, any minor is read), the rule that a role's `time_limit` plus the `time_limit`s of a stage's checks and reports must not exceed the role's `lease_duration` (with the defaults 40 + 10 + 10 fits 60, a stage with two checks and a report does not), and lists the faults a refused definition reports; `docs/operator-guide.md` points from the stop `pipeline_definition_invalid` to that list; `docs/decisions.md` records that the rules refuse at load and that the faults of one text are reported together.

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
