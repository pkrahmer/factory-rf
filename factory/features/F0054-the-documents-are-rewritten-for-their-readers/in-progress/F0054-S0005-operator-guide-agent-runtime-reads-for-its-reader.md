---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 613
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T00:17:26.058600Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T00:17:05.294071Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T00:17:05.301510Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T00:17:21.039257Z'
  stage: intake
  run: 0c107ab4b5584702a6fcf48c2c12c797
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T00:17:26.058600Z'
  stage: docs-only
---

# The operator guide's the agent runtime reads for the operator

## Description

`docs/operator-guide/agent-runtime.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/agent-runtime.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/agent-runtime.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/agent-runtime.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/agent-runtime.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/agent-runtime.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/operator-guide/agent-runtime.md`, one line in `docs/checked-documents.txt`, links to changed headings) and states that no code, test or agent file changes. Every path is one the documenter may write.
   Criteria: 1 (style, judged by the reviewer), 2 (nothing dropped, compared against the code), 3 (on the checked list, `make documents` prints `documents ok`) and 4 (no broken links) each have one check. The Interface's heading-link rule is covered by criterion 4. The Interface states no limit or validation, so there is no failing side to test. `make check` is criterion 5, and `docs:` is last.
   Smoke test: `grep -cx "docs/operator-guide/agent-runtime.md" docs/checked-documents.txt` runs as written and its `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: it refers to criteria 1 to 4 and names what the reader must know, which is the agent runtime facts kept in the file or its Reference section. It dictates no sentences.
   Architecture: the story changes documents only, so the code layers are untouched. `docs/decisions.md` is explicitly left alone.
   Scope: this is S0005 in the feature's story list, and the work is a document rewrite with no behaviour change. Nothing in the feature's Out of scope is touched.
4. factory: started docs-only as vm.
