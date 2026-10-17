---
stage: doing
pr: 158
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The fault of an unreadable pipeline definition on one line

<!-- takes in the parked draft F0003-S0011 (proposed by F0003's feature acceptance of 2026-10-14) -->

## Assignment (as of log entry 1)

When `factory/pipeline.yml` on `main` is not valid YAML, the stop `pipeline_definition_invalid` carries ruamel.yaml's own error text as its detail, and that text spans four to seven lines. `TimestampedFactoryLog` stamps each line, so the factory log gets one `stop repository pipeline_definition_invalid: not valid YAML: while constructing a mapping` line followed by several stamped lines without the `stop` prefix: `in "<unicode string>", line 5, column 3`, the actual problem (`found duplicate key "done" ...`), an empty line, and for a repeated key, ruamel's hint `To suppress this check see: https://yaml.dev/...`. An operator who greps the log for `stop repository` sees only the context line and misses the problem. The hint is also wrong advice, because the factory refuses a repeated key on purpose (F0003 decision 11). This story makes the fault one line: ruamel's problem and its 1-based position, with no context lines and no hint. The fault is the same in the health status, the log and `PipelineDefinitionInvalid`. This keeps F0003's kept thing 7 and its Goal's "a reported stop that names the fault". F0003's first acceptance found the issue (4.1). F0003's FEATURE.md decision 20 kept it out of F0003-S0008, and no story took it up, so F0003's second acceptance proposed it; the human folded it into this feature (FEATURE decision 5).

## Interface

`src/factory/adapters/pipeline_yaml.py`, `RuamelPipelineDefinitionReader.parse` (changes S0004's YAML fault only)

A new public function in the same module states the rule, and `parse` uses it:

```python
def yaml_fault(error: YAMLError) -> str:
    """The one-line fault of ruamel.yaml's `error`: its problem and 1-based position."""
```

When ruamel.yaml's safe loader raises a `YAMLError`, `parse` raises `PipelineDefinitionInvalid(yaml_fault(error))`. `yaml_fault` gives:

- `not valid YAML: <problem> (line <l>, column <c>)` when the error is a `ruamel.yaml.error.MarkedYAMLError` with a non-empty `problem` and a `problem_mark`. `<l>` is `problem_mark.line + 1` and `<c>` is `problem_mark.column + 1`.
- `not valid YAML: <problem>` when it is a `MarkedYAMLError` with a non-empty `problem` but no `problem_mark`.
- otherwise `not valid YAML: <the first non-blank line of str(error), stripped>`.

Rules:

- The fault never contains a line break (`\n` or `\r`).
- `context`, `context_mark`, `note` and ruamel's warning text (`To suppress this check see: ...`) are not part of the fault.
- Every other fault of `parse` (a text that is not a mapping, the field faults, the rules) is unchanged.

Tests: a new file `tests/adapters/test_pipeline_yaml_one_line_fault.py`, through `RuamelPipelineDefinitionReader`, with the texts built from `PIPELINE_YAML` in `tests/git_support.py` (26 lines). Criterion 8 calls `yaml_fault` directly. One case in a new file `tests/application/test_pipeline_loading_yaml_fault.py`, with the fixtures of `tests/conftest.py` that F0003-S0006's tests use (`boundaries`, `human`, `checkout`, `agent_home`) and `install_agents` of `tests/git_support.py`. The existing tests `test_a_text_that_is_not_yaml_is_refused` and `test_a_repeated_key_is_refused_naming_it` still pass unchanged, and no existing test changes.

## Acceptance criteria

1. `PIPELINE_YAML + "  done: {}\n"` (a repeated stage key) is refused with exactly the fault `not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 27, column 3)`.
2. `PIPELINE_YAML + "x: [\n"` (an unclosed list) is refused with exactly the fault `not valid YAML: did not find expected node content (line 28, column 1)`.
3. `PIPELINE_YAML` with `crash_cap: 2` replaced by `crash_cap: 2: 3` is refused with exactly the fault `not valid YAML: mapping values are not allowed in this context (line 3, column 13)`.
4. A Python tag, `PIPELINE_YAML + "x: !!python/object/apply:os.getcwd []\n"`, is refused with a fault that starts with `not valid YAML: could not determine a constructor for the tag` and ends with `(line 27, column 4)`.
5. A text that holds a control character, `PIPELINE_YAML + 'x: "\x07"\n'`, which ruamel refuses without a `problem`, is refused with exactly the fault `not valid YAML: unacceptable character #x0007: control characters are not allowed`.
6. For each text of criteria 1 to 5, the fault contains no `\n` and no `\r`. For the text of criterion 1, the fault does not contain `To suppress` and does not contain `<unicode string>`.
7. `PIPELINE_YAML` itself still parses, and a text that is valid YAML but not a mapping (`"- a\n"`) is still refused with `the pipeline definition must be a mapping`.
8. `yaml_fault(MarkedYAMLError(context="while x", problem="found y"))` is `not valid YAML: found y`; `yaml_fault(MarkedYAMLError(context="while x", problem="", problem_mark=FileMark("<s>", 0, 4, 2)))` is `not valid YAML: while x` (an empty problem falls to the first line of the text); `yaml_fault(YAMLError("plain\nsecond"))` is `not valid YAML: plain`. Rows of one parametrized test, the errors built by hand (`ruamel.yaml.error`).
9. Loaded through `PipelineLoader.load` at `origin/main`, the text of criterion 1 is one reported stop. `load` raises `PipelineDefinitionInvalid`. The health status holds one stop `pipeline_definition_invalid` whose `detail` is the fault of criterion 1. The factory log file gains exactly one line, and that line ends with `stop repository pipeline_definition_invalid: ` followed by that fault.
10. `make check` stays green.
11. docs: `docs/project-guide.md`, "Faults" under "The pipeline definition", gives the YAML fault as `not valid YAML: <problem> (line <l>, column <c>)`, on one line and 1-based, and no longer says that ruamel's text can span several lines. `docs/operator-guide.md`'s row for faults of the text in "The stop `pipeline_definition_invalid`" shows the same form with an example (the repeated key). `docs/decisions.md` records that the YAML fault is reduced to ruamel's problem and position: one stop, one log line, and no suppression hint for a check the factory wants.

## Demo

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
stages:
  doing: {role: coder, next: [done]}
  done: {}
'''
for broken in [TEXT + '  done: {}\n', TEXT.replace('next: [done]', 'next: [done')]:
    try:
        RuamelPipelineDefinitionReader().parse(broken)
        print('accepted')
    except PipelineDefinitionInvalid as error:
        print(error.fault)
"
```
Expect: exactly two lines and no `accepted`: `not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 7, column 3)` and `not valid YAML: did not find expected ',' or ']' (line 5, column 35)`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names `src/factory/adapters/pipeline_yaml.py`, `RuamelPipelineDefinitionReader.parse` and the new `yaml_fault(error: YAMLError) -> str`, with its three branches (problem and mark, problem without mark, first non-blank line), the no-line-break rule and what is excluded. The test files and their fixtures are named.
   - Criteria: each is testable by one test function. 1 to 5 give exact faults for the five kinds of YAML error (4 pins start and end). 6 covers the no-line-break and no-hint rules. 7 covers the unchanged side, with PIPELINE_YAML still parsing and a non-mapping still refused. 8 covers all three `yaml_fault` branches with hand-built errors, including the empty-problem fallback. 9 covers the single stop, status detail and log line through `PipelineLoader.load`. 10 and 11 are the closing `make check` and docs criteria. Every rule the Interface states has a criterion, and the refused-input side is the subject of the story.
   - Demo: runnable with `uv run python -c`, two broken texts. The Expect line gives the exact two output lines and the absence of `accepted`.
   - Architecture: the change sits in the adapters layer, in the module that already wraps ruamel.yaml. The error type is the domain's `PipelineDefinitionInvalid`, and no layer import is added.
   - Scope: within F0012's item 1.2, which takes in the parked draft F0003-S0011 (FEATURE.md's parked-drafts table). Nothing in Out of scope is touched.
3. tester: Wrote the red tests for the one-line YAML fault. First I checked ruamel's real errors for the five texts built from PIPELINE_YAML. Each problem and 0-based mark gives exactly the fault the criteria state. The control character raises a ReaderError with no `problem`.

   Criterion → test:
   - criterion 1: tests/adapters/test_pipeline_yaml_one_line_fault.py::test_a_yaml_error_is_refused_with_its_problem_and_position[repeated-key]
   - criterion 2: same test, [unclosed-list]
   - criterion 3: same test, [mapping-in-a-value]
   - criterion 4: tests/adapters/test_pipeline_yaml_one_line_fault.py::test_a_python_tag_is_refused_with_its_problem_and_position
   - criterion 5: test_a_yaml_error_is_refused_with_its_problem_and_position[control-character]
   - criterion 6: tests/adapters/test_pipeline_yaml_one_line_fault.py::test_a_yaml_fault_holds_no_line_break (all five texts) and ::test_a_repeated_key_fault_holds_no_hint_and_no_context
   - criterion 7: tests/adapters/test_pipeline_yaml_one_line_fault.py::test_the_example_definition_still_parses and ::test_a_yaml_text_that_is_not_a_mapping_is_still_refused_as_such
   - criterion 8: tests/adapters/test_pipeline_yaml_one_line_fault.py::test_yaml_fault_falls_back_to_the_first_line_of_the_text (rows: problem-without-mark, empty-problem, plain-error)
   - criterion 9: tests/application/test_pipeline_loading_yaml_fault.py::test_a_repeated_key_on_main_is_one_stop_and_one_log_line. It checks the raised fault, that the health status holds exactly one stop with that detail, and that the log gains exactly one line ending with `stop repository pipeline_definition_invalid: <fault>`.

   Files created: tests/adapters/test_pipeline_yaml_one_line_fault.py, tests/application/test_pipeline_loading_yaml_fault.py. No existing test changed.

   Result of `make test`: the adapter module fails to collect with an ImportError, because `yaml_fault` is not yet in `factory.adapters.pipeline_yaml`. The application test fails because `parse` still gives ruamel's multi-line text as the fault. `make lint` is green. I skipped the type check, as the stage says.

   No interpretation was needed. Every exact fault in the criteria matches what ruamel actually reports.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/adapters/test_pipeline_yaml_one_line_fault.py - ImportError while...
