---
stage: doing
pr: 200
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A cost record names its instance

## Assignment (as of log entry 1)

The status map reads GitHub only (the human's word of 2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", item 6). A cost record already says which run, work item, stage, role and attempt it belongs to, when the run started, what it cost and on which image it ran (`CostRecord`, `src/factory/domain/cost_records.py`), but not which instance ran it, and two instances may work on one project. The human's word: `CostRecord` gains `instance`, the name of the instance that ran the agent run. It is optional when read, so every sidecar line written before this story stays valid with no migration, and it is set for every new record: `CostRecorder.begin` takes it from the instance's settings, as it takes `image` (the decision log's "Every tool of the machine's image is pinned, and its identity is generated at build"), and `complete` keeps it. The cost record writer leaves the key out when it is unset, so an earlier line is written back exactly as it was read when `begin` rewrites the sidecar, and the pinned lines of the earlier tests stay. This story follows S0007, which adds the journal's `at`, `stage` and `run` and writes the decision-log entry this story completes. No test of an earlier story changes (FEATURE decision 28).

## Interface

`src/factory/domain/cost_records.py`: `CostRecord` gains `instance: Name | None = None` (`factory.domain.identifiers`), its last field, after `image`. The model stays frozen and refuses unknown keys. The rule on measures (`started` and `completed`) does not concern it: either status may carry it. The class docstring names it.

`src/factory/adapters/cost_records_jsonl.py`: `_line_of_record` writes `instance` as the last key when it is set (`..."image":"build-7","instance":"shakedown"}`) and leaves the key out when it is `None` (the line ends `..."image":null}` as today). Every other key is written as today. The reader is unchanged: a line without the key, or with `"instance":null`, reads with `None`; a value that is not a `Name` is `invalid instance: <reason>`, the reader's existing fault form.

