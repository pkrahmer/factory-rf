# What the factory shows and what it costs

This file covers the area `watching`: what shows the factory and what it costs. Read the index, [README.md](README.md), first. The [tick](glossary.md), its handlers, the stops and the boundaries are in [pipeline.md](pipeline.md). The exact detail (every field, fault and rule) is in the *Reference* at the end.

## The evaluation

The factory decides what to do next by looking at the remote. The evaluation turns what the remote shows into one event. It keeps no memory: the same facts give the same event.

The watcher is `Watcher` in [watcher.py](../../src/factory/watching/application/watcher.py). It gathers the facts and hands them to the pure function `evaluate` in [evaluation.py](../../src/factory/pipeline/domain/evaluation.py). The [events](../../src/factory/pipeline/domain/events.py) and the [boundaries](../../src/factory/pipeline/application/boundaries.py) are described in `pipeline.md`.

    Watcher(boundaries, instance, *, observer=False).evaluate(definition) -> Event
    evaluate(facts: EvaluationInput, lookup, claim_status) -> Event
    EvaluationInput(definition, snapshots, main_commit, illegal_changes=[], due=[])
    waiting(state, definition) -> bool
    question_posted(snapshot, comments) -> bool

- `Watcher.evaluate` reads the head of `origin/main`, the [work items](glossary.md) in progress and the running [acceptances](glossary.md), and sorts them by `(work_item_order(id), path)`.
- `due` comes from `AcceptanceReader(boundaries, definition).due_features()`; `AcceptanceReader` is in [acceptance_reading.py](../../src/factory/work/application/acceptance_reading.py).
- It does not fetch; the caller fetches first.
- `GitError` passes through, also when `origin/main` does not resolve (the message names `origin/main`), and so does `WorkItemFormatError`.
- The lookup it passes to `evaluate` calls `get_pull_request`, and `list_comments` only while the pull request is open.
- `ClaimService` is in [claims.py](../../src/factory/pipeline/application/claims.py). With `observer=False` (the tick) the claim status is `ClaimService.status`: an own [claim](glossary.md) is `own`, so it is a `crash` at any age.
- With `observer=True` the claim status is `ClaimService.observed_status`, which calls `observed_claim_status` in [lease.py](../../src/factory/pipeline/domain/lease.py). An own claim within its [lease](glossary.md) is `held`, and the event is `idle` with the detail `<work item> is held by <instance>`. An own claim at or past its lease is `own` again.
- Nothing else in `evaluate` depends on `observer`.
- `evaluate` checks every snapshot against the definition after the integrity tier and before any lookup. A work item with no state raises `ValueError("work item <id> has no state")`. One in a [stage](glossary.md) that the [pipeline definition](glossary.md) lacks raises `ValueError("work item <id>: stage <stage> is not in the pipeline definition")`.

See also: *The tick* in [pipeline.md](pipeline.md), and the claim in [work.md](work.md).

### The event

An event says what the factory should do about one work item, or that it should do nothing.

    Event(kind, work_item, pull_request, feature, remote_state, detail)
    Event.key -> str

