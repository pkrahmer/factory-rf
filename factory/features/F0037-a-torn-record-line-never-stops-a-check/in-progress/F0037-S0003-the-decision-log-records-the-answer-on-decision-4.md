---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 377
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:10:45.897427Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:10:45.902880Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T00:11:01.312971Z'
  stage: intake
  run: 1448a0989cd340f3b87f53466c61e84d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T00:11:22.111230Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T00:12:43.904150Z'
  stage: tests
  run: 56b93b64c0864db4ad90035870eb0861
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T00:13:04.819245Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T00:14:35.547802Z'
  stage: doing
  run: bd2a50c73ae4474ea2548ae2f6eb259f
---

# The decision log records the human's answer on F0037's decision 4

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`docs/decisions.md` has the entry *A record line that is not UTF-8 is skipped* (F0037-S0001). It ends with "Open (decision 4): a record appended after a torn line lands on the torn line's line and is skipped with it. A later story may start a new line first." The human answered decision 4 on 2026-10-20, after that entry was written: it is left, and no later feature makes `append` start on a new line after a torn one. The answer is in F0037's `feature.md` (decision 4) and nowhere in the documents. An agent that reads the decision log before it changes the record log would find the point still open and might propose the change the human turned down. This story replaces the entry's open point with the answer and its reason: before each append the writer would have to read the file's last byte, which two writers can race, and the loss is one telemetry record per kill. It changes no code and no test. The project guide's sentence that a record appended after a torn line shares its line and is skipped with it stays as it is, because it is still true.

## Interface

None: no module under `src/factory/` changes and no test is written. The documenter changes `docs/decisions.md` only.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, the entry *A record line that is not UTF-8 is skipped*. The bullet "Open (decision 4): …" becomes a bullet that starts with "Answered (decision 4, the human, 2026-10-20):". It says that a record appended after a torn line still lands on the torn line's line and is skipped with it, and that no later feature changes `append`. Its reason is that the writer would need to read the file's last byte before each append, which two writers can race, while the loss is one telemetry record per kill. The entry's date line names decision 4 beside 1, 2, 3 and 5. No other entry and no other document changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "A later story may start a new line first" docs/decisions.md; grep -c "Answered (decision 4, the human, 2026-10-20)" docs/decisions.md
```
Expect: `0`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None", and that fits: only `docs/decisions.md` changes. No module or signature is needed.
   - Criteria: criterion 3 names the exact edit (the "Open (decision 4)" bullet, line 890 of `docs/decisions.md`, becomes "Answered (decision 4, the human, 2026-10-20):"). It gives the content, the reason, the date line and the `check_documents` result. Criterion 1 (nothing under `src/` or `tests/` changes) and criterion 2 (`make check`) are checkable. The story has no Interface rules or behaviours, so no failing side is missing. The tester has no test to write and should say so in its entry.
   - Smoke test: both commands are runnable. The grep expectations `0` then `1` and the `documents ok` line can be checked against the output. No pytest command, so no `-q` problem.
   - Architecture: a documentation-only change, which the documenter stage's write paths allow. It touches no layer.
   - Scope: it matches F0037's decision 4 (answered by the human, 2026-10-20) and touches nothing in the feature's "Out of scope". The `docs/decisions.md` entry exists as the story describes.
4. factory: started tests as self.
5. tester: No tests written. This story only changes the documentation, and its Interface says no test is written.
   - criterion 1 (nothing under `src/` or `tests/` changes): this entry is the tester's half of it. I created and changed no file under `src/` or `tests/`, and `git status` shows no change there.
   - criterion 2 (`make check` stays green): no test of its own. The factory's checks cover it.
   - criterion 3 (the decision-log entry, and `check_documents` prints `documents ok`): no test. It is the documenter's change to `docs/decisions.md`, checked by the story's smoke test and `make documents`.
   Files created: none. Modules the test run could not import: none. I added no test, so there was no failing run to look at and I did not run `make test`. `make lint` is green. Nothing is open.

   `lint`: lint: green (0.5 s)
   `test`: test: green (62.9 s)
6. factory: started doing as self.
7. coder: No code changed. This story only changes documentation, and its Interface says no module under `src/factory/` changes. The edit to `docs/decisions.md` is the documenter's work, not the coder's.
   - Criterion 1 (nothing under `src/` or `tests/` changes): this entry is the coder's half of it. I created and changed no file. `git diff main --stat -- src tests` is empty.
   - Criterion 2: `make check` is green (`test: green (60.7 s)`, `check: green`).
   - Criterion 3: left to the documenter. The bullet "Open (decision 4): …" in the entry *A record line that is not UTF-8 is skipped* becomes "Answered (decision 4, the human, 2026-10-20): …", with the reason, and the entry's date line names decision 4.
   - Main choice: I left `docs/` alone, even though the edit is small. CLAUDE.md gives the decision log to the documenter stage. The alternative I rejected was writing the bullet myself in this stage.
   - Refactor: there is no diff, so there was nothing to refactor.
   - Noticed but did not touch: nothing.

   `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:21:09Z)
   `duplicates`: duplicates: 6 new, 33 known, 3 gone
