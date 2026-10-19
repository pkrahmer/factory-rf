---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-19T21:41:09.467403Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T21:41:09.461905Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T21:41:09.467403Z'
  stage: intake
---

# The wired known results and disk records read back what they write

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`build_boundaries` gives `Boundaries.result_records` (S0002) and `Boundaries.disk_records` (F0012) each a `JsonLinesRecordLog` of its record model. S0002's wiring test appends a record through the wired log and reads it back through a second log that the test builds itself, and no test reads `disk_records` through the wiring at all. So the feature acceptance's `make mutants` found two surviving mutants that build these logs with no model: a wiring like that writes its lines and then fails at its first `read()` with an `AttributeError`. `KnownResults` catches only an `OSError` of the read, so that error would end every stage run that has a check or a report, instead of costing one run of the command. This story adds the missing criterion: each wired log reads back, through the same object, what was appended through it. No code change is expected. The command records under `RecordingProjectCommands` are left out: the wiring does not expose their log, and reaching it would change code.

## Interface

No module under `src/factory/` changes. `factory.entry.wiring` (`entry`): `build_boundaries` as it is. The rule this story pins:

- `boundaries.result_records` and `boundaries.disk_records` of `build_boundaries` each give `[]` from `read()` before anything is appended, and after one `append(record)` their `read()` gives `[record]`, equal to the record appended.

Tests (the tester writes them): `tests/entry/test_wiring_record_logs.py`, with the `local_settings` fixture of `tests/conftest.py`, `CREDENTIAL` of `tests/wiring_support.py` and a `FakeHostingService`, as `tests/entry/test_wiring_stop_records.py` builds the boundaries. No earlier test changes.

## Acceptance criteria

1. The wired logs read back through themselves (rows of one parametrized test, one row per log). `result_records` is tested with `ResultRecord(key=ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None), at=2026-10-12T12:00:00Z, status="passed", last_line="check: green", duration_seconds=12.5)`. `disk_records` is tested with `DiskRecord(at=2026-10-12T12:00:00Z, occasion="start", folders=[DiskUse(path="/work", free_bytes=0, used_bytes=None)])`. In each row, `read()` of the wired log gives `[]` before the append, and `[record]` after one `append(record)` through the same object.
2. `make check` stays green.
3. docs: none. The operator guide already names `records/known-results.jsonl` and `records/disk.jsonl`, and nothing a reader sees changes.

## Smoke test

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_wiring_record_logs.py 2>&1 | tail -n 1
```
Expect: a line that starts with `2 passed`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
