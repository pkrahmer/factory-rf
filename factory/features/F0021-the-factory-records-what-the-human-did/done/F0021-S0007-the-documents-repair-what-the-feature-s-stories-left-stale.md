---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 242
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T00:54:26.611075Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T00:54:26.617127Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T00:54:47.753710Z'
  stage: intake
  run: 707f745ac3d541ea9d7f881bd182d205
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T00:55:07.692054Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T00:56:43.753529Z'
  stage: tests
  run: 8d60d618fa3e4f4ab95107b05a1509d2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T00:57:03.685853Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T00:58:47.276209Z'
  stage: doing
  run: 20a1975dff374fbe9467ce9d5351d6ed
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T00:59:07.599290Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T00:59:36.526730Z'
  stage: review
  run: 62706da793fa477c959f9075d7bc7577
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T00:59:56.557305Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T01:01:09.681293Z'
  stage: docs
  run: 9a9a4b03cd7a43ce8ac5d84cb3846150
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T01:01:29.669867Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T01:01:51.943657Z'
  stage: smoke-test
  run: df07998406254ed4b1cc8172c3875b4c
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-19T01:03:09.114229Z'
  stage: approval
---

# The documents repair what the feature's stories left stale

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's acceptance read the four documents from the top and found five passages that its stories left stale or wrong. Each story saw only its own sections. First, the project guide's journal example still shows the output it printed before `JournalRecord` gained `blocked` and `reason`. Second, the operator guide's table of the factory's own questions gives a stray "Comment reads" cell for two questions; the table is the one this feature gave a `blocked` column. Third, the project guide's `Boundaries` field list stops at `settings`. Fourth, the decision entry on the stop records gives another reason for leaving out the detail than the feature's decision 2, and leaves out one of decision 1's rejected places. Fifth, the operator guide's opening summary names neither the stop records nor the records contract. This story repairs exactly these five passages and changes no code, no test and no other passage.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide.md`, the journal example under *The journal's data*: the printed record reads `number=2 speaker='intake' kind='result' at=None stage=None run=None blocked=None reason=None`, which is what the example prints today.
   - `docs/project-guide.md`, *Boundaries*: the field list names `disk`, `disk_records` and `stop_records` after `settings`. Each is optional, and each gets one clause pointing to the paragraph that describes it.
   - `docs/operator-guide.md`, *The factory's own questions*, the table: the "Comment reads" cell of "The form has findings" reads `` `factory: ` and the findings question (`The work item's form has findings, so the stage cannot move forward: ...`) ``. The cell of "The round cap" reads `` `factory: ` and the round-cap question (`This work item has now been sent back <n> times, more than <cap>. ...`) ``. No other cell changes.
   - `docs/operator-guide.md`, the opening paragraph: one clause names the stop records published to `factory/stops.jsonl` on `main` and the records contract under `src/factory/contract/`.
   - `docs/decisions.md`, "The stops reach main as raised and cleared records":
     - The reason for leaving the detail out names `make secrets`. It reads every tracked file on `main`, a git error's text can hold a commit id or a URL, and a red `make secrets` on `main` would raise `main_branch_failing`.
     - The "Rejected" line adds a GitHub issue or comment, since the hosting-service interface does pull requests only (R10).
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "run=None blocked=None reason=None" docs/project-guide.md
```

Expect: `1`

```bash
grep -E '^\| (The form has findings|The round cap) \|' docs/operator-guide.md | grep -c 'time_limit'
```

Expect: `0`

```bash
awk '/^## The stops reach main as raised and cleared records/{p=1;next} /^## /{p=0} p' docs/decisions.md | grep -c 'make secrets'
```

Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a documents-only story. It names the three documents the documenter changes and says no module, test, image, template or agent file changes.
   Criteria: Each docs bullet is one checkable passage (a literal string, a cell, a field list, a clause), so one check can test each. The two rules the story states have both sides: "No other cell changes" and "No other passage changes" with `documents ok` are the failing side. Criterion 1 (nothing outside `docs/` changes) is checkable by a diff. I checked the passages against the current files. The journal example at project-guide line 496 ends `run=None`, with no `blocked` or `reason`. The two operator-guide cells (lines 601-602) hold the `time_limit` text under the `Comment reads` header. The `Boundaries` text in project-guide mentions `disk_records` and `stop_records`. The decisions section "The stops reach main as raised and cleared records" exists at line 616.
   Smoke test: All four commands are runnable. Each `Expect:` line is a count or an exact output that can be checked. The second test greps the two rows for `time_limit`, which sits only in the `Comment reads` cell being replaced, so `0` is right after the change.
   Architecture: No layer is touched.
   Scope: The story repairs the five passages the feature acceptance found and nothing else. It stays inside the feature's docs paths, and nothing in `feature.md`'s Out of scope covers it.
4. factory: started tests as self.
5. tester: No tests written, because this story only changes documents. Its Interface says no module under `src/factory/` and no test changes, and none of its criteria describes behaviour that code could test.
   criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test. A diff checks it, and on the tester's side nothing under those paths changed. `git status` shows only the work item's `.costs.jsonl` sidecar, which is the factory's.
   criterion 2 (`make check` stays green): no test; this is the factory's check after the stage.
   criterion 3 (docs): no test. These are the documenter's passages, checked by `make documents` / `python -m factory.entry.check_documents` and by the story's smoke test.
   Files created: none. Modules the test run could not import: none. `make test` is green: 99.06 % coverage, nothing red on purpose, since the coder has no code to write. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.1 s)
6. factory: started doing as self.
7. coder: Nothing built. This story changes only documents. Its Interface says no module, test, image, template or agent file changes, and the tester wrote no tests, so there was no failing test to make pass.
   criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed on my side either. `git status --short` shows only the work item's `.costs.jsonl` sidecar, which is the factory's.
   criterion 2: `make check` is green (check: green; test: green, coverage 99.06 %).
   criterion 3 (docs): left for the documenter. The five passages in `docs/project-guide.md`, `docs/operator-guide.md` and `docs/decisions.md` are not the coder's to write.
   Main choice: leave the docs to the docs stage. I rejected editing the three documents now, because CLAUDE.md gives them to the documenter alone. Refactor: there is no diff, so nothing to refactor. The journal did not change the task's meaning, so the Description stays as it is. Noticed but not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar (`git diff --name-status main...HEAD`), so criterion 1 holds: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed. Entries 5 and 7 each say so. Entry 7 shows the factory's `make check` was green after the coder (`check: green`). `duplicates: 0 new` means no new similar or dead code to read. No criterion describes behaviour that code could test, so the tester writing no tests is right.

   The docs criterion is the documenter's next input, so I checked it against the code and documents on this branch. It still matches:
   - `JournalRecord` (`src/factory/domain/journal.py:72-79`) ends with `run`, `blocked` and `reason`, all `None` by default. The example at `docs/project-guide.md:496` still prints only up to `run=None`.
   - `Boundaries` (`src/factory/application/boundaries.py:44-47`) has `disk`, `disk_records` and `stop_records` after `settings`, all optional.
   - `docs/operator-guide.md:601-602` still hold the stray `time_limit` cells. The two question texts the criterion quotes match `src/factory/domain/post_texts.py:80` and `:92`.
   - The section "The stops reach main as raised and cleared records" exists at `docs/decisions.md:616`.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
10. factory: started docs as self.
11. documenter: Files changed, all documents, so I did not run `make check` (the factory's run after this stage is the gate):
    - `docs/project-guide.md`: the journal example now prints `... run=None blocked=None reason=None`. The `Boundaries` field list now ends with `disk`, `disk_records` and `stop_records`, each optional and each with one clause pointing to the tick's step 0, the `DiskRecord` paragraph and "Stop records".
    - `docs/operator-guide.md`: the "Comment reads" cells of "The form has findings" and "The round cap" now hold the `factory: ` text with the findings question and the round-cap question. No other cell changed. The opening paragraph now names the stop records on `factory/stops.jsonl` and the records contract under `src/factory/contract/`.
    - `docs/decisions.md`, "The stops reach main as raised and cleared records": the reason for leaving the detail out now names `make secrets` (every tracked file on `main`, a commit id or URL in a git error's text, `main_branch_failing`). The "Rejected" line adds a GitHub issue or comment (the hosting-service interface does pull requests only, R10).

    Checks I ran: `python -m factory.entry.check_documents` prints `documents ok`. The first smoke-test grep (`run=None blocked=None reason=None`) gives 1.

    Cross-read and found current against the (empty) code diff: the `Boundaries` description in `src/factory/application/boundaries.py` and the two question texts in `post_texts.py`, as the reviewer also checked.

    Stale text I noticed and did not touch: none.

    Code findings: none. The branch changes nothing under `src/` or `tests/`.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed with no findings. I ran all four commands from the repository root, exactly as written and in order.

    1. `grep -c "run=None blocked=None reason=None" docs/project-guide.md`
    ```
    1
    ```
    Met: `Expect: 1`.

    2. `grep -E '^\| (The form has findings|The round cap) \|' docs/operator-guide.md | grep -c 'time_limit'`
    ```
    0
    ```
    Met: `Expect: 0`. The exit status is 1, which is normal for `grep -c` when nothing matches.

    3. `awk '/^## The stops reach main as raised and cleared records/{p=1;next} /^## /{p=0} p' docs/decisions.md | grep -c 'make secrets'`
    ```
    1
    ```
    Met: `Expect: 1`.

    4. `uv run python -m factory.entry.check_documents`
    ```
    documents ok
    ```
    Met: `Expect: documents ok` (exit 0).

    Criteria read again against `git diff main...HEAD`:
    - Criterion 1: holds. The branch changes only `docs/decisions.md`, `docs/operator-guide.md`, `docs/project-guide.md`, the work item and its `.costs.jsonl` sidecar. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed. Entries 5 and 7 each say so.
    - Criterion 2: entry 11 records `check: green` after the docs stage. I did not run `make check` myself, because this stage only runs the smoke test.
    - Criterion 3, project guide: the journal example prints the required record. The `Boundaries` list adds the optional `disk`, `disk_records` and `stop_records` after `settings`, each with one clause pointing to the tick's step 0, the `DiskRecord` paragraph and "Stop records".
    - Criterion 3, operator guide: the cells of "The form has findings" and "The round cap" read word for word as the criterion quotes them, and no other row of the table changed. The opening paragraph has one clause naming the stop records on `factory/stops.jsonl` on `main` and the records contract under `src/factory/contract/`.
    - Criterion 3, decision log: the stops section gives `make secrets` as the reason for leaving out the detail (every tracked file on `main`, a commit id or URL in a git error's text, `main_branch_failing`). The "Rejected" line adds a GitHub issue or comment, citing R10.
    - No other passage changed: the diff touches only these five passages, and `check_documents` prints `documents ok`.

    Nothing is open.
14. factory: done (pull request merged); cost: 6 runs, 3.3 min, 32 turns, 91715 tokens in (419802 more from cache), 8516 out, $0.77