`src/factory/application/costs.py`: `CostRecorder.begin` sets `instance=` the `instance` of `self._boundaries.settings`, and `None` when the `Boundaries` holds no settings (as `_image()` does for `image`). `complete` keeps it (it copies the record's fields). Nothing else changes; the `Boundaries` of `tests/conftest.py` hold no settings, so the records of the existing tests have no instance.

Tests: new modules `tests/domain/test_cost_record_instance.py`, `tests/adapters/test_cost_records_jsonl_instance.py` and `tests/application/test_cost_instance.py` (the last after `tests/application/test_cost_image.py`, with `InstanceSettings(repository_url=..., instance=..., image=...)` and `dataclasses.replace(boundaries, settings=...)`). No earlier test changes.

## Acceptance criteria

1. A cost record without `instance` is valid and has `instance` `None`; one with `instance` = `shakedown-podman` has it; `Shakedown` (not a `Name`) is refused. A `started` and a `completed` record may each carry it. One parametrized test holds every row (the wrong-typed value constructed through a variable typed `type[BaseModel]`).
2. The writer writes `"instance":"shakedown"` as the last key of a line whose record has it, and no `instance` key for a record without it; the line of a record without it is exactly the line of today. One parametrized test holds both rows, each with `parse(render(records)) == records`: the records without it are `_completed()` and `_started()` of `tests/adapters/test_cost_records_jsonl.py`, rendering to its constants `COMPLETED_LINE` and `STARTED_LINE`, and the records with it are the same two with `model_copy(update={"instance": "shakedown"})`; the helpers and constants are imported from that module (`from adapters.test_cost_records_jsonl import ...`), not copied.
3. The reader reads a line without the key and a line with `"instance":null` with `None`, a line with `"instance":"shakedown"` with that name, and refuses `"instance":"Shakedown"` with `CostRecordFormatError` and the fault `invalid instance: ...`. One parametrized test holds the rows.
4. `CostRecorder.begin` under settings with `instance` = `factory-1` gives a `started` record with `instance` `factory-1`, and `complete` keeps it in the `completed` record; the sidecar the stage launch writes has it (`launched.cost.records[-1].instance`). Without settings the record has `instance` `None`. One parametrized test holds the rows. It launches the stage with `_launch` of `tests/application/test_cost_image.py` and builds the settings with that module's `_settings` (whose `instance` is `factory-1`), both imported (`from application.test_cost_image import ...`), not copied.
5. What must still hold: the earlier sidecar lines and bills read and sum as before (the tests of `tests/adapters/test_cost_records_jsonl.py`, `tests/adapters/test_cost_records_jsonl_model_seconds.py`, `tests/domain/test_cost_records.py`, `tests/domain/test_bills.py`, `tests/application/test_costs.py` and `tests/application/test_cost_image.py` pass).
6. `make check` stays green.
7. docs: the project guide's *Cost records* names `instance` in the record's fields (a `Name`, optional when read, set by `begin` from the settings and kept by `complete`, `None` without settings) and says that the line leaves the key out when it is unset, with one example line that carries it beside the two existing ones; the bullet *Created at the start* of *When a record is created, completed and committed* says `begin` sets `instance` and `image` from the settings (it says today that `image` is `None` there, which `begin` already does not do). The decision-log entry S0007 wrote ("Journal records say when, in which stage and from which run; cost records on which instance") gets the cost record's part: why the instance comes from the settings like `image`; why its key is left out when unset while `image` is written `null` (`begin` rewrites the whole sidecar, so a line the writer of today wrote is written back unchanged, and the lines written before this story stay as they were); and that an instance built before this story refuses a line with the key, so the instances of one project are upgraded together. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.cost_records import CostRecord
fields = dict(work_item='F0014-S0008', stage='tests', role='tester', attempt=0, status='started', started_at=datetime(2026, 10, 17, 20, 31, tzinfo=UTC), image='build-7')
records = [CostRecord(run='b' * 32, instance='shakedown', **fields), CostRecord(run='c' * 32, **fields)]
print(JsonLinesCostRecordWriter().render(records), end='')
"
```
Expect: two lines. The first: `{"run":"` and 32 times `b`, then `","work_item":"F0014-S0008","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-17T20:31:00Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":"build-7","instance":"shakedown"}`. The second: the same with 32 times `c` as the run, ending `"cost_usd":null,"image":"build-7"}`, with no `instance` key.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_cost_record_instance.py tests/adapters/test_cost_records_jsonl_instance.py tests/application/test_cost_instance.py tests/adapters/test_cost_records_jsonl.py tests/application/test_cost_image.py tests/application/test_costs.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted.
   - Interface: names concrete modules and signatures: `CostRecord.instance: Name | None = None` (last field, after `image`) in `src/factory/domain/cost_records.py`; the key order and omit-when-unset rule in `_line_of_record` of `src/factory/adapters/cost_records_jsonl.py`; `CostRecorder.begin` taking `settings.instance` in `src/factory/application/costs.py`, `None` without settings. I checked that `Name` exists in `identifiers.py` and that `costs.py` already has `_image()` for `image`. The reader is unchanged, with the existing `invalid instance: <reason>` fault form. The three new test modules do not exist yet.
   - Criteria: each is testable by one parametrized test. Every rule has its failing side: `Shakedown` refused (1, 3), an unset instance leaves the key out (2), no settings gives `None` (4). Criteria 5 and 6 are the regression and gate criteria. The helpers and constants criteria 2 and 4 import exist: `_completed`, `_started`, `COMPLETED_LINE` and `STARTED_LINE` in `tests/adapters/test_cost_records_jsonl.py`, and `_settings` and `_launch` in `tests/application/test_cost_image.py`. I did not open `INSTANCE`, so I did not confirm it equals `factory-1`.
   - Demo: both commands are runnable. The expected line ends are checkable against the output, and the pytest run names the new modules and the earlier ones.
   - Architecture: the domain model, the adapter writer and the application recorder each stay in their layer, and the instance comes from the settings through `Boundaries`, as `image` does. Nothing new is wired.
   - Scope: this is S0008 of the feature (FEATURE scope bullet and decision 28). It follows S0007 and changes no earlier test (decision 28, "S0008 needs no leave"). Its docs criterion completes the decision-log entry S0007 writes.
3. tester: I wrote red tests for the cost record's `instance`. Each new criterion has one parametrized test:
   - criterion 1: tests/domain/test_cost_record_instance.py::test_a_cost_record_carries_an_optional_instance_name. Rows: without it (None), a started record with `shakedown-podman`, a completed record with `shakedown-podman`, and `Shakedown` refused with ValidationError. Every row is built through a `type[BaseModel]` variable.
   - criterion 2: tests/adapters/test_cost_records_jsonl_instance.py::test_the_writer_writes_the_instance_last_only_when_it_is_set. Rows: `_completed()` and `_started()` render exactly to `COMPLETED_LINE` and `STARTED_LINE`. The same two records with `model_copy(update={"instance": "shakedown"})` render to those lines with `,"instance":"shakedown"` before the closing brace. Both rows also check `parse(render(records)) == records`. The helpers and constants are imported from `adapters.test_cost_records_jsonl`, not copied.
   - criterion 3: tests/adapters/test_cost_records_jsonl_instance.py::test_the_reader_reads_the_instance_or_refuses_one_that_is_not_a_name. Rows: no key gives None; `"instance":null` gives None; `"shakedown"` gives the name; `"Shakedown"` raises CostRecordFormatError with a fault starting `invalid instance: `. The lines are built from the imported `REQUIRED`.
   - criterion 4: tests/application/test_cost_instance.py::test_a_cost_record_names_the_instance_of_the_settings_and_keeps_it_when_completed. Rows: `_settings("build-7")` (instance `factory-1`) and no settings (None). Each row checks the `begin` record, the `complete` record and `launched.cost.records[-1]`. `_launch` and `_settings` are imported from `application.test_cost_image`.
   - criterion 5: no new test. It is held by the existing modules it names, which I left unchanged.
   - criteria 6 and 7: the gate and the docs. They get no tests.

   Files created: tests/domain/test_cost_record_instance.py, tests/adapters/test_cost_records_jsonl_instance.py, tests/application/test_cost_instance.py.

   Every module imports, so there were no collection errors. The new tests fail for the right reason: `CostRecord` has no `instance` field yet, so constructing it is refused or reading `.instance` fails. The writer and recorder rows fail the same way. `make lint` is green. I skipped the type check, as this stage allows. No criterion needed interpreting.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/domain/test_cost_record_instance.py::test_a_cost_record_carries_an_optional_instance_name[completed-with]
