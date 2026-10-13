---
stage: tests
pr: 34
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Cost record sidecar format

## Assignment (as of log entry 1)

Build the cost record and the file it lives in: one JSON line per agent run, in a sidecar file beside the work item (`cost_records_path`), read and written by one reader class and one writer class (R15, R13). A record is created when an agent run starts (status `started`) and completed when it ends (status `completed`, with the end reason, duration and, when the runtime reported them, turns, tokens and cost). A measure the runtime did not report is unknown and is kept as `null`, never written as zero (R24); the cost is a JSON string so that no float can round it. Reading and writing are pure format work: when a record is created, completed or discarded, and how a bill is summed, belong to F0005. The story covers R15 (cost records as one JSON line each in a sidecar file) and R13 for this format, and keeps kept thing 20 (every agent run is measured and attributed to a work item and a stage). It uses `TokenCounts` and `EndReason` from `factory.domain.agent_runs` (F0001-S0008) and the ids of `factory.domain.identifiers` (`WorkItemId` and `Name`, built by F0001).

## Interface

`src/factory/domain/errors.py` (adds to the hierarchy)

```python
class CostRecordFormatError(FactoryError):
    line: int
    fault: str
    def __init__(self, line: int, fault: str) -> None: ...
```

`src/factory/domain/cost_records.py`

```python
class CostRecord(BaseModel):
    run: str                                  # 32 lowercase hexadecimal characters
    work_item: WorkItemId
    stage: Name
    role: Name
    attempt: NonNegativeInt
    status: Literal["started", "completed"]
    started_at: AwareDatetime
    duration_seconds: NonNegativeFloat | None = None
    end_reason: EndReason | None = None
    turns: NonNegativeInt | None = None
    tokens: TokenCounts | None = None
    cost_usd: Decimal | None = None           # not negative, finite
    image: str | None = None

    @property
    def ok(self) -> bool: ...
```

`src/factory/application/files.py` (adds to the module of F0002-S0003)

```python
class CostRecordReader(ABC):
    @abstractmethod
    def parse(self, text: str) -> list[CostRecord]: ...
    @abstractmethod
    def read(self, path: Path) -> list[CostRecord]: ...

class CostRecordWriter(ABC):
    @abstractmethod
    def render(self, records: Sequence[CostRecord]) -> str: ...
    @abstractmethod
    def write(self, path: Path, records: Sequence[CostRecord]) -> None: ...
```

`src/factory/adapters/cost_records_jsonl.py`

```python
class JsonLinesCostRecordReader(CostRecordReader):
    def __init__(self) -> None: ...

class JsonLinesCostRecordWriter(CostRecordWriter):
    def __init__(self) -> None: ...
```

`CostRecord` is frozen and forbids unknown fields; `started_at` is converted to UTC. The rules for the record; each has a criterion below:

- A `started` record has `duration_seconds`, `end_reason`, `turns`, `tokens` and `cost_usd` all `None`. A `completed` record has `duration_seconds` and `end_reason` set; its `turns`, `tokens` and `cost_usd` may be `None`, which means unknown.
- `run` matches `^[0-9a-f]{32}$`.
- `cost_usd`, when set, is at least 0 and finite: `Decimal("0")` is a cost, `Decimal("-0.01")`, `Decimal("NaN")` and `Decimal("Infinity")` are refused (F0001 treats a negative cost from the runtime as a reply that does not parse).
- The started/completed rule spans several fields, so it is a validation of the whole record and its error has no field location; `parse` reports it as `invalid record: <reason>`.
- `ok` is true exactly when `status` is `completed` and `end_reason` is `completed`.
- `CostRecordFormatError(line, fault)` carries both as attributes, has the message `line <line>: <fault>` and is a `FactoryError`.

The file format. A line is one JSON object, without spaces after `,` and `:`. This is the line of a completed record (`started_at` stands for the start time in UTC as `isoformat()` with the trailing UTC offset written as `Z`), then the line of a started record, a record of another run (a run id appears once in a file):

```json
{"run":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"<started_at>","duration_seconds":41.0,"end_reason":"completed","turns":7,"tokens":{"input":12,"output":3438,"cache_read":127336,"cache_creation":31343},"cost_usd":"0.3450","image":null}
{"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"<started_at>","duration_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
```

