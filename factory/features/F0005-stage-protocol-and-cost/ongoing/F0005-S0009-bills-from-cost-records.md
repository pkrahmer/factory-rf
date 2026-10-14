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
