# The evaluation and the costs

This file covers the evaluation, cost records and bills; read the index, `README.md`, first. The tick, its handlers, the stops and the boundaries are in `pipeline.md`.

## The evaluation

The watcher turns what the remote shows into one `Event`. The evaluation keeps no memory: the same facts give the same event, so a `run` event the dispatcher has capped is still the first one on the next evaluation.

`Watcher(boundaries, instance).evaluate(definition)` (`factory.watching.application.watcher`) reads `origin/main`'s head, `RemoteWorkItems.read(definition)` and `AcceptanceReader(boundaries, definition).snapshots()`, joins both lists sorted by `(work_item_order(id), path)`, and builds an `EvaluationInput(definition, snapshots, main_commit, illegal_changes, due)` (the illegal changes come from the move rule, below, over the joined list, so an acceptance's branch is held to the same stage changes as a story's; `due` is `AcceptanceReader.due_features()`) and calls the pure `evaluate(facts, lookup, claim_status)` (`factory.pipeline.domain.evaluation`). Like `RemoteWorkItems`, it does not fetch; the caller does, first. `GitError` passes through, also when `origin/main` does not resolve (its message names `origin/main`), and so does `WorkItemFormatError`. The `lookup` it hands over calls `get_pull_request`, and `list_comments` only while the pull request is open. `claim_status` is `ClaimService(...).status` for `Watcher(boundaries, instance)`, the tick's: an own claim is `own`, so a `crash`, at any age. With `observer=True` it is `ClaimService(...).observed_status`: an own claim within its lease is `held` (the event is `idle`, detail `<work item> is held by <instance>`), at and past it `own`. Nothing else in `evaluate` depends on `observer`.

### The event

`Event` (`factory.pipeline.domain.events`, frozen, no unknown keys) has `kind`, `work_item` (a `WorkItemSnapshot`), `pull_request` (the view of the one lookup, when it succeeded), `feature`, `remote_state` and `detail`. `detail` is for display; no code reads it back. `key` is `<kind>:<work item id>`, else `<kind>:<feature id>`, else `<kind>:-`.

`idle` and `acceptance_due` take no work item; every other kind needs one. `feature` is set for `acceptance_due` and only for it. A violation raises `ValidationError`. `remote_state` is the snapshot's `branch_commit`, else the head of `origin/main`; an event with no work item carries `origin/main`'s head.