- `render(records)` writes one such line per record, in the order given, each ending with `\n`; the keys are in the order of the fields and the keys of `tokens` in the order of `TokenCounts`; an unknown value is `null`; `cost_usd` is the string of the `Decimal`; `render([])` is `""`. It raises `CostRecordFormatError` with the line number (counted from 1) of the second of two records that have the same `run` and the fault `duplicate run: <run>`.
- `parse(text)` reads each line that is not blank as one record; blank lines are ignored but count in the line numbers. `run`, `work_item`, `stage`, `role`, `attempt`, `status` and `started_at` are required; the other keys may be absent and are then `None`. It raises `CostRecordFormatError` with the number of the offending line and a fault that is one of: `not valid JSON`; `not a JSON object`; `unknown key: <key>`; `missing key: <key>`; `invalid <key>: <reason>` for a bad value, where `<key>` names a key inside `tokens` after a dot (`tokens.extra`, `tokens.output`, `tokens.input`); or `invalid record: <reason>` for a rule that spans keys. A JSON number or boolean for `cost_usd` is an `invalid cost_usd` fault: the cost is a string or `null`; so is a string that is not a finite decimal number of at least 0. The lines are judged in file order and the first fault ends the parse. On one line the faults come in this order: not valid JSON, not a JSON object, unknown key, missing key, invalid value, invalid record; only a line without any of them can be a `duplicate run: <run>` (the second line with a `run` seen before).
- `read(path)` is `parse` of the file read as UTF-8, and `[]` for a file that does not exist. `write(path, records)` writes the text of `render` as UTF-8 with `\n` line ends and replaces the file whole, an empty file for no records.

