---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 621
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T03:23:23.549037Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T03:23:23.556207Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T03:23:38.463034Z'
  stage: intake
  run: a5f213ccc4ed4c88af53b22d7be4159e
---

# The project guide's page on the hosting area reads for the developer

## Description

`docs/project-guide/hosting.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/hosting.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/hosting.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/hosting.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/hosting.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/hosting.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/hosting.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/project-guide/hosting.md`, `docs/checked-documents.txt`); it states no code signatures and changes no code, test or agent file. Every path is one the documenter may write, so the route is docs-only.
   Criteria: 1 to 5 are checkable by the reviewer or by `make documents` (style, old-versus-new facts, the checked list, links, no dangling headings). Criterion 6 is `make check`. The Interface's behaviours (link once at first mention, the one-line checked list, changed headings relinked) are covered by criteria 4, 3 and 5. No rule states a failing side that needs its own criterion; broken links and unresolved names are the failing side of criteria 3 and 4.
   Smoke test: `grep -cx "docs/project-guide/hosting.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output.
   Docs criterion: criterion 7 points to criteria 1 to 5 (what the reader must know: the hosting area's names, rules and commands, true to the code). It dictates no sentences.
   Architecture: the story touches only documents, so the code's layering is not involved. It stays on the project guide's hosting page, which matches CLAUDE.md's docs layout.
   Scope: it is S0013 of F0054, one file rewritten and added to the checked list. It touches nothing in the feature's Out of scope (`decisions.md` is explicitly "none").