The kinds: `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `crash`, `expired`, `duplicate`, `pull_request_lookup`, `acceptance_due`, `idle`. `evaluate` makes all of them; it builds `acceptance_due` itself from `EvaluationInput.due` (its `detail`, `acceptance of <feature> is due`, is display only and no code reads it back). `reject` is an illegal stage change (see *The move rule*); `RejectHandler` handles it (see *An illegal stage change is put back*, `pipeline.md`). `build_handlers` registers a handler for every kind, `acceptance_due` included (see *The handlers of the events*, `pipeline.md`).

### The four tiers

The first tier that matches decides.

1. **Integrity.** Two snapshots with one id: `duplicate` for the first such id in id order, carrying the first snapshot; `detail` is `<id> at <path> and <path>`.
   - Then, after the validation below and the pull request lookup, `reject`: see *The move rule*. It comes before everything else in tier 2 and below.
2. **The human.** Only the first work item that waits, in id order, is looked at. A work item waits when `blocked` is set or its stage is an approval stage.
   - No pull request: `ask` (`no pull request`), without a lookup.
   - The lookup raises `HostingServiceError`: `pull_request_lookup`, with the error's text.
   - Merged: `merged`. Closed: `closed`.
   - Open, at an approval stage and not yet `handed_over` for it: `hand_over`.
   - Open, with a comment that is not the factory's and whose id is not in `comments_read`: `comment` (`<n> new comments`).
   - Open, blocked, and no factory post answers the latest `question` record in the journal: `ask`. A later record of another kind does not change which question is the latest.
   - Otherwise `idle`, its `detail` naming the work item, and nothing below tier 2 is reached.
3. **The agent at work.** The first work item with a claim decides by `claim_status`: `own` is `crash`, `expired` is `expired`, `held` is `idle` (the `detail` names the work item and the instance).
4. **New work.** Two kinds of candidate share one ranking: the runnable work items (stage has a role, does not wait; a stage without a role such as `done` is skipped) keyed by `work_item_order(id)`, and the features in `EvaluationInput.due` keyed by `(<feature id>, 1, "")`. The first candidate decides. A work item gives `run`, or `ask` (`attempts cap`) when `attempts` has reached `attempts_cap`. A due feature gives `acceptance_due` (no work item, `feature` set, `remote_state` the head of `origin/main`). So a feature's acceptance comes after its own stories and before the next feature's; tiers 1 to 3 still win over it. `due` empty is the behaviour without acceptances.

Nothing matched: `idle` at `origin/main`'s head.

Three rules follow. A waiting work item holds back all new work, so one never starts while another waits for the human; and while a claim is held, nothing else runs, so only one agent runs at a time. At most one pull request lookup is made per evaluation, so an idle tick costs at most one.

`evaluate` first checks every snapshot against the definition, after tier 1 and before any lookup: a work item with no state raises `ValueError("work item <id> has no state")`, and one in a stage the definition lacks raises `ValueError("work item <id>: stage <stage> is not in the pipeline definition")`. An unknown stage therefore never reaches the definition's accessors.

### The move rule

A stage changes only through the pipeline. `factory.work.domain.move_rule` holds the rule; every model in it is frozen and forbids unknown keys.

- `StageChange(from_stage, to_stage, correction=False)`: a change read from git. `correction` is true when the same commit appended a journal record of kind `move_back`. The factory's own correction is marked by that journal kind, never by a commit message.
- `is_legal_change(definition, change)` is true when `correction` is set, when the stage is unchanged, when `to_stage` is in `from_stage`'s `next`, or when `to_stage` is `done` and `from_stage` is an approval stage (the human's merge accepts, even when that stage's `next` does not list `done`). A stage the definition lacks is never a legal side.
- `factory_moves(definition)` lists every `FactoryMove(from_stage, to_stage)` the factory may make: every name in every stage's `next`, in stage order, then each approval stage to `done`, no pair twice. All of them are legal under `is_legal_change`. A handler that moves a work item must take its target from the definition, or this proof does not hold.

`RemoteWorkItems.last_stage_change(snapshot)` reads the change from git: `Git.log("origin/<branch>", since="origin/main", path=<story file>)`, so only commits not reachable from `origin/main` count, and the newest of them, `C`, decides. Only the last commit that touched the file is judged; an older illegal change that a later commit buried is not seen. The result is `None` when:

- the snapshot has no branch, or the log is empty;
- `C` is a merge commit (more than one parent);
- `C` is the opening commit: its parent is reachable from `origin/main` (the text the human started, which may say any stage);
- the file does not exist at `C` (deleted) or at its parent (added), or the parent's text cannot be parsed;
- the stage is the same at `C` and at its parent.

Otherwise it is a `StageChange`; `correction` is true only when `C`'s journal is longer than the parent's and its last record has kind `move_back`.

`Watcher.evaluate` fills `illegal_changes` with an `IllegalChange(work_item, change)` for each snapshot, in snapshot order, whose change is not legal.

**The pull request is read first.** After a merge by any method (merge commit, squash, rebase) the branch's commits may still be beyond `origin/main` and show a stage change nobody made by hand. So `evaluate` makes its one lookup (for the first waiting work item `W`, exactly when it did before) before it decides on `reject`. It returns `reject` for the first illegal change in snapshot order, with `remote_state` the snapshot's `branch_commit` and `detail` `stage changed from <from> to <to>, which the pipeline definition does not allow`. It skips the change of `W` only when the lookup returned a merged pull request; the next illegal change, if any, is then considered. A failed lookup skips nothing. The lookup is made at most once and not at all when no work item waits.

`waiting(state, definition)` and `question_posted(snapshot, comments)` are public in `factory.pipeline.domain.evaluation` for the handlers that come later.

### The watcher's command line

`factory.entry.watch` (`factory-watch`, see `docs/operator-guide/records.md`) shows the event of one evaluation and the board. `run_watch(boundaries, instance, out, err)` resolves `origin/main` (`GitError` when it does not), loads the definition with `PipelineLoader(boundaries).load(<that commit>)` (a commit id, not the ref, so no stop is raised or cleared), evaluates once with `Watcher(boundaries, instance, observer=True)` (a look from outside the tick) and writes `render_event(event)`, a blank line and `render_board(...)`. It returns 0, or 1 with `factory-watch: <fault>` on `err` for `PipelineDefinitionInvalid`. It fetches and writes nothing. `main(argv, *, boundaries, instance, out, err)` parses `argv` first with an `ArgumentParser(prog="factory-watch")` without options, so any option is `SystemExit(2)`; with no boundaries or no instance it takes both from `boundaries_from_environment(os.environ)` (the readers of `factory-run`) and runs as the settings' instance; a `SettingsInvalid` is written as `factory-watch: settings invalid: <variable>: <fault>` on `err`, nothing goes to `out`, and `main` returns 2.

The board is `factory.watching.domain.board` (`BoardRow`, `FeatureRow`, `work_item_row`, `feature_rows`, `render_board`, all pure) and `BoardReader(boundaries).read(definition)` in `factory.watching.application.board`, which returns a `BoardView`. The reader takes the story files of the three folders from `RemoteWorkItems.list_stories`, the feature titles from `Git.show_file("origin/main", ".../feature.md")` and the rows from `running_work_items(...)` (`factory.work.application.acceptance_reading`): the snapshots of `RemoteWorkItems.read` and of `AcceptanceReader.snapshots()`, sorted by `(work_item_order(id), path)`, each mapped by `work_item_row`. `Watcher.evaluate` calls the same function, so board and watcher order work items alike. A report that `snapshots()` cannot read raises `WorkItemFormatError` from `read`. It reads the remote-tracking refs a second time next to the `Watcher`; it does not share the watcher's snapshots, so `Watcher.evaluate` still returns one event. `read` ends with `AcceptanceReader(boundaries, definition).fill_board(rows)`, which sets `FeatureRow.acceptance` (it stays `None` without an `acceptance_stage`).

## Cost records

One agent run is one cost record: a JSON line in the sidecar file beside the work item, `cost_records_path(path)` (`<work item>.costs.jsonl`, see *Identity, order and places of work items*). The format is `CostRecord` (`factory.watching.domain.cost_records`), the interfaces `CostRecordReader` and `CostRecordWriter` (`factory.shared.application.files`), and `JsonLinesCostRecordReader` and `JsonLinesCostRecordWriter` (`factory.watching.adapters.cost_records_jsonl`). How a bill is summed is in *Bills*; a crashed stage's records are discarded with the stage.

### When a record is created, completed and committed

`CostRecorder` (`factory.watching.application.costs`) keeps the records of one run in a `CostRun` (frozen, no unknown keys): `path` (the sidecar), `run` (the record's id) and `records` (every record of the work item, this run's last).

- **Created at the start.** `StageLauncher.launch` calls `CostRecorder.begin` after it composes the request and right before the agent runtime runs. `begin` reads the sidecar in the work tree (a missing file is no records), adds a `started` record (a new `uuid4` hex `run`, the stage, the stage's role from the pipeline definition, `attempt` equal to the state's `attempts`, `started_at` from the clock, every measure `None`, and `image` and `instance` from the instance's settings) and writes the file.
- **Until the stage's commit, the running run's record is uncommitted.** From `begin` until the stage's commit, the sidecar in the work tree holds the running run's `started` record and is not committed. The agent works on the dataset, where the sidecar is the one committed at the stage-start commit; the factory writes the host's copy after the take. An agent leaves it alone. The agent's own `make check` does scan it, which is why a project's secrets scan leaves the cost records out.
- **Completed at the end.** Right after the runtime returns, `complete` replaces that record with a `completed` one: the duration in seconds, `model_seconds` (the run's `model_duration` in seconds, `None` when unknown), the end reason, and `turns`, `tokens` and `cost_usd` exactly as the runtime reported them. Unknown stays `None`, never 0 and never estimated; a reported zero stays zero. A run that failed (`ok` false) has its record like any other. `image` is `settings.image` and `instance` is `settings.instance`. `complete` keeps them. It also sets `denials`, the number of `permission_denials` the runtime reported, and `denied_paths`, the `path` of each denial that has one, each once, in the order reported; a run that ended `died` or `time_limit` (no reply) leaves both `None`, and a replied run without denials has `0` and `[]`. Only the tool calls the runtime reports as refused are counted: a refusal that is only text in a tool's output, such as a write the kernel refuses, is not parsed.
- **Committed with the next commit, never pushed alone.** The stage-start commit holds the records of earlier stages only. The new records travel in the stage's next commit: the result commit, or the stall commit of a stall (a died or timed-out run, a red check).
- **Rewritten after every take.** The factory rewrites the sidecar after the take: the sidecar is outside every write path, so the take never brings the dataset's copy. So the records are kept in memory (`CostRun`), and `CostRecorder.write` puts them back right after the take: in `AfterAgent.process`, and in `StallService.stall` when its `StallContext.cost` is set. An agent that overwrites or deletes the sidecar changes nothing in the commit. The factory's own rewrite is not named in the journal entry's paragraph about left-out changes.
A record has `run`, `work_item`, `stage`, `role`, `attempt`, `status` (`started` or `completed`), `started_at` (aware, stored in UTC), and the measures `duration_seconds`, `model_seconds`, `end_reason`, `turns`, `tokens` (`TokenCounts`), `cost_usd`, `image`, `instance`, `denials`, `denied_paths` and `login`. `login` is the `Login` of the run's result (`api_key`, `subscription` or `none`), copied by `complete`, `None` when the runtime has no login file. `instance` is a `Name` (`factory.shared.domain.identifiers`), the name of the instance that ran the agent run: optional when read, set by `begin` from the settings and kept by `complete`, so either status may carry it. `CostRecord` is frozen and refuses unknown fields. `run` is 32 lowercase hexadecimal characters.

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
from factory.watching.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.shared.domain.errors import CostRecordFormatError
try:
    JsonLinesCostRecordReader().parse('\n{not json}\n')
except CostRecordFormatError as error:
    print(error.line, error.fault, '|', error)
"
```

