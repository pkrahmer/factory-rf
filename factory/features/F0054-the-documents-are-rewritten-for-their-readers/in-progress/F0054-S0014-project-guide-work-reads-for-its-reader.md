---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 622
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T03:48:17.098338Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T03:47:57.817768Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T03:47:57.825123Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T03:48:12.406452Z'
  stage: intake
  run: 10e66264532943fd8db09367d103f89d
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T03:48:17.098338Z'
  stage: docs-only
---

# The project guide's page on the work area reads for the developer

## Description

`docs/project-guide/work.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/work.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/work.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/work.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/work.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/work.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/work.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/project-guide/work.md`, `docs/checked-documents.txt` with exactly one line), states link and heading rules, and says no code, test or agent file changes. It contains no signatures to test, since the story only changes documents.
   Criteria: 1 to 5 can each be judged or checked. The style and the old-versus-new comparison go to the reviewer, as the feature's decision 2 says. The checked list, `documents ok` and broken links are checked by `make documents`. The Interface states no rule with a failing side beyond the link and heading rules, which criteria 4 and 5 cover. 6 is `make check`.
   Smoke test: `grep -cx "docs/project-guide/work.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It runs no pytest.
   Docs criterion: it names what the reader must know, in the form "as criteria 1 to 5", and dictates no sentences. `docs/decisions.md` is stated as none.
   Architecture: the only paths changed are `docs/project-guide/work.md` and `docs/checked-documents.txt`, both documents the documenter may write. The docs-only route is chosen because the story changes only documents.
   Scope: it is S0014 of F0054, one file, and the feature scope lists "each of the 22 files, one story each". It touches nothing in the feature's Out of scope: `docs/decisions.md`, `docs/runs/`, the operator playbook and behaviour changes.
4. factory: started docs-only as vm.
