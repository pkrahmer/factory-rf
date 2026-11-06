---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 611
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-06T23:21:18.692790Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T23:20:58.705028Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T23:20:58.712080Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T23:21:13.433043Z'
  stage: intake
  run: 1d57cf013bc0402d8e8c1c995fd325ad
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T23:21:18.692790Z'
  stage: docs-only
---

# The operator guide's the machine reads for the operator

## Description

`docs/operator-guide/machine.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/machine.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/machine.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/machine.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/machine.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/machine.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names one concrete document (`docs/operator-guide/machine.md`) and `docs/checked-documents.txt`; both are paths the documenter may write, and it states no code, test or agent file changes, so the docs route fits.
   Criteria: 1 and 2 are judged by the reviewer against `docs/project-guide/style.md` and the code, as the docs route intends. 3 is checkable by `make documents` printing `documents ok` plus the list entry. 4 is checkable by following links. 5 is `make check`. The Interface states no behaviour or rule beyond the document rewrite, so no failing-side criterion is missing.
   Smoke test: `grep -cx "docs/operator-guide/machine.md" docs/checked-documents.txt` is runnable, and `Expect: 1` is checkable. It runs no pytest.
   Docs criterion: criterion 6 names what the reader must know (criteria 1 to 4) and quotes no sentences to write.
   Architecture: documents only, no code, so CLAUDE.md's layers are not touched. Operator-guide docs sit in the documenter's write paths.
   Scope: this is S0003 of F0054, listed in `feature.md`. It touches nothing in the feature's Out of scope (`decisions.md`, `docs/runs/`, `operator-playbook.md`, no behaviour change).
4. factory: started docs-only as vm.
