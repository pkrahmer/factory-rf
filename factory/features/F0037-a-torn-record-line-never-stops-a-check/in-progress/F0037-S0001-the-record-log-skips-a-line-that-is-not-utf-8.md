---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 339
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-20T06:45:59.225915Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T06:37:49.212370Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T06:37:49.218814Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T06:38:09.994305Z'
  stage: intake
  run: 89a0c1911e4340a6a5f75b12274dd9e0
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T06:38:30.484221Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T06:41:31.002285Z'
  stage: tests
  run: d65d9c7d431d4648be497ea5d9b826f7
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T06:41:51.815602Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T06:44:18.860290Z'
  stage: doing
  run: 985c272fe06b48b6960dbab5eda845bf
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T06:44:39.523330Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T06:45:38.771956Z'
  stage: review
  run: 6e393c52a5de40c59b322308166cdd52
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T06:45:59.225915Z'
  stage: docs
---

# The record log skips a line that is not UTF-8

## Description

`JsonLinesRecordLog.read` decodes its whole file with `read_text(encoding="utf-8")` before it looks at a line. A kill during an append can cut the last line inside a multibyte character, and then `read` raises `UnicodeDecodeError`. `KnownResults._read` catches only `OSError`, so every check and report of every stage fails with an error until a human repairs `/state/records/known-results.jsonl` (the feature's decision 1). This story makes `read` read the file as bytes, split them at `b"\n"` alone and decode each line on its own as strict UTF-8. A line that does not decode is skipped, as a blank line and a line that does not validate are skipped today, and every other line still counts, in file order. Splitting at `\n` alone also keeps a record whole whose text holds U+2028, U+2029 or U+0085, which `str.splitlines` cuts in two today (the feature's decision 5). The `RecordLog.read` docstring names the new skip. Unchanged: `append`, the skip of a line that does not validate, an `OSError` of reading (it still propagates), `KnownResults`, `DiskRecorder`, `StopPublisher`, the wiring and the four file paths. A record appended after a torn line still lands on the torn line's line and is skipped with it (the feature's decision 4); this story leaves that to a later one.

## Interface

`src/factory/adapters/record_log_jsonl.py` (`adapters`):

```python
class JsonLinesRecordLog[R: BaseModel](RecordLog[R]):
    @override
    def read(self) -> list[R]: ...
```

- `read()` is `[]` when the file does not exist.
- `read()` reads the file's bytes, splits them at `b"\n"` alone and decodes each line as UTF-8 with `errors="strict"`.
- A line that does not decode is skipped, wherever it stands in the file; so are a blank line and a line that does not validate. The records of the other lines are returned in file order.
- A `\r` before a `\n` stays in the line, and the line still validates.
- An `OSError` of reading the file (for example a directory at the path) propagates.

`src/factory/application/files.py` (`application`): the docstring of `RecordLog.read` becomes:

```python
    @abstractmethod
    def read(self) -> list[R]:
        """The records in file order; `[]` without a file.

        A line that is not UTF-8 or does not validate is skipped.
        """
```

Unchanged: `JsonLinesRecordLog.append`, `factory.application.known_results`, `factory.application.disk_records`, `factory.application.stops` and `factory.entry.wiring`.

Tests (the tester writes them):

- `tests/adapters/test_record_log_jsonl_torn.py` (new): criteria 1 to 4. The records are `ResultRecord`s (`factory.domain.known_results`) with `ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None)`, `at` 2026-10-20 00:00 UTC, `status="passed"`, `duration_seconds=1.0` and the `last_line` each row names; a torn line is the first bytes of a record's `model_dump_json().encode("utf-8")`, up to and inside the named character.
- `tests/application/test_known_results_torn.py` (new): criterion 5, with the rig of `tests/application/test_known_results.py` (`Rig`, `_rig`, `_answering`, `_result`). The tester may move them to a shared module under the standing leave of `CLAUDE.md` (*Tests*).
- `tests/adapters/test_record_log_jsonl.py` is not changed.

