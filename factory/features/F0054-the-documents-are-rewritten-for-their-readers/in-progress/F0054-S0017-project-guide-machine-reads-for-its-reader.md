---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 625
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T05:07:33.466602Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T05:07:12.856804Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T05:07:12.864192Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T05:07:28.449664Z'
  stage: intake
  run: 29d84c9e47de4a3da742810a8bc5a650
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T05:07:33.466602Z'
  stage: docs-only
---

# The project guide's page on the machine area reads for the developer

## Description

`docs/project-guide/machine.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/machine.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/machine.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/machine.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/machine.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/machine.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/machine.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it names one concrete file to rewrite (`docs/project-guide/machine.md`), the link rule, the one-line `docs/checked-documents.txt` change, and says no code, test or agent file changes. Every path is one the documenter may write.
   - Criteria: criteria 1 and 2 are judged by the reviewer against the style page and the code. Criteria 3 to 5 are checked by `make documents` and by link checks. Criterion 6 is `make check`. Criterion 7 is the docs criterion. The story states no code rules, so there is no failing side to cover. Each criterion is testable in one pass without further decisions.
   - Smoke test: `grep -cx "docs/project-guide/machine.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output. It runs no pytest, so the `-q` rule does not apply.
   - Docs criterion: it names what the reader must know. The page is rewritten for its reader, every fact is kept or moved to *Reference*, and the examples are runnable. It dictates no sentences.
   - Architecture: the page covers the machine area, which `CLAUDE.md` lists with containers, images, snapshots, disks and the preflight. The story changes only a document in `docs/project-guide/`, so no layer is touched.
   - Scope: this is S0017 in the feature's list, and the feature's scope is each file rewritten with its own story. `decisions.md`, `runs/` and the playbook are not touched. Route: docs-only.
4. factory: started docs-only as vm.
