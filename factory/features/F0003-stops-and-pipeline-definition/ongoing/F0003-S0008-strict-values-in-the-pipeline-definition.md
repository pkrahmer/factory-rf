---
stage: accept
pr: 49
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
2. intake: accepted
   - Interface: names the concrete module `src/factory/domain/pipeline_definition.py`, the four models that become strict, and the `WritePath` type (a str with at least one non-whitespace character). It names the test files and the S0006 fixtures to reuse.
   - Criteria: each is testable by one function or one parametrized table. Criterion 2 gives the refused values (`true`, `'30'`, `30.0`) and the accepted integer for each of the six paths. Criterion 3 gives refused and accepted `approval` values. Criterion 4 gives the blank write path and the accepted ones. Criterion 5 keeps text fields string-only. Criterion 6 gives the ordering against the rules. Criterion 7 covers the load. Every rule has its failing side and its passing side.
   - Demo: runnable as written. The `Expect:` line is checkable: five lines, no `accepted`.
   - Architecture: the change stays in `factory.domain`, pure Pydantic models, and the reader and loader are only exercised. This fits the layer rules in `CLAUDE.md`.
   - Scope: it is inside F0003's scope (the schema, the validation, and the stop `pipeline_definition_invalid`). The multi-line YAML fault is excluded, as FEATURE.md decision 20 says. It does not touch "Out of scope".
3. tester: wrote red tests for criteria 1–7. Every case is built from `PIPELINE_YAML` by text replacement, as the Interface asks. No existing test was changed.
   - criterion 1: tests/adapters/test_pipeline_strict_values.py::test_the_test_pipeline_definition_still_parses
   - criterion 2 (refused side, 6 paths × `true`, `'30'`, `30.0`): tests/adapters/test_pipeline_strict_values.py::test_an_integer_limit_not_written_as_an_integer_is_refused
   - criterion 2 (accepted side: 50 for lease_duration, 10 for lint.time_limit, 30 for the rest): tests/adapters/test_pipeline_strict_values.py::test_an_integer_limit_written_as_an_integer_is_accepted
   - criterion 3: tests/adapters/test_pipeline_strict_values.py::test_an_approval_not_written_as_a_boolean_is_refused (`'yes'`, `'off'`, `1`, `0`), ::test_an_approval_written_as_true_is_accepted, ::test_an_approval_written_as_false_is_accepted (on the stage `doing`)
   - criterion 4: tests/adapters/test_pipeline_strict_values.py::test_a_blank_write_path_is_refused_at_its_position (`''`, `'  '`), ::test_a_write_path_with_text_is_accepted (`'src/*'`, `'{work_item}'`)
   - criterion 5: tests/adapters/test_pipeline_strict_values.py::test_a_number_in_a_text_list_is_refused (checks[0] on `doing`, reports[0] on `tests`)
   - criterion 6: tests/adapters/test_pipeline_strict_values.py::test_a_strict_value_fault_comes_alone_before_a_fault_of_the_rules (`time_limit: true` together with `next: [review, ship]`; the fault starts with `invalid roles.coder.time_limit:` and does not contain `ship`)
   - criterion 7: tests/application/test_pipeline_loading_strict_values.py::test_a_time_limit_written_as_a_boolean_is_one_reported_stop (uses the fixtures `boundaries`, `agent_home`, `human` and `checkout`, plus `install_agents`)

   Files created: tests/adapters/test_pipeline_strict_values.py and tests/application/test_pipeline_loading_strict_values.py.

   Every module imports, because the reader and the loader already exist. The tests fail on wrong results: lax mode still accepts these values, so no fault is raised where the tests expect one. One `make test` run showed failures in the refused-side tests, for example the blank write path, the fault-order test and the load stop. All accepted-side tests are expected to pass. `make lint` is green. I did not run the type check, as the stage skill says. No criterion needed interpreting.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_pipeline_loading_strict_values.py::test_a_time_limit_written_as_a_boolean_is_one_reported_stop
