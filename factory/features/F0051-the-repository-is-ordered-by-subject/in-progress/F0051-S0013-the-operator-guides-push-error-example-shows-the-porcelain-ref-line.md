---
stage: review
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
