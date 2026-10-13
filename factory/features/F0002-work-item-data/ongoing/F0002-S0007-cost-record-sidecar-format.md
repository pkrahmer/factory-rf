---
stage: doing
pr: 34
blocked: null
comments_seen: 2
round: 1
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
3. tester: wrote red tests for criteria 1–19, one or more test functions per criterion.
      - criterion 1: tests/domain/test_cost_records.py::test_a_started_record_has_no_measures
      - criterion 2: tests/domain/test_cost_records.py::test_a_started_record_with_a_measure_is_refused_as_a_whole (parametrized over the five measures; also asserts the error has no field location, `loc == ()`, as the Interface states)
      - criterion 3: tests/domain/test_cost_records.py::test_a_completed_record_needs_duration_and_end_reason, ::test_a_completed_record_may_leave_turns_tokens_and_cost_unknown
      - criterion 4: tests/domain/test_cost_records.py::test_record_fields_keep_their_limits (run 32/31/33/upper case, attempt 0/-1, duration 0.0/-0.1, naive started_at, bad ids; also turns 0/-1 because the Interface types it NonNegativeInt, per CLAUDE.md Tests), ::test_started_at_is_stored_in_utc
      - criterion 5: tests/domain/test_cost_records.py::test_ok_only_for_a_run_that_completed
      - criterion 6: tests/domain/test_cost_records.py::test_a_record_is_frozen_and_refuses_unknown_fields
      - criterion 7: tests/domain/test_cost_records.py::test_a_cost_is_finite_and_not_negative
      - criterion 8: tests/domain/test_cost_record_errors.py::test_a_cost_record_format_error_names_its_line_and_fault
      - criterion 9: tests/adapters/test_cost_records_jsonl.py::test_render_writes_the_lines_of_the_format
      - criterion 10: tests/adapters/test_cost_records_jsonl.py::test_render_keeps_the_order_with_one_line_per_record, ::test_render_of_no_records_is_empty, ::test_render_refuses_a_run_twice
      - criterion 11: tests/adapters/test_cost_records_jsonl.py::test_parse_of_render_gives_the_records_back_with_unknowns_and_digits
      - criterion 12: tests/adapters/test_cost_records_jsonl.py::test_parse_ignores_blank_lines, ::test_parse_counts_blank_lines_in_the_line_number
      - criterion 13: tests/adapters/test_cost_records_jsonl.py::test_parse_of_the_required_keys_leaves_the_rest_unknown
      - criterion 14: tests/adapters/test_cost_records_jsonl.py::test_parse_names_a_broken_line_and_its_fault (exact faults), ::test_parse_names_a_bad_value_and_its_key (fault prefixes). In every case the bad line is line 2, after a valid line.
      - criterion 15: tests/adapters/test_cost_records_jsonl.py::test_parse_reports_the_first_fault_of_a_line, ::test_parse_reports_the_first_broken_line
      - criterion 16: tests/adapters/test_cost_records_jsonl.py::test_parse_refuses_a_run_twice (duplicate on line 3, after a different run on line 2)
      - criterion 17: tests/adapters/test_cost_records_jsonl.py::test_read_of_a_missing_file_is_no_records, ::test_read_parses_a_file, ::test_read_names_the_broken_line_of_a_file
      - criterion 18: tests/adapters/test_cost_records_jsonl.py::test_write_leaves_the_rendered_text_and_reads_back, ::test_write_replaces_the_old_content_whole, ::test_write_of_no_records_leaves_an_empty_file
      - criterion 19: tests/adapters/test_cost_records_jsonl.py::test_reader_and_writer_implement_abstract_interfaces
      Files created: tests/domain/test_cost_records.py, tests/domain/test_cost_record_errors.py, tests/adapters/test_cost_records_jsonl.py.
      `make test`: the 3 new modules fail at collection because the modules and names under test do not exist yet: factory.domain.cost_records, CostRecordFormatError in factory.domain.errors, CostRecordReader/CostRecordWriter in factory.application.files, factory.adapters.cost_records_jsonl. `make lint` is green. The type check was skipped, as the stage skill says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented the cost record and its JSON-lines sidecar format. `make check` is green and both demos print what their `Expect:` lines say.
      - Built:
        - `src/factory/domain/cost_records.py`: `CostRecord`. It is frozen, forbids unknown fields and converts `started_at` to UTC. `run` uses the `RunId` pattern. `cost_usd` is a `Decimal` with `ge=0` and `allow_inf_nan=False`. A model validator applies the started/completed rule to the whole record, so its error has `loc == ()`. `ok` is true only for a completed record whose end reason is `completed`.
        - `CostRecordFormatError(line, fault)` added to `src/factory/domain/errors.py`.
        - `CostRecordReader` and `CostRecordWriter` ABCs added to `src/factory/application/files.py`.
        - `src/factory/adapters/cost_records_jsonl.py`: `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter`. Parsing checks JSON, then that the line is an object, then validates with pydantic, then checks for a duplicate run. Rendering writes `model_dump(mode="json")` in field order, `started_at` with `Z`, `cost_usd` as `str(Decimal)` and separators without spaces.
      - Main decision: "the cost is a string or null" is a before-validator on `CostRecord.cost_usd`. It accepts only `Decimal`, `str` or `None` and refuses every int, float or bool. Because the check runs inside the same pydantic pass, a wrong-typed cost ranks as an invalid value in field order and the fixed fault order on a line holds without special cases. It also means Python code can never hand the record a float cost.
      - Rejected: a type check on the cost in the adapter before validation. It would have reported `invalid cost_usd` ahead of an unknown or missing key on the same line, which breaks the required fault order, or it would have needed a second ranking pass.
      - `parse` splits on `\n` only, not with `splitlines`. `splitlines` also breaks at characters such as U+2028, which can appear unescaped in a JSON string, and that would shift the line numbers.
      - Refactor (9439b37): `work_item_markdown.py` had the same pydantic fault-ranking code (`_key_path`, `_rank`, `_fault`, `_first_fault`). I moved it to the new `src/factory/adapters/validation_faults.py` as `first_fault(error, whole)`, where `whole` is `"state"` for work items and `"record"` for cost records. The work item reader's behaviour is unchanged and its tests stay green. I also put the duplicate-run check used by both `parse` and `render` into one helper, `_check_new_run`.
      - Not touched: the docs criterion (21) is the documenter's job.
      - Commits: 755a215 (feature), 9439b37 (refactor).

   `make check`: check: green