prints `2 not valid JSON | line 2: not valid JSON`.

## Bills

A bill is a sum of cost records and nothing else. The cost line a `done` journal entry carries is display text: no code reads it back, and a bill never depends on it.

`factory.watching.domain.bills` is pure. `Bill` (frozen, no unknown keys) holds `runs`, `runs_cost_unknown`, `duration`, `model_duration`, `turns`, `tokens` and `cost_usd`; `StageBill` pairs a `Name` with a `Bill`.

- `bill(records)` counts every record in `runs`, whatever its status and end reason, so a failed run is in the bill. `runs_cost_unknown` counts the records whose `cost_usd` is `None`. `duration`, `model_duration`, `turns`, `tokens` (field by field) and `cost_usd` sum the known values; a `None` is skipped, never zero.
- `bills_by_stage(records)` gives one `StageBill` per stage in the order of its first record; a stage that runs again joins its first group. `total(stage_bills)` sums them field by field.
- `cost_line(bill)` and `cost_table(stage_bills)` build the text `docs/operator-guide/records.md` describes. Minutes and dollars are rounded half up with `Decimal.quantize`; the minutes are computed from `Decimal(str(seconds))` to avoid float half-way errors. `one_decimal(value: Decimal) -> str` is the one public rounding helper of the module (one decimal, half up): the minutes and the human's hours both call it, so there is no second copy.

