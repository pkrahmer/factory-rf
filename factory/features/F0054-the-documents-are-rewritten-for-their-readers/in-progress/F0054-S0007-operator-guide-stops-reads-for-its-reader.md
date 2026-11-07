---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 615
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:01:31.999464Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:01:32.006481Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:01:46.356028Z'
  stage: intake
  run: b042b84a37d0422eba00902f2941d37f
---

# The operator guide's the stops reads for the operator

## Description

`docs/operator-guide/stops.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/stops.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/stops.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/stops.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/stops.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/operator-guide/stops.md`, `docs/checked-documents.txt`); it changes only documents the documenter may write, with no code, test or agent file.
   Criteria: criteria 1 to 4 are checkable against the files (style rules and the old-versus-new comparison by the reviewer, `make documents` printing `documents ok`, links resolving). The Interface states no behaviour or rule beyond the document list, so no failing side is missing.
   Smoke test: `grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt` is runnable, and its `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: criterion 6 says "as criteria 1 to 4", so it names what the reader must know (the stops, from the code) and dictates no sentences.
   Architecture: documents only; it matches the docs route and the CLAUDE.md docs split.
   Scope: it is one of the 22 per-file stories of F0054 (S0007), and `decisions.md` is untouched, which is outside the Out of scope list.
