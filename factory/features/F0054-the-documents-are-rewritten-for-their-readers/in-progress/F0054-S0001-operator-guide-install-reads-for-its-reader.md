---
stage: docs-review
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T21:45:12.897265Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T21:49:53.042261Z'
  stage: docs-only
  run: 9f381cd48fe04a53a40b142ccbcca99d
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
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/install.md` for the operator and put it under the checks. `make documents` ends `documents ok (1.7 s)` with no finding on this file. I ran no `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/install.md`: rewritten in the style of `docs/project-guide/style.md`. It now has numbered install steps and settings tables grouped by topic under *Configuration*, headed `Name`, `What it does`, `Default`, `Example`. Defaults come from `SETTINGS` in `src/factory/shared/domain/settings.py`. A *The refusals* table sits inside *Configuration* (first column `Refusal`, texts from `settings.py`). *When the process refuses to start* is now what you see, what it means and what you do. A final *Reference* section holds the detail moved out of the prose (see the list below). Old headings that other files link to are kept: *Install*, *Configuration*, *When the process refuses to start*, *The loop and its pauses*, *The checkout is cloned when it is missing*, *Mutation testing by sweep*. Glossary words are linked at their first use. There is no version history or feature ID.
   - `docs/checked-documents.txt`: added the line `docs/operator-guide/install.md`.

   I read the code before writing: `src/factory/shared/domain/settings.py`, `src/factory/pipeline/application/scheduler.py`, `src/factory/entry/run.py` and the token and URL functions in `src/factory/entry/wiring.py`. The one console example is `FACTORY_INSTANCE=Factory-1 factory-run`. It runs on `fixture=instance` and prints `<time> settings invalid: FACTORY_INSTANCE: is not a name`, which I took from a real run. The two `make mutants` blocks are `sh`, so they are never run. I did not run them or have a real run to copy from, so they are not claimed as run.

   What I corrected or removed on purpose, compared with the old text:
   - Dropped the opening paragraph that named v1 and v1.1.
   - Dropped the sentence pointing to "Replaced in v1.2" in `README.md`.
   - Dropped the human's-decision date for mutation sweeps.
   - Dropped the class and module names (`read_settings`, `SettingsInvalid`, `PyGithub`).
   - Corrected the refusal texts to the code's wording. For example, the runtime refusal is `holds <value>, which is neither claude nor opencode`, the status refusal is `is not an HTTP status from 100 to 599`, and the empty-file refusal is `<path> is empty`.
   - Added things the old text lacked: exit status 1 when a machine stop stood too long in a job, the `factory-watch: settings invalid:` line, and the faults `names more than one repository`, `holds a password; use the token file`, `names <name> twice`, and `is not a whole number of <unit> of at least <minimum>`.
   - Corrected the order of faults: `FACTORY_SNAPSHOTS` is read before the workspace faults, and the snapshot-base and transcript faults come after them.
   - Rounded the mutation-sweep figures in the prose and kept the exact ones in *Reference*.

   Moved to *Reference*:
   - the exact order of faults;
   - the stage-environment rationale;
   - the exit statuses;
   - the image identity;
   - the token-reading details;
   - the accepted repository URL forms;
   - the ignored variables;
   - the values the VM sets;
   - the exact sweep timings.

   Cross-read and found current, so I did not touch them:
   - `docs/operator-guide/stops.md`: its links to "When the process refuses to start", "The checkout is cloned when it is missing" and "The loop and its pauses" still resolve.
   - `docs/operator-guide/machine.md`: its line 346 links to *Configuration*.
   - The links in `docs/operator-guide/README.md`, `agent-runtime.md`, `cloud-run.md` and `records.md`, which point to the file as a whole.
   - `docs/project-guide/machine.md`, `shared.md`, `pipeline.md` and `style.md`, which name *Configuration* and *Mutation testing by sweep*.

   Stale text I noticed and did not touch, because it is unrelated to this story:
   - `docs/operator-guide/README.md` still has the "Replaced in v1.2" and "Replaced from v1" sections. They carry feature IDs and version history against style rules 1 and 7, and belong to the story for that file.
   - `docs/project-guide/shared.md` says "Today's operator guide has no `Default` column and no refusal table". That is false now that `install.md` has both.
   - The report from `make documents` lists "does not exist" notes for paths in other, unchecked files. These are not mine.

   Findings for the coder: none. Nothing in the code contradicts the Interface.

   Decision on `docs/decisions.md`: unchanged, as the story says. No "Why" or "Rejected" lines were written.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (1.9 s)
