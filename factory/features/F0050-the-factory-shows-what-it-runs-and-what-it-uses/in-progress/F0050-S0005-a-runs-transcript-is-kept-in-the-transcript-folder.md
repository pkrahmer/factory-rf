---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 543
comments_read: [6635484197, 6635579714, 6635598534, 6635866543, 6638353558]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-04T18:15:56.416893Z'
  lease_duration: 60
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T16:04:20.279611Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T16:04:49.536426Z'
  stage: intake
  run: f44b1ddc7e8848a0a70ab9d389118f7f
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T16:04:55.395432Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-04T16:08:04.642756Z'
  stage: tests
  run: d21fa20287144a658a0e6b09c3f3007c
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-04T16:08:51.875802Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T16:08:54.777801Z'
  stage: tests
- number: 11
  speaker: tester
  kind: question
  at: '2026-11-04T16:10:01.525473Z'
  stage: tests
  run: 9206d7470f7c407bb1e5b107fb58eb5f
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-04T16:10:12.809325Z'
  stage: tests
- number: 13
  speaker: human
  kind: comment
  at: '2026-11-04T16:22:16.755161Z'
  stage: tests
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-04T16:22:19.921758Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-04T16:25:49.057410Z'
  stage: tests
  run: 0788bbd65ab2443f9774fd3ea7defc3e
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T16:25:55.132277Z'
  stage: doing
- number: 17
  speaker: coder
  kind: question
  at: '2026-11-04T18:11:54.856345Z'
  stage: doing
  run: 36ba896be8fe439b8586dca255f981cc
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-11-04T18:13:49.421827Z'
  stage: doing
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-04T18:13:52.516524Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-04T18:14:41.499589Z'
  stage: doing
  run: c0322e70f6954cca8ae23bf5b6e7413b
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-04T18:14:47.846467Z'
  stage: tests
- number: 22
  speaker: tester
  kind: result
  at: '2026-11-04T18:15:50.200060Z'
  stage: tests
  run: c43a0e84fb474d208b3f9b0e8e4b2ba9
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-04T18:15:56.416893Z'
  stage: doing
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

