---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 614
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T00:42:00.199810Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T00:42:00.207016Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T00:42:18.510260Z'
  stage: intake
  run: d94a1610a34048dc9c1b92f1c0fa1371
---

# The operator guide's the preflight, the health check and the log reads for the operator

## Description

`docs/operator-guide/health.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/health.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/health.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/health.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/health.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/health.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/operator-guide/health.md` exists; `docs/checked-documents.txt` exists and does not yet list it). It changes only documents and no code, test or agent file, so the docs route fits.
   - Criteria: all six are about documents and each can be judged or checked. 1 and 2 are the reviewer's comparison, 3 is `make documents`, 4 is a link check, 5 is `make check`. The Interface states no behaviour or rule with a failing side, so no criterion is missing.
   - Smoke test: `grep -cx "docs/operator-guide/health.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output.
   - Docs criterion: it names the reader (an operator who knows Linux and does not read the code) and what the file must hold (the facts of the old file, corrected against the code). It quotes no sentences to write.
   - Architecture: no code is touched, so nothing conflicts with the layers in `CLAUDE.md`.
   - Scope: the story is S0006 of F0054's list and in its scope. It touches none of the out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`).
