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
  instance: vm
  stage: intake
  started_at: '2026-11-04T15:57:50.600196Z'
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
