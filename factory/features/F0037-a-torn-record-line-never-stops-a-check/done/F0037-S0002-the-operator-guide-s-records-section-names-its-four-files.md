---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 372
comments_read: []
handed_over: approval
claim: null
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
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T23:38:02.768961Z'
  stage: review
  run: 66e624c22b3a4ce7b27fd3f087d9e892
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T23:38:23.378274Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T23:38:44.367157Z'
  stage: docs
  run: 8630d0bd93934492b26bbb8d430d09d6
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T23:39:04.833339Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T23:39:26.680027Z'
  stage: smoke-test
  run: b40d68fcb35b48faa18b5a8c863c4c87
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-20T23:40:46.510192Z'
  stage: approval
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
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are this work item and its `.costs.jsonl` sidecar, both under `factory/`. Criterion 1 holds: nothing under `src/` or `tests/` changed.
   - Criterion 2: the coder's entry 7 records `check: green`, reused from the passed result on tree 4c5c6c3d981c. The record `duplicates: 6 new` cannot come from this story because the diff is empty.
   - Criterion 3 is the documenter's work. Intake and the coder had both left the story's code claims unchecked, so I read the code behind them. All three are true, and the docs criterion is sound to write from:
     - `KnownResults.run` reads `known-results.jsonl` through `_read` to decide whether a result is reused (`src/factory/application/known_results.py:33`).
     - `stops.jsonl` is published to `factory/stops.jsonl` on `main` by `src/factory/application/stops.py:132`.
     - `DiskRecorder.last` takes the last record the reader returns (`src/factory/application/disk_records.py:42`). Acceptance uses it as the previous measure (`src/factory/application/acceptance.py:160`).
     - All four files sit under `records/` (`src/factory/entry/wiring.py:138-141`).
   - The Description matches the plan: the code and tests are unchanged and the change is left to the documenter.
   - Earlier tests: the diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Files changed: `docs/operator-guide.md` only, in *The records* and *The disk record*.
    - *The records*: a new first paragraph names the four files under `records/` (`project-commands.jsonl`, `known-results.jsonl`, `stops.jsonl`, `disk.jsonl`) and points to the sections for the last three. It says none is committed, and that the tick publishes the stop records to `main`'s `factory/stops.jsonl`. It states the damage rule once: a line a kill cut, or that is not UTF-8, is skipped. A record appended right after a cut line is skipped with it, and a whole non-UTF-8 line costs only itself.
    - The `project-commands.jsonl` closing paragraph lost the "four record files" sentence. Its telemetry sentence now speaks of `project-commands.jsonl` alone.
    - *The disk record*: "Like the other records it is not committed and nothing reads it to decide anything" now says the file is not committed and that the factory uses only its last record that reads whole, to name the previous measure at a feature acceptance.

    Checks: `uv run python -m factory.entry.check_documents` printed `documents ok`. `grep -c "nothing reads them to decide anything"` gives 0. I did not run `make check`, because I changed only a document. I did not re-read the code. The reviewer's entry 9 had already confirmed these claims at `known_results.py:33`, `stops.py:132` and `disk_records.py:42`.

    Cross-read: the rest of *The records*, its three subsections and *The stop records on main* agree with the new text. Findings for the coder: none. Nothing under `src/` or `tests/` changed. Stale text noticed but not touched: none.

    `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test run from the repository root, commands as written, in order. No findings.

    1. `grep -c "nothing reads them to decide anything" docs/operator-guide.md; grep -c "Like the other records it is not committed" docs/operator-guide.md`
    ```
    0
    0
    ```
    Expect `0`, then `0`: met.

    2. `sed -n '/^### The records/,/^| Field/p' docs/operator-guide.md | grep -c "known-results.jsonl\|disk.jsonl\|stops.jsonl"`
    ```
    1
    ```
    Expect a number of at least `1`: met. All three names are on one line, the new first paragraph, and `grep -c` counts lines.

    3. `uv run python -m factory.entry.check_documents`
    ```
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
             If the cache and target directories are on different filesystems, hardlinking may not be supported.
             If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
    Installed 106 packages in 87ms
    Bytecode compiled 4164 files in 356ms
    documents ok
    ```
    Expect `documents ok`: met. The lines above it are uv setting up a fresh virtual environment, not output from the check.

    Criteria, checked against `git diff main...HEAD`:
    - Criterion 1: the diff touches only `docs/operator-guide.md` and this work item with its `.costs.jsonl` file. Nothing under `src/` or `tests/` changed.
    - Criterion 2: I did not run `make check`, because this stage runs only the smoke test. Entries 7 and 11 record `check: green` on tree 4c5c6c3d981c, and the factory runs the checks itself.
    - Criterion 3, *The records*: the new first paragraph comes before the `project-commands.jsonl` paragraph. It names the four files, says none is committed, and points to "The stop records on main" for the publishing to `main`. It points to "The known results", "The stop records" and "The disk record". It states the damage rule once, including that the record after a cut line is skipped with it and that a whole non-UTF-8 line costs only itself.
    - Criterion 3, closing paragraph of the `project-commands.jsonl` part: the four-files sentence is gone, and the telemetry sentence now speaks of `project-commands.jsonl` alone.
    - Criterion 3, *The disk record*: the sentence now says the file is not committed and that the factory uses only its last record that reads whole, to name the previous measure at a feature acceptance.
    - Criterion 3, no other passage: the diff changes only those three places.

    Nothing is open.
14. factory: done (pull request merged); cost: 6 runs, 4.1 min, 29 turns, 91965 tokens in (412149 more from cache), 7745 out, $0.79
