---
stage: docs
pr: 151
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted
   - Interface: names concrete modules and signatures. `StopRow` in `src/factory/domain/stop_table.py` changes to `_LIMIT.fullmatch` with the pattern `L[0-9]+`, raised as a `ValueError` in the model validator. `documents.py` is unchanged, and its constant and finding texts are given exactly. Every behaviour stated in an Interface comment has a criterion: criterion 1 pins the phrase order, criteria 2 to 4 pin the finding texts, and criterion 5 pins the limit rule.
   - Criteria: each is testable by one parametrized test function. The limit rule has both sides: `L7` and `L65` are accepted, and eight refused rows cover the newline, the space, the letter, a bare `L`, lowercase, a prefix, `X7` and the Arabic-Indic digit. The counts are 6 cases, 13 paths and 14 stop rows. The tests over the constants take their rows from the constants, so the counts follow whatever the constants hold.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable against the output: three named lines, a final `passed` line with no failed, error or skipped count, and `documents ok`.
   - Architecture: the change sits in `factory.domain`, which is pure, and adds no dependency or layer crossing. The tests go in `tests/domain/`, which mirrors the package. They reuse `tests/document_texts.py` and `FIRST_ROW`, with no new helper.
   - Scope: the story is within F0011's scope (the stop table and the document check) and touches nothing under Out of scope. The edits to earlier stories' tests (moving the `X7` row, removing three `absent` rows) are covered by FEATURE decision 22 and named exactly in the Interface. The docs criterion changes only the project guide.
3. tester: Wrote the tests for criteria 1 to 5. Each table test is parametrized over its constant, with ids taken from the row.
   - criterion 1: tests/domain/test_documents.py::test_the_replaced_phrases_are_the_nine_in_their_order
   - criterion 2: tests/domain/test_documents.py::test_every_kill_point_case_without_its_table_row_is_a_finding (one row per `KILL_POINT_CASES` case, id `case.id`)
   - criterion 3: tests/domain/test_documents.py::test_every_fault_path_without_a_row_naming_its_test_is_a_finding (one row per `FAULT_PATHS` path, id `str(path.number)`)
   - criterion 4: tests/domain/test_documents.py::test_every_stop_without_its_table_row_is_a_finding (one row per `STOP_TABLE` row, id `row.id`)
   - criterion 5: tests/domain/test_stop_table.py::test_a_limit_is_the_whole_text_l_and_ascii_digits (ten rows: `L7` and `L65` accepted; `"L7\n"`, `"L7 "`, `L7x`, `L`, `l7`, `XL7`, `X7` and `"L٣"` rejected). Each row is built from `FIRST_ROW` with its `limits` replaced, through `model: type[BaseModel] = StopRow`.
   - criteria 6 and 7: no test (`make check`, docs).

   Changes to earlier tests, as FEATURE decision 22 and the Interface allow, and nothing else: I removed the `X7` row and its id from `test_a_row_breaking_a_rule_of_the_table_is_rejected` (it is now a row of the limit test). I removed the `absent` row (`""`) and its id from `test_a_stop_without_its_table_row_is_a_finding`, `test_a_kill_point_case_without_its_table_row_is_a_finding` and `test_a_fault_path_without_a_row_naming_its_test_is_a_finding`. Their other rows are unchanged.

   Files changed: tests/domain/test_documents.py (adds imports of `FAULT_PATHS`/`FaultPath`, `KILL_POINT_CASES`/`KillPointCase` and `STOP_TABLE`/`StopRow`) and tests/domain/test_stop_table.py. No new helper and no new file. The texts come from `operator_guide(without_stop=...)` and `project_guide(without_case=..., without_path=...)` through the module's `_with` and `_finding`.

   Result of `make test`: every module imported. The only failures are the two rows the assignment expected: `test_a_limit_is_the_whole_text_l_and_ascii_digits[trailing-newline]` and `[non-ascii-digit]`. Today's `re.match` with `^L\d+$` accepts both; the coder's fix is `_LIMIT.fullmatch` with `L[0-9]+`. Criteria 1 to 4 pass on today's code, as the assignment says they should. My first `make test` run stopped at a collection error: I had put a new function between an existing parametrize decorator and its function. I fixed that and ran it again; the result above is from that run. `make lint` is green.

   Rejected: in the limit test, checking the accepted rows' `.limits` would have needed a `type: ignore`, which the project's test rules forbid. The accepted rows check `isinstance(model(**fields), StopRow)` instead. Open: nothing.

   `make lint`: lint: green
   `make test`: FAILED tests/domain/test_stop_table.py::test_a_limit_is_the_whole_text_l_and_ascii_digits[non-ascii-digit]
4. coder: Changed the limit rule in `src/factory/domain/stop_table.py` so that `StopRow` refuses any limit that is not, as a whole, `L` followed by ASCII digits. `_LIMIT` is now `re.compile(r"L[0-9]+")`, and `_limits_name_v1_limits` calls `_LIMIT.fullmatch(limit)` where it used to call `match` with `^L\d+$`. Commit: cae63fc.
      - Design: I used `fullmatch` instead of keeping the anchors and switching to `\Z`. With `fullmatch` the whole-string rule lives in the call, as `MakeProjectCommands` already does. Writing `[0-9]` instead of `\d` refuses non-ASCII digits such as `"L٣"`. I rejected `re.ASCII` with `\d`: it says the same thing less directly.
      - Result: both rows that failed before the change, `[trailing-newline]` and `[non-ascii-digit]`, now pass. `make check` is green.
      - Refactor: the diff is two lines with nothing to clean up, so there is no refactor commit.
      - Open: criterion 7 (the project guide paragraph on `STOP_TABLE` and `StopRow`) is the documenter's job; I did not write it. I noticed nothing else.

   `make check`: check: green
5. reviewer: no findings.
   - Criteria: each of criteria 1 to 5 has its test, as the tester's entry lists them. Criteria 2 to 4 are parametrized over `KILL_POINT_CASES`, `FAULT_PATHS` and `STOP_TABLE` themselves, with ids `case.id`, `str(path.number)` and `row.id`. Their texts come from `project_guide(...)` and `operator_guide(...)` in `tests/document_texts.py`, which drop exactly the named row, and each test asserts the exact one-finding list. Criterion 1 compares against the literal nine-phrase tuple, so removing a phrase now fails a test. Criterion 5 is one parametrized test with all ten rows (two accepted, eight refused, including `"L7\n"` and `"L٣"`), each built from `FIRST_ROW` with `limits` replaced, through `model: type[BaseModel] = StopRow`. The edits to earlier tests are exactly the ones FEATURE decision 22 allows: the `X7` row moved into the new limit test, and the `absent` row was removed from three tests. The coder's entry reports `make check` green.
   - Code: `src/factory/domain/stop_table.py` now uses `re.compile(r"L[0-9]+")` with `_LIMIT.fullmatch`, as the Interface specifies, and nothing else in the module changed. Architecture and security are unaffected: the change is a pure domain change with no new dependency and no suppression marker.
   - Other changes in the diff range: the `docs/runs/...night-log.md` and `planning/overnight/restructure-after-f0011.md` changes are the human's own commits (1a7bc24, 54e348b), brought in by the merge of main. They are not the ticket's work and were not reviewed.
   - Ticket: `Assignment` matches what was built, and criterion 7 still says what the documenter must add to the project guide.
