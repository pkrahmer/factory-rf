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

`read_baseline`: one key per line, each line stripped; blank lines and lines starting with `#` are skipped; the keys keep their order.

`compare`: `new` holds the findings whose key is not in the baseline, in the order given; `known` counts the findings whose key is in it; `gone` holds the baseline keys that no finding has, in the baseline's order. A key found twice counts twice.

`report_lines`: one line `new <key> at <where>: <message>` per new finding, then one line `gone <key>` per gone key, then the last line `duplicates: <n> new, <k> known, <g> gone`.

`src/factory/entry/check_duplicates.py`:

```python
def main(argv: Sequence[str] | None = None) -> int: ...
```

Arguments: the path of pylint's JSON, the path of vulture's text, `--baseline <path>` (required) and `--write-baseline`. `main` prints `report_lines` of the comparison, one per line, and returns 0 when nothing is new and 1 when something is. With `--write-baseline` it writes the keys of every finding (similar code first, then dead code, each in input order, a key found twice written once) to the baseline path, one per line after the first line `# Accepted findings of make duplicates, one key per line.`, prints `duplicates: baseline of <n> findings written to <path>` and returns 0. An input file that cannot be read or parsed, or a missing baseline without `--write-baseline`, prints `check-duplicates: <reason>` to standard error and returns 2. `argv` `None` reads the process's arguments.

Tests: `tests/domain/test_duplicates.py` (criteria 1 to 9), `tests/entry/test_check_duplicates.py` (criteria 10 to 13), with texts written in the tests in the formats above.

## Acceptance criteria

1. A pylint array with one `duplicate-code` object whose message is `Similar lines in 2 files\n==factory.domain.stops:[49:53]\n==factory.domain.git:[73:77]\n    @field_validator("at")\n    @classmethod` gives one finding with the key `similar-code factory.domain.git, factory.domain.stops: @field_validator("at")`, the where `factory.domain.stops:[49:53], factory.domain.git:[73:77]` and the message `Similar lines in 2 files`.
2. The same message with its line numbers changed gives the same key; with a different first code line it gives another key.
3. A message naming one module twice (two blocks in one file) lists it once in the key. Objects of another symbol (`unused-import`) give no finding, and `[]` gives none.
4. Each of these pylint texts raises `ValueError`: `not json`, `{}`, `[1]`, `[{"symbol": "duplicate-code"}]` (no message). Four rows of one parametrized test.
5. The vulture line `src/factory/x.py:12: unused function 'helper' (60% confidence)` gives the key `dead-code src/factory/x.py: unused function 'helper'`, the where `src/factory/x.py:12` and the message `unused function 'helper' (60% confidence)`; the same line with `, 3 lines` before the parenthesis gives the same key; a blank line gives nothing.
6. A vulture text whose second line is `oops` raises `ValueError` whose message names line 2; a line `src/x.py: unused function 'f' (60% confidence)` (no line number) and a line with leading spaces raise it too. Rows of one parametrized test.
7. `read_baseline("# comment\n\n  similar-code a, b: x  \ndead-code p: m\n")` is `["similar-code a, b: x", "dead-code p: m"]`.
8. `compare` of findings with keys `a`, `b`, `b` against the baseline `["b", "c"]` gives `new` with the one finding `a`, `known == 2` and `gone == ["c"]`; against an empty baseline every finding is new and nothing is gone.
9. `report_lines` of that report is `["new a at <where>: <message>", "gone c", "duplicates: 1 new, 2 known, 1 gone"]`, and of a report with nothing new and nothing gone exactly `["duplicates: 0 new, <k> known, 0 gone"]`.
10. `main` with a pylint file, a vulture file and a baseline that holds every key prints only the last line and returns 0; with a baseline missing one key it prints that `new` line first and returns 1.
11. `main` with `--write-baseline` writes the header line and each distinct key once to the baseline path, prints `duplicates: baseline of <n> findings written to <path>` and returns 0; a second run without the option on the same inputs then returns 0.
12. `main` with a missing input file, with an unparsable pylint file, or with a missing baseline and no `--write-baseline`, prints one line starting `check-duplicates: ` to standard error and returns 2. Rows of one parametrized test.
13. `main(None)` with the process's arguments set (monkeypatched `sys.argv`) behaves as `main` with those arguments.
14. `make check` stays green.
15. docs: the project guide gets a section *The duplicates report*: what `make duplicates` runs, the two key forms, the baseline file `security/duplicates-baseline.txt` and `--write-baseline`, the `new`, `gone` and last lines and the exit statuses, and that the pipeline runs it as a record after the coder; the decision log records why the keys carry no line numbers and why it is a record, not a check.

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