Tests: `tests/domain/test_cost_records.py`, `tests/domain/test_cost_record_errors.py`, `tests/adapters/test_cost_records_jsonl.py`. A test builds a run id from one repeated hexadecimal digit (`"a" * 32`, `"b" * 32`, `"c" * 32`), not as random hexadecimal text, so `make secrets` finds nothing. A test that constructs a model with an unknown field does so through a variable typed `type[BaseModel]`, and one that assigns to a frozen field does so with `setattr` (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `CostRecord` with `run="a" * 32`, a work item, stage, role, attempt 0, `status="started"` and a `started_at` is valid, and its `duration_seconds`, `end_reason`, `turns`, `tokens`, `cost_usd` and `image` are all `None`.
2. A `started` record with any one of `duration_seconds`, `end_reason`, `turns`, `tokens` or `cost_usd` set raises `ValidationError`.
3. A `completed` record without `duration_seconds`, or without `end_reason`, raises `ValidationError`; a `completed` record with `turns`, `tokens` and `cost_usd` all `None` is valid.
4. `run` of 31 characters, of 33 characters and with an upper-case letter raises `ValidationError`; `attempt` accepts 0 and refuses -1; `duration_seconds` accepts 0.0 and refuses -0.1; a naive `started_at` is refused; a `started_at` with a UTC offset of two hours east (`timezone(timedelta(hours=2))`) is stored as the same instant in UTC; `work_item` `F0002-X0001`, `stage` `Tests` and `role` `Tester` are refused.
5. `ok` is true only for `completed` with the end reason `completed`; it is false for `completed` with each of `no_result`, `time_limit`, `budget` and `died`, and for `started`.
6. `CostRecord` is frozen and refuses an unknown field with `ValidationError` (constructed through a variable typed `type[BaseModel]`).
7. A `completed` record accepts a `cost_usd` of `Decimal("0")` and `Decimal("0.3450")` and refuses `Decimal("-0.01")`, `Decimal("NaN")` and `Decimal("Infinity")` with `ValidationError`.
8. `CostRecordFormatError(3, "not valid JSON")` has `line == 3`, `fault == "not valid JSON"` and the message `line 3: not valid JSON`, and is a `FactoryError`.
9. One `render` of two records, a completed record with turns, tokens and a cost and the run `"a" * 32`, then a started record with the run `"b" * 32`, writes exactly the two lines of the example in that order, with `started_at` equal to `isoformat()` of the UTC time with the trailing UTC offset replaced by `Z`, each line ending with `\n`.
10. `render` of several records keeps their order with one line each, `render([])` is `""`, and `render` of two records with the same `run` raises `CostRecordFormatError` with `line == 2` and the fault `duplicate run: ` followed by the run.
11. `parse(render(records))` equals `records` for a started record, a completed record with a cost of `Decimal("0.3450")` and tokens, and a `time_limit` record whose `turns`, `tokens` and `cost_usd` are unknown: the unknown values come back as `None`, not 0, and the cost keeps its digits.
12. `parse` ignores blank and whitespace-only lines, and an error after a blank line reports the line number counted over all lines.
13. `parse` of a started line that holds only the seven required keys returns a started record whose other fields are `None`, and `parse` of a completed line that adds `duration_seconds` and `end_reason` but not `turns`, `tokens`, `cost_usd` and `image` returns a record whose `turns`, `tokens`, `cost_usd` and `image` are `None`, not 0.
14. `parse` raises `CostRecordFormatError` with the right line number for each of: a line that is not JSON (`not valid JSON`), a JSON list (`not a JSON object`), an extra key (`unknown key: extra`) and an extra key in `tokens` (`unknown key: tokens.extra`), an absent `run` (`missing key: run`), `status` `done` (a fault starting with `invalid status`), `turns` of -1 (a fault starting with `invalid turns`), `tokens` with `input` of -1 (a fault starting with `invalid tokens.input`), `tokens` without `output` (`missing key: tokens.output`), `cost_usd` given as the JSON number 0.34, as `true`, as the string `"abc"` and as the string `"-0.01"` (each a fault starting with `invalid cost_usd`), and a started record with a `cost_usd` (a fault starting with `invalid record:`).
15. On one line the faults come in a fixed order: a line with an extra key and no `run` gives `unknown key: extra`, a line with no `run` and `turns` of -1 gives `missing key: run`, and a line with `turns` of -1 on a started record that also has a `cost_usd` gives a fault starting with `invalid turns`; with a bad second line and a bad third line the fault is the second line's.
16. `parse` of two lines with the same `run` raises `CostRecordFormatError` with the number of the second line and the fault `duplicate run: ` followed by the run.
17. `read(path)` returns `[]` for a file that does not exist, the parsed records for a file in `tmp_path`, and raises `CostRecordFormatError` with the line number for a file with a broken line.
18. `write(path, records)` leaves a file whose bytes are the UTF-8 encoding of `render(records)`, replaces the old content whole, leaves an empty file for `[]`, and `read(path)` gives the records back.
19. `CostRecordReader` and `CostRecordWriter` are abstract base classes whose every operation is abstract, and `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter` are subclasses of them.
20. make check stays green.
21. docs: `docs/project-guide.md` describes the sidecar file (where it sits, the line format with an example, that an unknown measure is `null` and never 0, that the cost is a string and is not negative, that a run id is unique in a file, so that a record is completed by replacing its line); `docs/decisions.md` records why a cost is a string.

## Demo

```bash
uv run python -c "
import json
from datetime import UTC, datetime
from decimal import Decimal
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord
start = datetime(2026, 10, 12, tzinfo=UTC)
base = dict(run='a' * 32, work_item='F0002-S0007', stage='tests', role='tester', attempt=0, started_at=start)
started = CostRecord(**{**base, 'run': 'c' * 32}, status='started')
done = CostRecord(**base, status='completed', duration_seconds=41.0, end_reason='completed', turns=7, tokens=TokenCounts(input=12, output=3438), cost_usd=Decimal('0.3450'))
died = CostRecord(**{**base, 'run': 'b' * 32}, status='completed', duration_seconds=2400.0, end_reason='time_limit')
text = JsonLinesCostRecordWriter().render([started, done, died])
lines = text.splitlines()
print(len(lines), list(json.loads(lines[0])))
print(json.loads(lines[1])['cost_usd'], json.loads(lines[1])['tokens'])
back = JsonLinesCostRecordReader().parse(text)
print(back == [started, done, died], back[2].turns, back[2].tokens, back[2].cost_usd, back[2].ok)
"
```
Expect: three lines: `3 ['run', 'work_item', 'stage', 'role', 'attempt', 'status', 'started_at', 'duration_seconds', 'end_reason', 'turns', 'tokens', 'cost_usd', 'image']`, then `0.3450 {'input': 12, 'output': 3438, 'cache_read': 0, 'cache_creation': 0}`, then `True None None None False` (the run that hit its time limit round-trips with turns, tokens and cost still unknown).

```bash
uv run python -c "
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.domain.errors import CostRecordFormatError
try:
    JsonLinesCostRecordReader().parse('\n{not json}\n')
except CostRecordFormatError as error:
    print(error.line, error.fault, '|', error)
"
```
Expect: one line, `2 not valid JSON | line 2: not valid JSON`: the blank first line counts in the line number.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures are named (`domain/errors.py`, `domain/cost_records.py`, `application/files.py`, `adapters/cost_records_jsonl.py`). Each comment-stated behaviour has a criterion: UTC conversion (4), `Z` suffix and key order (9), `ok` (5), the `invalid record:` wording (14), the message format (8). `TokenCounts` in `agent_runs.py` matches the story: `input` and `output` are required and the cache fields default to 0.
   - Criteria: each can be tested by one test function. Every rule has its failing side: run pattern, attempt, duration, naive datetime, ids (4); started and completed field rules (2, 3); negative, NaN and infinite cost (7); duplicate run (10, 16); fault order (15); bad JSON, bad key and bad value cases (14).
   - Demo: both commands can be run and every `Expect:` line can be checked against the output. The second demo shows that the blank first line counts in the line number.
   - Architecture: the DTO and error are in domain, the ABCs in application, and the JSON-lines reader and writer in adapters, so the layers hold. Each ABC has one reader and one writer (R13, R15). The ABCs follow the project's interface convention.
   - Scope: it stays inside the feature's cost-record sidecar item. When a record is created, completed or summed is left to F0005, as `FEATURE.md` says.