- Seams (the human's answer, journal 4): `InstanceSettings` in `factory.domain.settings` gains `transcript_dir: Path | None = None` and `transcript_days: PositiveInt | None = None`, read by `read_settings`; an empty `FACTORY_TRANSCRIPT_DAYS` counts as unset. `TranscriptRef` (frozen, unknown keys refused) in `factory.domain.cost_records`, beside `CostRecord`, which gains `transcript: TranscriptRef | None = None`; `sha256` is refused unless 64 lowercase hex digits, `path` is refused when absolute, with `..`, or not ending in `.gz`. `Transcript` (frozen: `extension: str`, `content: bytes`) in the new `factory.domain.transcripts`. `AgentRuntime` (`factory.application.agent_runtime`) gains `read_transcript(home: Path, session: str) -> Transcript | None`, implemented by `claude_runtime`, `opencode_runtime` and the fake. `TranscriptStore` (ABC) in the new `factory.application.transcripts`: `write(path: str, data: bytes) -> str` (writes `<folder>/<path>` with mode `0600`, returns the SHA-256 of what it wrote) and `remove_older_than(days: int, now: datetime) -> int`; its adapter `FileTranscriptStore(folder: Path)` in `factory.adapters.transcript_files`; `TranscriptKeeper(store, log)` in `factory.application.transcripts`, with `keep(work_item, run, transcript) -> TranscriptRef | None` (compresses, writes, logs `transcript: not kept for ...` on an error) and `remove_old(days, now) -> int` (logs `transcript: removed ...` when it removed any). The deletion is called from `activity_tick` in `factory.entry.run`, on an idle outcome only, when `transcript_days` is set. A file older than `d` days is removed strictly: a file of exactly `d` days is kept. The coder may add arguments these need and says so in its entry.
- Records contract: this story produces version 4.3.

## Acceptance criteria

1. With the setting unset, and with it empty, the factory starts and runs a stage as before: no transcript is written, no `transcript:` line is logged, no stop is raised, and every record's `transcript` is `None`. Rows: unset, empty.
2. With the setting set, a completed run of each runtime leaves one gzip file at `<work item>/<run id>.<ext>.gz` with mode `0600`, whose content is the session's transcript; the record's `transcript.path` is that path and its `transcript.sha256` the file's SHA-256. Rows: Claude Code, opencode.
3. A run resumed within itself leaves one file, under its run id, with the content after the resume, and its record's `sha256` matches that file. A later run that continues an earlier session names a file under its own run id, and the earlier record still matches its own file.
4. A missing session, a missing transcript and a folder that cannot be written each write the log line and leave `transcript` as `None`; the run's result is unchanged. Rows for the three, and a row where a later run that continues an earlier session fails to copy: its record has `transcript` `None` and does not name the earlier run's file.
5. The settings refuse a relative path, a path inside the workspace, the checkout, the state directory or the agent home, and days of `0`, `-1` and `x`, each refusal naming the variable; they accept `1`, and an empty `FACTORY_TRANSCRIPT_DAYS` counts as unset. Rows for each.
6. With days set, an idle tick removes the files strictly older than the days and keeps the newer ones and a file of exactly the days; it writes its line only when it removed any; a tick that is not idle removes nothing. Rows for each side.
7. No container's mounts and no prompt name the transcript folder.
8. `TranscriptRef` refuses a `sha256` of 63 digits, with upper case and with a non-hex digit, and a `path` that is absolute, has `..` or does not end in `.gz`; it accepts a well-formed one. Rows for each.
9. The records contract's version is `4.3` and the regenerated schemas carry it. The `"4.2"` pins in `tests/domain/test_contract_version_4.py`, `tests/domain/test_contract_version_4_2.py` and `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` become `"4.3"`, nothing else in those modules (the human's leave, journal 4).
10. `make check` stays green.
11. docs: `docs/operator-guide.md`: a section *Transcripts*: what a transcript holds and why it never goes to GitHub, the two settings, the file names, the mode, the log lines, and that the folder must sit where only the site's own people can read it. `docs/decisions.md`: one entry with feature decision 6 and its reason. `README.md`: none. The project guide: the file on agent runs says where the runtimes' wrappers find a session.

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
5. factory: started intake as vm.
6. intake: accepted
   - Interface: accepted with the human's answers (journal 4) written into the story as a "Seams" line. It now names `InstanceSettings.transcript_dir`/`transcript_days`, `TranscriptRef` and `CostRecord.transcript` in `factory.domain.cost_records`, `Transcript` in `factory.domain.transcripts`, `AgentRuntime.read_transcript`, `TranscriptStore`/`TranscriptKeeper` in `factory.application.transcripts`, `FileTranscriptStore` in `factory.adapters.transcript_files`, and the call from `activity_tick`. The contract version is 4.3, strict "older than" is stated, and an empty days value counts as unset.
   - Criteria: carried in from journal 4. Criterion 4 gets a row where a later run's copy fails. Criterion 5 gets "names the variable" and the empty-days row. Criterion 6 gets the strict boundary and the non-idle row. New criterion 8 covers the `TranscriptRef` sha256 and path refusals, and new criterion 9 pins 4.3 with the test-pin leave. `make check` and `docs:` are now criteria 10 and 11, still last. Every other criterion was already testable by one function with rows.
   - Smoke test: the two greps are runnable. The `Expect:` line is checkable against their output. No pytest is involved.
   - Architecture: settings and models in domain, wrappers per runtime, keeper and store interface in application, the file adapter in adapters, and wiring in entry. This fits the four layers.
   - Scope: within F0050's S0005 line, with nothing from "Out of scope". The tester has the human's leave for the three "4.2" pins to "4.3".
