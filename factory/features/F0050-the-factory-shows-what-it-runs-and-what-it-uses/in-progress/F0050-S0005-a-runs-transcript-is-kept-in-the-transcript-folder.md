---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 543
comments_read: [6635484197]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T15:57:50.593155Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T15:57:50.600196Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T15:58:18.926178Z'
  stage: intake
  run: 7f3398670c97480fa870732aab6c51db
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T16:04:17.357395Z'
  stage: intake
---

# A run's transcript is kept in the transcript folder

## Description

An agent's session lives in its home on the stage's dataset, and the dataset is rolled back before every stage, so every run's transcript is lost: on 2026-11-04 factory-vm held none of F0049's 102 runs. Only the cost record, the journal entry and the pull request's comments survive, and they cannot say where a run spent its turns or why it went wrong. A transcript holds whole conversations: every file the agent read, every command's output, the agent's reasoning. It can hold what no scan of secrets finds, so it never goes to GitHub. This story keeps it in a folder the site chooses, named by the new setting `FACTORY_TRANSCRIPT_DIR`: on a VM a local directory, in a Cloud Run job a Cloud Storage bucket mounted as a volume (S0007). The factory knows only the folder. After each agent run, before anything rolls the dataset back, it copies the run's transcript there, compressed, named by the run's id, readable by the factory's user alone. An unset setting keeps no transcript, as today. An optional second setting, `FACTORY_TRANSCRIPT_DAYS`, makes the factory delete copies older than that many days; a bucket uses its own lifecycle rule instead. No container sees the folder.

## Interface

- Settings: `FACTORY_TRANSCRIPT_DIR`, optional, an absolute path outside the workspace, the checkout, the state directory and the agent home; unset or empty keeps no transcript. `FACTORY_TRANSCRIPT_DAYS`, optional, a positive whole number; unset means no deletion by the factory. A relative path, a path inside one of those four places, or a days value that is not a positive whole number is refused when the settings are read, with the variable's name.
- After each agent run that has a session (`AgentRunResult.session`), the factory copies that session's transcript from the agent's home on the dataset into `<FACTORY_TRANSCRIPT_DIR>/<work item>/<run id>.<ext>.gz`, gzip-compressed, mode `0600`. Each runtime's wrapper knows where its runtime keeps a session and in which form: Claude Code's `projects/<folder>/<session>.jsonl` under the agent home; opencode's session files under `.local/share/opencode`, gathered into one file. The coder decides the gathering and the extension.
- A run that is resumed within itself (a spent budget's resume, one cost record) keeps one transcript under its run id, the copy after the resume replacing the earlier one.
- A transcript that cannot be found or copied writes one log line `transcript: not kept for <run id>: <reason>` and does not fail the run, the stage or the factory.
- With `FACTORY_TRANSCRIPT_DAYS` set, the factory deletes the folder's files older than that many days once per idle tick, and writes `transcript: removed <n> older than <d> days` when it removed any.
- An unset or empty `FACTORY_TRANSCRIPT_DIR` is no fault anywhere: the factory starts, runs and records as today, writes no transcript, writes no `transcript:` log line, and the preflight has no item for it (the human, 2026-11-04).
- The cost record refers to its transcript reliably (the human, 2026-11-04): it gets `transcript: TranscriptRef | None`, `None` when none was kept. `TranscriptRef` (frozen, unknown keys refused) holds `path`, the file's path relative to `FACTORY_TRANSCRIPT_DIR` (always `<work item>/<run id>.<ext>.gz`, so it is also found from the record's own `work_item` and `run`), and `sha256`, the SHA-256 of the file as written (64 lowercase hex digits), so that a reader can tell that the file is the one the record names. A record of a later run that continues an earlier run's session (a provider limit's resume) names the file under its own run id; nothing is shared between records. The records contract's version follows its rule (an added optional field).
- The transcript folder is mounted into no container and named in no prompt.

## Acceptance criteria

1. With the setting unset, and with it empty, the factory starts and runs a stage as before: no transcript is written, no `transcript:` line is logged, no stop is raised, and every record's `transcript` is `None`. Rows: unset, empty.
2. With the setting set, a completed run of each runtime leaves one gzip file at `<work item>/<run id>.<ext>.gz` with mode `0600`, whose content is the session's transcript; the record's `transcript.path` is that path and its `transcript.sha256` the file's SHA-256. Rows: Claude Code, opencode.
3. A run resumed within itself leaves one file, under its run id, with the content after the resume, and its record's `sha256` matches that file. A later run that continues an earlier session names a file under its own run id, and the earlier record still matches its own file.
4. A missing session, a missing transcript and a folder that cannot be written each write the log line and leave `transcript` as `None`; the run's result is unchanged. Rows for the three.
5. The settings refuse a relative path, a path inside the workspace, the checkout, the state directory or the agent home, and days of `0`, `-1` and `x`; they accept `1`. Rows for each.
6. With days set, an idle tick removes the files older than the days and keeps the newer ones, and writes its line only when it removed any.
7. No container's mounts and no prompt name the transcript folder.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: a section *Transcripts*: what a transcript holds and why it never goes to GitHub, the two settings, the file names, the mode, the log lines, and that the folder must sit where only the site's own people can read it. `docs/decisions.md`: one entry with feature decision 6 and its reason. `README.md`: none. The project guide: the file on agent runs says where the runtimes' wrappers find a session.

## Smoke test

