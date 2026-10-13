---
stage: doing
pr: 43
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The pipeline definition schema and its defaults

## Assignment (as of log entry 1)

Build the pipeline definition as a Pydantic schema with defaults (R30) and the reader that turns the project's `factory/pipeline.yml` into it with ruamel.yaml (R13): stages with their role, approval, `next`, checks, reports and round cap; per role the write paths, `lease_duration` (default 60 minutes) and `time_limit` (default 40 minutes); the attempts cap and the crash cap (both default 2); the project commands with their `time_limit`; the contract version. A key that has a default may be left out and takes it (the second half of ST8.1); a key without a default that is missing, a key the schema does not know, a value of the wrong type and a text that is not YAML are each refused with `PipelineDefinitionInvalid`, whose `fault` names them. The faults are spelled by the module that F0002 built for the work item reader, `factory.adapters.validation_faults`, which this story extends with `all_faults`, so that two readers never name one fault in two ways. The rules that look across keys (a `next` naming no stage, the contract's major version, `time_limit`s that must fit inside `lease_duration`) are S0007, and reporting a refusal as a stop is S0006; this story only refuses what the schema itself cannot hold. The reader is the only reader of this format and there is no writer (no story writes the pipeline definition). `RuamelPipelineDefinitionReader` inherits the `PipelineDefinitionReader` abstract base class. Covers R30 (the schema and its defaults) and the schema half of ST8.1; keeps kept thing 7 (the pipeline definition is the project's configuration).

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
    contract: str                             # required, quoted text; its form "<major>.<minor>" and its major are checked by S0007
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

`src/factory/application/files.py` (adds to F0002-S0003's module)

```python
class PipelineDefinitionReader(ABC):
    @abstractmethod
    def parse(self, text: str) -> PipelineDefinition: ...    # PipelineDefinitionInvalid, naming the fault
```

`src/factory/adapters/pipeline_yaml.py`

```python
class RuamelPipelineDefinitionReader(PipelineDefinitionReader):
    def parse(self, text: str) -> PipelineDefinition: ...
```

`src/factory/adapters/validation_faults.py` (adds to F0002's module, beside `first_fault`)

```python
def all_faults(validation_error: ValidationError, whole: str) -> list[str]: ...
    # every fault, in the rank order of first_fault: unknown key, missing key, invalid value, invalid whole;
    # faults of one rank in the order pydantic reports them; first_fault is the first of them
```

`src/factory/application/boundaries.py` (adds the field `pipeline_reader: PipelineDefinitionReader` to `Boundaries`; the `boundaries` fixture gets `RuamelPipelineDefinitionReader()`).

The example definition used in the criteria is `PIPELINE_YAML` in `tests/git_support.py`: the shape of the `remote` fixture's `factory/pipeline.yml` and of the template that F0010 ships (its text is the interface sheet's `factory/pipeline.yml`, with `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, `acceptance`, `approval` and `done` as stages and seven roles).

The minimal text used where a case needs a small definition (it satisfies the load-time rules of S0007, so no test of this story changes when they arrive):

```yaml
contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
  tester: {write_paths: ['tests/*']}
stages:
  tests: {role: tester, next: [doing]}
  doing: {role: coder, next: [done]}
  done: {}
```

Rules:

- `parse` loads the text with ruamel.yaml in safe mode, so it builds plain data only, and a key that occurs twice in one mapping is refused. Whatever goes wrong, the only exception it raises is `PipelineDefinitionInvalid`.
- Faults, by their `fault` text: YAML that cannot be read (including a repeated key) is `not valid YAML: <problem>`, with the repeated key named in the problem; a text whose top level is not a mapping (an empty text included) is `the pipeline definition must be a mapping`. Otherwise the data is validated against `PipelineDefinition`, and each error of the validation is one fault, taken from `all_faults(error, "pipeline definition")` and joined by `; `: a missing key is `missing key: <path>`, a key the schema does not know is `unknown key: <path>`, any other error is `invalid <path>: <pydantic's message>`. `<path>` is the key path with dots between keys and `[n]` for a list position (for example `roles.coder.write_paths`). A text with several faults is refused once, with all of them in `fault`, in the order of `all_faults`: unknown keys, missing keys, invalid values.
- The schema forbids unknown keys at every level, so a misspelt key is a fault and never silently ignored. A key that has a default may be left out. A given `project_commands` replaces the default set as a whole (it does not merge with it); a command given as `{}` takes `time_limit` 10.
- Every limit above is a positive integer; stage, role and command names match `^[a-z][a-z0-9-]*$`; `contract` must be a string, so an unquoted `1.0` is a fault.
- `PipelineDefinition` and the domain package import no `ruamel`, and neither does `factory.application`. No variable is named `yaml`, because the project's semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`. Each abstract method's body is its docstring alone.

Tests: `tests/domain/test_pipeline_definition.py`, `tests/adapters/test_pipeline_yaml.py`, `tests/adapters/test_validation_faults.py`, `tests/application/test_pipeline_definition_reader.py`. The tests use `PIPELINE_YAML` from `tests/git_support.py`, which already holds the example definition and is the `remote` fixture's `factory/pipeline.yml`, and the minimal text above. Every accepting case is built on one of the two, with the case's change made by text replacement, so that the load-time rules that come later do not refuse it: each accepting case keeps a stage `done` with no role and no `next`, keeps every name in a `next` and every stage's `role` naming a stage or role of the text, lists in `checks` and `reports` only commands of `project_commands`, and keeps every role's `time_limit` plus the `time_limit`s of its stage's checks and reports within its `lease_duration`. So the accepted lease of 1 (criterion 13) is given on the minimal text, whose stage `doing` has no checks, together with a `time_limit` of 1 for the coder (on `PIPELINE_YAML` the stage `doing` checks `check`, 10 minutes); the other accepted values of criterion 13 may use `PIPELINE_YAML`, and a `round_cap` is given to the stage `doing`. The test that `PipelineDefinitionReader` cannot be instantiated (criterion 22) calls it through a variable typed `type[object]` (`interface: type[object] = PipelineDefinitionReader`), as `tests/application/test_interfaces.py` does, because a direct call is a `mypy --strict` error (`abstract`).

## Acceptance criteria

1. Parsing `PIPELINE_YAML` gives a `PipelineDefinition` with `contract == "1.0"`, `attempts_cap == 2`, `crash_cap == 2`, `acceptance_stage == "acceptance"`, nine stages in the order of the text (`list(definition.stages)` starts with `intake` and ends with `done`), seven roles, `stages["doing"].next == ["review", "tests"]`, `stages["tests"].checks == ["lint"]`, `stages["tests"].reports == ["test"]`, `stages["review"].round_cap == 3`, `stages["approval"].approval is True` and `roles["coder"].write_paths == ["src/*"]`.
2. `first_stage()` of that definition is `intake`.
3. `role_of("doing")` is the coder's `RoleDefinition`; `role_of("approval")` and `role_of("done")` are `None`.
4. `role_of("nowhere")` raises `KeyError`.
5. `position("intake")` is 0, `position("tests")` is 1 and `position("done")` is 8.
6. A role that leaves out `lease_duration` and `time_limit` has `lease_duration == 60` and `time_limit == 40`; a text that leaves out `attempts_cap`, `crash_cap` and `acceptance_stage` has 2, 2 and `None` (ST8.1: a key with a default takes it).
7. A stage written `done: {}` has `role is None`, `next == []`, `approval is False`, `checks == []`, `reports == []` and `round_cap is None`.
8. A text that leaves out `project_commands` has exactly the commands `check`, `lint` and `test`, each with `time_limit == 10`.
9. On the minimal text, a `project_commands` of `{check: {time_limit: 3}}` gives exactly the one command `check`, with `time_limit == 3`; a command written `lint: {}` takes `time_limit == 10`.
10. Given values replace the defaults: `lease_duration: 90`, `time_limit: 25`, `attempts_cap: 5` and `crash_cap: 3` are read as given.
11. A text without `contract`, without `stages`, without `roles`, or with a role that has no `write_paths` is refused with `PipelineDefinitionInvalid` whose `fault` is exactly `missing key: contract`, `missing key: stages`, `missing key: roles` and `missing key: roles.coder.write_paths` respectively (one test per case).
12. An unknown key is refused naming its path: `fault` is exactly `unknown key: lease_minutes` for a top-level `lease_minutes: 60`, `unknown key: stages.doing.agent` for `agent: coder` inside the stage `doing`, and `unknown key: roles.coder.lanes` for `lanes: []` inside the role `coder` (one test, three cases).
13. For each of `roles.coder.lease_duration`, `roles.coder.time_limit`, `attempts_cap`, `crash_cap`, `stages.doing.round_cap` and `project_commands.check.time_limit`, the values 0 and -1 are refused with a `fault` that starts with `invalid <that path>:`, and the value 1 is accepted.
14. A stage named `Doing`, `1st` or `do_ing` is refused with a `fault` that contains the name, and so are a role named `Coder` and a project command named `Check`; the names `smoke-test` and `a1` are accepted for a stage, a role and a command.
15. A value of the wrong type is refused with a `fault` that starts with `invalid <path>:` for its path: `stages` written as a list, `stages.doing.next` written as the string `review`, `roles.coder.write_paths` written as the string `src/*`, and `contract` written as the unquoted number `1.0`.
16. A text that is not YAML (for example an unclosed `[`), and a text with the stage `doing` written twice, are refused with a `fault` that starts with `not valid YAML:`; for the repeated key it contains `doing`.
17. A text whose top level is a list, a plain string, or empty is refused with the `fault` `the pipeline definition must be a mapping`.
18. A text that has both a missing `contract` and an unknown top-level key `x` is refused once, and its `fault` is exactly `unknown key: x; missing key: contract`.
19. `all_faults` of a `ValidationError` that holds an invalid value, a missing key and an unknown key returns three faults in the order unknown key, missing key, invalid value, spelled `unknown key: <path>`, `missing key: <path>` and `invalid <path>: <message>`, and `first_fault` of the same error is the first of them.
20. `PipelineDefinitionInvalid("m").fault` is `"m"`, `str(PipelineDefinitionInvalid("m"))` is `"m"`, and it is a `FactoryError`.
21. `WORK_ITEM_PLACEHOLDER` is `{work_item}` and `FEATURE_PLACEHOLDER` is `{feature}`.
22. `PipelineDefinitionReader` is an abstract base class that cannot be instantiated, whose one abstract method is `parse` with a body that is its docstring alone, and `RuamelPipelineDefinitionReader` inherits it.
23. `test_only_the_work_item_adapter_imports_frontmatter_and_ruamel` stays green: no module in `factory.domain`, `factory.application` or `factory.entry` imports `ruamel`.
24. `make check` stays green.
25. docs: `docs/project-guide.md` explains the pipeline definition's keys, which of them have defaults (`lease_duration` 60 and `time_limit` 40 minutes per role, `time_limit` 10 minutes per project command, `attempts_cap` 2, `crash_cap` 2), that unknown keys are refused, that a given `project_commands` replaces the default set, that `contract` must be quoted, that `done:` written as null is refused (`done: {}` is the stage), that a name that breaks the pattern is reported at the path `stages.<name>.[key]` (and `roles.<name>.[key]`, `project_commands.<name>.[key]`), and its *Faults* section gets a line for the pipeline reader: the spellings of `all_faults`, all faults joined by `; ` in the order unknown key, missing key, invalid value; `docs/decisions.md` records that the schema forbids unknown keys.

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
    print('missing key: contract' in error.fault, 'unknown key: contrakt' in error.fault)
"
```
Expect: four lines of output: `tests ['tests', 'doing', 'done'] 2`, then `90 60 40`, then `2 2 ['check', 'lint', 'test']`, then `True True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/errors.py`, `domain/pipeline_definition.py`, `application/files.py`, `adapters/pipeline_yaml.py`, `adapters/validation_faults.py`, `application/boundaries.py`). I checked that `Name`, `validation_faults.first_fault`, `Boundaries` and `PIPELINE_YAML` in `tests/git_support.py` exist. Every behaviour in the Interface comments has a criterion: fault ranking (18, 19), YAML order (1, 5), the `project_commands` replace-not-merge rule (9), and the defaults (6 to 8).
   - Criteria: each is testable by one test function. Every rule has its failing side: positive-int limits at 0 and -1 plus the accepted 1 (13), name pattern (14), wrong types and the unquoted contract (15), missing keys (11), unknown keys (12), invalid YAML and repeated key (16), non-mapping top level (17), unknown `role_of` stage (4).
   - Demo: runnable as written. The `Expect:` line gives four exact output lines.
   - Architecture: the schema is in domain, the reader interface in application, ruamel only in the adapter (criterion 23), and the reader is wired through `Boundaries`. This matches CLAUDE.md.
   - Scope: this is the schema half of ST8.1 and R30. The cross-key rules (S0007), the stop report (S0006) and a writer are excluded, as `FEATURE.md` says.
3. tester: Wrote the tests for the pipeline definition schema, its reader, `all_faults` and the reader interface. `make lint` is green. `make test` is red on purpose: pytest cannot load `tests/conftest.py`, because the `boundaries` fixture now imports `RuamelPipelineDefinitionReader` from `factory.adapters.pipeline_yaml`, which does not exist yet (`ModuleNotFoundError`). Until the coder builds the module, every test errors at collection.

   Criterion → test:
   - criterion 1: tests/adapters/test_pipeline_yaml.py::test_example_definition_is_read_in_its_order
   - criterion 2: tests/adapters/test_pipeline_yaml.py::test_first_stage_is_the_first_stage_of_the_text
   - criterion 3: tests/adapters/test_pipeline_yaml.py::test_role_of_a_stage_is_its_role_or_none
   - criterion 4: tests/adapters/test_pipeline_yaml.py::test_role_of_an_unknown_stage_raises_key_error
   - criterion 5: tests/adapters/test_pipeline_yaml.py::test_position_is_the_index_in_the_stages (intake 0, tests 1, done 8)
   - criterion 6: tests/adapters/test_pipeline_yaml.py::test_left_out_keys_with_defaults_take_them
   - criterion 7: tests/adapters/test_pipeline_yaml.py::test_an_empty_stage_takes_every_default
   - criterion 8: tests/adapters/test_pipeline_yaml.py::test_left_out_project_commands_are_check_lint_and_test
   - criterion 9: tests/adapters/test_pipeline_yaml.py::test_given_project_commands_replace_the_default_set, ::test_an_empty_project_command_takes_the_default_time_limit
   - criterion 10: tests/adapters/test_pipeline_yaml.py::test_given_values_replace_the_defaults
   - criterion 11: tests/adapters/test_pipeline_yaml.py::test_a_text_without_contract_is_refused, ::test_a_text_without_stages_is_refused, ::test_a_text_without_roles_is_refused, ::test_a_role_without_write_paths_is_refused
   - criterion 12: tests/adapters/test_pipeline_yaml.py::test_an_unknown_key_is_refused_by_its_path (top-level, stage, role)
   - criterion 13: tests/adapters/test_pipeline_yaml.py::test_a_limit_below_one_is_refused (6 paths × 0 and -1), ::test_a_limit_of_one_is_accepted (6 paths, all on the minimal text; the lease case sets the coder's time_limit to 1)
   - criterion 14: tests/adapters/test_pipeline_yaml.py::test_a_name_that_breaks_the_pattern_is_refused_naming_it, ::test_a_well_formed_name_is_accepted_for_stage_role_and_command
   - criterion 15: tests/adapters/test_pipeline_yaml.py::test_a_value_of_the_wrong_type_is_refused_by_its_path
   - criterion 16: tests/adapters/test_pipeline_yaml.py::test_a_text_that_is_not_yaml_is_refused, ::test_a_repeated_key_is_refused_naming_it
   - criterion 17: tests/adapters/test_pipeline_yaml.py::test_a_text_that_is_not_a_mapping_is_refused (list, string, empty)
   - criterion 18: tests/adapters/test_pipeline_yaml.py::test_several_faults_are_refused_once_in_rank_order
   - criterion 19: tests/adapters/test_validation_faults.py::test_all_faults_ranks_unknown_then_missing_then_invalid
   - criterion 20: tests/domain/test_pipeline_definition.py::test_pipeline_definition_invalid_carries_its_fault_as_message
   - criterion 21: tests/domain/test_pipeline_definition.py::test_write_path_placeholders_are_spelled_in_braces
   - criterion 22: tests/application/test_pipeline_definition_reader.py::test_pipeline_definition_reader_is_abstract_with_parse_alone, ::test_pipeline_definition_reader_parse_body_is_its_docstring_alone, ::test_ruamel_reader_implements_the_pipeline_definition_reader
   - criterion 23: the existing tests/adapters/test_work_item_markdown.py::test_only_the_work_item_adapter_imports_frontmatter_and_ruamel, unchanged
   - criteria 24 and 25: `make check` and the docs belong to the coder and the documenter, so they have no tests here.

   Extra tests drawn from the Interface's own rules, not from any criterion:
   - tests/adapters/test_validation_faults.py::test_all_faults_keeps_pydantic_order_within_one_rank checks that faults of one rank stay in pydantic's order.
   - tests/adapters/test_pipeline_yaml.py::test_a_name_value_that_breaks_the_pattern_is_refused tests the refused side of the `Name`-typed values `role`, `next[0]` and `acceptance_stage`. CLAUDE.md wants both sides of every limit the Interface states; criterion 1 covers the accepted side.
   - tests/adapters/test_pipeline_yaml.py::test_a_python_tag_is_refused_as_a_pipeline_definition_fault checks that a text using a Python tag raises `PipelineDefinitionInvalid` and nothing else, because the Interface says safe mode and that this is the only exception. It does not check the fault's wording.
   - tests/application/test_pipeline_definition_reader.py::test_boundaries_hand_out_the_ruamel_pipeline_reader checks the new `Boundaries.pipeline_reader` field.

   Files:
   - created: tests/domain/test_pipeline_definition.py, tests/adapters/test_pipeline_yaml.py, tests/adapters/test_validation_faults.py, tests/application/test_pipeline_definition_reader.py
   - changed: tests/conftest.py. The `boundaries` fixture passes `pipeline_reader=RuamelPipelineDefinitionReader()`, as the Interface says for `boundaries.py`.

   Modules and names the tests need that do not exist yet: `factory.adapters.pipeline_yaml`, `factory.domain.pipeline_definition`, `factory.domain.errors.PipelineDefinitionInvalid`, `factory.application.files.PipelineDefinitionReader`, `factory.adapters.validation_faults.all_faults` and the `Boundaries.pipeline_reader` field. Nothing in the criteria needed interpreting, so there is no open question.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.adapters.pipeline_yaml'
