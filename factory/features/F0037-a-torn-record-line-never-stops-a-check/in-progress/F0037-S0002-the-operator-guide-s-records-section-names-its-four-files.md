---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 372
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-20T23:37:43.484011Z'
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T23:32:37.728009Z'
  stage: intake
  run: 56c1476914aa4b158a160f3f76abdfc5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T23:32:58.242964Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T23:35:23.683947Z'
  stage: tests
  run: cf89ece99aee4987a94151bd9854ab1f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T23:35:44.232889Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T23:37:22.631660Z'
  stage: doing
  run: 838d93c382454abe8b11867ebe69316a
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T23:37:43.484011Z'
  stage: review
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
3. intake: accepted
   - Interface: "None" is right for a docs-only story. No module or signature is involved, and the story says the documenter touches `docs/operator-guide.md` only.
   - Criteria: no criterion is a test function. Criterion 1 (nothing under `src/` or `tests/` changes) is checked by the stages' entries, criterion 2 by `make check`, and criterion 3 (docs) by the smoke test and `check_documents`. Each docs bullet names the passage and the change. The two rules that change, the telemetry sentence and the disk record sentence, have a bullet and a grep for each. The damage rule, with its failing side (the line after a torn one is skipped with it, a line that is not UTF-8 costs only itself), is covered by the first bullet.
   - Smoke test: all three commands are runnable. I checked the guide: the telemetry sentence and "Like the other records" each occur once now (lines 592 and 662), so `0`, `0` is a real change. The `sed` range ends at the first `| Field` line (582) and needs the new paragraph to hold at least one of the three file names, as the `Expect:` says. No pytest command is involved.
   - Architecture: this is a docs change that touches no layer. The documenter owns `docs/*`.
   - Scope: the story is within F0037's goal of the four record files, and its docs are not in "Out of scope". It is not in the feature's Stories list, but it was proposed by acceptance. Not verified: the claims about `KnownResults`, `StopPublisher.publish` and the disk record's "last record that reads whole" are taken from the story, not read in the code.
4. factory: started tests as self.
5. tester: No tests written. This story only changes the docs, and none of its criteria is a test function.
   - criterion 1 (nothing under `src/` or `tests/` changes): no test function. I changed nothing under `src/` or `tests/`, and `git status` shows no change there.
   - criterion 2 (`make check` stays green): no test function. The project command checks it.
   - criterion 3 (docs, `docs/operator-guide.md` *The records*): no test function. The smoke test and `uv run python -m factory.entry.check_documents` check it in the docs stage.
   Files created: none. Modules the test run could not import: none.
   Because there is no new test, nothing is red on purpose: `make test` passed once (`test: green`, 99.14 % coverage) and `make lint` passed. There was nothing to interpret and nothing is open. For the coder: there is no code to write. The documenter makes the change.

   `lint`: lint: green (0.5 s)
   `test`: test: green (63.3 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes the docs, and the documenter makes its one change, in `docs/operator-guide.md` *The records*.
   - Criterion 1 (nothing under `src/` or `tests/` changes): I changed nothing under `src/` or `tests/`. `git status --short` shows only the factory's `.costs.jsonl` sidecar for this work item.
   - Criterion 2: I ran `make check` and it ended with `check: green` (`test: green (64.1 s)`, coverage 99.14 %).
   - Criterion 3 (docs): left to the docs stage, because the coder does not write `docs/`.
   Main choice: I left the guide untouched instead of making the docs edit in this stage. The story's Interface names the documenter as the only writer, and `CLAUDE.md` says the coder does not write the docs.
   Refactor: there is no diff, so there is nothing to refactor.
   Noticed but not touched: intake did not check the code behind the story's claims, that `KnownResults` reads `known-results.jsonl` to decide a check, that `StopPublisher.publish` reads `stops.jsonl`, and that the disk record uses only its last record that reads whole. I did not check them either. The documenter should confirm them in the code before writing them.
   The journal did not change the meaning of the task.

   `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
   `duplicates`: duplicates: 6 new, 33 known, 3 gone
8. factory: started review as self.
