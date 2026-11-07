---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 626
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T05:48:44.076997Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T05:48:44.085536Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T05:48:58.672149Z'
  stage: intake
  run: 0adfeb41fe064d398392476350541833
---

# The project guide's page on the pipeline area reads for the developer

## Description

`docs/project-guide/pipeline.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/pipeline.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/pipeline.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/pipeline.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/pipeline.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/pipeline.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete files only (`docs/project-guide/pipeline.md`, `docs/checked-documents.txt` with its one line) and rules for links and headings. It states no code behaviour, and the docs route fits because every path it changes is under `docs/`.
   - Criteria: each can be checked on the documents. `make documents` covers 3 and 4 mechanically, and the reviewer compares the old and new file for 1 and 2. The Interface states no rule with a failing side, so none is missing a criterion. The rule on links to changed headings has criterion 5, and the "linked once" rule has criterion 4.
   - Smoke test: `grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked. It runs no pytest.
   - Docs criterion: criterion 7 says what the reader must know (criteria 1 to 5, meaning the page is true to the code and complete). It quotes no sentences.
   - Architecture: the story only touches a project-guide page, which is a document the documenter may write. No code, test or agent file changes.
   - Scope: S0018 is listed in F0054's stories, and it changes nothing listed in "Out of scope" (`decisions.md`, `docs/runs/`, the playbook).