4. coder: all four models of the pipeline definition now validate in strict mode, and write paths must not be blank. Commit 91c7101.
      - Built: in `src/factory/domain/pipeline_definition.py`, `RoleDefinition`, `StageDefinition`, `ProjectCommandDefinition` and `PipelineDefinition` set `strict=True` in their `model_config`. A new `WritePath = Annotated[str, StringConstraints(pattern=r"\S")]` types `RoleDefinition.write_paths`. The reader and the loader did not change. Faults keep S0004's spelling `invalid <path>: <pydantic message>`, and pydantic's field errors still come before the `model_validator` rules of S0007.
      - Main decision: I used pydantic's own strict mode and a pattern constraint rather than custom validators. With strict mode pydantic refuses `true`, `'30'` and `30.0` for integers, and `'yes'`, `1` and `0` for booleans. Ruamel's `CommentedMap` and `CommentedSeq` still pass in strict mode, so `PIPELINE_YAML` and the texts from S0004 and S0007 still parse. Rejected: an `AfterValidator` with a message of our own for blank paths ("must not be blank"). It reads better than `String should match pattern '\S'`, but the Interface asks for pydantic's message. That message is a little cryptic for an operator, and the reviewer may want to weigh that.
      - Demo: run as written. It prints `30`, then `invalid roles.coder.time_limit` twice, then `invalid stages.gate.approval`, then `invalid roles.coder.write_paths[0]`. No line says `accepted`.
      - Refactor: I read the diff (one file, 18 lines) and found nothing to change, so there is no refactor commit.
      - `make check`: green (lint, types, layers, sast, secrets, licenses, and tests with 99.72 % coverage).
      - Not touched: the docs criterion (project guide and decision log) belongs to the documenter.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–7 has a test in `tests/adapters/test_pipeline_strict_values.py` or `tests/application/test_pipeline_loading_strict_values.py`, and each test checks what its criterion says.
        - Criterion 2 runs all six paths with `true`, `'30'` and `30.0`, and also checks the accepted integer for each path: 50 for `lease_duration`, 10 for `lint.time_limit`, 30 for the rest.
        - Criterion 3 covers `'yes'`, `'off'`, `1` and `0`, plus `true` on the stage `approval` and `false` on the stage `doing`.
        - Criterion 4 covers `''` and `'  '`, plus `'src/*'` and `'{work_item}'`.
        - Criterion 6 checks that the fault starts with the field path and does not contain `ship`.
        - Criterion 7 pushes the file to `main` through `HumanClone`, fetches, then checks that `load` raises and that exactly one `pipeline_definition_invalid` stop exists, with the right detail.
        - Every Interface rule has a test for both the refused and the accepted side. Every case is built from `PIPELINE_YAML` by text replacement, and `_changed` asserts that each replaced line appears exactly once. No existing test changed. The coder's entry says the factory's `make check` was green.
      - Architecture: the change touches only `src/factory/domain/pipeline_definition.py`, which is pure Pydantic with no I/O. It adds `strict=True` on the four models, plus `WritePath = Annotated[str, StringConstraints(pattern=r"\S")]`, built the same way as `Name` in `identifiers.py`. The reader and the loader are unchanged.
      - Security: no markers or secrets, and nothing builds a string into a command or query.
      - Quality: the diff is small and has no dead code. It uses pydantic's built-in strict mode instead of custom validators. The comment on `WritePath` says in words what the regex `\S` means. It is also the only description of a public alias, so I accept it.
      - Ticket hygiene: the coder's entry gives the main decision (pydantic strict mode plus a pattern constraint) and the rejected alternative (an `AfterValidator` with the factory's own "must not be blank" message, rejected because the Interface asks for pydantic's message). `Assignment` matches what was built. Criterion 9 still says what the documenter must write.
      - Open for the human, not a finding: a blank write path is refused with pydantic's message `String should match pattern '\S'`. The Interface asks for that message, but an operator may find it hard to read. A clearer message would need a new story.
6. documenter: wrote the docs criterion and cross-read the rest; no findings.
   - docs/project-guide.md, "The pipeline definition": a new first bullet says values are taken only in their YAML type (limits are integers, `approval` is `true` or `false`, text fields are strings) and that a write path must not be blank. It gives the refused examples and the fault position, `roles.<role>.write_paths[<n>]`, and says the message is pydantic's `String should match pattern '\S'`.
   - docs/decisions.md: new entry "The pipeline definition validates in strict mode". It gives the reason (decision "forbids unknown keys": no setting the project did not choose) and the rejected alternative (lax mode with a warning, which nothing would show the operator).
   - Cross-read and found current: README.md, docs/operator-guide.md (stop `pipeline_definition_invalid`), and the "Faults" and "The rules of the definition" sections of the project guide. The field-faults-first order is unchanged.
   - Code and docstrings agree with the Interface.
   - Not touched: nothing stale seen.
   - I did not run the demo; the coder and the reviewer did, and the code has not changed since. `make check` is green.

   `make check`: check: green
7. demo: ran the one command under `## Demo` exactly as written, from the repository root. No findings.

   Command 1 (the `uv run python -c …` script that parses the sample definition, then the four changed texts, through `RuamelPipelineDefinitionReader`). It exited with 0.

   ```
   30
   invalid roles.coder.time_limit
   invalid roles.coder.time_limit
   invalid stages.gate.approval
   invalid roles.coder.write_paths[0]
   ```

   Expect: met. The output has five lines, in the expected order: `30`, then `invalid roles.coder.time_limit` twice (for `true` and `'30'`), then `invalid stages.gate.approval` (for `'yes'`), then `invalid roles.coder.write_paths[0]` (for `''`). No line says `accepted`.

   Criteria cross-check: the output agrees with criterion 2 (an integer is accepted, and `true` and `'30'` are refused at the field's path), criterion 3 (`true` is accepted, `'yes'` is refused at `stages.<stage>.approval`) and criterion 4 (a blank write path is refused at its list position). The demo contradicts no other criterion. Criteria 5–7 were not exercised here; their tests are listed in the tester's and reviewer's entries.
