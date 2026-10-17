---
stage: accept
pr: 158
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# The fault of an unreadable pipeline definition on one line

<!-- takes in the parked draft F0003-S0011 (proposed by F0003's feature acceptance of 2026-10-14) -->

## Assignment (as of log entry 7)

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
- A line break inside ruamel's `problem` is written as the two characters `\n` or `\r` (a backslash followed by `n` or `r`).
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
10. `"a: 1\na: |\n  x\n  y\n"` (a repeated key whose value is a block scalar) is refused with exactly the fault `not valid YAML: found duplicate key "a" with value "x\\ny\\n" (original value: "1") (line 2, column 1)`, where each `\\n` is a backslash followed by `n`, and the fault contains no `\n` and no `\r`.
11. `make check` stays green.
12. docs: `docs/project-guide.md`, "Faults" under "The pipeline definition", gives the YAML fault as `not valid YAML: <problem> (line <l>, column <c>)`, on one line and 1-based, and no longer says that ruamel's text can span several lines. `docs/operator-guide.md`'s row for faults of the text in "The stop `pipeline_definition_invalid`" shows the same form with an example (the repeated key). `docs/decisions.md` records that the YAML fault is reduced to ruamel's problem and position: one stop, one log line, and no suppression hint for a check the factory wants.

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
4. coder: Made the YAML fault of the pipeline definition fit on one line (commit 4a502d2).

      Built, in `src/factory/adapters/pipeline_yaml.py`:
      - the public `yaml_fault(error: YAMLError) -> str`. If the error is a `MarkedYAMLError` with a non-empty `problem`, the fault is that problem plus `problem_mark` made 1-based as `(line l, column c)`. If there is no mark, it is the problem alone.
      - Any other error falls back to the first non-blank line of `str(error)`, stripped, through a private `_first_line`. This covers ruamel's `ReaderError` for control characters and the case where the problem is empty.
      - `RuamelPipelineDefinitionReader.parse` now raises `PipelineDefinitionInvalid(yaml_fault(error))`. No other fault of `parse` changed.

      Main decision: the fault is built from ruamel's structured attributes (`problem`, `problem_mark`). I rejected cutting up `str(error)` in every case: that text puts context first and adds the "To suppress" hint, so the problem's line would differ from error to error. The string is used only when no `problem` exists, as the Interface says.

      Refactor: I re-read the diff (one function, one helper, two changed lines). Nothing needed changing, so there is no refactor commit.

      Checks:
      - `make check` passed: lint, types, layers, sast, secrets, licenses and test all green.
      - The Demo prints exactly the two expected lines.

      Noticed but not touched: if a ruamel `problem` itself held a line break, it would pass through. No ruamel problem text does that today, and no test asks for it.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: Findings (group 1, acceptance criteria and the Interface's rules):

   1. `src/factory/adapters/pipeline_yaml.py`, `yaml_fault`, the two `error.problem` branches: these break the Interface rule "The fault never contains a line break". ruamel's duplicate-key problem includes the values (`with value "{value}" (original value: "{mk}")`, `ruamel/yaml/constructor.py:266`). So if a repeated key has a multi-line string value, the line break ends up in the fault. I fed the reader `a: 1\na: |\n  x\n  y\n` and the fault was `not valid YAML: found duplicate key "a" with value "x\ny\n" (original value: "1") (line 2, column 1)`, which is several log lines again. The coder's entry says "No ruamel problem text does that today", and that is wrong. Fix: put the problem on one line before using it, e.g. replace each `\n`/`\r` with an escaped `\n` or collapse the whitespace. The Interface doesn't say which form to use; if you don't want to pick one, end with `question`.
   2. Story gap for the human: the rule "The fault never contains a line break" has no criterion for its failing side, a `problem` that itself holds a line break. Criterion 6 only checks the five texts, and none of their problems contain a line break. A criterion is needed (e.g. a repeated key with a block-scalar value gives a fault with no `\n`/`\r`, in a stated form), and so is the tester's row for it. That's a test change, so it goes through the human's answer and `tests` (R9).
6. coder: coder (round 1): I fixed review finding 1 and need the human's decision on finding 2.

   Finding 1, fixed in commit ee70afa (`src/factory/adapters/pipeline_yaml.py`):
   - `yaml_fault` now passes ruamel's `problem` through a private `_escaped_line_breaks`, which writes each `\r` and `\n` as a literal backslash escape. The fault stays on one line even when a duplicate-key problem quotes a block-scalar value.
   - The reviewer's input `a: 1\na: |\n  x\n  y\n` now gives the one-line fault `not valid YAML: found duplicate key "a" with value "x\ny\n" (original value: "1") (line 2, column 1)`, with `\n` as two characters.
   - The faults of criteria 1 to 5 are unchanged, because none of those problems holds a line break.
   - `make check` passed (check: green).
   - Alternative I rejected: collapsing whitespace into single spaces. It loses where the value broke, and it would make different values read the same.
   - The fallback branch (`_first_line`) already returns a single line, so I did not change it.

   Question (finding 2): the Interface says "The fault never contains a line break", but no criterion tests the case where ruamel's `problem` itself holds a line break. Adding one is a test change, so it needs your answer (R9). Options:
   - (a) Add a criterion: `"a: 1\na: |\n  x\n  y\n"` is refused with exactly the fault `not valid YAML: found duplicate key "a" with value "x\\ny\\n" (original value: "1") (line 2, column 1)`, where each `\\n` is a backslash followed by `n`. Also add a sentence to the Interface: a line break inside the problem is written as `\n` / `\r`. The tester adds one row to `test_a_yaml_error_is_refused_with_its_problem_and_position`, plus that text in `test_a_yaml_fault_holds_no_line_break`.
   - (b) The same criterion, but asserting only that the fault has no `\n` and no `\r`, without pinning the form.
   - (c) No new criterion: the fix stays and remains untested.

   I recommend (a): it pins the escaped form the code now produces. If you choose (a) or (b), I will end the next round with `tests` so the tester adds the row.
7. human (pull request comment, 2026-10-17): (a). Add the criterion with the exact escaped fault for `"a: 1\na: |\n  x\n  y\n"`, the Interface sentence (a line break inside the problem is written as the two characters `\n` or `\r`), and the tester's row in `test_a_yaml_error_is_refused_with_its_problem_and_position` plus that text in `test_a_yaml_fault_holds_no_line_break`.
8. coder: coder (round 1): The human chose (a) in entry 7, so this round hands the ticket to the tester for a test change. No code changed. The escaping fix is already in commit ee70afa.

   The ticket now reflects the answer:
   - Assignment heading: "as of log entry 7".
   - Interface rule added: a line break inside ruamel's `problem` is written as the two characters `\n` or `\r`.
   - New criterion 10: `"a: 1\na: |\n  x\n  y\n"` is refused with exactly the fault `not valid YAML: found duplicate key "a" with value "x\\ny\\n" (original value: "1") (line 2, column 1)`, where each `\\n` is a backslash and `n`, and the fault has no `\n` and no `\r`.
   - The closing criteria are renumbered to 11 (`make check`) and 12 (docs).

   Test change for the tester:
   - In `tests/adapters/test_pipeline_yaml_one_line_fault.py`, add a row for that text and fault to `test_a_yaml_error_is_refused_with_its_problem_and_position`.
   - Add the same text to the texts of `test_a_yaml_fault_holds_no_line_break`.
9. tester: tester (test change approved by the human in entry 7, named by the coder in entry 8): I made exactly the named change in `tests/adapters/test_pipeline_yaml_one_line_fault.py`. Nothing else changed.
   - Added a module constant `BLOCK_SCALAR_REPEATED_KEY = "a: 1\na: |\n  x\n  y\n"`.
   - criterion 10: `test_a_yaml_error_is_refused_with_its_problem_and_position[block-scalar-repeated-key]` is a new row. It expects exactly `not valid YAML: found duplicate key "a" with value "x\\ny\\n" (original value: "1") (line 2, column 1)`, where each escaped `\n` is two characters.
   - criterion 10 (no line break): `test_a_yaml_fault_holds_no_line_break[block-scalar-repeated-key]`, the same text added to that test's rows.
   - Line-length limits made me split both `ids` lists over several lines. The ids are the same.

   Why: the Interface rule (a line break inside ruamel's `problem` is written as `\n` / `\r`) had no test for a problem that actually holds a line break.

   `make test` is green: test: green (25.0 s), coverage 99.51 %. The new rows pass because the coder's escaping fix (ee70afa) is already on the branch. `make lint` is green.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (24.5 s)
10. coder: coder (round 1): The tester's new rows for criterion 10 (entry 9) pass against the code already on the branch. This round needed no code change and has no new commit.
    - Built, in earlier rounds, in `src/factory/adapters/pipeline_yaml.py`:
      - `yaml_fault` (4a502d2): ruamel's `problem` plus the 1-based `problem_mark`, or the problem alone when there is no mark; otherwise the first non-blank line of `str(error)` through `_first_line`.
      - the escaping of `\n`/`\r` inside the problem through `_escaped_line_breaks` (ee70afa), which fixes review finding 1.
      - `RuamelPipelineDefinitionReader.parse` raises `PipelineDefinitionInvalid(yaml_fault(error))`.
    - Main decision: build the fault from ruamel's structured attributes instead of cutting up `str(error)`, and escape line breaks inside the problem instead of collapsing whitespace. Collapsing would lose where a value broke, and different values would read the same.
    - Review finding 2 is settled by the human's answer (a) in entry 7: criterion 10 is in the ticket and the tester added its rows in entry 9.
    - Refactor: I re-read `git diff main...HEAD -- src`. It is one public function and two small private helpers, with nothing unclear or duplicated, so there is no refactor commit.
    - Noticed, not touched: nothing.

    `make check`: check: green (test: green (24.4 s), coverage 99.51 %)

    `make check`: check: green
    `make duplicates`: duplicates: 0 new, 39 known, 0 gone
11. reviewer: reviewer (round 1): no findings.

    - Scope: `git diff main...HEAD -- . ':!factory'`. The changes to `tests/process_support.py`, `tests/adapters/test_process.py` and `tests/adapters/test_make_commands.py` come from the human's commit a637bc3 on origin/main, which reached this branch through the merge 17d5cc5. They are not this ticket's work and I did not review them as such. The ticket's own diff is `src/factory/adapters/pipeline_yaml.py` and the two new test files.
    - Acceptance criteria. Criteria 1–3, 5 and 10 are exact-fault rows of `test_a_yaml_error_is_refused_with_its_problem_and_position`. Criterion 4 pins the start and the end of the fault. Criterion 6 has a no-line-break row for each of the five texts plus criterion 10's text, and a test that the repeated-key fault has no hint and no context. Criterion 7 covers the definition that still parses and the refused non-mapping. Criterion 8 has three hand-built rows for the branches: problem without a mark, an empty problem falling back to the text, and a plain error with two lines. Criterion 9 goes through `PipelineLoader.load` and checks the raised fault, the single health stop and its detail, and exactly one added log line with its ending. The failing sides of the Interface's rules are tested: a problem that holds a line break (criterion 10, the human's answer in entry 7), context excluded (criterion 8's `context="while x"` row and criterion 6), and the +1 shift of both positions through exact line and column values. The coder's entry 10 reports `make check` green.
    - Architecture: the change stays in the adapter that already wraps ruamel.yaml, it raises the domain's `PipelineDefinitionInvalid`, it adds no layer import, and it is fully typed.
    - Security: no strings built into commands and no suppression markers. The fault carries ruamel's problem text and position, not a traceback.
    - Quality: `yaml_fault` has its docstring, and the comments explain why (the factory keeps the duplicate-key check; a block scalar brings line breaks). I looked for an existing helper in `src/factory` and found none that does what `_first_line` or `_escaped_line_breaks` does. `make duplicates` reports 0 new.
    - Ticket hygiene: the log explains the main decision (build the fault from ruamel's structured `problem`/`problem_mark` and escape line breaks) and what was rejected (cutting up `str(error)`, collapsing whitespace). The Assignment and Interface match the code. The docs criterion (12) names what the project guide, the operator guide and the decision log must say.
    - Considered, not raised:
      - Only `\n` inside a problem is tested, not `\r`. The human fixed the form of the new criterion in entry 7, and `\r` takes the same `replace` path.
      - The criterion 8 test name says "falls back", yet its first row (a problem without a mark) does not fall back. The rows match the criterion exactly.
12. documenter: docs (round 1): wrote the three documents of criterion 12; changed only documents, so I did not run `make check` (the factory does). `make documents`: documents ok.
    - `docs/project-guide.md`, "Faults" under "The pipeline definition": the YAML fault is now `not valid YAML: <problem> (line <l>, column <c>)`, on one line and 1-based. It names `yaml_fault`, the escaping of a line break inside the problem, what is left out (context, the "To suppress" hint), and the fallbacks (no mark, no problem). The sentence that said ruamel's text can span several lines is gone.
    - `docs/operator-guide.md`, the fault row of "The stop `pipeline_definition_invalid`": same form, with the repeated-key example (line 27, column 3).
    - `docs/decisions.md`: new entry on reducing the YAML fault to ruamel's problem and position (one stop, one log line, no hint for a check the factory wants), with the rejected alternatives.
    - Cross-read against the diff and found current: `README.md`, and the rest of the project guide and operator guide (agent-definition and work-item YAML faults are a different reader, unchanged). I found no findings for the coder: the code matches the Interface (criteria 1 to 10 are covered by tests, per the reviewer).
    - Stale but untouched: nothing.

    `make check`: check: green
    `make documents`: documents ok
13. demo: demo (round 1): ran the one Demo command from the repository root, exactly as written. No findings.

    Command 1 (`uv run python -c "..."`, which parses two broken pipeline definitions with `RuamelPipelineDefinitionReader`):
    ```
    not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 7, column 3)
    not valid YAML: did not find expected ',' or ']' (line 5, column 35)
    ```
    Exit status 0. This meets its `Expect:` line: exactly two lines, both identical to the expected faults, and no `accepted`.

    Checked against the acceptance criteria: each fault is one line with ruamel's problem and its 1-based position. Neither fault has context lines, `<unicode string>` or the `To suppress` hint. Both start with `not valid YAML: `, as the Interface's first branch says. Nothing in the demo contradicts any criterion. The criteria the demo does not exercise (the health status and log line, the fallback branches, block-scalar escaping) are covered by the tests the reviewer listed in entry 11.
