---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 617
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:39:43.325229Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:39:43.332643Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:40:00.049524Z'
  stage: intake
  run: 871a78ae3eb145c787aa0f4e5e53a45b
---

# The operator guide's the records, the bill and the watch reads for the operator

## Description

`docs/operator-guide/records.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/records.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/records.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/records.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/records.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/records.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only: `docs/operator-guide/records.md` (exists; covers the records contract, `factory-bill`, `factory-watch`), `docs/checked-documents.txt` (does not list it yet), link fixes. No code, tests or agent files.
   - Criteria: each is checkable by the reviewer or a command: style compliance (judged), old-versus-new fact comparison (judged), file on the checked list plus `make documents` printing `documents ok`, no dead links, `make check` green. No Interface rule states a limit, default or error, so no failing side is owed.
   - Smoke test: `grep -cx "docs/operator-guide/records.md" docs/checked-documents.txt` is runnable and `Expect: 1` is checkable. It prints 0 now and 1 after the story.
   - Docs criterion: criterion 6 says "as criteria 1 to 4", which name what the reader must know only by reference to style and facts, but it dictates no sentences. I accepted it, since it is the same shape across this feature.
   - Architecture: every path the Interface changes is one the documenter may write (`docs/*`), so the docs route applies. No `factory/` change.
   - Scope: within F0054's scope (one file, one story, S0009) and outside its out-of-scope list (`decisions.md` is untouched).
