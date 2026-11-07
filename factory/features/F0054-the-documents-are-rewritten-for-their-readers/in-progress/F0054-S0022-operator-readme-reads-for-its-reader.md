---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 630
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T09:25:47.414080Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T09:25:27.205799Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T09:25:27.213456Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T09:25:42.661061Z'
  stage: intake
  run: 909f335fda7046d79c5bb6b009ebde27
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T09:25:47.414080Z'
  stage: docs-only
---

# The operator folder's README reads for its reader

## Description

`operator/README.md` is rewritten for its reader, a developer who opens the `operator/` folder (the skill staged there and the folder's scripts), in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `operator/README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `operator/README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `operator/README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `operator/README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "operator/README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `operator/README.md` and `docs/checked-documents.txt` (one line, `operator/README.md`) and states that no code, test or agent file changes. Both paths are ones the documenter may write, so the story takes the docs route.
   - Criteria: all concern documents only. Criterion 1 is the reviewer's judgment against style.md. Criterion 2 is the reviewer's comparison of old and new file against the code. Criterion 3 is checked by the file being on the list and `make documents` printing `documents ok`. Criterion 4 is a link check. Criterion 5 is `make check`. The story states no code rules, so there is no failing side to cover.
   - Smoke test: `grep -cx "operator/README.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output. It runs no pytest.
   - Docs criterion: criterion 6 points to criteria 1 to 4, which say what the document must satisfy (facts kept or moved to Reference, claims corrected, examples runnable or marked, links intact). It quotes no sentences to write. `docs/decisions.md` is named as unchanged.
   - Architecture: only a document and the checked list change. No layer or module is touched.
   - Scope: within F0054, where S0022 is listed and the story is one file. `operator/README.md` is not in the feature's "Out of scope" list, and the story changes no behaviour.
4. factory: started docs-only as vm.