`BillService(git, cost_reader)` (`factory.watching.application.costs`) builds a `WorkItemBill` (`work_item`, `total`, `stages`, `line`, `table`). `for_work_item` reads only remote-tracking refs: `origin/<branch>` when it exists, else `origin/main`. It finds the first `.md` file under the features directory whose name parses to the id (none gives `None`), and reads that file's sidecar with `show_file` (no sidecar means no records). A local commit that was not pushed, and the contents of the `work` volume, have no influence, so a fresh clone shows the same bill. The service never fetches; the caller does. `in_flight()` returns the ids of the remote branches named like work item branches, sorted with `work_item_order`.

`factory.entry.bill` is the command `factory-bill` (`run(argv, service, out)` returns the exit status; `main` builds the service with `build_bill_service` from `factory.entry.wiring`, the only adapter import of the entry layer).

### The human's waits

`factory.watching.domain.human_waits` (pure) turns the journal's records into the time the factory waited for the human. The cause of each blocking question is data in the front matter (`blocked`), so no text is read.

- `human_waits(journal)` gives one `HumanWait` (`question`, `blocked`, `asked_at`, `answered_at`) for each record of kind `question` that has both `blocked` and `at`, in journal order. Any other record starts no wait.
- A wait ends at the `at` of the first later record (higher `number`) whose speaker is `human` and that has an `at`, whatever its kind: a `comment` or a `close`. A record of another speaker, a human record without `at` and a human record before the question end nothing. With no such record `answered_at` is `None`.
- A comment's record carries the time the factory copied it from the pull request, not the time the human wrote it. A wait therefore ends up to one tick late.
- `human_line(waits)` is `<n> questions answered (<cause> <count>, ...), <hours> h waited`. Only answered waits count: `<n>` is their number, the parenthesis is left out when `<n>` is 0, the causes follow the order of `Blocked`'s values, and the hours are the sum of the waits in hours with `one_decimal`. No waits give `0 questions answered, 0.0 h waited`. The word is `questions` for 1 as well.

