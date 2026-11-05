---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 555
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T00:06:51.128909Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T00:06:51.136317Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T00:07:09.821781Z'
  stage: intake
  run: 8037b0aac87d47b3824f622d4b22235c
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T00:07:14.746249Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T00:07:33.059428Z'
  stage: tests
  run: 1bee7eb532974451a57b6476e197047e
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T00:07:38.428122Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-05T00:12:13.541453Z'
  stage: doing
  run: de5fb6ac684a44b295738439e6ab0d9d
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-05T00:12:18.857226Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-05T00:12:40.887823Z'
  stage: review
  run: 678fdf08d8f8451289813b4e8d461b52
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T00:12:46.189507Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-05T00:13:08.746559Z'
  stage: docs
  run: a4f64e208a1d4e27ad6d32e3ef9feaef
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T00:13:14.355410Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-11-05T00:13:39.201989Z'
  stage: smoke-test
  run: d182995e609d45dda1b20b5b02638f90
---

# The operator guide's push error example shows the ref line the factory writes

<!-- proposed by F0050's feature acceptance A0003 of 2026-11-05 as F0050-S0015; moved to F0051 by the human, so that it needs no further acceptance of F0050 -->

## Description

The operator guide's example of a counted handler error (`docs/operator-guide.md:2487`, written by F0050-S0008) reads `... PushFailed: push of work-item/F0001-S0001 failed: rejected: remote: Internal Server Error | ! [remote rejected] work-item/F0001-S0001 -> work-item/F0001-S0001 (Internal Server Error)`. That is git's human-readable ref line (`! [remote rejected] <from> -> <to> (<reason>)`). The factory never gets that form, because it pushes with `git push --porcelain` (`GitCli.push`), and `push_reason` turns the porcelain ref line `!<tab>refs/heads/<b>:refs/heads/<b><tab>[remote rejected] (<reason>)` into `! refs/heads/<b>:refs/heads/<b> [remote rejected] (<reason>)`. The feature acceptance F0050-A0003 shows that form in every retry line of its walk-through. An operator who searches the factory log for the example's `-> work-item/` finds nothing. The sentence two paragraphs further on, "a refusal by the server (git's `! [remote rejected]`, ...)", names a string that does not occur in the factory's reasons either: the `!` and `[remote rejected]` are separated by the refs. This story rewrites the example line in the porcelain form and names the marker as `[remote rejected]`, the text `push_is_retried` looks for (`SERVER_REFUSAL`). The rule, the code and the decision log's entries, which are history, stay as they are.

## Interface

- No module under `src/factory/` changes, and no test is written.
- `docs/operator-guide.md`, the example under the handler-error lines: the ref line becomes `! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, and the rest of the line stays as it is.
- `docs/operator-guide.md`, *A refused push is tried again*: "git's `! [remote rejected]`" becomes "git's `[remote rejected]` on the refused ref's line".

## Acceptance criteria

1. The handler-error example in `docs/operator-guide.md` reads `2026-11-04T09:40:41Z handler error <event key> 2 of 3: PushFailed: push of work-item/F0001-S0001 failed: rejected: remote: Internal Server Error | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, and no line of the guide holds `-> work-item/` any more.
2. The paragraph *A refused push is tried again* names the server's refusal as git's `[remote rejected]` on the refused ref's line, and `docs/operator-guide.md` no longer holds the string `` `! [remote rejected]` ``.
3. No other paragraph of `docs/operator-guide.md` changes, and `docs/decisions.md` does not change.
4. `make check` stays green.
5. docs: `docs/operator-guide.md` as criteria 1 to 3 say. `README.md`, the project guide and `docs/decisions.md`: none. The project guide already describes the porcelain form (`docs/project-guide/git-and-hosting.md`), and the decision log's entries are history.

## Smoke test

```bash
grep -c '! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 \[remote rejected\] (Internal Server Error)' docs/operator-guide.md
```

Expect: `1`.