7. factory: started tests as vm.
8. tester: Tests are written for the seams the Interface names exactly. Some criteria are only partly covered, because the seams they go through at stage level are not named. I stopped there instead of guessing.

   Written so far (red on purpose, `make lint` green):
   - criterion 5: tests/domain/test_settings_transcripts.py::test_the_transcript_folder_is_read_or_refused (rows: unset, empty, absolute outside, relative, inside workspace, checkout, state directory, agent home) and ::test_the_transcript_days_are_read_or_refused (rows: unset, empty, 1, 0, -1, x)
   - criterion 8: tests/domain/test_transcript_ref.py::test_a_transcript_ref_takes_only_a_relative_gz_path_and_a_lowercase_sha256
   - criterion 9: the three `"4.2"` pins became `"4.3"`, under the human's leave (journal 4), nothing else changed: tests/domain/test_contract_version_4.py, tests/domain/test_contract_version_4_2.py, tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version
   - criterion 2 (keeper and store side; Claude Code row only): tests/application/test_transcript_keeper.py::test_a_kept_transcript_is_a_gzip_file_under_its_run_id_that_its_ref_names, tests/adapters/test_transcript_files.py::test_a_written_transcript_is_owner_only_and_its_sha256_returned, tests/adapters/test_claude_runtime_transcript.py::test_a_session_is_read_from_its_project_folder
   - criterion 3 (keeper side): tests/application/test_transcript_keeper.py::test_a_run_kept_again_replaces_its_file_and_a_later_run_keeps_its_own
   - criterion 4 (keeper and wrapper side): tests/application/test_transcript_keeper.py::test_a_folder_that_cannot_be_written_logs_the_line_and_keeps_nothing, tests/adapters/test_claude_runtime_transcript.py::test_a_session_without_a_file_has_no_transcript
   - criterion 6 (store and keeper side): tests/adapters/test_transcript_files.py::test_only_files_strictly_older_than_the_days_are_removed (rows: older, exactly, newer), tests/application/test_transcript_keeper.py::test_removing_old_transcripts_logs_a_line_only_when_it_removed_any

   Files created: the five new test modules above. Modules the test run could not import: factory.adapters.transcript_files, factory.application.transcripts, factory.domain.transcripts, and `TranscriptRef` from factory.domain.cost_records. These are collection errors, as expected.

   Questions. Criteria 1, 3 and 4 (record level), 6 (tick level), 7 and the opencode row of 2 run through seams the Interface leaves to the coder ("the coder may add arguments"). A test cannot be written against them yet:

   1. How the keeper reaches the stage run, and how a test scripts a transcript. This is needed for criterion 1 (no file, no `transcript:` line, record `transcript` None, unset and empty rows), the record half of 3 (a resumed run's record and a later run's record), the stage rows of 4 (missing session, missing transcript, a later run's failed copy) and criterion 7. Options: (a) `Boundaries` gains `transcripts: TranscriptStore | None = None` (None when the setting is unset; the stage builds the keeper from it and `boundaries.log`), and `ScriptedRun` in the fake runtime gains `transcript: Transcript | None = None`, which the fake's `read_transcript` returns for the result's session; (b) the stage takes a `TranscriptKeeper | None` argument. I would choose (a). The stage reads from `settings.agent_home`, or from the dataset's home path: please say which home path the stage passes to `read_transcript`.
   2. Criterion 6 at tick level: how does `activity_tick` get the keeper, the days and the clock? I would choose keyword arguments `transcripts: TranscriptKeeper | None = None, transcript_days: int | None = None, clock: Clock | None = None`. The idle and non-idle rows would then drive it with a fake `Tick` that returns an idle and a busy outcome.
   3. Opencode (criterion 2's second row): which files under `.local/share/opencode` make up session S, and what must the gathered content contain? I would choose: every file under `.local/share/opencode/storage` whose path names S (`session/*/S.json`, `message/S/*`, and the parts of those messages), and the test checks that the gathered content holds each of those files' text. If this opencode version keeps sessions in its `opencode.db` instead, the test would need a different stand-in. Please name the layout.
   4. Criterion 7: I would check that, with `transcript_dir` set, no mount of a container started through the fake containers and no `AgentRunRequest.prompt` recorded by the fake runtime contains the folder's path. Is that the check you want?
9. 2026-11-04 human: A correction of the human, which replaces parts of the answer above: **the factory does not delete old transcripts.** The VM uses a `tmpfiles.d` rule (S0007) and a Cloud Run bucket its lifecycle rule; the factory needs no code for it.

   So, from this story:
   - `FACTORY_TRANSCRIPT_DAYS`, `InstanceSettings.transcript_days`, `TranscriptStore.remove_older_than`, `TranscriptKeeper.remove_old`, the call from `activity_tick` and the log line `transcript: removed <n> older than <d> days` go.
   - Answers 4 and 5 above fall away (the age boundary, the non-idle tick, the empty days value).
   - Criterion 6 goes; criterion 5 keeps only its rows for `FACTORY_TRANSCRIPT_DIR`; the smoke test's first command expects only `FACTORY_TRANSCRIPT_DIR`, and its second only `transcript: not kept for`.
   - The docs criterion no longer names the days setting; it says that removing old transcripts is the site's (a `tmpfiles.d` rule on a VM, a lifecycle rule on a bucket).

   Leave for the intake (or, if the story has moved on, the reviewer): make exactly these edits to the Description, Interface, criteria and smoke test. Everything else of the answer above stands.
10. factory: started tests as vm.
11. tester: I took the human's correction (journal 9) into the tests I wrote earlier. The factory deletes no transcripts, so these tests are gone:
    - `test_the_transcript_days_are_read_or_refused` in tests/domain/test_settings_transcripts.py
    - `test_only_files_strictly_older_than_the_days_are_removed` in tests/adapters/test_transcript_files.py
    - `test_removing_old_transcripts_logs_a_line_only_when_it_removed_any` in tests/application/test_transcript_keeper.py

    I also removed the imports and constants only those tests used. `make lint` is green. One run of the transcript test files: collection errors because factory.adapters.transcript_files, factory.application.transcripts, factory.domain.transcripts and `TranscriptRef` in factory.domain.cost_records do not exist yet. That is the expected failure. I did not edit the Description, Interface, criteria or smoke test, because journal 9 leaves those edits to the intake or the reviewer.

    Tests as they stand (red on purpose):
    - criterion 5 (only the `FACTORY_TRANSCRIPT_DIR` rows are left): tests/domain/test_settings_transcripts.py::test_the_transcript_folder_is_read_or_refused
    - criterion 8: tests/domain/test_transcript_ref.py::test_a_transcript_ref_takes_only_a_relative_gz_path_and_a_lowercase_sha256
    - criterion 9: the three `"4.2"` pins became `"4.3"` under the leave in journal 4: tests/domain/test_contract_version_4.py, tests/domain/test_contract_version_4_2.py, tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version
    - criterion 2, keeper and store side, Claude Code row only: tests/application/test_transcript_keeper.py::test_a_kept_transcript_is_a_gzip_file_under_its_run_id_that_its_ref_names, tests/adapters/test_transcript_files.py::test_a_written_transcript_is_owner_only_and_its_sha256_returned, tests/adapters/test_claude_runtime_transcript.py::test_a_session_is_read_from_its_project_folder
    - criterion 3, keeper side: tests/application/test_transcript_keeper.py::test_a_run_kept_again_replaces_its_file_and_a_later_run_keeps_its_own
    - criterion 4, keeper and wrapper side: tests/application/test_transcript_keeper.py::test_a_folder_that_cannot_be_written_logs_the_line_and_keeps_nothing, tests/adapters/test_claude_runtime_transcript.py::test_a_session_without_a_file_has_no_transcript
    - criterion 6: removed, per journal 9.

    Files changed in this run: tests/domain/test_settings_transcripts.py, tests/adapters/test_transcript_files.py, tests/application/test_transcript_keeper.py. Modules the test run could not import: factory.adapters.transcript_files, factory.application.transcripts, factory.domain.transcripts, and `TranscriptRef` from factory.domain.cost_records.

    Still open. Journal 9 answers only the deletion part of my questions in journal 8. My question 2 (`activity_tick`) falls away with it. These three still have no answer, and I cannot write criteria 1, 7, the record level of 3 and 4, and the opencode row of 2 without guessing:

    1. How the keeper reaches the stage run, and how a test scripts a transcript. Criteria 1, 3 (record level), 4 (stage rows: missing session, missing transcript, a later run's failed copy) and 7 depend on this.
       (a) `Boundaries` gains `transcripts: TranscriptStore | None = None`, which is None when the setting is unset or empty. The stage builds a `TranscriptKeeper` from it and `boundaries.log`. `ScriptedRun` in the fake runtime gains `transcript: Transcript | None = None`, which the fake's `read_transcript` returns for the result's session.
       (b) The stage takes a `TranscriptKeeper | None` argument directly.
       I would choose (a). Please also say which home path the stage passes to `read_transcript`: `settings.agent_home` or the dataset's home path.
    2. Opencode, the second row of criterion 2: which files under `.local/share/opencode` make up session S, and what must the gathered content hold? I would choose every file under `.local/share/opencode/storage` whose path names S (`session/*/S.json`, `message/S/*`, and those messages' parts). The test would then check that the gathered content holds each of those files' text. If this opencode version keeps sessions in `opencode.db`, please name that layout instead.
    3. Criterion 7: with `transcript_dir` set, I would check two things. No mount of any container started through the fake containers contains the folder's path, and no `AgentRunRequest.prompt` the fake runtime recorded contains it. Is that the check you want?
12. 2026-11-04 human: Answers of the human (read together with the correction just above: the factory deletes no old transcripts):

    0. Because of the correction, the tester removes again what it wrote for the deletion: `test_the_transcript_days_are_read_or_refused`, `test_only_files_strictly_older_than_the_days_are_removed` and `test_removing_old_transcripts_logs_a_line_only_when_it_removed_any`. Criterion 6 is gone.

    1. **(a)** `Boundaries` gains `transcripts: TranscriptStore | None = None` (None when `FACTORY_TRANSCRIPT_DIR` is unset or empty); the stage builds the `TranscriptKeeper` from it and `boundaries.log`. `ScriptedRun` in the fake runtime gains `transcript: Transcript | None = None`, which the fake's `read_transcript` returns for the result's session. The home the stage passes to `read_transcript` is the agent's home on the dataset as the host sees it: `settings.workspace / "home"` (the container's `WORK_HOME`, `/work/home`, is the dataset's `home`). Not `settings.agent_home`, which holds the read-only agent files.

    2. Falls away with the correction: `activity_tick` does not change in this story.

    3. opencode: no file layout. The opencode wrapper already reads the run's JSON event stream as it runs; that stream, one event per line as printed, is the transcript (`extension` `jsonl`). `read_transcript(home, session)` returns the lines of the last run of that session, or `None` when the wrapper saw none. The test scripts a stream and checks that the content is its lines. Put this into the Interface.

    4. Yes, exactly that check.
13. 2026-11-04 human: Answers of the human (the same as in the comment of 16:09 UTC, which came before your question was posted):

    1. **(a)** `Boundaries` gains `transcripts: TranscriptStore | None = None` (None when `FACTORY_TRANSCRIPT_DIR` is unset or empty); the stage builds the `TranscriptKeeper` from it and `boundaries.log`. `ScriptedRun` in the fake runtime gains `transcript: Transcript | None = None`, which the fake's `read_transcript` returns for the result's session. The home the stage passes to `read_transcript` is the dataset's home as the host sees it, `settings.workspace / "home"` (the container's `WORK_HOME`, `/work/home`). Not `settings.agent_home`, which holds the read-only agent files.

    2. opencode: no file layout. The opencode wrapper already reads the run's JSON event stream as it runs; that stream, one event per line as printed, is the transcript (`extension` `jsonl`). `read_transcript(home, session)` returns the lines of the last run of that session, or `None` when the wrapper saw none. The test scripts a stream and checks that the content is its lines. Leave for the reviewer: put this into the Interface.

    3. Yes, exactly that check.
14. factory: started tests as vm.
15. tester: With the answers in journals 12 and 13, I wrote the tests that were still missing: criterion 1, the record and stage level of criteria 3 and 4, criterion 7 and the opencode row of criterion 2. The earlier modules are kept as journal 11 left them. `make lint` is green.

    Criterion → test:
    - criterion 1: tests/application/test_stage_transcripts.py::test_without_a_transcript_folder_a_stage_runs_as_before_and_keeps_nothing. It checks no stall, no `.gz` file, no `transcript:` log line, no stop record, and every record's `transcript` is None. Also tests/entry/test_wiring_transcripts.py::test_the_built_boundaries_hold_a_transcript_store_only_with_a_folder, which checks `Boundaries.transcripts` is None without a folder and a `FileTranscriptStore` with one. The empty row comes from tests/domain/test_settings_transcripts.py::test_the_transcript_folder_is_read_or_refused[empty], where empty is read as None.
    - criterion 2, Claude Code row: tests/application/test_stage_transcripts.py::test_a_completed_run_leaves_its_transcript_that_its_record_names, tests/adapters/test_claude_runtime_transcript.py::test_a_session_is_read_from_its_project_folder, tests/application/test_transcript_keeper.py::test_a_kept_transcript_is_a_gzip_file_under_its_run_id_that_its_ref_names, tests/adapters/test_transcript_files.py::test_a_written_transcript_is_owner_only_and_its_sha256_returned
    - criterion 2, opencode row: tests/adapters/test_opencode_runtime_transcript.py::test_a_session_transcript_is_the_event_stream_of_its_run. It checks `extension` is `jsonl` and the content is the scripted event lines.
    - criterion 3: tests/application/test_stage_transcripts.py::test_a_run_resumed_within_itself_keeps_one_file_with_the_content_after_the_resume (a provider-limit wait inside one stage run), ::test_a_later_run_of_an_earlier_session_names_its_own_file (a stalled run, then a later run on the same session), and tests/application/test_transcript_keeper.py::test_a_run_kept_again_replaces_its_file_and_a_later_run_keeps_its_own
    - criterion 4: tests/application/test_stage_transcripts.py::test_a_transcript_not_kept_writes_its_line_and_leaves_the_run_unchanged (rows: missing-session, missing-transcript, folder-not-writable) and ::test_a_later_run_whose_copy_fails_names_no_earlier_file. Also tests/application/test_transcript_keeper.py::test_a_folder_that_cannot_be_written_logs_the_line_and_keeps_nothing, tests/adapters/test_claude_runtime_transcript.py::test_a_session_without_a_file_has_no_transcript and tests/adapters/test_opencode_runtime_transcript.py::test_a_session_the_runtime_never_saw_has_no_transcript
    - criterion 5: tests/domain/test_settings_transcripts.py::test_the_transcript_folder_is_read_or_refused (only the `FACTORY_TRANSCRIPT_DIR` rows)
    - criterion 6: gone (journal 9)
    - criterion 7: tests/application/test_stage_transcripts.py::test_no_container_and_no_prompt_names_the_transcript_folder. It checks the mount sources of every `FakeContainerRuns` call and the prompt of every request the fake runtime got.
    - criterion 8: tests/domain/test_transcript_ref.py::test_a_transcript_ref_takes_only_a_relative_gz_path_and_a_lowercase_sha256
    - criterion 9: the three `"4.2"` pins became `"4.3"` under the leave in journal 4 (done in an earlier run): tests/domain/test_contract_version_4.py, tests/domain/test_contract_version_4_2.py, tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version

    What the stage tests take for granted, from journal 12 answer 1(a):
    - `Boundaries.transcripts: TranscriptStore | None = None`.
    - `ScriptedRun.transcript: Transcript | None = None`. The fake's `read_transcript` returns the transcript of the latest played run whose result has that session.
    - The stage passes `settings.workspace / "home"` as the home. The fixture sets `workspace` to the fake dataset (`<tmp_path>/workspace`) and `transcript_dir` to `<tmp_path>/transcripts`.
    - The `not kept` line is read from `<state>/factory.log`, as a substring.

    Files created in this run: tests/application/test_stage_transcripts.py, tests/adapters/test_opencode_runtime_transcript.py, tests/entry/test_wiring_transcripts.py. Earlier runs created tests/domain/test_settings_transcripts.py, tests/domain/test_transcript_ref.py, tests/application/test_transcript_keeper.py, tests/adapters/test_transcript_files.py and tests/adapters/test_claude_runtime_transcript.py.

    Modules the test run could not import (5 collection errors, as expected): factory.adapters.transcript_files, factory.application.transcripts, factory.domain.transcripts, and `TranscriptRef` from factory.domain.cost_records. The opencode, Claude Code and settings transcript tests collect and fail on the missing `read_transcript` and `transcript_dir`.

    Still open: journal 9 leaves the edits of the Description, Interface, criteria and smoke test (the deletion parts removed) to the intake or the reviewer. Journal 13 leaves the opencode event-stream sentence for the Interface to the reviewer. I made neither edit.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: Stopped with the implementation done and `make check` red, because tests contradict the Interface's seam (R9). A question for the human.

    **Contradiction.** The Interface says `AgentRuntime` (`factory.application.agent_runtime`) gains `read_transcript(home, session) -> Transcript | None`, and `CLAUDE.md` says every interface operation is an `@abstractmethod`. Existing tests from other stories rule this out:
    - `tests/application/test_interfaces.py::test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract` pins `AgentRuntime.__abstractmethods__ == {"run", "version"}`. A non-abstract method would fail `test_an_interface_has_no_public_member_but_its_abstract_operations` in the same file instead.
    - Six test stand-ins derive from `AgentRuntime` without `read_transcript`, so Python refuses to create them. This fails `make types` and about 40 tests:
      - `WorkspaceRuntime` (tests/container_support.py), used by test_stall_container, test_container_environment_take and test_container_stage_checks
      - `ObservingRuntime` (tests/observing_runtime.py), used by test_stage_launch
      - `HeadNotingRuntime` (tests/application/test_stage_run.py)
      - `RefusingRuntime` (tests/application/test_agent_run_probe.py)
      - `SidecarRuntime` (tests/application/test_costs.py)
      - `SwitchingRuntime` (tests/application/test_stall_environment.py)

    The tester's own test has a separate bug: `tests/application/test_stage_transcripts.py::test_no_container_and_no_prompt_names_the_transcript_folder` (lines 264 and 266) calls `containers.calls()`. `FakeContainerRuns.calls` is a property (`src/factory/adapters/fake_containers.py:32`), so mypy reports `"list[ContainerCall]" not callable` and the test raises `TypeError: 'list' object is not callable`.

    **Options:**
    - (a) Keep the seam as named. The tester changes the pin in test_interfaces.py to `{"run", "version", "read_transcript"}` and gives each of the six stand-ins a `read_transcript` that returns `None` (or delegates, for `ObservingRuntime`). This touches tests other stories wrote, so it needs your leave.
    - (b) Leave `AgentRuntime` unchanged. Add a separate ABC `TranscriptSource` in `factory.application.transcripts`, which the Claude, opencode and fake runtimes also implement; the stage would check `isinstance(agent_runtime, TranscriptSource)` and log "not kept" otherwise. No test of another story changes, but this departs from the Interface and adds a type check on a boundary.

    Either way the tester changes `containers.calls()` to `containers.calls` in test_stage_transcripts.py. I would choose (a). With (a), the next doing round only runs `make check`. With (b), the coder moves `read_transcript` into the new ABC and the tester's three runtime transcript tests stay as they are.

    **Built** (left in the working tree):
    - `src/factory/domain/transcripts.py`: `Transcript`.
    - `src/factory/domain/cost_records.py`: `TranscriptRef` (sha256 must be 64 lowercase hex; path refused when absolute, with `..`, or not ending in `.gz`) and `CostRecord.transcript`. The field sits before `machine` because `tests/domain/test_login_records.py` pins `login` as the last field. A started record refuses a transcript.
    - `src/factory/adapters/cost_records_jsonl.py`: leaves out a `None` transcript, as it does for login and denials, so existing lines are written back as read.
    - `src/factory/domain/contract.py`: version 4.3; schemas regenerated with `uv run python -m factory.entry.contract`.
    - `src/factory/domain/settings.py`: `FACTORY_TRANSCRIPT_DIR` and `InstanceSettings.transcript_dir`. The new `transcript_dir_fault` refuses a relative path, or one inside the workspace, checkout, state directory or agent home. `read_settings` raises it as `SettingsInvalid` with the variable's name; a model validator applies the same rule.
    - `src/factory/application/agent_runtime.py`: abstract `read_transcript`.
    - `src/factory/application/transcripts.py`: `TranscriptStore` (ABC, `write` only, per journal 9), `TranscriptKeeper` (`keep`, plus a public `not_kept`, which writes the log line), `SessionTranscripts`, and `session_transcripts(store, log, runtime, workspace)`. `SessionTranscripts` handles a missing session, a missing workspace, a transcript the runtime does not have and an `OSError`, each with the `transcript: not kept for <run>: <reason>` line.
    - `src/factory/adapters/transcript_files.py`: `FileTranscriptStore`. It opens the file `0600` from the start (folders `0700`) and returns the SHA-256.
    - `src/factory/adapters/claude_runtime.py`: `read_transcript` globs `projects/*/<session>.jsonl` and also `.claude/projects/*/<session>.jsonl`. The test puts the file at `<home>/projects`, but inside the container `HOME=/work/home`, so Claude Code writes to `$HOME/.claude/projects`; only the `.claude` path would find a real session.
    - `src/factory/adapters/opencode_runtime.py`: keeps what each run's calls printed (the first call and its resume) per session, and `read_transcript` returns those lines (`jsonl`).
    - `src/factory/adapters/fake_agent_runtime.py`: `ScriptedRun.transcript`; `read_transcript` returns the transcript of the latest played run with that session.
    - `src/factory/application/boundaries.py`: `transcripts: TranscriptStore | None = None`.
    - `src/factory/entry/wiring.py`: a `FileTranscriptStore` only when `transcript_dir` is set.
    - `src/factory/application/stage.py` and `src/factory/application/costs.py`: `StageLauncher.launch` keeps the transcript right after `run_agent` and before `complete`. A run that resumed within itself is kept once, after the resume. `CostRecorder.complete` gained an optional `transcript` argument; that, `printed` (opencode) and `SessionTranscripts` are the arguments and classes I added beyond the Interface.

    **Main choice:** the keeping step runs once, in the launcher, after the whole patient run. The rejected alternative was keeping inside `PatientRuns` after every call, which would write a file and then replace it.

    **Not done:** the refactor step, since `make check` is not green yet. I did not touch the Description: journal 9 removes the days setting, the deletion, criterion 6 and the `removed` log line, and journal 13 adds the opencode event-stream sentence. Both leave those edits to the intake or the reviewer.
18. 2026-11-04 human: Answers of the human:

    1. **(a)** "Keep the seam as named." Leave for the tester: in `tests/application/test_interfaces.py` the pin becomes `{"run", "version", "read_transcript"}`; the six stand-ins you list (`WorkspaceRuntime` in tests/container_support.py, `ObservingRuntime` in tests/observing_runtime.py, `HeadNotingRuntime`, `RefusingRuntime`, `SidecarRuntime`, `SwitchingRuntime`) each get a `read_transcript` that returns `None`, or delegates where the stand-in wraps a real runtime (`ObservingRuntime`); nothing else in those modules. Any further `AgentRuntime` stand-in that needs only that method is covered by the same leave, named in the tester's entry.

    2. Yes: `containers.calls()` becomes `containers.calls` in the tester's own `tests/application/test_stage_transcripts.py`.

    3. The Claude Code session lives where the real runtime writes it: `<home>/.claude/projects/*/<session>.jsonl` (`HOME=/work/home` in the container). The tester moves its test file to that path; the coder keeps only that glob and drops `<home>/projects`. Leave for the reviewer: say so in the Interface.

    End with `tests` as you propose.
19. factory: started doing as vm.
20. coder: The human's answer (journal 18) calls for test changes, so this round ends with `tests`. The only code change is the one answer 3 asks of the coder.

    Code change:
    - `src/factory/adapters/claude_runtime.py`: `read_transcript` now looks only in `<home>/.claude/projects/*/<session>.jsonl`. The bare `<home>/projects` glob is gone, and the tuple `_SESSION_FOLDERS` is now the single constant `_SESSION_FOLDER`. `make lint` is green and `mypy --strict` passes on the module. Until the tester moves its test file, `tests/adapters/test_claude_runtime_transcript.py::test_a_session_is_read_from_its_project_folder` stays red.

    Test changes for the tester, all from journal 18:
    1. `tests/application/test_interfaces.py`: the `AgentRuntime` abstract-operations pin becomes `{"run", "version", "read_transcript"}`.
    2. Six `AgentRuntime` stand-ins each get a `read_transcript(home, session)` that returns `None`, except `ObservingRuntime`, which delegates to the runtime it wraps. Nothing else in those modules changes. The six are:
       - `WorkspaceRuntime` (`tests/container_support.py`)
       - `ObservingRuntime` (`tests/observing_runtime.py`)
       - `HeadNotingRuntime` (`tests/application/test_stage_run.py`)
       - `RefusingRuntime` (`tests/application/test_agent_run_probe.py`)
       - `SidecarRuntime` (`tests/application/test_costs.py`)
       - `SwitchingRuntime` (`tests/application/test_stall_environment.py`)
       If another stand-in needs only this method, the same leave covers it; name it in your entry.
    3. `tests/application/test_stage_transcripts.py::test_no_container_and_no_prompt_names_the_transcript_folder`: `containers.calls()` becomes `containers.calls` (it is a property).
    4. `tests/adapters/test_claude_runtime_transcript.py`: the scripted session file moves from `<home>/projects/<folder>/<session>.jsonl` to `<home>/.claude/projects/<folder>/<session>.jsonl`.

    Main choice: I made the one code change answer 3 assigns to the coder now, so the next doing round only has to run `make check` and refactor. The alternative I rejected was to change no code before the tests: that would leave the dropped glob in place for another round.

    Still open:
    - The refactor step and a green `make check` wait for the next doing round, after the tester's changes.
    - I did not rewrite the Description. Journals 9, 13 and 18 leave those edits to the intake or the reviewer:
      - journal 9: remove the days setting, the deletion, criterion 6 and the `removed` log line, and change the smoke test to match;
      - journal 13: the opencode transcript is the run's event stream (`jsonl`);
      - journal 18: the Claude Code session path is `<home>/.claude/projects/*/<session>.jsonl`.
21. factory: started tests as vm.
22. tester: I made the test changes the human approved in journal 18, as the coder's entry 20 listed them. I changed no test beyond what that leave covers.

    Changes:
    1. `tests/application/test_interfaces.py`: the `AgentRuntime` abstract-operations pin is now `{"run", "version", "read_transcript"}`.
    2. I added `read_transcript(home, session) -> Transcript | None` to the stand-ins that derive directly from `AgentRuntime`. Nothing else in those modules changed apart from the `Transcript` import.
       - `ObservingRuntime` (`tests/observing_runtime.py`) delegates to the `FakeAgentRuntime` it wraps.
       - `WorkspaceRuntime` (`tests/container_support.py`), `HeadNotingRuntime` (`tests/application/test_stage_run.py`) and `RefusingRuntime` (`tests/application/test_agent_run_probe.py`) each return `None`. Each also runs `del home, session` so ruff's ARG002 stays green.
       - `SidecarRuntime` (`tests/application/test_costs.py`) and `SwitchingRuntime` (`tests/stall_support.py`, not `test_stall_environment.py` as entry 20 says) both derive from `ObservingRuntime`. They inherit its delegating method, so neither file changed.
       - I found no other `AgentRuntime` stand-in that needed the method.
    3. `tests/application/test_stage_transcripts.py::test_no_container_and_no_prompt_names_the_transcript_folder`: `containers.calls()` is now `containers.calls`, in both places.
    4. `tests/adapters/test_claude_runtime_transcript.py`: both tests now build the session folder at `<home>/.claude/projects/-work-checkout`. I updated the module docstring to match and shortened it to fit the line length.

    Run: `make lint` is green. One run of `uv run pytest -q -n auto` over the changed modules and the modules that use the changed stand-ins (test_interfaces, test_stage_transcripts, test_claude_runtime_transcript, test_agent_run_probe, test_stage_run, test_costs, test_stall_environment, test_stage_launch) passed all 126 tests, with no failures.

    Files changed: tests/application/test_interfaces.py, tests/observing_runtime.py, tests/container_support.py, tests/application/test_stage_run.py, tests/application/test_agent_run_probe.py, tests/application/test_stage_transcripts.py, tests/adapters/test_claude_runtime_transcript.py. Files created: none. Every module imported.

    `lint`: lint: green (0.1 s)
23. factory: started doing as vm.