`cost_table_post(table, human=None)` (`factory.hosting.domain.post_texts`) appends an empty line and `Human: <human>` when `human` is set. `HandOverHandler` and `AcceptanceHandOver` pass `human_line(human_waits(journal))` of the document they read; the post's key is unchanged. `AcceptanceService.facts` passes the line of the waits of every story in the feature's `done/` on `origin/main` (not an acceptance report, not a backlog story), read with `AcceptanceReader.document`; a done story file that `parse` refuses adds no wait.

### No code reads data from the journal's text

The journal's text is for people; its data is the front matter and the sidecar. `tests/guards/test_no_journal_reading.py` parses every module under `src/factory` (`modules()` of `tests/support/source_search.py`) and fails when:

- `entry_text` is referenced (imported, used as a name or as an attribute) outside `factory.work.domain.journal`, `factory.hosting.domain.hand_over`, `factory.pipeline.application.handlers.questions`, `factory.pipeline.application.recovery` (the display text of the crash-cap question) and `factory.work.domain.acceptance` (the findings in the acceptance's description);
- `JOURNAL` of `factory.shared.domain.sections` is referenced outside `factory.shared.domain.sections`, `factory.work.domain.journal`, `factory.work.domain.story_form`, `factory.work.adapters.work_item_markdown`, `factory.hosting.application.opening` and `factory.work.domain.acceptance` (`acceptance_head` builds its `## Journal` heading from the constant);
- a string literal equal to `Journal` or `## Journal` stands outside `factory.shared.domain.sections`.

A local variable named like a forbidden name counts too. To read something from a journal entry, put it in the front matter or a sidecar instead; do not add the module to the list.
