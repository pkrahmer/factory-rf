---
stage: docs
pr: 66
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Bills from the cost records

## Assignment (as of log entry 1)

Compute the bill of a stage and of a work item from the cost records alone (SI1.2): every record counts, whatever its end reason (GH4.2), and a cost or token count that the runtime did not report is not in a sum and is not turned into zero. The cost line and the cost table are display text built from those sums and never read back. A bill service reads a work item's sidecar from the remote-tracking refs only, so a tick with an empty `work` volume, or a fresh clone, shows the same bills (GH4.5). A search test shows that no code under `src/factory` turns journal text into data (SI1.4). `factory-bill` prints the table and the cost line of one work item, or of every work item in flight; `pyproject.toml` already registers `factory-bill = "factory.entry.bill:main"`. Covers SI1.2, SI1.4, GH4.5; keeps kept thing 20 (each story carries its bill, posted at the approval by F0007 and written at the archive).

## Interface

`src/factory/domain/bills.py`

```python
class Bill(BaseModel):
    runs: NonNegativeInt
    runs_cost_unknown: NonNegativeInt
    duration: timedelta
    turns: NonNegativeInt
    tokens: TokenCounts
    cost_usd: Decimal

class StageBill(BaseModel):
    stage: Name
    bill: Bill

def bill(records: Sequence[CostRecord]) -> Bill: ...
def bills_by_stage(records: Sequence[CostRecord]) -> list[StageBill]: ...
def total(stage_bills: Sequence[StageBill]) -> Bill: ...
def cost_line(bill: Bill) -> str: ...
def cost_table(stage_bills: Sequence[StageBill]) -> str: ...
```

`src/factory/application/costs.py` (grown by this story)

```python
class WorkItemBill(BaseModel):
    work_item: WorkItemId
    total: Bill
    stages: list[StageBill]
    line: str
    table: str

class BillService:
    def __init__(self, git: Git, cost_reader: CostRecordReader) -> None: ...
    def for_work_item(self, work_item: WorkItemId) -> WorkItemBill | None: ...
    def in_flight(self) -> list[WorkItemId]: ...
```

`src/factory/entry/bill.py`

