---
stage: ready
pr: 154
blocked: question
comments_seen: 0
round: 0
attempts: 0
---
# The duplicates report

## Assignment (as of log entry 1)

The reviewer counts a second copy of a helper as a finding, but only where it happens to see one; three feature acceptances found copies that no story owned. This story builds the report the human's `make duplicates` target prints (change H3, after this story): it reads pylint's duplicate-code messages (R0801, as JSON) and vulture's dead-code lines, keys each finding without its line numbers, compares the keys with a baseline of accepted findings, and prints the new findings, the baseline keys no longer found, and one closing line that v1 writes into the coder's entry as a record. The rules are pure functions in `factory.domain.duplicates`; the command `python -m factory.entry.check_duplicates` only reads the files. pylint and vulture are development dependencies (change H2, before this story); this story does not run them: its tests feed it texts in their formats.

## Interface

`src/factory/domain/duplicates.py`:

```python
class DuplicateFinding(BaseModel):
    """A similar block or a piece of dead code: its line-independent key, where it is, what it is."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    where: str
    message: str


class DuplicateReport(BaseModel):
    """The findings not in the baseline, the count of those in it, and baseline keys not found."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    new: list[DuplicateFinding]
    known: NonNegativeInt
    gone: list[str]


def similar_code_findings(pylint_json: str) -> list[DuplicateFinding]: ...
def dead_code_findings(vulture_text: str) -> list[DuplicateFinding]: ...
def read_baseline(text: str) -> list[str]: ...
def compare(findings: Sequence[DuplicateFinding], baseline: Sequence[str]) -> DuplicateReport: ...
def report_lines(report: DuplicateReport) -> list[str]: ...
```

