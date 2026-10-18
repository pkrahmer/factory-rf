---
stage: done
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
4. coder: cost records now say which instance ran them. Commit ef7dff29.
   - `src/factory/domain/cost_records.py`: `CostRecord` has a new last field, `instance: Name | None = None`, after `image`. The class docstring now names `image` and `instance`. The rule that only completed records carry measures does not touch it, so a started or a completed record may have it.
   - `src/factory/adapters/cost_records_jsonl.py`: when `instance` is `None`, `_line_of_record` drops the key from the dumped fields. So a record without it gives the same line as before, and a record with it gets `"instance":...` as the last key. The reader is unchanged: the existing `first_fault` form gives `invalid instance: ...`.
   - `src/factory/application/costs.py`: `CostRecorder.begin` reads `self._boundaries.settings` once and sets both `image` and `instance` from it, `None` when there are no settings. That replaces the private `_image()` helper, which would otherwise have needed an `_instance()` twin. `complete` keeps the instance with no change, because `_completed` copies `record.model_dump()`.
   - Main decision: drop the key in the writer when `instance` is `None`. The alternative was a model-level `exclude_none`, which I rejected because it would also drop `image` and the null measures, which must still be written as `null`.
   - Refactor pass: the diff is 12 lines and needed nothing beyond folding `_image()` into `begin`, which the feature commit already does. So there is no separate refactor commit.
   - Checks: `make check` is green (coverage 99.47 %). The first demo command prints the two lines the ticket expects.
   - Not touched: the docs for criterion 7 belong to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Criteria 1–4: each has one parametrized test that tests what it is named after. 1 (`tests/domain/test_cost_record_instance.py`): rows for no instance, a started record with it, a completed record with it, and `Shakedown` refused, all built through `type[BaseModel]`. 2 (`tests/adapters/test_cost_records_jsonl_instance.py`): `_completed`, `_started`, `COMPLETED_LINE` and `STARTED_LINE` are imported, not copied; the line without an instance is exactly today's line, the line with one ends `,"instance":"shakedown"}`, and both rows round-trip. 3: rows for no key, `null`, a name, and `Shakedown` refused with `CostRecordFormatError` and the fault `invalid instance: `. 4 (`tests/application/test_cost_instance.py`): `_launch` and `_settings` are imported from `application.test_cost_image`, and `INSTANCE` there is `factory-1`; each row checks the `begin` record, the `complete` record and `launched.cost.records[-1]`, with settings and without. Criterion 5 is held by the earlier modules, which the diff leaves unchanged. The coder's entry records `make check` as green.
      - Architecture: the field is `Name | None` in the domain. The omit-when-`None` rule sits in the adapter's `_line_of_record`, and the comment beside it says why. `begin` reads `Boundaries.settings` in the application layer. No new import crosses a layer.
      - Security: no markers, secrets or string-built commands. The reader still validates through Pydantic at the boundary.
      - Quality: `begin` folds the private `_image()` into one `settings` local, so there is no `_instance()` twin. No dead code is left. The `CostRecord` docstring names both `image` and `instance`. `make duplicates` reports 0 new.
      - Ticket hygiene: the coder's entry names the main decision (drop the key in the writer) and the rejected alternative (a model-wide `exclude_none`, which would also drop `image` and the null measures). The Assignment matches what was built. Criterion 7 still describes what the documenter must write.
6. documenter: Docs for criterion 7 are written. I found no findings: the diff matches the Interface.
   - `docs/project-guide.md`, *Cost records*:
     - The field list now names `instance`: a `Name`, optional when read, set by `begin` from the settings, kept by `complete`, `None` without settings, and either status may carry it.
     - The line-format paragraph says `instance` is the last key and that the writer leaves it out when it is `None`, while every other unset field is written `null`.
     - A third example line carries `instance`.
   - `docs/project-guide.md`, *Created at the start*: `begin` now sets `image` and `instance` from the settings. The old text said `image` was `None` there, which was already wrong. The *Completed at the end* bullet says `complete` keeps both and that both are `None` without settings.
   - `docs/decisions.md`: the S0007 entry gets three bullets for the cost record's part:
     - why `instance` comes from the settings, like `image`;
     - why its key is left out when unset: `begin` rewrites the whole sidecar, so a `null` would change every old line;
     - that an instance built before this story refuses a line with the key (`unknown key: instance`), so the instances of one project are upgraded together.
     - I also changed the entry's intro sentence, "The cost record's `instance` is S0008.", to point at those bullets.
   - Checks: I ran the three-line example through the reader and writer, and it renders back unchanged. `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only docs.
   - Cross-read: the project guide's *Bills* and the journal section, and the README. No stale text found.
   - Stale and unrelated: none seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands ran from the repository root and met their `Expect:` lines. No findings.

   1. Rendering two started records, one with `instance` and one without:
   ```
   {"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0014-S0008","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-17T20:31:00Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":"build-7","instance":"shakedown"}
   {"run":"cccccccccccccccccccccccccccccccc","work_item":"F0014-S0008","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-17T20:31:00Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":"build-7"}
   ```
   Met. The output has two lines. In the first, `"instance":"shakedown"` is the last key, after `"image":"build-7"`. The second line is the same apart from its run of 32 `c`s, ends `"cost_usd":null,"image":"build-7"}` and has no `instance` key. The command exited with 0.

   2. pytest over the three new modules and the three earlier ones:
   ```
   ........................................................................ [100%]
   72 passed in 4.98s
   ```
   Met. The last line names `72 passed`, with no `failed`, `error` or `skipped` count.

   Cross-check against the acceptance criteria:
   - Criterion 2: the writer puts `instance` last when it is set and leaves the key out when it is not. Command 1 shows this.
   - Criteria 1, 3 and 4: the reader, model and recorder are covered by the new tests in command 2, which passed.
   - Criterion 5: the earlier modules it names that command 2 ran (`test_cost_records_jsonl`, `test_cost_image` and `test_costs`) passed.

   Not run here: `tests/adapters/test_cost_records_jsonl_model_seconds.py`, `tests/domain/test_cost_records.py` and `tests/domain/test_bills.py`, which criterion 5 also names. The demo does not list them, and the factory's `make check` covers them. Criteria 6 and 7 are the factory's checks after this stage and the documenter's recorded `make check: green` and `documents ok`. Nothing in the demo contradicts any criterion.
8. done (pull request merged); cost: 6 runs, 4.3 min, 40 turns, 120k tokens in (649k more from cache), 14k out, $1.10