```python
def run(argv: Sequence[str], service: BillService, out: TextIO) -> int: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

`src/factory/entry/wiring.py` (grown by this story)

```python
def build_bill_service(checkout: Path) -> BillService: ...
```

`build_bill_service` is added to the module's `__all__`, and `bill.py` imports it from `factory.entry.wiring` only (`tests/entry/test_wiring.py` lets no other entry module import the adapters).

Types: `CostRecord` from `factory.domain.cost_records`, `TokenCounts` from `factory.domain.agent_runs`, `Git` from `factory.application.git`, `CostRecordReader` from `factory.application.files`. All models are frozen and forbid unknown keys. `build_bill_service` returns `BillService(GitCli(checkout), JsonLinesCostRecordReader())`.

- `bill(records)`: `runs` is the number of records, every record whatever its `status` and `end_reason`; `runs_cost_unknown` is the number whose `cost_usd` is `None`; `duration` is the sum of the known `duration_seconds`; `turns`, `tokens` (field by field) and `cost_usd` are the sums of the known values. A value that is `None` is skipped, never counted as zero.
- `bills_by_stage(records)`: one `StageBill` per distinct `stage`, in the order of its first record, each the `bill` of that stage's records (a stage that runs again joins its first group). `total(stage_bills)` is the field-by-field sum of their bills.
- `cost_line(bill)` returns `<runs> runs, <m> min, <turns> turns, <i> tokens in (<c> more from cache), <o> out, $<usd>` with `<m>` the duration in minutes, `<i>` the tokens' `input` plus `cache_creation`, `<c>` its `cache_read`, `<o>` its `output`. Minutes are shown with one decimal and dollars with two decimals, both rounded half up. When `runs_cost_unknown` is above zero, ` + <n> unknown` follows the dollars.
- `cost_table(stage_bills)` returns these lines joined by one newline, without a trailing newline: `| stage | runs | min | turns | in | cached | out | USD |`; `| :-- | --: | --: | --: | --: | --: | --: | --: |`; one line `| <stage> | <runs> | <min> | <turns> | <in> | <cached> | <out> | <usd> |` per stage bill in the given order; and a last line of the same form for `total(stage_bills)` whose first cell is `**total**`. The cells use the same figures and rounding as the cost line, and the USD cell has ` + <n> unknown` after the dollars like the line.
- `BillService.for_work_item(work_item)` reads only remote-tracking refs: the ref is `origin/<branch of the work item>` when that ref exists, else `origin/main`. In that ref, `list_files` over `FEATURES_DIRECTORY` finds the first path ending in `.md` whose file name parses to the work item's id; none gives `None`. The sidecar is `cost_records_path(<that path>)` read with `show_file` and `CostRecordReader.parse`; an absent sidecar means no records. The result holds `total=bill(records)`, `stages=bills_by_stage(records)`, `line=cost_line(total)` and `table=cost_table(stages)`.
- `BillService.in_flight()` returns the work item ids of the remote branches named like work item branches, sorted with `work_item_order`.
- `run(argv, service, out)` with one id argument writes the work item's table, an empty line and `Cost: <line>` and returns 0; for an id that has no bill it writes `no work item <id>` and returns 1; for an argument that is not a work item id it writes `not a work item id: <argument>` and returns 2. With no argument it writes, for each id from `in_flight()` that has a bill, the id on its own line and then the same block, blocks separated by an empty line, and returns 0. With more than one argument it writes `usage: factory-bill [<work item id>]` and returns 2.
- `main(argv)` returns `run(sys.argv[1:] if argv is None else argv, build_bill_service(Path.cwd()), sys.stdout)`; the module runs `raise SystemExit(main())` under `if __name__ == "__main__"`.
- Nothing under `src/factory` turns journal text into data. The search test parses every module with `modules()` of `tests/source_search.py` and applies one function, `violations(trees)`, to the real tree and to small trees built with `ast.parse` for the failing cases. A module references a name when it imports it (an `ast.ImportFrom` alias with that name), uses it as an `ast.Name`, or uses it as the attribute of an `ast.Attribute` (a local variable of that name counts too; S0009 renames any such variable in the modules of F0005). `entry_text` may be referenced only in `factory.domain.journal`, `factory.application.handlers.hand_over` and `factory.application.handlers.questions` (F0007 posts a recorded question from it). `JOURNAL` of `factory.domain.sections` may be referenced only in `factory.domain.sections`, `factory.domain.journal`, `factory.domain.story_form`, `factory.adapters.work_item_markdown` and `factory.application.opening` (S0002 adds a missing `## Journal` section with it). A string literal equal to `Journal` or to `## Journal` (found with `string_literals`) is allowed only in `factory.domain.sections`, so a call such as `section_text(body, "Journal")` fails the search too.

Tests: `tests/domain/test_bills.py`, `tests/application/test_bill_service.py`, `tests/entry/test_bill.py`, and `tests/test_no_journal_reading.py` at the `tests/` root (it uses `tests/source_search.py`). `Bill`, `StageBill` and `WorkItemBill` refuse what their types refuse (a negative `runs`, `runs_cost_unknown` or `turns`, an unknown key), tested on both sides (criterion 22). Criterion 19's test imports nothing from `factory.entry.bill` before `runpy`, or names the warning in `pytest.warns(RuntimeWarning)`. The service tests write sidecars with `JsonLinesCostRecordWriter` into work items pushed through `human.push_file`.

## Acceptance criteria

