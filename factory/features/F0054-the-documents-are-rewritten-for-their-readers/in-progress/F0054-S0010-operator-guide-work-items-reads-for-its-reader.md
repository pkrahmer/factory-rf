---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 618
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:07:21.054390Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:07:21.061631Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:07:35.545760Z'
  stage: intake
  run: da90882f7e2948c7b810fb77bc7154f8
---

# The operator guide's work items, approval and merges reads for the operator

## Description

`docs/operator-guide/work-items.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/work-items.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/work-items.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/work-items.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/work-items.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/work-items.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names `docs/operator-guide/work-items.md` and `docs/checked-documents.txt` with its one line. Both are paths the documenter may write. No code, test or agent file changes, and no behaviour is stated in it that would need its own criterion.
   Criteria: each can be judged on the docs route. Criteria 1 and 2 are the reviewer's comparison against the style guide and the code. Criterion 3 is checked by `make documents` printing `documents ok`. Criterion 4 is a link check and criterion 5 is `make check`. The Interface states no limit, validation or default, so there is no failing side to cover.
   Smoke test: `grep -cx "docs/operator-guide/work-items.md" docs/checked-documents.txt` is runnable as written. Its `Expect: 1` can be checked against the output. It does not run pytest.
   Docs criterion: criterion 6 asks for criteria 1 to 4 and names no sentences to write. `docs/decisions.md`: none.
   Architecture: the change touches documents only. It fits CLAUDE.md's split between the operator guide, the project guide and the README.
   Scope: it is S0010 in the feature's list. It touches no file the feature lists as out of scope. I made no change to the story.