```bash
grep -rhoE 'FACTORY_TRANSCRIPT_(DIR|DAYS)' src/factory/domain/settings.py | sort -u
grep -rhoE 'transcript: (not kept for|removed)' src/factory | sort -u
```

Expect: the two lines `FACTORY_TRANSCRIPT_DAYS` and `FACTORY_TRANSCRIPT_DIR`, then the two lines `transcript: not kept for` and `transcript: removed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions before the story can move on:

   1. Interface names no concrete modules or signatures. Please name them: the settings fields (class, module, field names, e.g. `Settings.transcript_dir: Path | None`, `transcript_days: PositiveInt | None`); the module of `TranscriptRef` and the `CostRecord.transcript` field; the interface operation each runtime wrapper gains (name, arguments, return type) to find and gather a session; the application class that copies, hashes and removes old files (and the filesystem interface it uses, if any); and where the idle-tick deletion is called. "The coder decides the gathering and the extension" leaves the tester without a seam. I would choose: `factory.domain.settings`, `factory.domain.cost` (or wherever `CostRecord` lives), `AgentRuntime.read_transcript(home: Path, session: str) -> Transcript | None`, and an `application.transcripts.TranscriptKeeper`.
   2. The `TranscriptRef` rules have no failing-side criterion: `sha256` must be 64 lowercase hex digits (rows: 63 digits, uppercase, non-hex) and `path` always `<work item>/<run id>.<ext>.gz` (a path that is absolute, has `..`, or does not end in `.gz`). I would add a criterion for each.
   3. The contract version has no criterion. Interface says "follows its rule (an added optional field)", but S0002 already moves the contract to 4.2. Which version does this story produce (4.3?), and should a criterion pin it and the regenerated schemas (and the test pins in `tests/domain/test_contract_version_4.py`, which would need the human's leave)? I would choose 4.3 with a criterion.
   4. The Interface says deletion runs "once per idle tick". Criterion 6 tests only an idle tick. Add a row for a non-idle tick that deletes nothing. The age boundary is also open: is a file exactly `d` days old kept or removed? I would choose "older than" means strictly older, kept at exactly `d` days, with a row for each side.
   5. An empty `FACTORY_TRANSCRIPT_DAYS` is not stated. Is it unset, or refused with the variable's name? I would choose unset, with a row in criterion 5. The refusal of the other values also needs the days rows `0`, `-1`, `x` to name the variable in the error. Criterion 5 should say "with the variable's name".
   6. "The copy after the resume replaces the earlier one" (Interface) is covered by criterion 3. But "a record of a later run names the file under its own run id; nothing is shared" needs the case where the later run's copy fails: its record has `transcript` `None` and does not name the earlier run's file. Add this as a row in criterion 4 or 3.
   7. Scope check: the story is within F0050's scope (S0005 line) and no "Out of scope" item. The smoke test is runnable and its `Expect:` is checkable, and the project's pytest is not used there. The architecture fits (settings in domain, wrappers per runtime, keeper in application). These need no change.
4. 2026-11-04 human: Answers of the human:

   1. The seams, put into the Interface:
      - `InstanceSettings` in `factory.domain.settings` gains `transcript_dir: Path | None = None` and `transcript_days: PositiveInt | None = None`, read by `read_settings`.
      - `TranscriptRef` (frozen, unknown keys refused) in `factory.domain.cost_records`, beside `CostRecord`, which gains `transcript: TranscriptRef | None = None`.
      - A domain model `Transcript` in a new `factory.domain.transcripts` (frozen: `extension: str`, e.g. `jsonl`, and `content: bytes`).
      - `AgentRuntime` (`factory.application.agent_runtime`) gains `read_transcript(home: Path, session: str) -> Transcript | None`; `claude_runtime`, `opencode_runtime` and the fake implement it.
      - An application interface `TranscriptStore` in a new `factory.application.transcripts`: `write(path: str, data: bytes) -> str` (writes `<folder>/<path>` with mode `0600`, returns the SHA-256 of what it wrote) and `remove_older_than(days: int, now: datetime) -> int`; its adapter `FileTranscriptStore(folder: Path)` in `factory.adapters.transcript_files`; and `TranscriptKeeper(store, log)` in the same application module, with `keep(work_item, run, transcript) -> TranscriptRef | None` (compresses, writes, logs `transcript: not kept for ...` on an error) and `remove_old(days, now) -> int` (logs `transcript: removed ...` when it removed any).
      - The deletion is called from `activity_tick` in `factory.entry.run`, on an idle outcome only, when `transcript_days` is set.
      The coder may add arguments these need and says so in its entry.

   2. Yes, a criterion each: `sha256` refused with 63 digits, upper case and a non-hex digit; `path` refused when absolute, with `..`, or not ending in `.gz`.

   3. 4.3, with a criterion that pins it and the regenerated schemas. Leave for the tester: the `"4.2"` pins in `tests/domain/test_contract_version_4.py`, `tests/domain/test_contract_version_4_2.py` and `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` become `"4.3"`; nothing else in those modules.

   4. Yes: strictly older is removed, a file of exactly `d` days is kept (a row for each side), and a row for a tick that is not idle, which removes nothing.

   5. An empty `FACTORY_TRANSCRIPT_DAYS` counts as unset (a row); the refusals of `0`, `-1` and `x` name the variable.

   6. Yes: a row where the later run's copy fails: its record has `transcript` `None` and does not name the earlier run's file.
