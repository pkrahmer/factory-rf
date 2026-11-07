---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 629
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T08:52:56.845747Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T08:52:56.852774Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T08:53:14.015007Z'
  stage: intake
  run: 2ef7ecf4ac59493d923e2804b97ca887
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T08:53:18.729510Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T08:58:56.854623Z'
  stage: docs-only
  run: 55358520de1a4333b727145fb649f6a3
---

# The README reads for a newcomer

## Description

`README.md` is rewritten for its reader, a newcomer who opens the repository for the first time, in the style of `docs/project-guide/style.md` (what the factory is for in plain words, then how to try it in a few commands, then where to read next). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it names concrete paths only: `README.md`, `docs/checked-documents.txt` (one line, `README.md`), links from other documents, and "no code, test or agent file changes". Every path is one the documenter may write, so the docs route fits.
   - Criteria: criteria 1 to 4 are judged by the reviewer or checked by `make documents` and a link check, which is the docs route's form. The Interface rule "a section another file links to keeps its heading, or the link changes with it" has its own criterion (4). The failing side, a dropped fact or a broken link, is covered by criteria 2 and 4. The Description's rule that every shown command is runnable or marked for the VM, GitHub or a model falls under criterion 3 ("runnable examples pass") and criterion 1 (style).
   - Smoke test: `grep -cx "README.md" docs/checked-documents.txt` is runnable and `Expect: 1` is checkable. It doesn't run pytest.
   - Docs criterion: criterion 6 refers to criteria 1 to 4 for what the reader must know and dictates no sentences. `docs/decisions.md` is marked "none".
   - Architecture: it is a documents-only change, with no layer or module touched.
   - Scope: the story is S0021 in `feature.md`'s list and within its scope. It touches none of the out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`).
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `README.md`: rewritten for a newcomer, following `docs/project-guide/style.md`. It now has what the factory is, "Try it" (`uv sync`, `make check`), "Where to read next" (one line per document, with relative links), and a closing *Reference*.
   - `docs/checked-documents.txt`: added the line `README.md`.

   Old text moved into the *Reference*, not cut. It holds the five console commands and their table, the `contract`, `check_documents` and `check_demos` modules, and the document check with its blocking rules, `Report (not checked yet):` and `documents ok`. It also holds the machine and the cloud-run script, the stage file, and how the repository is built with the history tag.

   Dropped or changed on purpose:
   - "v1.1" and "second implementation" are gone (style rule 1). The first implementation and the handover date stay as one line in *How it is built*.
   - The "Replaced from v1" section, with its `--follow` sentence, is gone. The document check rejects that sentence as a replaced behaviour (rule 7), and the code has no `--follow`.
   - The stage-file path is now written `<project>/factory/stage.Containerfile`, because the name check found the bare path does not exist in this repository.
   - The `agents/` and `CLAUDE.md` lines are kept.
   - I added links to `operator/README.md` and `demo/README.md`. Both files exist.

   Checks:
   - `make documents` ends with `documents ok (58.6 s)`.
   - I did not run `make check`, because only documents changed.
   - No document links to a README heading (I grepped `README.md#`), so no link needed changing.
   - The README's examples are indented plain blocks, not `console` blocks. `make check` is skipped by the suite rule anyway, and the other commands need a machine or a long run. The reviewer may judge whether a `console` example would serve better.
   - The glossary has no per-word headings, so the first use of "stories" links to `glossary.md`. Other factory words are used in the README only inside the *Reference*, in the quoted names of checks and stages, and I linked none of them.

   Cross-read: `docs/project-guide/style.md` (README section), `docs/project-guide/glossary.md`, `pyproject.toml` scripts, and `src/factory/entry/` (the modules exist). Nothing in them was stale.

   Stale text noticed and not touched: none.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (58.8 s)
