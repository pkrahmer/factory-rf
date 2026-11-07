---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 623
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T04:12:31.267176Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T04:12:31.274946Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T04:12:45.946559Z'
  stage: intake
  run: f9c96d4ca24f45e6a60fd82371ed819b
---

# The project guide's page on the agents area reads for the developer

## Description

`docs/project-guide/agents.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/agents.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/agents.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/agents.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/agents.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/agents.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/project-guide/agents.md`, `docs/checked-documents.txt` with its one line), and says no code, test or agent file changes. Every path it changes is one the documenter may write.
   - Criteria: on the docs route there are no tests, so criteria 1 and 2 are judged by the reviewer against `docs/project-guide/style.md` and the code. Criteria 3 to 5 are checked by `make documents` (`documents ok`, no broken link) and by the link rule. Criterion 6 is `make check`. The failing side is covered: a dropped fact, a broken link and a missing checked-list entry each fail a criterion.
   - Smoke test: `grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It does not run pytest.
   - Docs criterion (7): says docs are as criteria 1 to 5 and `docs/decisions.md` is unchanged. It names what the reader must know and dictates no sentences.
   - Architecture: a documents-only change to the project guide's page on the agents area. It touches nothing in `factory/`, `src/` or `tests/`, and the story does not use the `.claude/` or `planning/` paths.
   - Scope: within F0054's scope (S0015 is listed, one file per story). It touches nothing in the feature's out-of-scope list (`decisions.md`, `docs/runs/`, the operator playbook, behaviour changes).

   Route: docs-only.