## Acceptance criteria

1. A torn last line is skipped and the whole lines before it count (rows of one parametrized test). The file holds the lines of two whole records, with the `last_line`s `check: green é` and `lint: green ✓`, then, without a line feed, the first bytes of a third record whose `last_line` is `x <character>`, cut inside that character. Rows: `é` cut after 1 of its 2 bytes; `€` cut after 1 of its 3 bytes; `€` cut after 2 of its 3 bytes; `😀` cut after 3 of its 4 bytes; and an ASCII cut, the bytes of a third record whose `last_line` is `x é`, up to and including `"last_line":"x`. Each row's `read()` equals the two whole records, in order, and raises nothing. One more row holds only the torn line cut inside `é`, and its `read()` is `[]`.
2. A line that does not decode is skipped wherever it stands (rows of one parametrized test). The file holds three lines, records A, B and C, each ending in `\n`, with `last_line`s `a é`, `b ✓` and `c 😀`. Rows: unchanged, `read()` gives `[A, B, C]`; B's line prefixed with the byte `0xff`, `read()` gives `[A, C]`; B's line with the bytes `0xc3 0x28` put right after the `b` of its `last_line` (inside the JSON string, where a decoding with replacement would give a record that validates), `read()` gives `[A, C]`; A's line prefixed with `0xff`, `read()` gives `[B, C]`; an empty line (one `\n` alone) between A and B, `read()` gives `[A, B, C]`.
3. A record whose text holds a character `str.splitlines` breaks at reads back whole (rows of one parametrized test). Rows: a `last_line` of `before`, then the character U+2028, U+2029 or U+0085, then `after`. Each row appends the record through `append`, the file then holds exactly one `b"\n"`, and `read()` equals `[record]`. One more row writes the line of a record with the `last_line` `plain` and `b"\r\n"` at its end directly to the file, and `read()` equals `[record]`.
4. An `OSError` of reading propagates: with a directory at the log's path, `read()` raises `IsADirectoryError`; with no file at the path, `read()` is `[]` (rows of one parametrized test).
5. `KnownResults.run("check")` on a known-results log with a torn last line neither raises nor logs (rows of one parametrized test, with the rig of `tests/application/test_known_results.py`). Row "after a pass": `run("check")` runs once and records its pass; then the first bytes of the line of a `ResultRecord` whose `last_line` is `x é`, cut after the first byte of `é`, are appended to the file without a line feed; the second `run("check")` returns a `CheckResult` with `reused` set and `last_line` `check: green`, the project commands were called once in all, and the factory log holds no line. Row "only a torn line": the file holds only the first bytes of the line of a `ResultRecord` whose `last_line` is `x é`, cut after the first byte of `é`; `run("check")` returns `_result("check", 0)`, the project commands were called once, and the factory log holds no line.
6. `make check` stays green.
7. docs: `docs/project-guide/processes-and-checks.md`, the paragraph on `RecordLog[R]`: `read()` "skips a line that does not validate" becomes "skips a blank line, a line that is not UTF-8 and a line that does not validate", and it says that `JsonLinesRecordLog` reads the file's bytes, splits them at `\n` alone and decodes each line on its own, so that a line cut inside a multibyte character by a kill is skipped and a record holding U+2028, U+2029 or U+0085 stays whole; and that a record appended after a torn line shares its line and is skipped with it. `docs/operator-guide.md`, *The records*: the last sentence of the paragraph after the table of `project-commands.jsonl`'s fields, "A line cut off by a kill is skipped when the file is read.", becomes one sentence: a line of any of the four record files that a kill cut, or that is not UTF-8, is skipped when the factory reads the file, so a damaged record file needs no repair. The rule for deleting `stops.jsonl` under *The stop records* stays as it is. `docs/decisions.md`: an entry *A record line that is not UTF-8 is skipped*, dated with the story, from the feature's decisions 1, 2, 3 and 5, rejecting a wider `except` in `KnownResults._read` (decision 2) and decoding with replacement (decision 3), with decision 4 as its open point. `README.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d/known-results.jsonl" <<'PY'
import sys
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.known_results import ResultKey, ResultRecord
path = Path(sys.argv[1])
log = JsonLinesRecordLog(path, ResultRecord)
key = ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None)
whole = ResultRecord(key=key, at=datetime(2026, 10, 20, tzinfo=UTC), status="passed", last_line="check: green ✓", duration_seconds=1.0)
log.append(whole)
line = whole.model_dump_json().encode()
with path.open("ab") as file:
    file.write(line[: line.index("✓".encode()) + 1])
