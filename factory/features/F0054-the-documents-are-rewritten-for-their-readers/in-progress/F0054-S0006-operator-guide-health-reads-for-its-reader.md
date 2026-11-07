---
stage: docs-approval
blocked: null
round: 2
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
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T00:48:11.155882Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:50:41.573513Z'
  stage: docs-review
  run: d4c6da3cebaa49f78ee00a2c0bf0c5ef
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T00:50:46.711489Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T00:53:58.595059Z'
  stage: docs-only
  run: 08a8abf2fe7d4a7294ec70fc2b1dc3d8
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T00:54:04.601793Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:55:33.251016Z'
  stage: docs-review
  run: ca58f79675884ba9854373d302f221ba
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T00:55:38.030197Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T00:58:34.792654Z'
  stage: docs-only
  run: c6ac785d4ecd462ab1f18c77b40da835
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T00:58:39.844289Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:59:02.587961Z'
  stage: docs-review
  run: cd447a95522c4e07b22f37c8b07a8b68
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
6. factory: started docs-review as vm.
7. reviewer: I reviewed `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/health.md` and `docs/checked-documents.txt`. I compared the old and new `health.md` with each other, with the code (`preflight.py`, `entry/wiring.py`, `scheduler.py`, `pipeline/domain/stops.py`, `entry/health.py`, `operator/vm/git-credential-factory`) and with `docs/project-guide/style.md`.

   Checked and true: the credential helper's rules, including "with `FACTORY_REPOSITORY_URL` unset, it answers every host". Also true: the probe's 0.10 dollar budget and its 2-minute and 10-minute limits; the `origin/main has no factory/pipeline.yml yet` detail, built by an f-string in `scheduler.py:136`; the corrected `scope` for `stage_image_failed`; and the default `/state` of `factory-health`. The VM paths under `/srv/factory/<instance>/state` (`setup.sh:425`) and every section another file names ("The service", "The steps", "The stop records on main" and the rest) are true too.

   Criterion 2 is met without a *Reference* section. Things dropped on purpose: "PyGithub" became "the hosting-service client"; `Preflight.run` became "the preflight"; "behaves as before" became "answers every host"; and the cross-reference "The exception is a `main` that differs ... see the next bullet" was cut from the stale-stop bullet.

   Findings:
   1. `docs/operator-guide/health.md:93`: "They run in the order of the table" is wrong. `entry/wiring.py:746-752` runs `opencode` after `metadata-block`, just before `agent-run-probe`, but the table puts it right after `token-file` (line 102). Fix: move the `opencode` row to just before `agent-run-probe`.
   2. `docs/operator-guide/health.md:27`: "A failed check raises a stop of the machine" is wrong for the probe of `main`. `preflight.py:549,559` raises `main_branch_failing` with scope `repository`. Fix: say the machine's items raise `preflight_failed`, a machine stop, and a red `lint` on `main` raises `main_branch_failing`, a repository stop.
   3. `docs/operator-guide/health.md:137-143`: "a state directory that cannot be written" and "a missing agent `coder`" are listed as causes of a run that does not end `completed`. In `preflight.py:281-288` they raise before or instead of an end reason, and the detail is the error's own message, not `the probe run ended <reason>`. Fix: move them to a row of their own in the table above (what you see: the runtime's or the reader's message), as the old text kept them apart.
   4. `docs/operator-guide/health.md:73`: "this one is copied from a real status" is a claim the documenter's own entry contradicts: the line was copied from the old file and never seen produced. Fix: say the line shows the format, built in `src/factory/entry/health.py:19`. Or replace it with a line from a named real run (style rules 6 and "A `vm` example comes from a real run").
   5. `docs/operator-guide/health.md:262`: `Git.work_tree_id` names a class and method, which the operator guide's rule "Name no module or class" forbids. Fix: say "a hash of the files the command reads, without those its `not_read` leaves out".
   6. `docs/operator-guide/health.md:181-186`: the `repository_unavailable` faults are a two-column table (what you see, what you do). The stop rule of the operator guide asks for three parts. Fix: add the column "What it means", as the token-file table at lines 56-61 has, and keep only the action in "What you do".
   7. `docs/operator-guide/health.md:3, 27`: the glossary word "stop" is first used on line 3 ("Every stop it names") but is linked only on line 27 (style rule 3, criterion 1). Fix: link it on line 3.
   8. `docs/operator-guide/health.md:109, 204`: "stage" is first used on line 109 ("as a stage makes it") but is linked on line 204. Fix: move the link to line 109.
   9. `docs/operator-guide/health.md:356, 363`: "cost record" is first used on line 356 ("its cost record") but is linked on line 363. Fix: move the link to line 356.
   10. `docs/operator-guide/health.md:79, 106, 145, 164, 204, 330`: glossary words with no link anywhere in the file: "work item" (line 79), "base" (line 106), "claim" (line 145, "claimed"), "tick" (line 164), "stage environment" (line 204) and "feature" (line 330). Fix: link each at its first use.
   11. `docs/operator-guide/health.md:233, 255, 300, 320`: "`<state>/records/<file>`, in the state directory holds ..." has a stray comma between subject and verb, and lines 233 and 255 are also long sentences of 35 to 50 words. Fix: "`<file>` in the state directory holds ...", with the VM path in a sentence of its own.
   12. `docs/operator-guide/health.md:153, 233, 324, 363`: each sentence has two parentheses (style rule 2 allows one). Fix: turn one parenthesis of each into its own sentence or list item.
   13. `docs/operator-guide/health.md:3`: the opening sentence after "A topic of the operator guide." runs to about 45 words (style rule 2). Fix: split it into who the page is for and what it covers.
   14. `docs/operator-guide/health.md:284, 346`: "runs as it did before" and "starts and runs as before" are history wording (style rule 7). The documenter removed the same phrase from the helper's rules. Fix: "the command runs" and "the factory starts and runs normally".

   Also checked: criterion 3 (the file is on `docs/checked-documents.txt` and `make documents` printed `documents ok` per the journal) and criterion 4 (no changed heading, so the links from other files still resolve). The `sh` blocks of VM and gcloud commands each say where they run.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed all 14 review findings in `docs/operator-guide/health.md`. `make documents` ends with `documents ok (12.0 s)`. I ran no `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/health.md`: the fixes below. No heading changed, so no link in another file needed a change. `docs/checked-documents.txt` is unchanged.

   Findings, by number:
   1. I moved the `opencode` row of the items table to just before `agent-run-probe`, which is the order `entry/wiring.py` runs them in.
   2. The preflight intro now says the machine's items raise `preflight_failed`, a machine stop. A red `lint` on `main` raises `main_branch_failing`, a repository stop.
   3. I took "a state directory that cannot be written" and "a missing agent `coder`" out of the causes list. They are now two rows of the probe's table (what you see, what it means, what you do). Their "what you see" text is a description, not a quoted message: I did not read the exact message in the code.
   4. The sample stop line is no longer called "copied from a real status". The text now says it shows the format built in `src/factory/entry/health.py`, and that no example here produced it.
   5. `Git.work_tree_id` became "a hash of the files the command reads, without those its `not_read` leaves out".
   6. The `repository_unavailable` faults are now a table of what you see, what it means and what you do.
   7. to 10. I moved or added glossary links at the first use of stop, stage, cost record, work item, claimed, tick, stage environment and feature. I did not link "base". The only first uses of it are inside `dataset` item text and code literals, and it is not a prose use.
   11. I rewrote the four record-file openings as "`<file>` in the state directory's `records/` folder holds ...", with the VM path in its own sentence.
   12. I removed the second parenthesis from the sentences at the opencode login line, the disk record's `folders` line, the transcript file-mode line and the cost-record sentence. A few other sentences still hold two parentheses, for example the preflight's `lint` probe bullets; I did not touch them.
   13. I split the opening sentence into three shorter ones.
   14. "Runs as it did before" and "runs as before" became "the command still runs" and "starts and runs normally".

   Cross-read: the sentences in other operator-guide files that cite `health.md` headings are unchanged and still resolve.

   Stale text I noticed and did not touch: `make documents` still lists many "does not exist" report lines for files that are not on `docs/checked-documents.txt` yet. They are not part of this story.

   Findings for the coder: none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (12.2 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md`: `docs/operator-guide/health.md` and `docs/checked-documents.txt`. I read the whole new `health.md` against `docs/project-guide/style.md` and the code.

    The round-0 fixes I checked against the code, and they hold:
    - The order of the items table now matches `src/factory/entry/wiring.py:741-752`: `opencode` comes after `metadata-block` and before `agent-run-probe`.
    - The preflight intro names `preflight_failed` (machine) and `main_branch_failing` (repository).
    - The probe's table now has its own rows for the state directory that cannot be written and for the missing agent `coder`. This is consistent with `preflight.py:281-298`.
    - The login-file messages match `agent_launch.py:158,162`. The login hints and details match `preflight.py:307-344`.
    - The `repository_unavailable` table has three columns.
    - `Git.work_tree_id` and the history wording are gone.
    - The glossary links for stop, stage, cost record, work item, claim, tick, stage environment and feature now sit at their first use in prose.

    Criteria 3 and 4 are unchanged since round 0: the file is on `docs/checked-documents.txt`, `make documents` printed `documents ok` per entry 9, and no heading changed.

    Findings:
    1. `docs/operator-guide/health.md:107, 126, 133, 208`: the glossary word "base" is still not linked anywhere (round-0 finding 10). Entry 9's reason, that its only first uses are inside code, is wrong: line 107 ("the workspace and the base are directories"), line 126 ("the base moves"), line 133 ("the dataset has no base") and line 208 ("the move of its base") are prose. This breaks style rule 3 and criterion 1. Fix: link "base" to `../project-guide/glossary.md` at its first prose use, line 107.
    2. `docs/operator-guide/health.md:93`: the sentence "The extras are `token-file`, … `metadata-block` (under the profile `job` only), `opencode` (under opencode only) and `agent-run-probe`." holds two parentheses (style rule 2). Fix: list the extras without the parentheses and add a sentence of its own: "`metadata-block` runs only under the profile `job`, and `opencode` only under opencode."
    3. `docs/operator-guide/health.md:75`: the round-0 fix names the source path `src/factory/entry/health.py`. The operator-guide rule says "Name no module or class. Name a source path only if the operator edits or runs that file". Fix: "A line for a stop has this format; `factory-health` prints it:", without the source path and without "no example here produced it".
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the three round-1 review findings in `docs/operator-guide/health.md`. `make documents` ends with `documents ok (12.1 s)`. I ran no `make check`, because I changed only documents.

    Files changed:
    - `docs/operator-guide/health.md`: the fixes below. No heading changed, so no link in another file needed a change. `docs/checked-documents.txt` is unchanged.

    Findings, by number:
    1. I linked "base" to the glossary at its first prose use, in the `snapshots` row of the items table ("the workspace and the base are directories"). This is the link round 0 left out.
    2. I took the two parentheses out of the sentence on the extras. It now lists the extras plainly and adds one sentence: "`metadata-block` runs only under the profile `job`, and `opencode` only under opencode."
    3. The sample stop line is now introduced by "A line for a stop has this format; `factory-health` prints it:". The source path and "no example here produced it" are gone. The sample line itself is still the one copied from the old file, and I did not see it produced.

    Cross-read: I changed no heading, so the sentences in other documents that cite `health.md` still resolve.

    Stale text I noticed and did not touch: `make documents` still lists "does not exist" report lines for files that are not on `docs/checked-documents.txt` yet. They are not part of this story.

    Findings for the coder: none.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (12.1 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 review of `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/health.md` and `docs/checked-documents.txt`. I read this round's change (`git diff f65377c1c ec879053b -- docs`) and the lines around it against the code and `docs/project-guide/style.md`.

    All three round-1 findings are fixed:
    1. "base" now links to the glossary at its first use in prose, in the `snapshots` row of the items table (`health.md:107`).
    2. The sentence on the extras no longer has its two parentheses (`health.md:93`). The new sentence, "`metadata-block` runs only under the profile `job`, and `opencode` only under opencode.", matches the rows at lines 110 and 111.
    3. The sample stop line is now introduced by "A line for a stop has this format; `factory-health` prints it:" (`health.md:75`), with no source path. The line matches the format `src/factory/entry/health.py:17-19` builds: `<reason> (<scope>): <detail> (since <%Y-%m-%dT%H:%M:%SZ>)`. It sits in a `text` block as a format sample, not a command, so it needs no record of a real run.

    This round changed nothing else. The findings fixed in rounds 0 and 1, and the checks of criteria 1 to 4, still hold:
    - the file is on `docs/checked-documents.txt`;
    - `make documents` printed `documents ok` (entry 13);
    - no heading changed, so links from other documents still resolve.

    Criterion 2 is met without a *Reference* section. Entry 7 names what was dropped on purpose.

    No findings.
