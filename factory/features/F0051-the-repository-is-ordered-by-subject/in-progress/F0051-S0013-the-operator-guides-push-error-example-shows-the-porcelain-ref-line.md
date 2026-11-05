---
stage: tests
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