print([record.last_line for record in log.read()])
PY
```
Expect: one line, `['check: green ✓']`, and no traceback.

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: `JsonLinesRecordLog.read` in `src/factory/adapters/record_log_jsonl.py` and the `RecordLog.read` docstring in `application/files.py` are named with exact signatures and text. I read the current code, and the constructor `(path, model)` and `ResultRecord` fields match the story's use. The rules are bytes, split at `\n` alone, strict per-line decode, `\r` kept, and `OSError` propagating.
   Criteria: each is one parametrized test with concrete rows. Every Interface rule has both sides. Torn lines cover 2-, 3- and 4-byte cuts and an ASCII cut. The skip covers a line at the start, the middle and the end, and a decoding-with-replacement trap. U+2028, U+2029 and U+0085 cover whole-record reading, with a `\r\n` row. A directory raises and a missing file gives `[]`. Criterion 5 covers `KnownResults` on a torn log. The `make check` and docs criteria are last.
   Smoke test: the command is runnable, since the Python snippet uses no pytest and so no `-q` issue. The `Expect:` line gives an exact printed list and no traceback, which can be checked against the output.
   Architecture: the change is inside the adapters layer, plus a docstring in application. No new dependency or wiring, and the callers are untouched, matching CLAUDE.md.
   Scope: it matches feature.md's Scope and decisions 1 to 5. The append-after-torn-line case (decision 4) and `KnownResults._read` are left out as the feature's Out of scope says. The existing test file is not changed, and the moves of the rig fall under the standing leave.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 5, one parametrized test per criterion. The rows are the ones each criterion names.

   - criterion 1: tests/adapters/test_record_log_jsonl_torn.py::test_a_torn_last_line_is_skipped_and_the_whole_lines_before_it_count
   - criterion 2: tests/adapters/test_record_log_jsonl_torn.py::test_a_line_that_does_not_decode_is_skipped_wherever_it_stands
   - criterion 3: tests/adapters/test_record_log_jsonl_torn.py::test_a_record_holding_a_line_break_other_than_a_line_feed_reads_back_whole (the rows are U+2028, U+2029 and U+0085 through `append`, plus the `\r\n` line written directly)
   - criterion 4: tests/adapters/test_record_log_jsonl_torn.py::test_an_error_of_reading_propagates_and_a_missing_file_reads_empty
   - criterion 5: tests/application/test_known_results_torn.py::test_a_torn_last_line_of_the_known_results_neither_raises_nor_logs
   - criteria 6 and 7 (`make check`, docs) have no test of their own.

   Files created: tests/adapters/test_record_log_jsonl_torn.py, tests/application/test_known_results_torn.py and tests/torn_record_support.py. The last is a shared helper with `KEY`, `result_record`, `line_of` and `torn_inside`, which both new modules use, so neither holds a copy.

   The rig (`Rig`, `_rig`, `_answering`, `_result`, `TIME_LIMIT`) is imported from `application.test_known_results`. I did not move it, so no earlier test file changed. tests/adapters/test_record_log_jsonl.py is unchanged.

   Rejected: separate test functions for the `\r\n` row and for the missing-file row. The criteria make them rows of the parametrized tests above.

   `make lint` is green.

   `make test` fails, with these failures in the tail it printed:
   - the u2029 and u0085 rows of criterion 3 (`splitlines` cuts the record today)
   - both rows of criterion 5 (the `UnicodeDecodeError` from `read`)

   The other new tests fail against the current `read_text`/`splitlines` reading in the same way. Every module imported; the runner reported no import errors. I skipped the type check, as the stage allows.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/application/test_known_results_torn.py::test_a_torn_last_line_of_the_known_results_neither_raises_nor_logs[only-a-torn-line]
6. factory: started doing as self.
7. coder: Built: `src/factory/adapters/record_log_jsonl.py`. `JsonLinesRecordLog.read` now reads the file's bytes and splits them at `b"\n"` alone. `_parse` takes a line's bytes and decodes them as strict UTF-8. A line that does not decode is skipped, and so are a blank line and a line that does not validate, as before. A `\r` before the `\n` stays in the text, and the JSON parser accepts it as whitespace. I also changed `src/factory/application/files.py`: the `RecordLog.read` docstring now has the Interface's exact text. `make check` is green.

   Main choice: each line is decoded on its own, inside `_parse`, so one bad line costs only itself. I rejected decoding the whole file with `errors="replace"` and then splitting. It would turn the `0xc3 0x28` case into a record that validates. It would also need `splitlines` or a str split, which brings back the U+2028/U+2029/U+0085 problem.

   Refactor pass: I read the diff (three small hunks) and found nothing to change.

   Noticed but not touched:
   - A record appended after a torn line still shares the torn line and is skipped with it (the feature's decision 4, left for a later story).
   - `KnownResults._read` still catches only `OSError`. The story leaves it unchanged, and with this change it no longer needs to catch more.

   The journal did not change the task's meaning, so `## Description` is unchanged.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I read: the work item, and `git diff main...HEAD -- . ':!factory'`. It changes `src/factory/adapters/record_log_jsonl.py` and `src/factory/application/files.py`, and adds `tests/adapters/test_record_log_jsonl_torn.py`, `tests/application/test_known_results_torn.py` and `tests/torn_record_support.py`.

   - Acceptance criteria: criteria 1 to 5 each have one parametrized test, with the rows the criterion names.
     - Criterion 1 has the é 1/2, € 1/3, € 2/3, 😀 3/4, ASCII-cut and only-torn rows.
     - Criterion 2 has the unchanged row, `0xff` before B, `0xc3 0x28` inside B's string, `0xff` before A, and the empty line.
     - Criterion 3 has U+2028, U+2029 and U+0085 written through `append`, and the `\r\n` row written directly. Each row checks that the file holds exactly one `\n`.
     - Criterion 4 has the directory row raising `IsADirectoryError` and the missing-file row giving `[]`.
     - Criterion 5 has the after-a-pass and only-a-torn-line rows. Both check one call of the project commands and an empty factory log, and the first checks that the second run is reused with `last_line` `check: green`.
     - Every Interface rule is tested on its failing side as well as its passing side. The Interface states no numeric limit.
     - The coder's journal entry (7) records `check: green`.
   - Architecture: the change stays inside the adapter, plus the docstring the Interface gives in `application/files.py`. There is no new import, wiring or dependency, and no other module calls a tool.
   - Security: there is no marker, secret, shell or string-built query. The read is strict decoding per line, and an `OSError` still propagates.
   - Quality: `read` splits the bytes at `b"\n"`, and `_parse` decodes each line as strict UTF-8 and skips one that fails. The comments say why. I found no dead code.
     - `make duplicates` reports 5 new findings, all in `claude_runtime`/`opencode_runtime` and `clock.py`. This diff touches none of those files.
     - The new shared module `tests/torn_record_support.py` is used by both new test modules. The rig is imported from `application.test_known_results`, as other test modules already import from test modules. No helper is copied.
   - Work item hygiene: the coder's entry names the main choice (decode each line on its own) and the rejected one (decode the whole file with `errors="replace"`). The Description matches what was built, and the docs criterion (7) still says what the reader needs to know.

   Earlier tests: none. The diff adds test files and changes, renames or deletes no test file that `main` already holds.
10. factory: started docs as self.
