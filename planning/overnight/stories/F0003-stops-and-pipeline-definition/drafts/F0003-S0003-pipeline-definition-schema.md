# The pipeline definition schema and its defaults

## Assignment (as of log entry 1)

Build the pipeline definition as a Pydantic schema with defaults (R30) and the reader that turns the project's `factory/pipeline.yml` into it with ruamel.yaml (R13): stages with their role, approval, `next`, checks, reports and round cap; per role the write paths, `lease_duration` (default 60 minutes) and `time_limit` (default 40 minutes); the attempts cap and the crash cap (both default 2); the project commands with their `time_limit`; the contract version. A key that has a default may be left out and takes it (the second half of ST8.1); a key without a default that is missing, a key the schema does not know, a value of the wrong type and a text that is not YAML are each refused with `PipelineDefinitionInvalid`, whose `fault` names them. The rules that look across keys (a `next` naming no stage, the contract's major version, `time_limit`s that must fit inside `lease_duration`) are S0005, and reporting a refusal as a stop is S0004; this story only refuses what the schema itself cannot hold. The reader is the only reader of this format and there is no writer (no story writes the pipeline definition). Covers R30 (the schema and its defaults) and the schema half of ST8.1; keeps kept thing 7 (the pipeline definition is the project's configuration).

## Interface

`src/factory/domain/errors.py` (adds to F0001-S0001's hierarchy)

```python
class PipelineDefinitionInvalid(FactoryError):
    fault: str
    def __init__(self, fault: str) -> None: ...      # the message is the fault
```

`src/factory/domain/pipeline_definition.py`

```python
WORK_ITEM_PLACEHOLDER = "{work_item}"         # in write_paths: the work item's own file
FEATURE_PLACEHOLDER = "{feature}"             # in write_paths: the work item's feature directory

class RoleDefinition(BaseModel):
    write_paths: list[str]                    # required, no default
    lease_duration: PositiveInt = 60          # minutes
    time_limit: PositiveInt = 40              # minutes: the agent run's time_limit

class StageDefinition(BaseModel):
    role: Name | None = None                  # None: no agent runs here (an approval, done)
    next: list[Name] = []                     # where the stage may move; next[0] is the forward move
    approval: bool = False                    # the human decides here
    checks: list[str] = []                    # project commands, in order, after the agent
    reports: list[str] = []                   # project commands after green, recorded only
    round_cap: PositiveInt | None = None      # rework rounds before the human is asked; None: no cap

class ProjectCommandDefinition(BaseModel):
    time_limit: PositiveInt = 10              # minutes

class PipelineDefinition(BaseModel):
    contract: str                             # required, "<major>.<minor>"
    stages: dict[Name, StageDefinition]       # required; YAML order is the pipeline's order
    roles: dict[Name, RoleDefinition]         # required; a role's name is its agent definition's name
    project_commands: dict[Name, ProjectCommandDefinition] = {
        "check": ProjectCommandDefinition(), "lint": ProjectCommandDefinition(),
        "test": ProjectCommandDefinition()}
    attempts_cap: PositiveInt = 2
    crash_cap: PositiveInt = 2
    acceptance_stage: Name | None = None
    def first_stage(self) -> str: ...                              # the first key of stages
    def role_of(self, stage: str) -> RoleDefinition | None: ...    # KeyError for an unknown stage
    def position(self, stage: str) -> int: ...                     # its index in stages
```

`src/factory/application/files.py` (adds to F0002-S0002's module)

```python
class PipelineDefinitionReader(Protocol):
    def parse(self, text: str) -> PipelineDefinition: ...    # PipelineDefinitionInvalid, naming the fault
```

`src/factory/adapters/pipeline_yaml.py`

```python
class RuamelPipelineDefinitionReader:
    def parse(self, text: str) -> PipelineDefinition: ...
```

`src/factory/application/boundaries.py` (adds the field `pipeline_reader: PipelineDefinitionReader` to `Boundaries`; the `boundaries` fixture gets `RuamelPipelineDefinitionReader()`).

The example definition used in the criteria (the shape of the fixture's `factory/pipeline.yml` and of the template that F0010 ships):

```yaml
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [docs, doing], round_cap: 3}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check], round_cap: 3}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 3}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
```

Rules:

- `parse` loads the text with ruamel.yaml in safe mode, so it builds plain data only, and a key that occurs twice in one mapping is refused. Whatever goes wrong, the only exception it raises is `PipelineDefinitionInvalid`.
- Faults, by their `fault` text: YAML that cannot be read (including a repeated key) is `not valid YAML: <problem>`, with the repeated key named in the problem; a text whose top level is not a mapping (an empty text included) is `the pipeline definition must be a mapping`. Otherwise the data is validated against `PipelineDefinition`, and each error of the validation is one fault: a missing key is `missing key <path>`, a key the schema does not know is `unknown key <path>`, any other error is `<path>: <pydantic's message>`. `<path>` is the key path joined by `.` (for example `roles.coder.write_paths`). All faults of one text are in `fault`, in the order pydantic reports them, joined by `; `.
- The schema forbids unknown keys at every level, so a misspelt key is a fault and never silently ignored. A key that has a default may be left out. A given `project_commands` replaces the default set as a whole (it does not merge with it); a command given as `{}` takes `time_limit` 10.
- Every limit above is a positive integer; stage, role and command names match `^[a-z][a-z0-9-]*$`; `contract` must be a string, so an unquoted `1.0` is a fault.
- `PipelineDefinition` and the domain package import no `ruamel`, and neither does `factory.application`.

Tests: `tests/domain/test_pipeline_definition.py`, `tests/adapters/test_pipeline_yaml.py`. The tests spell out the example definition above as a constant.

## Acceptance criteria

1. Parsing the example definition gives a `PipelineDefinition` with `contract == "1.0"`, `attempts_cap == 2`, `crash_cap == 2`, `acceptance_stage == "acceptance"`, nine stages in the order of the text (`list(definition.stages)` starts with `intake` and ends with `done`), seven roles, `stages["doing"].next == ["review", "tests"]`, `stages["tests"].checks == ["lint"]`, `stages["tests"].reports == ["test"]`, `stages["review"].round_cap == 3`, `stages["approval"].approval is True` and `roles["coder"].write_paths == ["src/*"]`.
2. `first_stage()` of the example definition is `intake`.
3. `role_of("doing")` is the coder's `RoleDefinition`; `role_of("approval")` and `role_of("done")` are `None`.
4. `role_of("nowhere")` raises `KeyError`.
5. `position("intake")` is 0, `position("tests")` is 1 and `position("done")` is 8.
6. A role that leaves out `lease_duration` and `time_limit` has `lease_duration == 60` and `time_limit == 40`; a text that leaves out `attempts_cap`, `crash_cap` and `acceptance_stage` has 2, 2 and `None` (ST8.1: a key with a default takes it).
7. A stage written `done: {}` has `role is None`, `next == []`, `approval is False`, `checks == []`, `reports == []` and `round_cap is None`.
8. A text that leaves out `project_commands` has exactly the commands `check`, `lint` and `test`, each with `time_limit == 10`.
9. A text whose `project_commands` is `{check: {time_limit: 3}}` has exactly the one command `check`, with `time_limit == 3`; a command written `lint: {}` takes `time_limit == 10`.
10. Given values replace the defaults: `lease_duration: 90`, `time_limit: 25`, `attempts_cap: 5` and `crash_cap: 3` are read as given.
11. A text without `contract`, without `stages`, without `roles`, or with a role that has no `write_paths` is refused with `PipelineDefinitionInvalid` whose `fault` is exactly `missing key contract`, `missing key stages`, `missing key roles` and `missing key roles.coder.write_paths` respectively (one test per case).
12. An unknown key is refused naming its path: `fault` is exactly `unknown key lease_minutes` for a top-level `lease_minutes: 60`, `unknown key stages.doing.agent` for `agent: coder` inside the stage `doing`, and `unknown key roles.coder.lanes` for `lanes: []` inside the role `coder` (one test, three cases).
13. For each of `roles.coder.lease_duration`, `roles.coder.time_limit`, `attempts_cap`, `crash_cap`, `stages.review.round_cap` and `project_commands.check.time_limit`, the values 0 and -1 are refused with a `fault` that starts with that path, and the value 1 is accepted.
14. A stage named `Doing`, `1st` or `do_ing` is refused with a `fault` that contains the name, and so are a role named `Coder` and a project command named `Check`; the names `smoke-test` and `a1` are accepted for a stage, a role and a command.
15. A value of the wrong type is refused with a `fault` that starts with its path: `stages` written as a list, `stages.doing.next` written as the string `review`, `roles.coder.write_paths` written as the string `src/*`, and `contract` written as the unquoted number `1.0`.
16. A text that is not YAML (for example an unclosed `[`), and a text with the stage `doing` written twice, are refused with a `fault` that starts with `not valid YAML:`; for the repeated key it contains `doing`.
17. A text whose top level is a list, a plain string, or empty is refused with the `fault` `the pipeline definition must be a mapping`.
18. A text that has both a missing `contract` and an unknown top-level key `x` is refused once, and its `fault` holds both faults, `missing key contract` and `unknown key x`, joined by `; `.
19. `PipelineDefinitionInvalid("m").fault` is `"m"`, `str(PipelineDefinitionInvalid("m"))` is `"m"`, and it is a `FactoryError`.
20. `WORK_ITEM_PLACEHOLDER` is `{work_item}` and `FEATURE_PLACEHOLDER` is `{feature}`.
21. No module in `factory.domain` or `factory.application` imports `ruamel` (a test that walks the sources with `ast`).
22. `make check` stays green.
23. docs: `docs/project-guide.md` explains the pipeline definition's keys, which of them have defaults (`lease_duration` 60 and `time_limit` 40 minutes per role, `time_limit` 10 minutes per project command, `attempts_cap` 2, `crash_cap` 2), that unknown keys are refused, that a given `project_commands` replaces the default set, and that `contract` must be quoted; `docs/decisions.md` records that the schema forbids unknown keys.

## Demo

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
  tester: {write_paths: ['tests/*'], lease_duration: 90}
stages:
  tests: {role: tester, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
'''
reader = RuamelPipelineDefinitionReader()
definition = reader.parse(TEXT)
print(definition.first_stage(), list(definition.stages), definition.position('done'))
print(definition.roles['tester'].lease_duration, definition.roles['coder'].lease_duration, definition.roles['coder'].time_limit)
print(definition.attempts_cap, definition.crash_cap, sorted(definition.project_commands))
try:
    reader.parse(TEXT.replace('contract', 'contrakt'))
except PipelineDefinitionInvalid as error:
    print('missing key contract' in error.fault, 'unknown key contrakt' in error.fault)
"
```
Expect: four lines of output: `tests ['tests', 'doing', 'done'] 2`, then `90 60 40`, then `2 2 ['check', 'lint', 'test']`, then `True True`.

## Log (append only)

1. 2026-10-12 human: created.