1. `bill` of the three records of the demo (below) returns `runs=3`, `runs_cost_unknown=1`, a duration of 210 seconds, `turns=12`, tokens `input=22`, `output=400`, `cache_read=1500`, `cache_creation=50` and `cost_usd=Decimal("1.545")`; `bill([])` returns zero runs, a zero duration, zero turns, zero tokens and `Decimal("0")`.
2. A record that ended `died`, `time_limit` or `budget` counts in `runs` and its known duration counts in `duration`: a run that failed is in the bill (GH4.2).
3. A record whose `cost_usd` is `None` is left out of `cost_usd` and counted in `runs_cost_unknown`; a record whose `turns` or `tokens` is `None` adds nothing to them: unknown is skipped, never zero.
4. `bills_by_stage` returns one entry per stage in the order of the stage's first record, and records of a stage that comes back after another stage (`doing`, `review`, `doing`) are in the first `doing` entry.
5. `cost_line` of the demo's total bill returns exactly `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`; the same bill with all costs known has no ` + 1 unknown`.
6. Rounding is half up: a bill of cost `Decimal("0.125")` and duration 3 seconds gives `$0.13` and `0.1 min` in the line.
7. `cost_table` of the demo's two stage bills returns exactly the five lines that are lines 1 to 5 of the Demo's output, the total row last and carrying ` + 1 unknown` in its USD cell.
8. `for_work_item` of a work item with a branch on the remote reads the sidecar from that branch: a sidecar pushed to the branch only gives a bill with the branch's records, and `line` and `table` equal `cost_line` and `cost_table` of them.
9. `for_work_item` of an archived work item (no branch, the file and its sidecar in a `done/` folder on `main`) gives the bill of that sidecar.
10. `for_work_item` returns `None` for an id with no file on any remote-tracking ref, and a `WorkItemBill` with zero runs and no stages for a work item that has a file but no sidecar.
11. The cost line written in a `done` journal entry of the work item has no influence: a journal that says `cost: 99 runs, $999.00` and a sidecar with two records give `runs == 2` (SI1.2).
12. A local commit that was not pushed and changes the sidecar has no influence: only the remote-tracking refs are read.
13. A `BillService` built on a fresh clone of the remote, in another directory with no state of any kind, returns a `WorkItemBill` equal to the one of the original checkout (GH4.5).
14. `in_flight` returns the ids of the remote branches `work-item/<id>`, sorted by `work_item_order`, and ignores other branches.
15. `run` with one valid id prints the table, an empty line and `Cost: <line>` and returns 0.
16. `run` returns 1 and prints `no work item <id>` for an id without a bill, returns 2 and prints `not a work item id: <argument>` for `F1`, and returns 2 and prints `usage: factory-bill [<work item id>]` for two arguments.
17. `run` with no argument prints, for each in-flight work item that has a bill, its id and then its block, blocks separated by an empty line, and returns 0.
18. `main()` run inside a clone of the remote with `sys.argv` set to the program name and one id prints that work item's block and returns 0; `main(["<id>"])` with a list uses that list instead of `sys.argv`.
19. Running the module as a program (`runpy.run_module("factory.entry.bill", run_name="__main__")` inside the clone, `sys.argv` holding an id without a bill) prints `no work item <id>` and exits with `SystemExit` status 1.
20. The search test passes on the real tree: `entry_text` and `JOURNAL` are referenced under `src/factory` only in the modules named in the Interface, and no string literal equal to `Journal` or `## Journal` stands outside `factory.domain.sections` (SI1.4).
21. The search fails for a module outside the allow-list that references `entry_text` or `JOURNAL`, each of the three ways (parametrised): by `from factory.domain.journal import entry_text`, by the name `entry_text(document, 1)` and by the attribute `journal.entry_text(document, 1)`; and it fails for a module that holds the literal `"Journal"` or `"## Journal"`, as in `section_text(body, "Journal")` (tested on trees built with `ast.parse`).
22. The models refuse what their types refuse, on both sides: `Bill` accepts `runs`, `runs_cost_unknown` and `turns` of 0 and refuses -1 for each; `Bill`, `StageBill` and `WorkItemBill` are frozen (assigning to `runs`, `stage` and `line`, through `setattr` with the field's name in a variable, raises `ValidationError`) and each refuses an unknown key (built through a variable typed `type[BaseModel]`).
23. make check stays green.
24. docs: `docs/operator-guide.md` explains `factory-bill`, the cost table's columns and the cost line, including that an unknown cost is shown as `+ <n> unknown`; `docs/project-guide.md` states that bills are sums of the cost records and that no code reads data from the journal's text, with the search test's rule (the allowed modules and the forbidden literal).

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4
from factory.domain.agent_runs import TokenCounts
from factory.domain.bills import bill, bills_by_stage, cost_line, cost_table
from factory.domain.cost_records import CostRecord
def record(stage, role, seconds, reason, turns, tokens, cost):
    return CostRecord(run=uuid4().hex, work_item='F0001-S0001', stage=stage, role=role, attempt=0, status='completed', started_at=datetime(2026, 10, 12, 9, 0, tzinfo=UTC), duration_seconds=seconds, end_reason=reason, turns=turns, tokens=tokens, cost_usd=cost)
records = [
    record('tests', 'tester', 60.0, 'completed', 7, TokenCounts(input=12, output=300, cache_read=1000, cache_creation=50), Decimal('0.345')),
    record('doing', 'coder', 120.0, 'died', None, None, None),
    record('doing', 'coder', 30.0, 'completed', 5, TokenCounts(input=10, output=100, cache_read=500), Decimal('1.2')),
]
print(cost_table(bills_by_stage(records)))
print(cost_line(bill(records)))
"
```
Expect: 6 lines. Line 1 is `| stage | runs | min | turns | in | cached | out | USD |`. Line 2 is `| :-- | --: | --: | --: | --: | --: | --: | --: |`. Line 3 is `| tests | 1 | 1.0 | 7 | 62 | 1000 | 300 | 0.35 |`. Line 4 is `| doing | 2 | 2.5 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |`. Line 5 is `| **total** | 3 | 3.5 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |`. Line 6 is `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`.

```bash
uv run pytest tests/domain/test_bills.py tests/application/test_bill_service.py tests/entry/test_bill.py tests/test_no_journal_reading.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (domain/bills.py, application/costs.py, entry/bill.py, entry/wiring.py). Every stated behaviour has a rule: the sums, the unknown-is-skipped rule, stage grouping, the line and table formats, rounding, the ref choice, and the in_flight and run outputs. The types it imports are named with their modules.
   - Criteria: each is testable by one test function. The failing sides are covered: a failed run still counts (2), unknown cost, turns and tokens are skipped (3), no id on any ref gives None (10), local unpushed commits and journal text are ignored (11, 12), other branches are ignored (14), a bad id, an unknown id and too many arguments (16), and negative or unknown fields (22). Minor gap, not blocking: the tests for 17 may also cover an in-flight id without a bill being skipped, since the Interface states that rule.
   - Demo: both commands are runnable. I checked the expected figures by hand: 210 s is 3.5 min, input 22 + cache_creation 50 is 72, and 1.545 rounds half up to 1.55. The `Expect:` lines are checkable against the output.
   - Architecture: pure sums and formats sit in domain, the service in application behind the Git and CostRecordReader interfaces, and the command and wiring in entry, with `bill.py` importing only from `wiring`. This matches CLAUDE.md.
   - Scope: the story stays within the feature's Bills scope and touches none of the Out of scope items (the hand-over posting is F0007).
3. tester: wrote red tests for criteria 1–22. `make lint` is green. `make test` stops at collection on purpose because the modules under test don't exist yet.
   - criterion 1: tests/domain/test_bills.py::test_the_bill_of_the_demo_records_sums_every_known_value, ::test_the_bill_of_no_records_is_all_zero
   - criterion 2: tests/domain/test_bills.py::test_a_failed_run_counts_in_runs_and_duration (parametrised over died, time_limit, budget)
   - criterion 3: tests/domain/test_bills.py::test_an_unknown_cost_turns_or_tokens_is_skipped_never_zero
   - criterion 4: tests/domain/test_bills.py::test_bills_by_stage_groups_in_first_order_and_a_returning_stage_joins_its_first_group
   - criterion 5: tests/domain/test_bills.py::test_the_cost_line_of_the_demo_bill
   - criterion 6: tests/domain/test_bills.py::test_minutes_and_dollars_round_half_up (0.125 → $0.13, 3 s → 0.1 min; half-even would give $0.12 and 0.0)
   - criterion 7: tests/domain/test_bills.py::test_the_cost_table_of_the_demo_stage_bills
   - criterion 8: tests/application/test_bill_service.py::test_a_work_item_with_a_branch_is_billed_from_the_branch (main holds a 1-record sidecar, the branch a 2-record one)
   - criterion 9: tests/application/test_bill_service.py::test_an_archived_work_item_is_billed_from_its_sidecar_on_main
   - criterion 10: tests/application/test_bill_service.py::test_an_id_without_a_file_has_no_bill, ::test_a_work_item_without_a_sidecar_has_an_empty_bill
   - criterion 11: tests/application/test_bill_service.py::test_the_cost_line_in_the_journal_has_no_influence
   - criterion 12: tests/application/test_bill_service.py::test_a_local_commit_that_was_not_pushed_has_no_influence
   - criterion 13: tests/application/test_bill_service.py::test_a_fresh_clone_gives_the_same_bill
   - criterion 14: tests/application/test_bill_service.py::test_in_flight_lists_the_work_item_branches_in_work_item_order (ignores `feature/notes` and `work-item/notes`)
   - criterion 15: tests/entry/test_bill.py::test_one_id_prints_the_table_and_the_cost_line
   - criterion 16: tests/entry/test_bill.py::test_a_wrong_argument_prints_why_and_returns_its_status (parametrised: no bill, `F1`, two arguments)
   - criterion 17: tests/entry/test_bill.py::test_no_argument_prints_every_in_flight_work_item_that_has_a_bill (it also covers the gap intake raised: the branch `work-item/F0001-S0003` has no work item file and is skipped)
   - criterion 18: tests/entry/test_bill.py::test_main_reads_the_id_from_sys_argv_in_the_current_checkout, ::test_main_with_a_list_uses_the_list_instead_of_sys_argv
   - criterion 19: tests/entry/test_bill.py::test_the_module_runs_as_a_program_and_exits_with_the_status (wraps `runpy` in `pytest.warns(RuntimeWarning)` because the module imports `factory.entry.bill` at the top)
   - criterion 20: tests/test_no_journal_reading.py::test_no_module_reads_data_from_the_journal_text
   - criterion 21: tests/test_no_journal_reading.py::test_a_journal_reference_outside_the_allowed_modules_is_found (8 cases: `entry_text` and `JOURNAL` each by import, name and attribute, plus the literals "Journal" and "## Journal"). The allowed side is ::test_a_journal_reference_in_an_allowed_module_is_not_found.
   - criterion 22: tests/domain/test_bills.py::test_a_bill_count_of_zero_is_accepted, ::test_a_negative_bill_count_is_refused, ::test_a_bill_is_frozen, ::test_a_stage_bill_is_frozen, ::test_a_bill_refuses_an_unknown_key, ::test_a_stage_bill_refuses_an_unknown_key; tests/application/test_bill_service.py::test_a_work_item_bill_is_frozen, ::test_a_work_item_bill_refuses_an_unknown_key

   Files created: tests/domain/test_bills.py, tests/application/test_bill_service.py, tests/entry/test_bill.py, tests/test_no_journal_reading.py, tests/bill_support.py (a helper that builds completed records and renders their sidecar with `JsonLinesCostRecordWriter`).

   Setup notes for the coder:
   - The service tests call `checkout.fetch()` before they use `BillService`. The Interface does not say the service fetches, so the tests do not rely on it either way.
   - `violations(trees)` is defined in the test module itself.
   - The search test on the real tree is a guard and may already pass: only `factory.domain.journal` references `entry_text` today, and `JOURNAL` appears only in allowed modules.

   Imports that fail during collection: `factory.domain.bills` (the module is missing), `BillService` and `WorkItemBill` from `factory.application.costs` (the names are missing), and `factory.entry.bill` (the module is missing).

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented bills, the bill service and `factory-bill`. `make check` is green (coverage 99.43 %) and the Demo's six lines match exactly. Commit 6b3790a.
   - `src/factory/domain/bills.py`: the `Bill` and `StageBill` models, plus `bill`, `bills_by_stage`, `total`, `cost_line` and `cost_table`. Each record becomes a one-run bill in which an unknown measure adds nothing, and the bills are summed field by field. So `bill`, the stage grouping (a dict keyed on the first time a stage appears) and `total` share one adding path. Minutes and dollars are rounded with `Decimal.quantize(ROUND_HALF_UP)`. The minutes come from `Decimal(str(seconds))`, which avoids float half-way errors.
   - `src/factory/application/costs.py`: added `WorkItemBill` and `BillService`. It picks the ref `origin/<branch>` when `resolve` finds that ref, else `origin/main`. Then it takes the first path under `FEATURES_DIRECTORY` whose file name parses to the id, reads the sidecar with `show_file` and parses it with `CostRecordReader.parse`; a missing sidecar gives no records. `in_flight` maps `remote_branches()` through `work_item_of_branch` and sorts with `work_item_order`. The service never fetches; the caller fetches, as the tests do.
   - `src/factory/entry/bill.py`: `run` and `main`, ending with `raise SystemExit(main())` under `__main__`. It imports only `build_bill_service` from the adapter side, through wiring.
   - `src/factory/entry/wiring.py`: added `build_bill_service` and listed it in `__all__`.
   - Design choice: the bill is built only from per-record bills and their sum. I rejected keeping separate running totals for each field, because that would repeat the skip-if-unknown rule in several places.
   - Id check in `run`: a regex built from the domain's `STORY_ID|ACCEPTANCE_ID`. I rejected calling the private `_checked` in identifiers, and building a pydantic TypeAdapter just to answer yes or no.
   - Refactor pass: I read the diff and found nothing to change.
   - Noticed, not touched: the search test already passed on the real tree. No module in F0005 had a local variable named `entry_text`, so nothing needed renaming.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: I read every test against its criterion. Criteria 1–22 each have tests that check what the criterion names. The failing sides are covered: failed runs (died, time_limit, budget), unknown cost, turns and tokens being skipped, no file on any ref giving None, unpushed local commits, journal text, non-work-item branches, `F1`, two arguments, an in-flight branch without a file, and negative counts and unknown keys tested on both sides of zero. The search test's eight failing cases run on `ast.parse` trees, and the allowed modules are tested too. Criterion 8 is a real test: if the service read main, the branch's file would sit at the backlog path with no sidecar there, giving 0 runs, not 2. The coder's entry reports `make check` green.
      - Architecture: `domain/bills.py` is pure (Pydantic and Decimal only). `BillService` sits in application and depends only on the `Git` and `CostRecordReader` interfaces. `entry/bill.py` reaches the adapters only through `wiring.build_bill_service`, which is in `__all__`. No `dict[str, Any]` crosses a boundary.
      - Security: nothing to flag. No subprocess, no strings built into commands, no suppression markers. The argument is checked against the id pattern before it is used.
      - Quality: `bill`, `bills_by_stage` and `total` share one per-record-bill-plus-sum path, so the skip-unknown rule lives in one place (`_record_bill`). `parse_work_item_file_name` already requires `.md`, so a sidecar can never be taken for the work item file. Docstrings are present on the public names and match what the code does.
      - Rejected as findings: `_is_work_item_id` in `src/factory/entry/bill.py` rebuilds the id regex from the domain's `STORY_ID|ACCEPTANCE_ID` constants instead of calling a public domain predicate. No such public predicate exists, and the coder's entry explains why it rejected the alternatives. It reuses domain constants rather than copying them. The Name and WorkItemId patterns on `StageBill` and `WorkItemBill` have no refused-side test. They are existing domain types, and the Interface lists only the counts and unknown keys as the limits to test.
      - Ticket hygiene: the Assignment matches what was built. The coder's log explains the main design choice and what it rejected. Criterion 24 still says what the documenter has to write.
