---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Strict values in the pipeline definition

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The pipeline definition is the project's configuration, and decision 9 of F0003 refuses a misspelt key and an unquoted contract so that the factory never runs on a setting the project did not choose. The values themselves are still read in pydantic's lax mode, which turns some wrong values into settings without a word:

- `time_limit: true` is 1 minute.
- `time_limit: '30'` and `time_limit: 30.0` are 30.
- `approval: 'yes'` is true, and `approval: 'off'` and `approval: 0` are false.
- An empty write path `''`, or one of spaces only, is accepted.

This story makes every model of the pipeline definition validate in strict mode, so a value is taken only when YAML gives it in its own type, and refuses a blank write path. Each refusal is a field fault, `invalid <path>: <message>`, reported through the existing reader and, at load, the existing `pipeline_definition_invalid` stop. Covers R30 (the schema) and keeps kept thing 7. The acceptance of F0003 found the gap (section 2 probes, 4.2). Decided by the human on 2026-10-14, as the pre-check recommended: values are taken only as written; lax mode with a warning was rejected, because nothing would show the warning to the operator. The multi-line YAML fault (acceptance 4.1) is not part of this story.

## Interface

`src/factory/domain/pipeline_definition.py` (changes S0004's models)

```python
class RoleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    write_paths: list[WritePath]              # WritePath: a str that holds at least one non-whitespace character
    ...

class StageDefinition(BaseModel):            # strict=True
class ProjectCommandDefinition(BaseModel):   # strict=True
class PipelineDefinition(BaseModel):         # strict=True
```

Rules:

- Each of the four models validates in strict mode. An integer limit takes only a YAML integer: a boolean, a string or a float is refused. `approval` takes only a YAML boolean (`true`, `false`): a string or a number is refused. Names, `contract`, `checks`, `reports` and `write_paths` take only strings, as today.
- A write path holds at least one character that is not whitespace. An empty or whitespace-only write path is refused at its list position: the fault starts with `invalid roles.<role>.write_paths[<n>]:`.
- The faults keep S0004's spelling (`invalid <path>: <pydantic's message>`) and order, and come before the rules of S0007, as today.
- `PIPELINE_YAML` in `tests/git_support.py` still parses unchanged, and so does every text S0004's and S0007's tests accept.

Tests: a new file `tests/adapters/test_pipeline_strict_values.py`, through `RuamelPipelineDefinitionReader`, every case built on `PIPELINE_YAML` by text replacement as S0004 and S0007 do. The load through `PipelineLoader` is in a new file `tests/application/test_pipeline_loading_strict_values.py` and uses S0006's fixtures (`boundaries`, `human`, `checkout`, `agent_home`, `install_agents`). No existing test changes.

## Acceptance criteria

1. `PIPELINE_YAML` still parses. (S0004's `MINIMAL` keeps parsing in S0004's own tests, which this story does not change.)
2. For each of `roles.coder.lease_duration`, `roles.coder.time_limit`, `attempts_cap`, `crash_cap`, `stages.review.round_cap` and `project_commands.lint.time_limit`, the values `true`, `'30'` and `30.0` are each refused with a `fault` that starts with `invalid <that path>:`. An integer is still accepted: `30` for each path, except `roles.coder.lease_duration`, which takes `50`, and `project_commands.lint.time_limit`, which takes `10`, so that S0007's lease rule holds for the stages `doing` and `tests`.
3. `approval` written as `'yes'`, `'off'`, `1` or `0` in the stage `approval` is refused with a `fault` that starts with `invalid stages.approval.approval:`. `true` is accepted there, and `approval: false` is accepted on the stage `doing`.
4. A write path `''` or `'  '` in the role `coder` is refused with a `fault` that starts with `invalid roles.coder.write_paths[0]:`. `'src/*'` and `'{work_item}'` are accepted.
5. Text fields still take only strings: `checks: [1]` in the stage `doing` is refused with a `fault` that starts with `invalid stages.doing.checks[0]:`, and `reports: [1]` in the stage `tests` with one that starts with `invalid stages.tests.reports[0]:`.
6. A text with a strict-value fault and a fault of the rules (a `next` naming `ship`) is refused with the field fault alone, and its `fault` does not contain `ship`.
7. Loaded through `PipelineLoader.load` at `origin/main`, a `time_limit: true` is a reported stop. `load` raises `PipelineDefinitionInvalid`, and the health status holds one stop `pipeline_definition_invalid` whose `detail` starts with `invalid roles.coder.time_limit:`.
8. `make check` stays green.
9. docs: `docs/project-guide.md`, "The pipeline definition", says that values are taken only in their YAML type (`true` is no integer, `'yes'` no boolean, `'30'` no number) and that a write path must not be blank. `docs/decisions.md` records that the definition validates in strict mode, with the reason (decision 9's: no setting the project did not choose) and the rejected alternative (lax mode with a warning).

## Demo

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*'], time_limit: 30}
stages:
  gate: {approval: true, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
'''
reader = RuamelPipelineDefinitionReader()
print(reader.parse(TEXT).roles['coder'].time_limit)
for old, new in [('time_limit: 30', 'time_limit: true'), ('time_limit: 30', \"time_limit: '30'\"), ('approval: true', \"approval: 'yes'\"), (\"['src/*']\", \"['']\")]:
    try:
        reader.parse(TEXT.replace(old, new))
        print('accepted')
    except PipelineDefinitionInvalid as error:
        print(error.fault.split(':')[0])
"
```
Expect: five lines: `30`, then `invalid roles.coder.time_limit` twice, then `invalid stages.gate.approval`, then `invalid roles.coder.write_paths[0]`. No line says `accepted`.

## Log (append only)

1. 2026-10-14 human: created.
