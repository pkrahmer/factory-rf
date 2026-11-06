---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 610
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T22:56:08.353005Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T22:56:08.360408Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T22:56:25.002334Z'
  stage: intake
  run: 97a9d5fcadaa4232aa87610a67507be2
---

# The operator guide's the site file and an operator's machine reads for the operator

## Description

`docs/operator-guide/site.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/site.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/site.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/site.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/site.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/site.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `docs/operator-guide/site.md` (exists) and `docs/checked-documents.txt` (exists; its entry is one added line). Both are paths the documenter may write; no code, test or agent file changes.
   - Criteria: all are about documents. Criterion 1 is the style judgment (reviewer). Criterion 2 is the fact comparison against the code (reviewer). Criterion 3 is testable with `make documents` printing `documents ok`, plus the checked-list entry. Criterion 4 is a link check. Criterion 5 is `make check`. The Interface states no behaviour or rule that needs a failing side.
   - Smoke test: `grep -cx "docs/operator-guide/site.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It runs no pytest.
   - Docs criterion: criterion 6 asks for criteria 1 to 4 and names no sentences to write. It dictates no text. It says what the reader must know only through the Description: an operator who runs an instance and does not read the code.
   - Architecture: nothing in `src` changes. This is a document rewrite on the docs route, checked by the F0053 document checks.
   - Scope: it is S0002 of F0054, which lists it. It stays inside the feature's scope (one file rewritten and added to the checked list). It touches none of the feature's out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`) and changes no behaviour.
