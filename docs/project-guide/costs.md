# Costs

This file covers cost records and bills; read the index, `README.md`, first.

## Cost records

One agent run is one cost record: a JSON line in the sidecar file beside the work item, `cost_records_path(path)` (`<work item>.costs.jsonl`, see *Identity, order and places of work items*). The format is `CostRecord` (`factory.domain.cost_records`), the interfaces `CostRecordReader` and `CostRecordWriter` (`factory.application.files`), and `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter` (`factory.adapters.cost_records_jsonl`). How a bill is summed is in *Bills*; a crashed stage's records are discarded with the stage.

### When a record is created, completed and committed

`CostRecorder` (`factory.application.costs`) keeps the records of one run in a `CostRun` (frozen, no unknown keys): `path` (the sidecar), `run` (the record's id) and `records` (every record of the work item, this run's last).

- **Created at the start.** `StageLauncher.launch` calls `CostRecorder.begin` after it composes the request and right before the agent runtime runs. `begin` reads the sidecar in the work tree (a missing file is no records), adds a `started` record (a new `uuid4` hex `run`, the stage, the stage's role from the pipeline definition, `attempt` equal to the state's `attempts`, `started_at` from the clock, every measure `None`, and `image` and `instance` from the instance's settings) and writes the file.
- **Until the stage's commit, the running run's record is uncommitted.** From `begin` until the stage's commit, the sidecar in the work tree holds the running run's `started` record and is not committed. The agent works on the dataset, where the sidecar is the one committed at the stage-start commit; the factory writes the host's copy after the take. An agent leaves it alone. The agent's own `make check` does scan it, which is why a project's secrets scan leaves the cost records out.
- **Completed at the end.** Right after the runtime returns, `complete` replaces that record with a `completed` one: the duration in seconds, `model_seconds` (the run's `model_duration` in seconds, `None` when unknown), the end reason, and `turns`, `tokens` and `cost_usd` exactly as the runtime reported them. Unknown stays `None`, never 0 and never estimated; a reported zero stays zero. A run that failed (`ok` false) has its record like any other. `image` is `settings.image` and `instance` is `settings.instance`. `complete` keeps them. It also sets `denials`, the number of `permission_denials` the runtime reported, and `denied_paths`, the `path` of each denial that has one, each once, in the order reported; a run that ended `died` or `time_limit` (no reply) leaves both `None`, and a replied run without denials has `0` and `[]`. Only the tool calls the runtime reports as refused are counted: a refusal that is only text in a tool's output, such as a write the kernel refuses, is not parsed.
- **Committed with the next commit, never pushed alone.** The stage-start commit holds the records of earlier stages only. The new records travel in the stage's next commit: the result commit, or the stall commit of a stall (a died or timed-out run, a red check).
- **Rewritten after every take.** The factory rewrites the sidecar after the take: the sidecar is outside every write path, so the take never brings the dataset's copy. So the records are kept in memory (`CostRun`), and `CostRecorder.write` puts them back right after the take: in `AfterAgent.process`, and in `StallService.stall` when its `StallContext.cost` is set. An agent that overwrites or deletes the sidecar changes nothing in the commit. The factory's own rewrite is not named in the journal entry's paragraph about left-out changes.
A record has `run`, `work_item`, `stage`, `role`, `attempt`, `status` (`started` or `completed`), `started_at` (aware, stored in UTC), and the measures `duration_seconds`, `model_seconds`, `end_reason`, `turns`, `tokens` (`TokenCounts`), `cost_usd`, `image`, `instance`, `denials`, `denied_paths` and `login`. `login` is the `Login` of the run's result (`api_key`, `subscription` or `none`), copied by `complete`, `None` when the runtime has no login file. `instance` is a `Name` (`factory.domain.identifiers`), the name of the instance that ran the agent run: optional when read, set by `begin` from the settings and kept by `complete`, so either status may carry it. `CostRecord` is frozen and refuses unknown fields. `run` is 32 lowercase hexadecimal characters.

- A `started` record has no duration, model time, end reason, turns, tokens, cost, `denials`, `denied_paths` or `login` (`a started record has no login`). A `completed` record has `duration_seconds` and `end_reason`; its `model_seconds`, `turns`, `tokens` and `cost_usd` may be unknown. The rule spans fields, so its error has no field location and `parse` reports it as `invalid record: <reason>`.
- A measure the runtime did not report is `null` in the file and `None` in the record, never 0 (a run the `time_limit` ended has `turns`, `tokens` and `cost_usd` unknown). A key that is absent when reading is `None` too.
- `duration_seconds` and `model_seconds` are at least 0 and finite. `model_seconds` is the part of the duration the model took; the rest is the tools' and the factory's. A line written before the key existed reads with `model_seconds` `None`. `denials` is at least 0. `cost_usd` is at least 0 and finite, and is a JSON **string** (`"0.3450"`), because a float would round it and a `Decimal` keeps its digits. A JSON number or boolean for `cost_usd` is `invalid cost_usd`.
- `ok` is true exactly when the status is `completed` and the end reason is `completed`.
- A `run` appears once in a file. A record is completed by replacing its `started` line with the `completed` one (read, replace the record, `write` the whole file), never by appending a second line for the run.

A line is one JSON object without spaces after `,` and `:`; keys are in field order (`instance`, `denials`, `denied_paths`, `login` last), the writer leaves the `instance`, `denials`, `denied_paths` and `login` keys out when each is `None`, so a line written before they existed stays as it is (every other unset field is written `null`), `tokens` in the order of `TokenCounts`, `started_at` ends in `Z`. The file is strict JSON: `NaN`, `Infinity` and `-Infinity` are `not valid JSON`. A completed line, then a started line, then a started line that carries an instance:

```json
{"run":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-12T00:00:00Z","duration_seconds":41.0,"model_seconds":30.5,"end_reason":"completed","turns":7,"tokens":{"input":12,"output":3438,"cache_read":127336,"cache_creation":31343},"cost_usd":"0.3450","image":null}
{"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0002-S0007","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-12T00:00:00Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
{"run":"cccccccccccccccccccccccccccccccc","work_item":"F0014-S0008","stage":"tests","role":"tester","attempt":0,"status":"started","started_at":"2026-10-17T20:31:00Z","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":"build-7","instance":"shakedown"}
```

| Operation | Does |
|---|---|
| `reader.parse(text)` | the records, in file order |
| `reader.read(path)` | `parse` of the file as UTF-8; `[]` when the file does not exist |
| `writer.render(records)` | one line per record, each ending in `\n`; `""` for none |
| `writer.write(path, records)` | `render` as UTF-8 with `\n` line ends, replacing the file whole |

`parse` ignores blank lines, which still count in line numbers. Of `run`, `work_item`, `stage`, `role`, `attempt`, `status` and `started_at`, each is required; the other keys may be absent. A fault is a `CostRecordFormatError(line, fault)` (a `FactoryError`; message `line <line>: <fault>`, both attributes), the line counted from 1, and the first fault ends the parse. The faults are `not valid JSON`, `not a JSON object`, `unknown key: <key>`, `missing key: <key>`, `invalid <key>: <reason>` and `invalid record: <reason>`; a key inside `tokens` is named after a dot (`tokens.output`). On one line they come in that order. Only a line with none of them can be `duplicate run: <run>`, the second line with a run seen before; `render` raises the same fault, with the line of the second record.

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

prints `2 not valid JSON | line 2: not valid JSON`.

## Bills

A bill is a sum of cost records and nothing else. The cost line a `done` journal entry carries is display text: no code reads it back, and a bill never depends on it.

`factory.domain.bills` is pure. `Bill` (frozen, no unknown keys) holds `runs`, `runs_cost_unknown`, `duration`, `model_duration`, `turns`, `tokens` and `cost_usd`; `StageBill` pairs a `Name` with a `Bill`.

- `bill(records)` counts every record in `runs`, whatever its status and end reason, so a failed run is in the bill. `runs_cost_unknown` counts the records whose `cost_usd` is `None`. `duration`, `model_duration`, `turns`, `tokens` (field by field) and `cost_usd` sum the known values; a `None` is skipped, never zero.
- `bills_by_stage(records)` gives one `StageBill` per stage in the order of its first record; a stage that runs again joins its first group. `total(stage_bills)` sums them field by field.
- `cost_line(bill)` and `cost_table(stage_bills)` build the text the operator guide describes. Minutes and dollars are rounded half up with `Decimal.quantize`; the minutes are computed from `Decimal(str(seconds))` to avoid float half-way errors. `one_decimal(value: Decimal) -> str` is the one public rounding helper of the module (one decimal, half up): the minutes and the human's hours both call it, so there is no second copy.

`BillService(git, cost_reader)` (`factory.application.costs`) builds a `WorkItemBill` (`work_item`, `total`, `stages`, `line`, `table`). `for_work_item` reads only remote-tracking refs: `origin/<branch>` when it exists, else `origin/main`. It finds the first `.md` file under the features directory whose name parses to the id (none gives `None`), and reads that file's sidecar with `show_file` (no sidecar means no records). A local commit that was not pushed, and the contents of the `work` volume, have no influence, so a fresh clone shows the same bill. The service never fetches; the caller does. `in_flight()` returns the ids of the remote branches named like work item branches, sorted with `work_item_order`.

`factory.entry.bill` is the command `factory-bill` (`run(argv, service, out)` returns the exit status; `main` builds the service with `build_bill_service` from `factory.entry.wiring`, the only adapter import of the entry layer).

### The human's waits

`factory.domain.human_waits` (pure) turns the journal's records into the time the factory waited for the human. The cause of each blocking question is data in the front matter (`blocked`), so no text is read.

- `human_waits(journal)` gives one `HumanWait` (`question`, `blocked`, `asked_at`, `answered_at`) for each record of kind `question` that has both `blocked` and `at`, in journal order. Any other record starts no wait.
- A wait ends at the `at` of the first later record (higher `number`) whose speaker is `human` and that has an `at`, whatever its kind: a `comment` or a `close`. A record of another speaker, a human record without `at` and a human record before the question end nothing. With no such record `answered_at` is `None`.
- A comment's record carries the time the factory copied it from the pull request, not the time the human wrote it. A wait therefore ends up to one tick late.
- `human_line(waits)` is `<n> questions answered (<cause> <count>, ...), <hours> h waited`. Only answered waits count: `<n>` is their number, the parenthesis is left out when `<n>` is 0, the causes follow the order of `Blocked`'s values, and the hours are the sum of the waits in hours with `one_decimal`. No waits give `0 questions answered, 0.0 h waited`. The word is `questions` for 1 as well.

`cost_table_post(table, human=None)` (`factory.domain.post_texts`) appends an empty line and `Human: <human>` when `human` is set. `HandOverHandler` and `AcceptanceHandOver` pass `human_line(human_waits(journal))` of the document they read; the post's key is unchanged. `AcceptanceService.facts` passes the line of the waits of every story in the feature's `done/` on `origin/main` (not an acceptance report, not a backlog story), read with `AcceptanceReader.document`; a done story file that `parse` refuses adds no wait.

### No code reads data from the journal's text

The journal's text is for people; its data is the front matter and the sidecar. `tests/test_no_journal_reading.py` parses every module under `src/factory` (`modules()` of `tests/source_search.py`) and fails when:

- `entry_text` is referenced (imported, used as a name or as an attribute) outside `factory.domain.journal`, `factory.domain.hand_over`, `factory.application.handlers.questions`, `factory.application.recovery` (the display text of the crash-cap question) and `factory.domain.acceptance` (the findings in the acceptance's description);
- `JOURNAL` of `factory.domain.sections` is referenced outside `factory.domain.sections`, `factory.domain.journal`, `factory.domain.story_form`, `factory.adapters.work_item_markdown`, `factory.application.opening` and `factory.domain.acceptance` (`acceptance_head` builds its `## Journal` heading from the constant);
- a string literal equal to `Journal` or `## Journal` stands outside `factory.domain.sections`.

A local variable named like a forbidden name counts too. To read something from a journal entry, put it in the front matter or a sidecar instead; do not add the module to the list.
