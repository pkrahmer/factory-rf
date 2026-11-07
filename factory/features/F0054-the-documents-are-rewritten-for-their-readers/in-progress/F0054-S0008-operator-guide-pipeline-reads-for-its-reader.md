---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 616
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:20:39.829429Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:20:39.836540Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:20:55.732384Z'
  stage: intake
  run: 85aa48470a8a40dfbc7509742ac9debc
---

# The operator guide's the pipeline definition reads for the operator

## Description

`docs/operator-guide/pipeline.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/pipeline.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/pipeline.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/pipeline.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/pipeline.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/pipeline.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only, `docs/operator-guide/pipeline.md` and `docs/checked-documents.txt`, and states that no code, test or agent file changes. Every path is one the documenter may write, so the story takes the docs route.
   Criteria: all six concern documents only. Criteria 1 and 2 are judged by the reviewer against the style guide and the code. Criterion 3 is checked by `make documents` printing `documents ok`, and criterion 4 by link resolution. Criterion 5 is `make check`. The Interface states no limits, defaults or error rules, so there is no failing side to cover.
   Smoke test: the `grep -cx` command is runnable from the repository root and its `Expect: 1` can be checked against the output. It runs no pytest, so no `-q` issue arises.
   Docs criterion: criterion 6 refers back to criteria 1 to 4, which say what the reader gets (a rewritten operator guide page that is accurate, complete and checked). It dictates no sentences.
   Architecture: documentation only, no code placement. It sits in the operator guide, where CLAUDE.md puts operator material. `docs/decisions.md` is left alone, as the feature requires.
   Scope: this is S0008 of F0054's list. It is one file, and it avoids the feature's Out of scope items (`decisions.md`, `docs/runs/`, the playbook).
