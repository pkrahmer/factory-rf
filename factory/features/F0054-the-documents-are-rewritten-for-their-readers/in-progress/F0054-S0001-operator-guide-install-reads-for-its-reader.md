---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 608
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T21:44:51.909141Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T21:44:51.915841Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T21:45:07.857042Z'
  stage: intake
  run: 164f6c5d5a854b05a13e83b7e52e6b90
---

# The operator guide's installing and running an instance reads for the operator

## Description

`docs/operator-guide/install.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The settings tables and the refusals table take the shapes the style page's operator-guide section names (headed `Name`, `What it does`, `Default` and `Example`; the refusals in a table under *The refusals* inside *Configuration*, first column `Refusal`), so that the settings check compares the defaults and the refusal texts with the settings code. The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/install.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/install.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/install.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/install.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/install.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/operator-guide/install.md`, `docs/checked-documents.txt` with one line, links from other documents). There are no signatures and no behaviour comments, so there is nothing that needs its own criterion. It says no code, test or agent file changes.
   Criteria: 1 and 2 are judged by the reviewer against the style page and the old file, as the feature's decision 2 says. 3 is testable by `make documents` printing `documents ok` and the path being on the checked list. 4 is checkable by link resolution. 5 is `make check`. There is no code rule, so no failing side applies.
   Smoke test: `grep -cx "docs/operator-guide/install.md" docs/checked-documents.txt` is runnable. Its Expect line, `1`, is checkable against the output. It runs no pytest.
   Docs criterion: criterion 6 points back to criteria 1 to 4, which say what the document must satisfy and give no sentences to write. It names the facts only by reference to the old file and the code. I accepted this because the whole story is the document and it dictates no text. `docs/decisions.md` is explicitly unchanged.
   Architecture: documents only, inside the documenter's write paths (`docs/*`). No code area is touched.
   Scope: F0054 lists this file as S0001. The story changes no behaviour, which matches the feature's out of scope. `docs/decisions.md`, `docs/runs/` and the playbook are not touched.
   Route: docs-only, because every changed path is a document the documenter may write.