`similar_code_findings`: the text is a JSON array of objects (pylint's `--output-format=json`). Each object whose `symbol` is `"duplicate-code"` is one finding; objects of any other symbol are ignored. Its `message` is lines: the first (`Similar lines in 2 files`), then one line `==<module>:[<start>:<end>]` per module, then the similar code. The finding's:

- `key` is `similar-code <modules>: <first code line>`, the modules sorted and unique, joined by `, `, and the first code line the first non-blank line after the `==` lines, stripped;
- `where` is the `==` lines without their `==`, in the message's order, joined by `, ` (`factory.domain.git:[73:77], factory.domain.stops:[49:53]`);
- `message` is the message's first line.

A text that is not valid JSON, not an array, or holds an element that is not an object or a `duplicate-code` object without a string `message`, raises `ValueError`. An empty array gives no finding.

`dead_code_findings`: every non-blank line must fully match `<path>:<line>: <message> (<n>% confidence)`, optionally with `, <m> line` or `, <m> lines` before the closing parenthesis (vulture's output). The finding's `key` is `dead-code <path>: <message>`, `where` is `<path>:<line>`, `message` is `<message> (<n>% confidence)`. A non-blank line of another form raises `ValueError` naming its 1-based line number. Blank lines are skipped.

`read_baseline`: one key per line, each line stripped; a line whose stripped text is empty or starts with `#` is skipped; the keys keep their order.

`compare`: `new` holds the findings whose key is not in the baseline, in the order given; `known` counts the findings whose key is in it; `gone` holds the baseline keys that no finding has, in the baseline's order. A key found twice counts twice.

`report_lines`: one line `new <key> at <where>: <message>` per new finding, then one line `gone <key>` per gone key, then the last line `duplicates: <n> new, <k> known, <g> gone`.

`src/factory/entry/check_duplicates.py`:

```python
def main(argv: Sequence[str] | None = None) -> int: ...
```

Arguments: the path of pylint's JSON, the path of vulture's text, `--baseline <path>` (required; without it argparse refuses with `SystemExit` code 2) and `--write-baseline`. `main` prints `report_lines` of the comparison, one per line, and returns 0 when nothing is new (gone keys alone return 0) and 1 when something is. With `--write-baseline` it writes the keys of every finding (similar code first, then dead code, each in input order, a key found twice written once) to the baseline path: the first line `# Accepted findings of make duplicates, one key per line.`, then one key per line, every line ending with a newline; it prints `duplicates: baseline of <n> findings written to <path>`, `<n>` the number of keys written, and returns 0. An input file that cannot be read, a pylint or vulture text that cannot be parsed, or a missing baseline without `--write-baseline`, prints `check-duplicates: <reason>` to standard error and returns 2. `argv` `None` reads the process's arguments.

Tests: `tests/domain/test_duplicates.py` (criteria 1 to 9), `tests/entry/test_check_duplicates.py` (criteria 10 to 13), with texts written in the tests in the formats above.

## Acceptance criteria

1. A pylint array with one `duplicate-code` object whose message is `Similar lines in 2 files\n==factory.domain.stops:[49:53]\n==factory.domain.git:[73:77]\n    @field_validator("at")\n    @classmethod` gives one finding with the key `similar-code factory.domain.git, factory.domain.stops: @field_validator("at")`, the where `factory.domain.stops:[49:53], factory.domain.git:[73:77]` and the message `Similar lines in 2 files`.
2. The same message with its line numbers changed gives the same key, and so does the same message with a blank line between the last `==` line and the code; with a different first code line it gives another key. Rows of one parametrized test.
3. A message naming one module twice (`==factory.a:[1:5]` and `==factory.a:[9:13]`, code `x = 1`) gives the key `similar-code factory.a: x = 1`. Objects of another symbol (`unused-import`) give no finding, and `[]` gives none.
4. Each of these pylint texts raises `ValueError`: `not json`, `{}`, `[1]`, `[{"symbol": "duplicate-code"}]` (no message), `[{"symbol": "duplicate-code", "message": 5}]` (a message that is not a string). Five rows of one parametrized test.
5. The vulture line `src/factory/x.py:12: unused function 'helper' (60% confidence)` gives the key `dead-code src/factory/x.py: unused function 'helper'`, the where `src/factory/x.py:12` and the message `unused function 'helper' (60% confidence)`; the same line with `, 3 lines` or with `, 1 line` before the parenthesis gives the same key; a blank line gives nothing. Rows of one parametrized test.
6. A vulture text whose second line is `oops` raises `ValueError` whose message names line 2; a line `src/x.py: unused function 'f' (60% confidence)` (no line number) and a line with leading spaces raise it too. Rows of one parametrized test.
7. `read_baseline("# comment\n\n  similar-code a, b: x  \n  # indented comment\ndead-code p: m\n")` is `["similar-code a, b: x", "dead-code p: m"]`.
8. `compare` of findings with keys `a`, `d`, `b`, `b` (in that order) against the baseline `["e", "b", "c"]` gives `new` with the findings `a` and `d` in that order, `known == 2` and `gone == ["e", "c"]`; against an empty baseline `new` is the four findings in their order and `gone` is empty.
9. `report_lines` of that first report is the `new` line of `a`, the `new` line of `d` (each `new <key> at <where>: <message>`), `gone e`, `gone c` and `duplicates: 2 new, 2 known, 2 gone`, in that order; of a report with nothing new and nothing gone it is exactly `["duplicates: 0 new, <k> known, 0 gone"]`.
10. `main` with a pylint file, a vulture file and a baseline that holds every key prints only the last line and returns 0; with a baseline missing one key it prints that `new` line first and returns 1; with a baseline holding every key and one more, it prints `gone <that key>` and the last line and returns 0. Rows of one parametrized test.
11. `main` with `--write-baseline`, a pylint file of one finding with key `S` and a vulture file of three lines whose keys are `D`, `D` and `E` (the first two on different line numbers), writes exactly `# Accepted findings of make duplicates, one key per line.\nS\nD\nE\n` to the baseline path (missing before the call), prints `duplicates: baseline of 3 findings written to <path>` and returns 0; a second run without the option on the same inputs then returns 0.
12. `main` with a missing input file, with an unparsable pylint file, with an unparsable vulture file, or with a missing baseline and no `--write-baseline`, prints one line starting `check-duplicates: ` to standard error and returns 2. Rows of one parametrized test.
13. `main(None)` with the process's arguments set (monkeypatched `sys.argv`) behaves as `main` with those arguments. `main` without `--baseline` raises `SystemExit` with code 2 (argparse's refusal), with or without `--write-baseline`. Two test functions.
14. `make check` stays green.
15. docs: the project guide gets a section *The duplicates report*: what `make duplicates` runs, the two key forms, the baseline file `security/duplicates-baseline.txt` and `--write-baseline`, the `new`, `gone` and last lines and the exit statuses, and that this repository's pipeline runs it after the coder and writes its last line into the coder's journal entry, whatever its exit status; the decision log records why the keys carry no line numbers and why it is a record, not a check. Outside a `## Replaced from v1` section no v1 word of the document check is used (name v1's configuration as "v1's pipeline configuration for this repository", not by its file name), and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
import json
from factory.domain.duplicates import compare, dead_code_findings, report_lines, similar_code_findings
message = 'Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[9:13]\n    return value.astimezone(UTC)'
found = similar_code_findings(json.dumps([{'symbol': 'duplicate-code', 'message': message}]))
found += dead_code_findings(\"src/factory/c.py:7: unused function 'old' (60% confidence)\n\")
for line in report_lines(compare(found, ['dead-code src/factory/c.py: unused function \'old\'', 'gone-key'])):
    print(line)
"
```
Expect: three lines: `new similar-code factory.a, factory.b: return value.astimezone(UTC) at factory.a:[1:5], factory.b:[9:13]: Similar lines in 2 files`, `gone gone-key` and `duplicates: 1 new, 1 known, 1 gone`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_duplicates.py tests/entry/test_check_duplicates.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: 1. `similar_code_findings` leaves one input undefined. What does a `duplicate-code` message do when it has no `==<module>:[<start>:<end>]` line, or when no non-blank code line follows the `==` lines? The key needs "the first non-blank line after the `==` lines", and `where` is built from the `==` lines. Two coders would read this two ways and both would pass the tests.
      - Options: (a) raise `ValueError`, the way a message that is not a string does; (b) accept it, with an empty `where` or an empty first code line in the key.
      - I would choose (a). A message in pylint's format always has both parts, and a `ValueError` makes `make duplicates` stop with `check-duplicates: <reason>` and exit status 2 instead of hiding a format change.
      - Whichever you pick, it needs a criterion with a row for each case: no `==` line, and no code line after the `==` lines. This failing side is what step 3 of intake asks for.

   2. The `==` lines have no failing side. What does a line that starts with `==` but does not match `==<module>:[<start>:<end>]` do? An example is `==factory.a`. Does it raise `ValueError` like (a) above, or does it count as code? I would choose raising, with a row in the same criterion.

   Everything else I checked is fine. That covers the Interface signatures, criteria 1 to 15 apart from the two points above, the Demo (both commands run, and the first Expect matches the Interface's rules), the architecture (a pure `factory.domain` module plus an `entry` command that only reads files) and the scope (F0012 item 1.2).