5. reviewer: one finding, sent back. Criteria 1–19 each have a test that matches them, and the coder reported `make check` green. The limits the Interface states are tested on both sides. The layers hold: the DTO and error are in domain, the ABCs in application, the reader, writer and `validation_faults.py` in adapters. Security is clean and there are no silencing markers. Moving the fault ranking into `validation_faults.py` keeps the work item reader's behaviour.
      1. `src/factory/adapters/cost_records_jsonl.py:20` and `:42`, with `src/factory/domain/cost_records.py:38`: the format says each line is one JSON object, but the reader and the writer both accept text that is not JSON. `json.loads` by default accepts the non-standard constants `NaN`, `Infinity` and `-Infinity`. `duration_seconds` is `NonNegativeFloat`, which allows `inf`. So a line with `"duration_seconds":Infinity` parses into a record when it should fail with `not valid JSON`. Going the other way, a record with `duration_seconds=float("inf")` renders a line that contains `Infinity`. `jq` and other strict JSON readers would refuse that file.
         Fix, reader: give `json.loads` a `parse_constant` that raises, and report the line as `not valid JSON`. This stays inside the Interface.
         Fix, writer: make `duration_seconds` finite in the domain (`Field(ge=0, allow_inf_nan=False)`, the same as `cost_usd`). This tightens the Interface and needs a criterion and a test for the refused side, so the coder should ask the human (`question`) whether to make that change, or to render with `allow_nan=False` and raise `CostRecordFormatError` instead.
         The story has a gap here: it states no finiteness rule for `duration_seconds`, so no criterion covers the refused side.
6. coder: coder (round 1): fixed the reader side of the review finding. The writer side changes the Interface, so I am asking before doing it.

   Done (dfd95fb): in `src/factory/adapters/cost_records_jsonl.py`, `json.loads` now gets a `parse_constant` that raises. A line with `NaN`, `Infinity` or `-Infinity` (for example `"duration_seconds":Infinity`) is now reported as `not valid JSON` instead of becoming a record. This stays inside the Interface. `make check` is green. No test covers this yet, because the criteria do not name the case.

   Open question: `duration_seconds` is typed `NonNegativeFloat`, which accepts `float("inf")`. `render` then writes a line that contains `Infinity`, which is not JSON. There are two ways to close this:
     A. (my choice) Make `duration_seconds` finite in the domain with `Field(ge=0, allow_inf_nan=False)`, the same way `cost_usd` already works. Two criteria would change:
        - criterion 4 becomes "`duration_seconds` accepts 0.0 and refuses -0.1, `float('inf')` and `float('nan')`";
        - criterion 14 also requires a line with `"duration_seconds":Infinity` to give `not valid JSON`.
        An infinite duration is never a real measure, and this keeps both the record and the file strict JSON.
     B. Leave the type alone and render with `allow_nan=False`, so `render` raises `CostRecordFormatError(line, "not valid JSON")` for such a record. This adds a second fault to `render` beyond `duplicate run`, and the record itself can still hold a value that cannot be written to the file.

   If you choose A (or B), I will end with `tests` and name the test changes so the tester adds them, then implement the domain change.
7. human (pull request comment, 2026-10-13): A: make `duration_seconds` finite in the domain with `Field(ge=0, allow_inf_nan=False)`, as `cost_usd` already is (F0002's cost rule: a measure is unknown or a finite value of at least 0). Change criterion 4 to "`duration_seconds` accepts 0.0 and refuses -0.1, `float('inf')` and `float('nan')`", and add to criterion 14 that a line with `"duration_seconds":Infinity` gives `not valid JSON`. End with `tests` and name the two test changes; the tester adds them, then implement the domain change. Your reader change (`parse_constant` that raises) stays.