```bash
grep -c -e '-> work-item/' -e '`! \[remote rejected\]`' docs/operator-guide.md
```

Expect: `0`.

```bash
uv run python -c 'from factory.domain.git import push_reason; print(push_reason("!\trefs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001\t[remote rejected] (Internal Server Error)\nDone\n"))'
```

Expect: `! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, the ref line of criterion 1's example.

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: docs-only story, no module or signature changes (stated). The two edits are located and match the guide today: `docs/operator-guide.md:2487` holds the `-> work-item/` example line and line 2498 holds `` `! [remote rejected]` ``. Both are named exactly.
   - Criteria: criterion 1 is checkable by grep (exact line and no `-> work-item/`), criterion 2 by grep (new wording; old string gone), criterion 3 by a diff limited to those two lines and an unchanged `docs/decisions.md`, criterion 4 is `make check`. The story states no new rule, limit or error, so there is no failing side to cover.
   - Smoke test: the greps and the `uv run python -c` command are runnable. The pytest-addopts rule does not apply because none of them runs pytest. Each `Expect:` is checkable (`1`, `0`, the exact ref line). The third command imports `factory.domain.git`, which still exists until S0002, as the feature's build order notes.
   - Architecture: documentation only, with no layer or wrapper involved. The docs criterion names the operator guide, which the documenter keeps.
   - Scope: within F0051 (listed first in its build order, carried over from F0050-A0003). It changes no code, no decision-log entry and no behaviour, so nothing in "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: No tests written, as the Interface says ("No module under `src/factory/` changes, and no test is written"). The story only changes the docs, and its criteria are checked by the smoke test's greps and by the review of the diff, not by pytest.
   - criterion 1 (the example line in the porcelain form, no `-> work-item/` left): no test. The smoke test's first and second grep check it.
   - criterion 2 (`[remote rejected]` on the refused ref's line, `` `! [remote rejected]` `` gone): no test. The smoke test's second grep checks it.
   - criterion 3 (no other paragraph changes, `docs/decisions.md` unchanged): no test. The review of the diff checks it.
   - criterion 4 (`make check` green): the factory's check.
   - criterion 5 (docs): the documenter's criterion.
   Files created: none. Modules the test run could not import: none. No tests were run, because there were no new test files. `make lint` is green. Rejected: a pytest test that greps `docs/operator-guide.md`. The Interface rules it out, and it would make guide wording a code check.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: No change. This story changes only the docs. The Interface says no module under `src/factory/` changes and no test is written, and the tester wrote none. `make test` therefore had no failures to work from, and there is no code to implement.
   - Main choice: I left `docs/operator-guide.md` untouched and left both edits to the documenter, which turns criteria 1 to 3 into the guide's text through criterion 5. CLAUDE.md (*Docs*) says the documenter keeps the operator guide true and the coder does not write it. Rejected: making the two edits here. That would take over the docs stage's work and put this stage's commit outside the coder's part.
   - For the documenter: the two places are still exactly as the Description says. `docs/operator-guide.md:2487` holds the `! [remote rejected] work-item/F0001-S0001 -> work-item/F0001-S0001 (Internal Server Error)` example. `docs/operator-guide.md:2498` holds "git's `` `! [remote rejected]` ``". No other line of the guide holds `-> work-item/` or `` `! [remote rejected]` ``.
   - Refactor: nothing to refactor, because there is no diff.
   - The journal does not change what the task means. The Description stays as written.
   - Noticed, not touched: nothing.

   `make check`: check: green (test: green (116.8 s), total coverage 99.26 %).

   `check`: check: green
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
8. factory: started review as vm.
9. reviewer: no findings

   Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch only adds the work item and its `.costs.jsonl` sidecar. That matches the Interface ("No module under `src/factory/` changes, and no test is written") and the coder's entry 7, which leaves the two guide edits to the documenter, because the docs criterion (5) puts them there.

   1. Acceptance criteria: criteria 1 to 3 are documentation criteria. The documenter meets them through criterion 5, and the smoke test's greps check them. pytest does not, and the Interface rules a test out. The story states no rule or limit, so no failing side or boundary needs a test. The factory's `make check` after the coder was green (entry 7: `check: green`, coverage 99.26 %).
   2. Architecture: nothing under `src/` changed.
   3. Security: nothing changed, and no suppression marker was added.
   4. Quality: no code under review. `make duplicates` reported 4 new findings in entry 7, but this diff changes no code under `src/factory`, so those findings are not this story's.
   5. Work item hygiene: I checked the Description's claims against the code and the guide, without relying on the work item's own account.
      - `docs/operator-guide.md:2487` holds the `-> work-item/` example line.
      - `docs/operator-guide.md:2498` holds "git's `` `! [remote rejected]` ``".
      - `SERVER_REFUSAL = "[remote rejected]"` is at `src/factory/domain/git.py:40`, and `push_is_retried` uses it at line 187.
      - `push_reason` is at `src/factory/domain/git.py:158`.
      - The journal explains the main choice (the edits go to the documenter, not the coder) and what was rejected. Criterion 5 tells the documenter exactly which two lines to change and what to write.
   6. Earlier tests: none. The diff changes no test file.
10. factory: started docs as vm.
11. documenter: Changed `docs/operator-guide.md` only, two lines, as criteria 1 to 3 say:
    - Line 2487, the handler-error example: the ref line is now `! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)`, the porcelain form `push_reason` produces. The rest of the line is unchanged.
    - Line 2498, *A refused push is tried again*: "git's `! [remote rejected]`" now reads "git's `[remote rejected]` on the refused ref's line".

    Checked by running the smoke test's two greps: the first prints 1 and the second prints 0. I did not run the third command, the `push_reason` one. `make check` was not run, as only documents changed. The factory's check decides.

    Cross-read and found current: `README.md` and `docs/project-guide/git-and-hosting.md` need no change (the criterion says the guide already describes the porcelain form), and `docs/decisions.md` is untouched on purpose. No other line of the operator guide holds `-> work-item/` or the old marker string.

    Stale text noticed but not touched: none. No findings for the coder.

    `check`: check: green (not run again: passed on tree e345589ce7fb at 2026-11-05T00:10:05Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
13. smoke-tester: Smoke test run from the repository root. I ran the three commands exactly as written, in order. No server was involved and I fixed nothing.

    1. First grep (the porcelain ref line):
    ```
    1
    ```
    Met `Expect: 1`.

    2. Second grep (`-> work-item/` or `` `! [remote rejected]` ``):
    ```
    0
    ```
    Met `Expect: 0`. grep exited with 1, which is what grep does when it finds no match.

    3. `push_reason` on the porcelain output:
    ```
    Bytecode compiled 4164 files in 47ms
    ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (Internal Server Error)
    ```
    Met the Expect line. The line `uv` prints first is its own bytecode-compile notice. The output from `push_reason` is exactly the ref line that criterion 1's example now shows.

    Check against the acceptance criteria:
    - Criterion 1: met. `grep -nF` finds the full example line exactly as criterion 1 gives it, at `docs/operator-guide.md:2487`, and command 2 shows no `-> work-item/` is left.
    - Criterion 2: met. `docs/operator-guide.md:2498` reads "git's `[remote rejected]` on the refused ref's line", and command 2 shows `` `! [remote rejected]` `` is gone.
    - Criterion 3: met. Against `main`, the branch changes only those two lines (`docs/operator-guide.md`, 2 insertions and 2 deletions). Nothing under `docs/decisions.md`, `README.md`, `src` or `tests` changed.
    - Criterion 4: not re-run here. The factory's `make check` was green after the coder (entry 7), and the documenter's gate reused that result (entry 11).
    - Criterion 5: met, as for criteria 1 to 3.

    No command contradicts any criterion.

    Findings: none.