- `Event` is frozen and forbids unknown keys.
- `key` is `<kind>:<work item id>`, else `<kind>:<feature id>`, else `<kind>:-`.
- `idle` and `acceptance_due` take no work item; every other kind needs one. `feature` (the [feature](glossary.md)'s id) is set for `acceptance_due` and for no other kind. A violation raises `ValidationError`.
- `remote_state` is the snapshot's `branch_commit`, else the head of `origin/main`. An event with no work item carries the head of `origin/main`.
- `detail` is for display. No code reads it back.
- `evaluate` makes every kind: `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `crash`, `expired`, `duplicate`, `pull_request_lookup`, `acceptance_due` and `idle`. `build_handlers` registers a handler for each of them.
- `reject` is an illegal stage change (see *The move rule*); `RejectHandler` handles it.

See also: *The handlers of the events* and *An illegal stage change is put back* in [pipeline.md](pipeline.md).

### The four tiers

`evaluate` looks at four tiers in turn, and the first that matches decides.

1. **Integrity.** Two snapshots with one id give `duplicate` for the first such id in id order.
2. **The human.** Only the first work item that waits, in id order, is looked at. A work item waits when `blocked` is set or its stage is an [approval](glossary.md) stage. The pull request decides: `merged`, `closed`, `hand_over`, `comment`, `ask`, or `idle` when nothing is open.
3. **The agent at work.** The first work item with a claim decides by the claim's status: `crash`, `expired` or `idle`.
4. **New work.** The runnable work items and the features whose acceptance is due compete in one order. The first gives `run`, `ask` or `acceptance_due`.

Nothing matched: `idle` at the head of `origin/main`.

- A waiting work item holds back all new work, so no work item starts while another waits for the human.
- While a claim is held, nothing else runs, so one agent runs at a time.
- `evaluate` makes at most one pull request lookup, so an idle tick costs at most one.
- A feature's acceptance comes after its own [stories](glossary.md) and before the next feature's. Tiers 1 to 3 still win over it. An empty `due` is the behaviour without acceptances.

The tiers in detail are in the *Reference*, *The tiers*.

### The move rule

A stage changes only through the pipeline. The move rule finds a stage change that nobody had the right to make, so that the factory can put it back.

[move_rule.py](../../src/factory/work/domain/move_rule.py) holds the rule, and `RemoteWorkItems` in [work_items.py](../../src/factory/work/application/work_items.py) reads the change from git.

    StageChange(from_stage, to_stage, correction=False)
    IllegalChange(work_item, change)
    FactoryMove(from_stage, to_stage)
    is_legal_change(definition, change) -> bool
    factory_moves(definition) -> list[FactoryMove]
    RemoteWorkItems.last_stage_change(snapshot) -> StageChange | None

- Every model in the module is frozen and forbids unknown keys.
- `correction` is true when the same commit appended a [journal](glossary.md) record of kind `move_back`. The factory's own correction is marked by that journal kind, never by a commit message.
- `is_legal_change` is true when `correction` is set, when the stage is unchanged, when `to_stage` is in the `next` of `from_stage`, or when `to_stage` is `done` and `from_stage` is an approval stage. A stage the definition lacks is never a legal side.
- `factory_moves` lists every move the factory may make: every name in every stage's `next`, in stage order, then each approval stage to `done`, no pair twice. All of them are legal under `is_legal_change`.
- A handler that moves a work item must take its target from the definition, or that proof does not hold.
- `last_stage_change` judges only the newest commit beyond `origin/main` that touched the file, so an older illegal change that a later commit buried is not seen.
- `Watcher.evaluate` fills `illegal_changes` with one `IllegalChange` for each snapshot, in snapshot order, whose change is not legal. An acceptance's branch is held to the same rule as a story's.
- After a merge by any method (merge commit, squash, rebase) the branch's commits may still be beyond `origin/main` and show a stage change nobody made by hand. So `evaluate` reads the pull request before it decides on `reject`.
- It skips the change of the waiting work item only when the lookup returned a merged pull request. A failed lookup skips nothing.

When `last_stage_change` gives `None`, and what `reject` carries, is in the *Reference*, *The move rule*.

See also: *An illegal stage change is put back* in [pipeline.md](pipeline.md).

### The watcher's command line

`factory-watch` shows the event of one evaluation and the board. The operator's side is in [records.md](../operator-guide/records.md). The command is `main` in [watch.py](../../src/factory/entry/watch.py).

    run_watch(boundaries, instance, out, err) -> int
    main(argv=None, *, boundaries=None, instance=None, out=None, err=None) -> int
    render_event(event) -> str

- `run_watch` resolves `origin/main` (`GitError` when it does not), loads the definition at that commit with `PipelineLoader(boundaries).load(commit)`, evaluates once with `Watcher(boundaries, instance, observer=True)`, and writes `render_event(event)`, a blank line and the board.
- It loads at the commit and not at the ref, so that it raises or clears no [stop](glossary.md).
- It fetches and writes nothing. It returns 0.
- A `PipelineDefinitionInvalid` or an `AgentDefinitionInvalid` gives 1 and a line `factory-watch: <fault>` on `err`.
- `main` parses `argv` with an `ArgumentParser(prog="factory-watch")` that has no options, so any option is `SystemExit(2)`.
- With no boundaries or no instance, `main` takes both from `boundaries_from_environment(os.environ)` and runs as the settings' [instance](glossary.md). A `SettingsInvalid` is written as `factory-watch: settings invalid: <variable>: <fault>` on `err`, nothing goes to `out`, and `main` returns 2.

### The board

The board is the table `factory-watch` prints: one row for each feature with its story counts, one for each work item in progress. The pure part is [board.py](../../src/factory/watching/domain/board.py); the reader is `BoardReader` in [board.py](../../src/factory/watching/application/board.py).

    BoardReader(boundaries).read(definition) -> BoardView
    BoardView(features, rows)
    work_item_row(snapshot) -> BoardRow
    feature_rows(stories, titles) -> list[FeatureRow]
    render_board(features, rows) -> str

- `read` takes the story files of the three folders from `RemoteWorkItems.list_stories`, the feature titles from `Git.show_file("origin/main", ...)` of each `feature.md`, and the rows from `running_work_items` in `acceptance_reading.py`.
- `running_work_items` joins the snapshots of `RemoteWorkItems.read` and of `AcceptanceReader.snapshots()`, sorted by `(work_item_order(id), path)`. `Watcher.evaluate` calls the same function, so the board and the watcher order work items alike.
- A report that `snapshots()` cannot read raises `WorkItemFormatError` from `read`.
- `read` ends with `AcceptanceReader(boundaries, definition).fill_board(rows)`, which sets `FeatureRow.acceptance`. It stays `None` without an `acceptance_stage`.
- `BoardReader` reads the remote-tracking refs a second time and does not share the watcher's snapshots, so `Watcher.evaluate` still returns one event.
- The rows of the board are pure data: `work_item_row` and `feature_rows` do no I/O.

See also: *The remote's work items* and *The feature acceptance* in [work.md](work.md).

## Cost records

Every agent run is written down in a [cost record](glossary.md): what ran, how long it took and what it cost. The records of a work item are the lines of a sidecar file beside it, and every [bill](#bills) is a sum of them.

The sidecar path is `cost_records_path(path)` (`<work item>.costs.jsonl`, see *Identity, order and places of work items* in [work.md](work.md)). The format is `CostRecord` in [cost_records.py](../../src/factory/watching/domain/cost_records.py). The file is read and written through the interfaces `CostRecordReader` and `CostRecordWriter` in [files.py](../../src/factory/shared/application/files.py), implemented by the JSON Lines classes in [cost_records_jsonl.py](../../src/factory/watching/adapters/cost_records_jsonl.py).

    CostRecord(run, work_item, stage, role, attempt, status, started_at, ...)
    CostRecord.ok -> bool
    JsonLinesCostRecordReader().parse(text) -> list[CostRecord]
    JsonLinesCostRecordReader().read(path) -> list[CostRecord]
    JsonLinesCostRecordWriter().render(records) -> str
    JsonLinesCostRecordWriter().write(path, records) -> None

- `CostRecord` is frozen and refuses unknown fields. `run` is 32 lowercase hexadecimal characters and appears once in a file.
- A `started` record has no measures. A `completed` record has `duration_seconds` and `end_reason`; its other measures may be unknown.
- A measure the runtime did not report is `null` in the file and `None` in the record, never 0.
- `ok` is true exactly when the status is `completed` and the end reason is `completed`.
- A record is completed by replacing its `started` line with the `completed` one, never by appending a second line for the run.
- `cost_usd` is a JSON string (`"0.3450"`), because a float would round it. A JSON number or boolean for it is `invalid cost_usd`.
- The file is strict JSON: `NaN`, `Infinity` and `-Infinity` are `not valid JSON`.
- `parse` returns the first fault as a `CostRecordFormatError(line, fault)`, the line counted from 1.

Every field, the line format and every fault are in the *Reference*, *Cost record fields* and *The file*. A crashed stage's records are discarded with the stage.

An example you can run: a blank line counts in the line numbers, and the first fault ends the parse.

```console
$ uv run python -c "from factory.watching.adapters.cost_records_jsonl import JsonLinesCostRecordReader as R; R().parse('\n{not json}\n')" 2>&1 | tail -1
factory.shared.domain.errors.CostRecordFormatError: line 2: not valid JSON
```

### When a record is created, completed and committed

The records of one run live in memory as a `CostRun` while the stage runs, and the sidecar is written around the agent's run. `CostRecorder` in [costs.py](../../src/factory/watching/application/costs.py) does the writing.

    CostRecorder(boundaries).begin(started, role) -> CostRun
    CostRecorder(boundaries).complete(run, result, transcript=None, *, tools=None) -> CostRun
    CostRecorder(boundaries).write(run) -> None
    CostRun(path, run, records, start_totals=None)

- `CostRun` is frozen and forbids unknown keys: `path` is the sidecar, `run` the record's id and `records` every record of the work item, this run's last.
- `StageLauncher.launch` calls `begin` after it composes the request and right before the agent runtime runs. `begin` reads the sidecar in the work tree (a missing file is no records), adds a `started` record and writes the file.
- The `started` record has a new `uuid4` hex `run`, the stage, the stage's [role](glossary.md) from the pipeline definition, `attempt` equal to the state's `attempts`, `started_at` from the clock, and `image` and `instance` from the instance's settings. Every measure is `None`. `begin` also reads the machine's totals into `start_totals`.
- Right after the runtime returns, `complete` replaces that record with a `completed` one and writes the file. It copies `turns`, `tokens` and `cost_usd` exactly as the runtime reported them: unknown stays `None`, never 0 and never estimated, and a reported zero stays zero. A run that failed has its record like any other.
- `complete` sets `duration_seconds` from the result's duration, `model_seconds` from its `model_duration` in seconds (`None` when unknown) and `end_reason`.
- It also sets `login`, `denials` and `denied_paths`, `machine`, `transcript` and `tools`; see *Cost record fields* in the *Reference*.
- From `begin` until the stage's commit, the sidecar in the work tree holds the `started` record and is not committed. The agent works on the [dataset](glossary.md), where the sidecar is the one committed at the stage-start commit. An agent leaves it alone. The agent's own `make check` does scan it, which is why a project's secrets scan leaves the cost records out.
- The new records are committed with the stage's next commit, never pushed alone: the result commit, or the commit of a [stall](glossary.md) (a died or timed-out run, a red check). The stage-start commit holds the records of earlier stages only.
- The sidecar is outside every [write path](glossary.md), so the [take](glossary.md) never brings the dataset's copy. The factory writes it back from memory right after the take, in `AfterAgent.process` and in `StallService.stall` when its `StallContext.cost` is set. An agent that overwrites or deletes the sidecar changes nothing in the commit.
- The factory's own rewrite is not named in the journal entry's paragraph about left-out changes.

See also: *Starting a stage*, *After the agent run* and *Stalls* in [pipeline.md](pipeline.md), and *The take* in [machine.md](machine.md).

### Transcripts and the machine's readings

A run leaves two more traces: its transcript and the machine's load while it ran. Both are kept without ever failing the run.

[transcripts.py](../../src/factory/watching/application/transcripts.py) holds `TranscriptStore` (the interface of the transcript folder), `TranscriptKeeper` and `SessionTranscripts`. The adapter `FileTranscriptStore` is in [transcript_files.py](../../src/factory/watching/adapters/transcript_files.py). The pure readings are in [machine.py](../../src/factory/watching/domain/machine.py) of the domain. The interface `MachineReadings` is in [machine.py](../../src/factory/watching/application/machine.py) of the application layer, and its adapter is in [machine_files.py](../../src/factory/watching/adapters/machine_files.py).

    session_transcripts(store, log, runtime, workspace) -> SessionTranscripts
    SessionTranscripts(keeper, runtime, home).read(result) -> SessionTranscript
    SessionTranscripts(keeper, runtime, home).keep(work_item, run, read) -> TranscriptRef | None
    TranscriptKeeper(store, log).keep(work_item, run, transcript) -> TranscriptRef | None
    FileTranscriptStore(folder)
    CgroupMachineReadings(slice_folder, meminfo)
    machine_differences(start, end) -> MachineTotals

- `FileTranscriptStore` writes each file with mode `0600` and returns its SHA-256.
- `SessionTranscripts.read` reads the transcript of the session the result names from the agent's home on the dataset, before the dataset is reset. A transcript that is missing or unreadable gives a reason, never an error.
- `SessionTranscripts.keep` hands a transcript it read to the keeper, and returns `None` without a transcript folder. `TranscriptKeeper.keep` compresses the transcript to `<work item>/<run>.<extension>.gz` and returns a `TranscriptRef(path, sha256)`. It logs one line when it cannot write. Without a transcript folder nothing is kept.
- `StageLauncher` also asks the agent runtime for the `ToolUse` sums of the transcript (`AgentRuntime.tool_uses`) and passes them to `complete`.
- The domain module also holds `MachineTotals`, `count_warnings`, `gigabytes` and the readers of cgroup and meminfo text.
- `complete` takes the difference of the totals at the start and the end of the run. A reading that is missing at either end, or a total that went back, is `None`.
- A machine that gave nothing at all is one unknown `machine`, not nine unknown measures.

The operator's side is in `records.md` and *Transcripts* in [health.md](../operator-guide/health.md).

## Bills

A bill is the sum of cost records and nothing else. The cost line in a `done` journal entry is display text: no code reads it back, and a bill never depends on it.

[bills.py](../../src/factory/watching/domain/bills.py) is pure, and `BillService` in `costs.py` reads the records from the remote.

    bill(records) -> Bill
    bills_by_stage(records) -> list[StageBill]
    total(stage_bills) -> Bill
    cost_line(bill) -> str
    cost_table(stage_bills) -> str
    one_decimal(value: Decimal) -> str
    BillService(git, cost_reader).for_work_item(work_item) -> WorkItemBill | None
    BillService(git, cost_reader).in_flight() -> list[WorkItemId]

- `Bill` and `StageBill` are frozen and forbid unknown keys. `Bill` holds `runs`, `runs_cost_unknown`, `duration`, `model_duration`, `turns`, `tokens` and `cost_usd`; `StageBill` pairs a `Name` with a `Bill`. `Name` is in [identifiers.py](../../src/factory/shared/domain/identifiers.py).
- `bill` counts every record in `runs`, whatever its status and end reason, so a failed run is in the bill. `runs_cost_unknown` counts the records whose `cost_usd` is `None`.
- `duration`, `model_duration`, `turns`, `tokens` (field by field) and `cost_usd` sum the known values. A `None` is skipped, never zero.
- `total` sums the stage bills field by field.
- `bills_by_stage` gives one `StageBill` per stage, in the order of its first record. A stage that runs again joins its first group.
- `cost_line` and `cost_table` build the text that `records.md` describes. Minutes and dollars are rounded half up with `Decimal.quantize`. The minutes are computed from `Decimal(str(seconds))` to avoid float half-way errors.
- `one_decimal` gives one decimal, rounded half up. It is the one rounding helper of the module: the minutes and the human's hours both call it, so there is no second copy.
- `WorkItemBill` has `work_item`, `total`, `stages`, `line` and `table`.
- `for_work_item` reads only remote-tracking refs: `origin/<branch>` when it exists, else `origin/main`.
- It finds the first `.md` file under the features directory whose name parses to the id; none gives `None`.
- It reads that file's sidecar with `show_file`; no sidecar means no records.
- A local commit that was not pushed, and the contents of the `work` volume, have no influence, so a fresh clone shows the same bill.
- `BillService` never fetches; the caller does.
- `in_flight` returns the ids of the remote branches named like work item branches, sorted with `work_item_order`.

An example you can run: the cost line and table of one completed record.

```console
$ uv run python -c "import json; from factory.watching.adapters.cost_records_jsonl import JsonLinesCostRecordReader as R; from factory.watching.domain.bills import bill, bills_by_stage, cost_line, cost_table; d = {'run': 'a' * 32, 'work_item': 'F0002-S0007', 'stage': 'tests', 'role': 'tester', 'attempt': 0, 'status': 'completed', 'started_at': '2026-10-12T00:00:00Z', 'duration_seconds': 41.0, 'end_reason': 'completed', 'turns': 7, 'tokens': {'input': 12, 'output': 3438, 'cache_read': 127336, 'cache_creation': 31343}, 'cost_usd': '0.3450'}; r = R().parse(json.dumps(d)); print(cost_line(bill(r))); print(cost_table(bills_by_stage(r)))"
...
1 runs, 0.7 min, 7 turns, 31355 tokens in (127336 more from cache), 3438 out, $0.35
| stage | runs | min | model min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| tests | 1 | 0.7 | 0.0 | 7 | 31355 | 127336 | 3438 | 0.35 |
| **total** | 1 | 0.7 | 0.0 | 7 | 31355 | 127336 | 3438 | 0.35 |
```

### The bill command

`factory-bill` prints the bill of one work item, or of every work item in flight. It is `main` in [bill.py](../../src/factory/entry/bill.py).

    run(argv, service, out) -> int
    main(argv=None) -> int

- `run` returns the exit status; `main` builds the service with `build_bill_service` from [wiring.py](../../src/factory/entry/wiring.py), the only adapter import of the entry layer.
- With one id, `run` writes the table, a blank line and `Cost: <line>`, and returns 0. An argument that is no work item id gives `not a work item id: <argument>` and 2. A work item with no bill gives `no work item <id>` and 1.
- With more than one argument, `run` writes `usage: factory-bill [<work item id>]` and returns 2.
- With no argument, `run` writes one block for each work item in flight that has a bill, headed by its id, and returns 0.

### The human's waits

The factory also records how long it waited for the human. [human_waits.py](../../src/factory/watching/domain/human_waits.py) is pure and turns the journal's records into that time. The cause of each blocking question is data in the front matter (`blocked`), so no text is read.

    human_waits(journal) -> list[HumanWait]
    human_line(waits) -> str
    HumanWait(question, blocked, asked_at, answered_at=None)

- `human_waits` gives one `HumanWait` for each record of kind `question` that has both `blocked` and `at`, in journal order. Any other record starts no wait.
- A wait ends at the `at` of the first later record (higher `number`) whose speaker is `human` and that has an `at`, whatever its kind: a `comment` or a `close`. A record of another speaker, a human record without `at` and a human record before the question end nothing. With no such record `answered_at` is `None`.
- A comment's record carries the time the factory copied it from the pull request, not the time the human wrote it, so a wait ends up to one tick late.
- `human_line` is `<n> questions answered (<cause> <count>, ...), <hours> h waited`. Only answered waits count.
- The parenthesis is left out when `<n>` is 0. The word is `questions` for 1 as well.
- The causes follow the order of the values of `Blocked`, and the hours are the sum of the waits in hours, rounded with `one_decimal`. No waits give `0 questions answered, 0.0 h waited`.
- `cost_table_post(table, human=None)` in [post_texts.py](../../src/factory/hosting/domain/post_texts.py) appends an empty line and `Human: <human>` when `human` is set. `HandOverHandler` and `AcceptanceHandOver` pass `human_line(human_waits(journal))` of the document they read, and the post's key is unchanged.
- `AcceptanceService.facts` passes the line of the waits of every story in the feature's `done/` on `origin/main`, read with `AcceptanceReader.document`. It leaves out an acceptance report and a [backlog](glossary.md) story. A done story file that `parse` refuses adds no wait.

See also: *The handlers of the events* in [pipeline.md](pipeline.md).

## The factory log and the health file

Three small adapters in this area keep what the operator reads. The tick uses them; see *Stops, the clock and the factory log* in [pipeline.md](pipeline.md).

[factory_log.py](../../src/factory/watching/adapters/factory_log.py), [health_file.py](../../src/factory/watching/adapters/health_file.py) and [record_log_jsonl.py](../../src/factory/watching/adapters/record_log_jsonl.py) hold them. The interfaces `Clock`, `Waiter`, `FactoryLog`, `HealthStatusStore`, `DiskSpace`, `MachineReadings` and `PowerOff` are in the application layer's `machine.py`, linked above.

    TimestampedFactoryLog(path, clock)
    JsonHealthStatusFile(path)
    JsonLinesRecordLog(path, model)

- `TimestampedFactoryLog` implements `FactoryLog`. It stamps each line with the UTC time in whole seconds. It writes the line to standard output first, then appends it to the log file.
- `JsonHealthStatusFile` implements `HealthStatusStore`. It replaces the file atomically. A missing or damaged file reads as healthy, so every stop is raised again while its fault lasts.
- `JsonLinesRecordLog` implements `RecordLog`, an append-only file of one model's records. A line that was torn by a kill is skipped on reading.

## No code reads data from the journal's text

The journal's text is for people. Its data is the front matter and the sidecar. To read something from a journal entry, put it in the front matter or a sidecar instead.

[test_no_journal_reading.py](../../tests/guards/test_no_journal_reading.py) parses every module under `src/factory` (`modules()` of [source_search.py](../../tests/support/source_search.py)) and fails when:

- `entry_text` is referenced (imported, used as a name or as an attribute) outside the allowed modules. Those are [journal.py](../../src/factory/work/domain/journal.py), [hand_over.py](../../src/factory/hosting/domain/hand_over.py), [questions.py](../../src/factory/pipeline/application/handlers/questions.py), [recovery.py](../../src/factory/pipeline/application/recovery.py) and [acceptance.py](../../src/factory/work/domain/acceptance.py). `recovery` uses it for the display text of the crash-cap question, and `acceptance` for the findings in the acceptance's description.
- `JOURNAL` of [sections.py](../../src/factory/shared/domain/sections.py) is referenced outside `sections`, `journal`, `acceptance`, [story_form.py](../../src/factory/work/domain/story_form.py), [work_item_markdown.py](../../src/factory/work/adapters/work_item_markdown.py) and [opening.py](../../src/factory/hosting/application/opening.py). `acceptance_head` builds its `## Journal` heading from the constant.
- A string literal equal to `Journal` or `## Journal` stands outside `sections`.

A local variable named like a forbidden name counts too. Do not add a module to the lists.

## Reference

### The tiers

The detail of *The four tiers*. The order of the checks inside `evaluate` is: integrity, the validation of the snapshots, the one pull request lookup, `reject`, the human, the agent at work, new work.

1. **Integrity.** `duplicate` carries the first snapshot of the first id seen twice, in id order. Its `detail` is `<id> at <path> and <path>`. After the validation and the lookup comes `reject` (see *The move rule* below), before everything else in tier 2 and below.
2. **The human.** The first work item that waits is looked up:
   - No pull request: `ask` with the detail `no pull request`, without a lookup.
   - The lookup raises `HostingServiceError`: `pull_request_lookup`, with the error's text.
   - Merged: `merged`. Closed: `closed`.
   - Open, at an approval stage and not yet `handed_over` for it: `hand_over`.
   - Open, with a comment that is not the factory's and whose id is not in `comments_read`: `comment`, with the detail `<n> new comments`.
   - Open, blocked, and no factory post answers the latest `question` record in the journal: `ask`. A later record of another kind does not change which question is the latest.
   - Otherwise `idle`, with no work item and the detail `<work item> waits for the human`. Nothing below tier 2 is reached.
3. **The agent at work.** The first work item with a claim decides by the claim status: `own` is `crash`, `expired` is `expired`, `held` is `idle` with the detail `<work item> is held by <instance>`.
4. **New work.** Two kinds of candidate share one ranking:
   - The runnable work items (the stage has a role and the work item does not wait; a stage without a role, such as `done`, is skipped), keyed by `work_item_order(id)`.
   - The features in `EvaluationInput.due`, keyed by `(<feature id>, 1, "")`.
   - The first candidate decides. A work item gives `run`, or `ask` with the detail `attempts cap` when `attempts` has reached `attempts_cap` (the [attempts cap](glossary.md)). A due feature gives `acceptance_due`: no work item, `feature` set, `remote_state` the head of `origin/main`, detail `acceptance of <feature> is due`.

`question_posted` is true when a comment by the factory, for this work item, with the key kind of `blocked` and the number of the latest `question` record, exists.

### The move rule

`last_stage_change(snapshot)` runs `Git.log("origin/<branch>", since="origin/main", path=<story file>)`, so only commits not reachable from `origin/main` count. The newest of them, `C`, decides. The result is `None` when:

- the snapshot has no branch, or the log is empty;
- `C` is a merge commit (more than one parent);
- `C` is the opening commit: its parent is reachable from `origin/main` (the text the human started, which may say any stage);
- the file does not exist at `C` (deleted) or at its parent (added), or the parent's text cannot be parsed;
- the stage is the same at `C` and at its parent.

Otherwise the result is a `StageChange`. Its `correction` is true only when the journal at `C` is longer than at its parent and its last record has kind `move_back`.

`evaluate` returns `reject` for the first illegal change in snapshot order. Its `remote_state` is the snapshot's `branch_commit` and its `detail` is `stage changed from <from> to <to>, which the pipeline definition does not allow`. If the lookup of the waiting work item returned a merged pull request, that work item's change is skipped and the next illegal change, if any, is considered. The lookup is made at most once, and not at all when no work item waits.

### Cost record fields

| Field | Type and rule |
|---|---|
| `run` | 32 lowercase hexadecimal characters; required; once in a file |
| `work_item`, `stage`, `role` | required |
| `attempt` | integer, 0 or more; required |
| `status` | `started` or `completed`; required |
| `started_at` | aware, stored in UTC; required |
| `duration_seconds` | at least 0 and finite; required when completed |
| `model_seconds` | the part of the duration the model took, at least 0 and finite; the rest is the tools' and the factory's |
| `end_reason` | the run's end reason; required when completed |
| `turns` | integer, 0 or more |
| `tokens` | `TokenCounts`: `input`, `output`, `cache_read`, `cache_creation` |
| `cost_usd` | at least 0 and finite; a JSON string such as `"0.3450"` |
| `image` | the image the run ran in |
| `instance` | a `Name`: the instance that ran the agent run; optional; set by `begin` from the settings and kept by `complete`, so either status may carry it |
| `denials` | the number of `permission_denials` the runtime reported, at least 0 |
| `denied_paths` | the `path` of each denial that has one, each once, in the order reported |
| `transcript` | a `TranscriptRef(path, sha256)`: the kept transcript, a relative `.gz` path inside the transcript folder and the SHA-256 of the file |
| `tools` | a list of `ToolUse(tool, calls, failed, seconds)`, one for each tool, sorted by name; `failed` is at most `calls`; `[]` for a run without a call; `None` when the calls could not be read |
| `machine` | `MachineMeasures`, see below |
| `login` | the `Login` of the run's result, copied by `complete`; `None` when the runtime has no login file |

- `Login` is in [agent_runs.py](../../src/factory/agents/domain/agent_runs.py). It is one of three literal values, and one of them is the string `none`, which is not the `None` of a run with no login file.
- A `started` record has none of the measures from `duration_seconds` to `cost_usd`, nor `denials`, `denied_paths`, `login`, `machine`, `transcript` and `tools`; the first one found raises `a started record has no <field>` (`a started record has no login`).
- A `completed` record without `duration_seconds` or `end_reason` raises `a completed record needs <field>`.
- These rules span fields, so the error has no field location and `parse` reports it as `invalid record: <reason>`.
- A key that is absent when reading is `None` too. A line written before a key existed reads with that key `None`.
- A run that ended `died` or `time_limit` (no reply) leaves `denials` and `denied_paths` `None`, and its `turns`, `tokens` and `cost_usd` are unknown. A replied run without denials has `0` and `[]`.
- Only the tool calls the runtime reports as refused are counted as denials. A refusal that is only text in a tool's output, such as a write the kernel refuses, is not parsed.
- `ToolUse` holds nothing of a call's input or output. `ToolUse.seconds` is `None` when no call of the tool carried times.
- `MachineMeasures` holds `base_image_bytes`, `project_layer_bytes`, `store_free_bytes`, `dataset_free_bytes`, `memory_peak_since_boot_bytes`, `memory_total_bytes`, `cpu_seconds`, `cpu_wait_seconds` and `memory_wait_seconds`, each unknown as `None`. The memory peak is the user slice's high-water mark since it began, not the run's. The CPU time and the waits are the run's own, but count every container of the user.

### The file

A line is one JSON object without spaces after `,` and `:`.

- Keys are in field order: `instance`, `denials`, `denied_paths`, `transcript`, `tools`, `machine`, `login` come last.
- The writer leaves out the keys `instance`, `denials`, `denied_paths`, `transcript`, `tools` and `login` when each is `None`, so that a line written before they existed stays as it is. Every other unset field is written `null`.
- `machine` is left out when it was never asked, and written `null` when it was asked and told nothing.
- `tokens` is in the order of `TokenCounts`, and `started_at` ends in `Z`.

A completed line, then a started line, then a started line that carries an instance:

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

`parse` splits on `\n` alone and ignores blank lines, which still count in the line numbers. Of `run`, `work_item`, `stage`, `role`, `attempt`, `status` and `started_at`, each is required; the other keys may be absent.

A fault is a `CostRecordFormatError(line, fault)`, a `FactoryError` with the message `line <line>: <fault>` and both attributes. The first fault ends the parse. The faults are:

- `not valid JSON`
- `not a JSON object`
- `unknown key: <key>` (a key inside `tokens` is named after a dot, `tokens.output`)
- `missing key: <key>`
- `invalid <key>: <reason>`
- `invalid record: <reason>`

On one line they come in that order. Only a line with none of them can be `duplicate run: <run>`, the second line with a run seen before. `render` raises the same fault, with the line of the second record.

### Bills

- `cost_line(bill)` is `<runs> runs, <minutes> min, <turns> turns, <in> tokens in (<cache_read> more from cache), <out> out, $<dollars>`. Tokens in are `input` plus `cache_creation`. The dollars have two decimals and, when some record's cost is unknown, end in ` + <n> unknown`.
- `cost_table` is a Markdown table with the header `| stage | runs | min | model min | turns | in | cached | out | USD |`, one row for each stage and a last row `**total**`.
- The table's `min` and `model min` have one decimal.
