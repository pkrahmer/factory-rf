---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 289
comments_read: []
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T21:41:28.793183Z'
  stage: intake
  run: 00469f4ea1a9460e8571778f8b2f6978
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T21:41:50.516176Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T21:44:03.189350Z'
  stage: tests
  run: 68ce178efcbd44c6840658807086c092
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T21:44:23.800167Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T21:46:20.348776Z'
  stage: doing
  run: 436fb0f0e12e4c8ba23858e51c5fab5f
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
3. intake: accepted
   Interface: no module under `src/` changes. `factory.entry.wiring.build_boundaries` exists and sets `result_records` (`JsonLinesRecordLog(..., ResultRecord)`) and `disk_records` (`JsonLinesRecordLog(..., DiskRecord)`). The rule is stated concretely: `read()` gives `[]` before an append and `[record]` after one. The named test helpers exist: `CREDENTIAL` in `tests/wiring_support.py`, `local_settings` in `tests/conftest.py`, and `tests/entry/test_wiring_stop_records.py` as the pattern. `DiskUse` has path, free_bytes and used_bytes as the story's example uses them. I did not check `ResultRecord`, `ResultKey` or `DiskRecord` field by field.
   Criteria: criterion 1 is one parametrized test with a row per log, and both sides (before and after the append) are stated. The Interface states no limit, rejected input or default beyond that. `make check` and `docs: none` are the last two, as the form requires.
   Smoke test: the command is runnable and the `Expect:` line (`2 passed`) can be checked against the output. It matches the two rows.
   Architecture: tests only, in `tests/entry/`, which mirrors `factory.entry`. Nothing is faked except the hosting service, as `CLAUDE.md` allows.
   Scope: `feature.md` lists only S0001 and S0002 under Stories, and its Scope names `result_records` but not `disk_records` (F0012's). This story is the feature acceptance's proposal and it is test-only, so I accepted it. If you would rather add it to the feature's story list, that edit is yours.
4. factory: started tests as self.
5. tester: Wrote the test of criterion 1 as one parametrized test with one row per wired log. It builds the boundaries the way `tests/entry/test_wiring_stop_records.py` does: the `local_settings` fixture, `CREDENTIAL` from `tests/wiring_support.py` and a `FakeHostingService`. In each row a typed helper calls `read()` on the wired log, then `append(record)`, then `read()` again, all through the same object. The test checks that the first read gives `[]` and the second gives `[record]`. The two records are the ones the criterion gives.

   criterion 1: tests/entry/test_wiring_record_logs.py::test_a_wired_record_log_reads_back_what_was_appended_through_it[result_records] and [disk_records]
   criterion 2 (`make check` green): no test; the factory's checks cover it.
   criterion 3 (docs: none): no test.

   Files created: tests/entry/test_wiring_record_logs.py. No earlier test changed.

   Modules the test run could not import: none. The story expects no code change, and `build_boundaries` already gives both logs their models, so both rows pass now instead of failing. That is what the description says: the test catches the surviving mutants that build these logs with no model, and it does not ask the coder for anything.

   Runs: `make test` is green (40.0 s, coverage 99.12 %) and `make lint` is green. I also ran `make types`, which the stage says to skip, to confirm that the typed rows pass `mypy --strict`; it is green.

   I set one step aside: I ran the new test file once on its own, to check the smoke test's `2 passed` line. The stage asks for a single `make test` run only.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.5 s)
6. factory: started doing as self.
7. coder: I didn't change any code, which is what the story expected. I ran `make check` before doing anything and it was already green (`check: green`, test 39.0 s, coverage 99.12 %). The tester's test `tests/entry/test_wiring_record_logs.py` passes against `build_boundaries` in `src/factory/entry/wiring.py` as it stands. That module already builds `result_records` with `JsonLinesRecordLog(..., ResultRecord)` and `disk_records` with `JsonLinesRecordLog(..., DiskRecord)`.

   Paths built: none. My diff outside `factory/` and `tests/` is empty, so the refactor step had nothing to change.

   Main choice: I left `src/factory/` untouched. The alternative I rejected was adding something to the wiring so this story has a code change of its own. The interface says no module under `src/factory/` changes, and the test only pins behaviour that already exists.

   What the journal changed: nothing in the meaning of the task, so I did not rewrite `## Description`.

   Noticed but not touched: the log of the command records under `RecordingProjectCommands` is still not read back through the wiring by any test. The description leaves that out because reaching the log would change code. `feature.md` does not list this story; intake already pointed that out to the human.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
