# The document check and the stop table's limits, pinned in full

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0011's feature acceptance ran a hand mutation pass over the feature's code, and four mutations survived. In each, the tests check one example where the rule covers every row:

- The S0005 Interface gives `REPLACED_PHRASES` in `src/factory/domain/documents.py` as nine phrases in a fixed order. No test pins that list. The test of the rule runs one case per phrase over the constant itself, so if a phrase is removed, its test case goes too.
- In the project guide, the rule "a table row for every case of `KILL_POINT_CASES` and every path of `FAULT_PATHS`" is tested only for case `commit-push` and path 7. A check that skipped the last case or the last path would pass.
- The rule for the limits of a `StopRow` in `src/factory/domain/stop_table.py`, "each entry matches `^L\d+$`", has one refused example in its test, `X7`. A pattern without its `$` would pass. The code calls `re.match` with `$`, and `$` also matches just before a final newline, so `"L7\n"` is accepted today. `MakeProjectCommands` once had the same trap, and it was fixed with `fullmatch`.

This story pins the list, tests every row of the three tables, and refuses a limit with anything after its digits. The only code change expected is the limit rule's use of `fullmatch`. It adds no new behaviour: the README, the guides and the decision log already state the rules as the Interface below gives them.

## Interface

`src/factory/domain/stop_table.py`: `StopRow` refuses a limit unless the whole entry is `L` followed by one or more ASCII digits. The rule raises a `ValueError` in its model validator, so the caller gets a `pydantic.ValidationError`. A trailing newline, a trailing space or a trailing letter is refused. The check is `_LIMIT.fullmatch(limit)` with the pattern `L[0-9]+`, in place of `match` with `^L\d+$`. Nothing else in the module changes.

`src/factory/domain/documents.py` does not change. Its rules, as built:

- `REPLACED_PHRASES == ("--follow", "factory-last-line", "tasks/.gitkeep", "factory-tick.lock", "factory-run.json", "recover_dirty_tree", "lease plus ten minutes", "local branch first", "run record")`.
- For each case of `KILL_POINT_CASES`, a project guide without a table row that holds the case's id in backticks gives the finding `kill point case '<id>' has no table row`.
- For each path of `FAULT_PATHS`, a project guide without a table row that holds the path's test in backticks gives the finding `fault-injection path <number> has no table row naming '<test>'`.
- For each row of `STOP_TABLE`, an operator guide without a table row that holds the stop's id in backticks and its destination in words gives the finding `stop '<id>' has no table row with its destination`.

Tests:

- `tests/domain/test_documents.py` and `tests/domain/test_stop_table.py`, which are new test functions or new rows of the existing parametrized tests.
- The clean texts come from `tests/document_texts.py`: `operator_guide(without_stop=...)` and `project_guide(without_case=..., without_path=...)`.
- Each table is a parametrization over the constant: the rows of one test, ids taken from the row.

## Acceptance criteria

1. `REPLACED_PHRASES` equals the nine-phrase tuple of the Interface, in that order.
2. For each of the six cases of `KILL_POINT_CASES`, a project guide that is clean except for that case's missing row gives exactly the one finding `kill point case '<id>' has no table row`. These are six rows of one parametrized test.
3. For each of the thirteen paths of `FAULT_PATHS`, a project guide that is clean except for that path's missing row gives exactly the one finding `fault-injection path <number> has no table row naming '<test>'`. These are thirteen rows of one parametrized test.
4. For each of the fourteen rows of `STOP_TABLE`, an operator guide that is clean except for that stop's missing row gives exactly the one finding `stop '<id>' has no table row with its destination`. These are fourteen rows of one parametrized test.
5. A `StopRow` whose limits are `("L7",)` or `("L65",)` is accepted. A `StopRow` whose limits are `("L7\n",)`, `("L7 ",)`, `("L7x",)`, `("L",)`, `("l7",)` or `("XL7",)` is rejected with `pydantic.ValidationError`. All are rows of one parametrized test, built through a variable typed `type[BaseModel]`.
6. `STOP_TABLE` still holds its fourteen rows, and `python -m factory.entry.check_documents` still prints `documents ok` on the repository's four documents.
7. `make check` stays green.
8. docs: the project guide's description of `StopRow`, next to the stop table, says that a limit is the whole text `L<digits>`, with nothing after it. No other document changes, because the document check's rules are already described as built.

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
