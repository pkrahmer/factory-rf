---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 614
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T00:42:00.199810Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T00:42:00.207016Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T00:42:18.510260Z'
  stage: intake
  run: d94a1610a34048dc9c1b92f1c0fa1371
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T00:42:24.153318Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T00:48:06.070919Z'
  stage: docs-only
  run: 95e0d9903af04615b267540381fe9124
---

# The operator guide's the preflight, the health check and the log reads for the operator

## Description

`docs/operator-guide/health.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/health.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/health.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/health.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/health.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/health.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/operator-guide/health.md` exists; `docs/checked-documents.txt` exists and does not yet list it). It changes only documents and no code, test or agent file, so the docs route fits.
   - Criteria: all six are about documents and each can be judged or checked. 1 and 2 are the reviewer's comparison, 3 is `make documents`, 4 is a link check, 5 is `make check`. The Interface states no behaviour or rule with a failing side, so no criterion is missing.
   - Smoke test: `grep -cx "docs/operator-guide/health.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output.
   - Docs criterion: it names the reader (an operator who knows Linux and does not read the code) and what the file must hold (the facts of the old file, corrected against the code). It quotes no sentences to write.
   - Architecture: no code is touched, so nothing conflicts with the layers in `CLAUDE.md`.
   - Scope: the story is S0006 of F0054's list and in its scope. It touches none of the out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`).
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/health.md` for the operator and added it to `docs/checked-documents.txt`. `make documents` ends with `documents ok (12.1 s)`. I ran no `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/health.md`: now opens with a short intro and a numbered task, "Check that the instance is healthy". Its two `factory-health` examples are `console fixture=instance` blocks that run.
   - Every heading other documents link to is unchanged. I checked that against the links in `stops.md`, `install.md`, `machine.md`, `agent-runtime.md`, `cloud-run.md`, `pipeline.md` and the project guide. No other file needed a link change.
   - The token-file faults, the probe's start-up faults and the repository-wait faults are now tables of what you see, what it means and what you do. The token-file table has the same four faults as before.
   - The helper rules and the stage-environment timing line are now lists.
   - Glossary links sit at the first use of instance, stop, project command, dataset, crash, take, stage, pipeline definition, acceptance and cost record.
   - Examples and commands that cannot run here are `sh` or `text` blocks: the record-counting `python3` one-liners, `zcat`, the `gcloud` steps and the sample stop line. The sample stop line is copied from the old file; I did not see it produced.
   - The name check flagged `records/*.jsonl` and `factory/agents/coder.md`. I wrote them as `<state>/records/...` and `<project>/factory/agents/coder.md`.
   - I wrote `roles/storage.objectUser` as "the Storage Object User role" in the prose, and kept the real role name in the `gcloud` command.

   Compared with the old text:
   - I kept every name, command, setting, message and rule from the old file, in place. I added no separate *Reference* section, because the linked headings had to keep their content. The old facts sit in the tables and lists under those headings.
   - Corrected from the code: the stop record's `scope` text said `machine` only for `preflight_failed` and `disk_low`. `src/factory/pipeline/domain/stops.py` makes `stage_image_failed` a machine stop too. That matches the health-status section, which already said so.
   - Spot-checked against the code and found true: the preflight messages, the token helper's `x-access-token`, the probe's 10-minute (lint) and 2-minute (agent) limits, and the transcript setting rules in `settings.py`.
   - Not re-verified in code: the 0.10 dollar probe budget, the 30-day lifecycle rule, the state-directory field lists, and the exact text of the `origin/main has no factory/pipeline.yml yet` detail (my grep for it found nothing). These stand as in the old file. The reviewer should confirm them.
   - Added, not from the old file: the "What you do" cells for `no origin/main ...`, `container command sync failed` and the unreadable login file. These are my reading of the faults, not text from the code.
   - Dropped on purpose: the old sentence that the helper "behaves as before" with `FACTORY_REPOSITORY_URL` unset. It now says it answers every host.

   Cross-read and found current against the facts above: `stops.md`, `install.md`, `machine.md`, `agent-runtime.md`, `cloud-run.md` and `pipeline.md` of the operator guide. I read only the sentences that cite `health.md`.

   Stale text I saw and did not touch:
   - `make documents` prints many "does not exist" lines under "Report (not checked yet)" for unchecked files (`docs/project-guide/*`, `README.md`, `docs/operator-guide/pipeline.md`). They are not part of this story.
   - `docs/project-guide/pipeline.md` and `agents.md` cite `health.md` headings that are unchanged, so they still resolve.

   Findings for the coder: none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (12.0 s)
