# A torn record line never stops a check

## Goal

The factory keeps four records in JSON lines under `/state/records/`: `project-commands.jsonl`, `known-results.jsonl`, `stops.jsonl` and `disk.jsonl`. All four go through `JsonLinesRecordLog`, whose interface promises "A line that does not validate is skipped", because "a kill during a write can tear the last line". The promise breaks when the tear falls inside a multibyte UTF-8 character. `JsonLinesRecordLog.read` (`src/factory/adapters/record_log_jsonl.py`) decodes the whole file at once with `read_text(encoding="utf-8")`, so such a file raises `UnicodeDecodeError` before any line is parsed. `UnicodeDecodeError` is a `ValueError`, not an `OSError`, so `KnownResults._read` (`src/factory/application/known_results.py`), which turns an `OSError` into "no records", lets it through. `KnownResults.run` then raises for every check and report of every stage, and the dispatcher counts an error on every work item until a human repairs the file. A non-ASCII character in a record is ordinary: a `ResultRecord`'s `last_line` is the last line of a tool's output (a check mark, a quote, an emoji). Confirmed on 2026-10-20 against today's code in a throwaway container: a known-results file with one whole record and a last line cut inside `é` made `read()` raise `UnicodeDecodeError 'utf-8' codec can't decode byte 0xc3 in position 526: unexpected end of data` (found by the read-only review `planning/overnight/mess-scan-2026-10-20.md`, finding A1). The same reading has a second, quieter fault: it splits the text with `str.splitlines`, which also breaks at U+2028, U+2029 and U+0085, and pydantic writes those characters raw inside a JSON string, so a record holding one is cut in two and lost without a word (confirmed in the same container: `model_dump_json()` of a string with U+2028 gives one line that `splitlines` makes two). This feature reads the log as bytes, splits at `\n` alone and decodes each line on its own, so a line that is not UTF-8 is skipped as a line that does not validate is skipped today. It is for the operator, whose telemetry can no longer halt the factory, and for every stage that runs a check. Done when every story below is merged and `make check` is green.

## Scope

- `src/factory/adapters/record_log_jsonl.py`: `JsonLinesRecordLog.read` reads bytes, splits at `b"\n"`, decodes each line as strict UTF-8 and skips one that does not decode (S0001).
- `src/factory/application/files.py`: the `RecordLog.read` docstring names the undecodable line beside the line that does not validate (S0001).
- `tests/adapters/test_record_log_jsonl_torn.py` and `tests/application/test_known_results_torn.py` (new): the reading on both sides, and `KnownResults.run` on a torn log (S0001).
- `docs/project-guide/processes-and-checks.md`, `docs/operator-guide.md` and `docs/decisions.md`, from the story's docs criterion (S0001).

## Out of scope

- `KnownResults._read`, `DiskRecorder.last` and `StopPublisher.publish`: they read through `RecordLog.read`, whose promise now holds, so they keep their code (decision 2).
- A record appended after a torn line. `append` writes `<record>\n` at the end of the file, so the next record lands on the torn line's line and is skipped with it: one torn line costs the record after it too, as it does today for a tear in plain ASCII. Starting every append on a new line is a change of the writer, left as it is by the human (decision 4).
- The cost records sidecar (`JsonLinesCostRecordReader`): it is committed, written whole with `write_text`, and refuses a bad line with `CostRecordFormatError` on purpose; it already splits at `\n` alone.
- The stop records on `main` (`factory/stops.jsonl`, read through `GitCli.show_file`, which decodes with replacement, and `parse_stop_records`): they never raise on bytes.
- The review's C5 (the missing `__init__` docstring and `newline="\n"` on `append`) and B2 (the stop record line's second codec): other findings, other features.
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The record log skips a line that is not UTF-8

## The human's changes

None. Checked against `factory/pipeline.yml`: the coder writes `src/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. The story touches only those.

## Decisions taken for the human

1. The cause, found in the code and reproduced on 2026-10-20: `JsonLinesRecordLog.read` decodes the whole file before it looks at a line, and its caller `KnownResults._read` catches only `OSError`. The fix is at the cause, in the reader, so that the interface's promise holds for every caller; the callers stay as they are (S0001).
2. `KnownResults._read` keeps catching `OSError` alone. Widening it to `ValueError` would hide the symptom in one caller and leave `DiskRecorder.last` (no guard at all) and `StopPublisher.publish` (the tick catches `GitError`, `PushFailed` and `OSError`) with the same fault (S0001).
3. A line that does not decode is skipped whole, never decoded with replacement. A torn line decoded with U+FFFD would still fail validation, but a damaged byte inside an otherwise whole line would validate and give a record with a character that was never written; a skipped line is the rule the reader already has for damage (S0001).
4. Answered by the human (2026-10-20): left, no later feature. The question was whether a later feature makes `append` start on a new line when the file does not end in one, so that a torn line no longer takes the next record with it. It needs a read of the file's last byte before each append, which two writers can race; the loss is one record of telemetry per kill, so this feature leaves it (S0001 pins today's behaviour only where it must: the first run after a torn line runs the command).
5. The lines are split at `\n` alone, as `JsonLinesCostRecordReader.parse` already does and for its reason: `str.splitlines` also breaks at characters a JSON string may hold raw (U+2028, U+2029, U+0085), and such a record is lost today without a word. A `\r` before the `\n` stays part of the line, and JSON allows it as whitespace (S0001).
