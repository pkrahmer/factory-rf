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
  started_at: '2026-10-20T23:32:14.582026Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T23:32:14.576190Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T23:32:14.582026Z'
  stage: intake
---

# The operator guide's records section names its four files

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`docs/operator-guide.md`, *The records*, opens with `records/project-commands.jsonl` alone. The other three files have their own subsections further down: *The known results*, *The stop records* and *The disk record*. Its closing paragraph now ends with F0037-S0001's sentence "A line of any of the four record files that a kill cut, or that is not UTF-8, is skipped when the factory reads the file, so a damaged record file needs no repair". A newcomer reads about "the four record files" before the guide has named three of them. The same paragraph says "The records are telemetry beside the factory log, not a work item's state: they are not committed and nothing reads them to decide anything". Once the closing sentence speaks of all four files, that line reads as true of all four too, and it is not. `KnownResults` reads `known-results.jsonl` to decide whether a stage's check runs. `StopPublisher.publish` reads `stops.jsonl` to push its records to `main`. *The disk record* repeats the claim: "Like the other records it is not committed and nothing reads it to decide anything". This story gives *The records* an opening paragraph that names the four files and states the damage rule once. It limits the telemetry sentence to `project-commands.jsonl` and corrects the disk record's sentence. It changes no code and no test, and adds no section.

## Interface

None: no module under `src/factory/` and no test changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The records*:
   - A new first paragraph, before the paragraph on `project-commands.jsonl`. It says that the state directory's `records/` folder holds four JSON Lines files, not committed (the tick publishes the stop records to `main`'s `factory/stops.jsonl`, see "The stop records on main"): `project-commands.jsonl` (every project command run), `known-results.jsonl` (see "The known results"), `stops.jsonl` (see "The stop records") and `disk.jsonl` (see "The disk record"). It also says that a line of any of them that a kill cut, or that is not UTF-8, is skipped when the factory reads the file, so a damaged record file needs no repair, and that a record appended right after a line a kill cut shares that line and is skipped with it (a whole line that is not UTF-8 costs only itself).
   - The closing paragraph of the `project-commands.jsonl` part no longer has the sentence on the four record files. Its sentence on telemetry speaks of `project-commands.jsonl` alone: it is telemetry beside the factory log, and nothing reads it to decide anything.
   - *The disk record*: "Like the other records it is not committed and nothing reads it to decide anything" becomes a sentence saying that the file is not committed and that the factory uses only its last record that reads whole, to name the previous measure beside the new one at a feature acceptance.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "nothing reads them to decide anything" docs/operator-guide.md; grep -c "Like the other records it is not committed" docs/operator-guide.md
```
Expect: `0`, then `0`

```bash
sed -n '/^### The records/,/^| Field/p' docs/operator-guide.md | grep -c "known-results.jsonl\|disk.jsonl\|stops.jsonl"
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
