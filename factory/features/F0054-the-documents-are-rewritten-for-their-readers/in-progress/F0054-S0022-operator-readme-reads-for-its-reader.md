---
stage: docs-only
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 630
comments_read: []
handed_over: null
claim: null
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
- number: 5
  speaker: documenter
  kind: question
  at: '2026-11-07T09:28:59.277469Z'
  stage: docs-only
  run: a68cff5061064f26a19cc9fd35a1bce2
  blocked: question
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
5. documenter: I rewrote `operator/README.md` but could not finish criterion 3. `docs/checked-documents.txt` is unchanged and `operator/README.md` is not on it, because the check refuses that line.

   **Where I stopped.** I added the line `operator/README.md` to `docs/checked-documents.txt` and ran `make documents`. It failed with `docs/checked-documents.txt: operator/README.md is no document of the check`. `checked_list_findings` in `src/factory/shared/domain/documents.py` accepts only the documents the check reads: the README, the operator guide files and the project guide files (constants at lines 23-41). `operator/README.md` is not among them. I took the line out again, so `make documents` now ends `documents ok (58.8 s)`.

   **What the story needs.** The Interface says no code changes. Criterion 3 cannot be met without one: the document set in `documents.py` must include `operator/README.md`, and probably its tests under `tests/` as well. I could not tell whether that is a code story or whether the Interface is wrong, so I am asking instead of ending with `tests` (the docs-only route's way out for a story that needs code).

   Options:
   1. (My choice.) Keep this story docs-only and drop the checked-list part of criterion 3 and of the Interface. A separate story then makes `operator/README.md` a document of the check, and a follow-up adds the line to the list.
   2. Change the Interface so the story takes the code route: tester, then coder, to make `operator/README.md` a document of the check. I then end with `tests` on the next run and the list line goes in at the docs stage.
   3. You make the change to `documents.py` yourself and re-run this stage.

   **What I changed.** `operator/README.md` is rewritten, and it is the only changed file.
   - It is headed "The operator folder". It starts with what the folder is and for whom, and says that the skill is a trial and where the plan is.
   - Its sections are *Installing* (numbered steps), *What you need*, *How Kumpel's acts are told from yours*, and a *Reference* with the file table and the settings table. `docs/operator-guide/site.md` refers to the heading *Installing*, so I kept it.
   - Every file, command, setting and rule of the old text is kept. The signature strings, `KUMPEL_SETTINGS`, the settings file path and the switch defaults (`merge` off, `answer` and `start_next` on) were checked against `settings.sh`.
   - Dropped on purpose, per style rules 1 and 7: the "Second version, 2026-11-01" paragraph, the trial notes, the "Story" column of the table (feature and story IDs), and "(for the trial)". The trial wording survives as one paragraph about the skill's status.
   - Added because the code has them: the `vm/` files (`setup.sh`, `factory.service`, `Dockerfile`, `git-credential-factory`, `job-start.sh`) and `template/`, which the old table's "each file" claim left out. The old table also had no `settings.sh` row in the installing text, which I now cover in step 5.
   - Glossary links on first use of instance, work item and stop. The one runnable `console` example, `site init`, was run by hand. Every command that touches a machine, an account or `~` is in an `sh` block.

   **Cross-read, found current.** No link needs changing. `docs/operator-guide/site.md` (lines 7, 279, 302) points to this file and to *Installing*. `docs/project-guide/operator.md` and `agents.md` link only the file. `docs/operator-guide/pipeline.md` line 56 names the file as a document.

   **Checks.** `make documents` ended `documents ok (58.8 s)`. The new file is not on the checked list, so its examples were not checked by that run. Only documents changed, so I did not run `make check`.

   **Stale text I saw and did not touch.** `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's file, not a document I may write. The old README linked nothing in `planning/`; I kept `planning/operator-skill/DESIGN.md` as a plain path because the folder belongs to the human.
