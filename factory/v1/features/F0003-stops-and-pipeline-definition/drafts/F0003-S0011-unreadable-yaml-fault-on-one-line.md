# The fault of an unreadable pipeline definition on one line

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

When `factory/pipeline.yml` on `main` is not valid YAML, the stop `pipeline_definition_invalid` carries ruamel.yaml's own error text as its detail, and that text spans four to seven lines. `TimestampedFactoryLog` stamps each line, so the factory log gets one `stop repository pipeline_definition_invalid: not valid YAML: while constructing a mapping` line followed by several stamped lines without the `stop` prefix: `in "<unicode string>", line 5, column 3`, the actual problem (`found duplicate key "done" ...`), an empty line, and for a repeated key, ruamel's hint `To suppress this check see: https://yaml.dev/...`. An operator who greps the log for `stop repository` sees only the context line and misses the problem. The hint is also wrong advice, because the factory refuses a repeated key on purpose (F0003 decision 11). This story makes the fault one line: ruamel's problem and its 1-based position, with no context lines and no hint. The fault is the same in the health status, the log and `PipelineDefinitionInvalid`. This keeps kept thing 7 and the Goal's "a reported stop that names the fault". F0003's first acceptance found the issue (4.1). FEATURE.md decision 20 kept it out of S0008, and no story took it up, so the second acceptance proposes it.

## Interface

`src/factory/adapters/pipeline_yaml.py`, `RuamelPipelineDefinitionReader.parse` (changes S0004's YAML fault only)

When ruamel.yaml's safe loader raises a `YAMLError`, `parse` raises `PipelineDefinitionInvalid(fault)` with:

- `not valid YAML: <problem> (line <l>, column <c>)` when the error is a `ruamel.yaml.error.MarkedYAMLError` with a non-empty `problem` and a `problem_mark`. `<l>` is `problem_mark.line + 1` and `<c>` is `problem_mark.column + 1`.
- `not valid YAML: <problem>` when it has a non-empty `problem` but no `problem_mark`.
- otherwise `not valid YAML: <the first non-blank line of str(error), stripped>`.

Rules:

- The fault never contains a line break (`\n` or `\r`).
- `context`, `context_mark`, `note` and ruamel's warning text (`To suppress this check see: ...`) are not part of the fault.
- Every other fault of `parse` (a text that is not a mapping, the field faults, the rules) is unchanged.

Tests: a new file `tests/adapters/test_pipeline_yaml_one_line_fault.py`, through `RuamelPipelineDefinitionReader`, with the texts built from `PIPELINE_YAML` in `tests/git_support.py` (26 lines). One case in a new file `tests/application/test_pipeline_loading_yaml_fault.py`, with S0006's fixtures (`boundaries`, `human`, `checkout`, `agent_home`, `install_agents`). The existing tests `test_a_text_that_is_not_yaml_is_refused` and `test_a_repeated_key_is_refused_naming_it` still pass unchanged, and no existing test changes.

## Acceptance criteria

1. `PIPELINE_YAML + "  done: {}\n"` (a repeated stage key) is refused with exactly the fault `not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 27, column 3)`.
2. `PIPELINE_YAML + "x: [\n"` (an unclosed list) is refused with exactly the fault `not valid YAML: did not find expected node content (line 28, column 1)`.
3. `PIPELINE_YAML` with `crash_cap: 2` replaced by `crash_cap: 2: 3` is refused with exactly the fault `not valid YAML: mapping values are not allowed in this context (line 3, column 13)`.
4. A Python tag, `PIPELINE_YAML + "x: !!python/object/apply:os.getcwd []\n"`, is refused with a fault that starts with `not valid YAML: could not determine a constructor for the tag` and ends with `(line 27, column 4)`.
5. A text that holds a control character, `PIPELINE_YAML + 'x: "\x07"\n'`, which ruamel refuses without a `problem`, is refused with exactly the fault `not valid YAML: unacceptable character #x0007: control characters are not allowed`.
6. For each text of criteria 1 to 5, the fault contains no `\n` and no `\r`. For the text of criterion 1, the fault does not contain `To suppress` and does not contain `<unicode string>`.
7. `PIPELINE_YAML` itself still parses, and a text that is valid YAML but not a mapping (`"- a\n"`) is still refused with `the pipeline definition must be a mapping`.
8. Loaded through `PipelineLoader.load` at `origin/main`, the text of criterion 1 is one reported stop. `load` raises `PipelineDefinitionInvalid`. The health status holds one stop `pipeline_definition_invalid` whose `detail` is the fault of criterion 1. The factory log file gains exactly one line, and that line ends with `stop repository pipeline_definition_invalid: ` followed by that fault.
9. `make check` stays green.
10. docs: `docs/project-guide.md`, "Faults" under "The pipeline definition", gives the YAML fault as `not valid YAML: <problem> (line <l>, column <c>)`, on one line and 1-based, and no longer says that ruamel's text can span several lines. `docs/operator-guide.md`'s row for faults of the text in "The stop `pipeline_definition_invalid`" shows the same form with an example (the repeated key). `docs/decisions.md` records that the YAML fault is reduced to ruamel's problem and position: one stop, one log line, and no suppression hint for a check the factory wants.

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
        print(repr(error.fault))
"
```
Expect: two lines and no `accepted`. The first is `'not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 7, column 3)'`. The second starts with `'not valid YAML: ` and ends with `(line <l>, column <c>)'`. Neither line contains `\n`.

## Log (append only)

1. 2026-10-14 human: created.
