# The document check and the stop table's limits, pinned in full

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0011's feature acceptance ran a hand mutation pass over the feature's code, and four mutations survived. In each, the tests check one example where the rule covers every row:

- The S0005 Interface gives `REPLACED_PHRASES` in `src/factory/domain/documents.py` as nine phrases in a fixed order. No test pins that list. The test of the rule runs one case per phrase over the constant itself, so if a phrase is removed, its test case goes too.
- In the project guide, the rule "a table row for every case of `KILL_POINT_CASES` and every path of `FAULT_PATHS`" is tested only for case `commit-push` and path 7. A check that skipped the last case or the last path would pass.
- The rule for the limits of a `StopRow` in `src/factory/domain/stop_table.py`, "each entry matches `^L\d+$`", has one refused example in its test, `X7`. A pattern without its `$` would pass. The code calls `re.match` with `$`, and `$` also matches just before a final newline, so `"L7\n"` is accepted today. `MakeProjectCommands` once had the same trap, and it was fixed with `fullmatch`.

This story pins the list, tests every row of the three tables, and refuses a limit with anything after its digits or with a digit outside ASCII. The only code change expected is the limit rule's use of `fullmatch` with `L[0-9]+`. Criteria 1 to 4 pin behaviour already built and pass on today's code; of criterion 5, only the refused rows `"L7\n"` and `"L٣"` fail before the change. The project guide and the decision log already state the document check's rules as the Interface below gives them; no document states the limit rule yet, and the docs criterion adds it to the project guide. To keep each rule's cases in one test, the tester moves one row of a F0011-S0004 test and removes three rows of F0011-S0005 tests, by the human's leave (FEATURE decision 22).

## Interface

`src/factory/domain/stop_table.py`: `StopRow` refuses a limit unless the whole entry is `L` followed by one or more ASCII digits. The rule raises a `ValueError` in its model validator, so the caller gets a `pydantic.ValidationError`. A trailing newline, a trailing space or a trailing letter is refused, and so is a digit outside ASCII (`"L٣"`, which `\d` would accept). The check is `_LIMIT.fullmatch(limit)` with the pattern `L[0-9]+`, in place of `match` with `^L\d+$`. Nothing else in the module changes.

`src/factory/domain/documents.py` does not change. Its rules, as built:

- `REPLACED_PHRASES == ("--follow", "factory-last-line", "tasks/.gitkeep", "factory-tick.lock", "factory-run.json", "recover_dirty_tree", "lease plus ten minutes", "local branch first", "run record")`.
- For each case of `KILL_POINT_CASES`, a project guide without a table row that holds the case's id in backticks gives the finding `kill point case '<id>' has no table row`.
- For each path of `FAULT_PATHS`, a project guide without a table row that holds the path's test in backticks gives the finding `fault-injection path <number> has no table row naming '<test>'`.
- For each row of `STOP_TABLE`, an operator guide without a table row that holds the stop's id in backticks and its destination in words gives the finding `stop '<id>' has no table row with its destination`.

Tests:

- New test functions in `tests/domain/test_documents.py` (criteria 1 to 4) and `tests/domain/test_stop_table.py` (criterion 5). Each table is a parametrization over the constant itself: the rows of one test, ids taken from the row (`case.id`, `str(path.number)`, `row.id`).
- The texts come from `tests/document_texts.py` (`operator_guide(without_stop=...)`, `project_guide(without_case=..., without_path=...)`) through the module's `_with` and `_finding`; the limit test builds each row from `FIRST_ROW` with its `limits` replaced. No new helper.
- By the human's leave (FEATURE decision 22), and no other change to a test of an earlier story: the `X7` row of `test_a_row_breaking_a_rule_of_the_table_is_rejected` moves into the limit test of criterion 5, and that test's other rows (`health-without-reason`, `pull-request-with-reason`, `none-with-reason`, `no-limits`) stay; the `absent` row is removed from `test_a_stop_without_its_table_row_is_a_finding`, `test_a_kill_point_case_without_its_table_row_is_a_finding` and `test_a_fault_path_without_a_row_naming_its_test_is_a_finding`, whose other rows stay.

## Acceptance criteria

1. `REPLACED_PHRASES` equals the nine-phrase tuple of the Interface, in that order.
2. For each of the six cases of `KILL_POINT_CASES`, a project guide that is clean except for that case's missing row gives exactly the one finding `kill point case '<id>' has no table row`. These are six rows of one parametrized test.
3. For each of the thirteen paths of `FAULT_PATHS`, a project guide that is clean except for that path's missing row gives exactly the one finding `fault-injection path <number> has no table row naming '<test>'`. These are thirteen rows of one parametrized test.
4. For each of the fourteen rows of `STOP_TABLE`, an operator guide that is clean except for that stop's missing row gives exactly the one finding `stop '<id>' has no table row with its destination`. These are fourteen rows of one parametrized test.
5. A `StopRow` whose limits are `("L7",)` or `("L65",)` is accepted. A `StopRow` whose limits are `("L7\n",)`, `("L7 ",)`, `("L7x",)`, `("L",)`, `("l7",)`, `("XL7",)`, `("X7",)` or `("L٣",)` (an Arabic-Indic digit three, written with the escape) is rejected with `pydantic.ValidationError`. All ten are rows of one parametrized test, each built from `FIRST_ROW` with its `limits` replaced, through a variable typed `type[BaseModel]`.
6. `make check` stays green.
7. docs: the project guide's section *Stops, the clock and the factory log* gets one paragraph on `STOP_TABLE` and `StopRow` in `factory.domain.stop_table`: one row per stop with its v1 limits, its destination, its reason and its test; a reason exactly when the destination is the health status; and each limit the whole text `L` followed by ASCII digits, with nothing after it (`L7` yes; `L7x`, `L7 ` and a trailing newline no). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.stop_table import StopRow
for limit in ['L7', 'L7\n', 'L7x']:
    try:
        StopRow(id='x', limits=(limit,), destination='none', test='t'); print(repr(limit), 'accepted')
    except ValidationError:
        print(repr(limit), 'rejected')
"
```
Expect: three lines: `'L7' accepted`, `'L7\n' rejected`, `'L7x' rejected`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_documents.py tests/domain/test_stop_table.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
uv run python -m factory.entry.check_documents
```
Expect: the single line `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
