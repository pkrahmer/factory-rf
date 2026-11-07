---
stage: docs-review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 612
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T00:11:59.113781Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T23:58:32.177570Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T23:58:32.184919Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T23:58:47.150520Z'
  stage: intake
  run: 28327dec91dc42258679ae60ffe93c01
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T23:58:52.079670Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T00:02:54.622085Z'
  stage: docs-only
  run: 4e6ebb47bfa64cfea4bc4c70480b9aee
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T00:02:59.838631Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:04:37.977030Z'
  stage: docs-review
  run: 97dca653a4f1497db1ad6f5ed5918c70
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T00:04:43.348004Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T00:07:27.569611Z'
  stage: docs-only
  run: 034919b05e504258bda5f67d329f61d2
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T00:07:32.706414Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:09:11.435661Z'
  stage: docs-review
  run: 0c707730ab8f4d4aac3065c6a6cddfff
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T00:09:17.543979Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T00:11:53.674224Z'
  stage: docs-only
  run: 8404cf02407d4b5c9a3e59db2983a3fe
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T00:11:59.113781Z'
  stage: docs-review
---

# The operator guide's on cloud run reads for the operator

## Description

`docs/operator-guide/cloud-run.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/cloud-run.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/cloud-run.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/cloud-run.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/cloud-run.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/cloud-run.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/operator-guide/cloud-run.md`, `docs/checked-documents.txt`), all in the documenter's write paths. It states no code, signature or behaviour, so there is nothing for a criterion to be missing.
   - Criteria: 1 and 2 are judged by the reviewer, as the feature's decision 2 says for the docs route. 3 is checked by `make documents` printing `documents ok`, with the checked-list entry. 4 is a link check. 5 is `make check`. None of them states a rule with a failing side that lacks its own criterion.
   - Smoke test: `grep -cx "docs/operator-guide/cloud-run.md" docs/checked-documents.txt` runs as written. Its `Expect: 1` is checkable against the output.
   - Docs criterion: criterion 6 asks for criteria 1 to 4 and names no decision-log change. It says what the reader must know (the operator's tasks, stops and settings, taken from the code) and dictates no sentences.
   - Architecture: the story touches documents only, so there is no code layering to break. The route is docs-only, since every path the story changes is one the documenter may write.
   - Scope: the story is one of the 22 files in F0054's scope (S0004). It leaves out `docs/decisions.md`, `docs/runs/` and the operator playbook, and it makes no behaviour change.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/cloud-run.md` for the operator and added it to `docs/checked-documents.txt`. `make documents` ends with `documents ok (6.4 s)` and prints no finding for the file. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/cloud-run.md`: rewritten and checked against `operator/vm/job-start.sh` (read in full) and `operator/job/job.sh` (messages, defaults, limits and the usage line).
     - It follows the style page: glossary links at first use, numbered steps for tasks, the environment variables in `Name / What it does / Default / Example` tables, and one-idea sentences.
     - Headings that other files link to are kept: *On Cloud Run*, *What the job needs*, *Creating the job*, *Starts, restarts and the end of an execution*, *Watching the job*. The `README.md` and `docs/operator-guide/site.md` links still resolve.
     - Added a *Reference* section at the end. It holds the `job-start.sh` messages with their statuses, the texts `log --quiet` drops, and the `job.sh` messages.
     - Two `console` examples were run and copied from real output: `job-start.sh` with an empty environment, and the usage line of `job.sh`. Commands that need `gcloud` or the cloud account stand in `sh` blocks under a numbered step.
   - `docs/checked-documents.txt`: added the path `docs/operator-guide/cloud-run.md`.

   Removed or corrected on purpose:
   - The P15, P16, P18 and P20 measurement labels, and the date "measured on 2026-10-31". Those are history, so the text says "about" or nothing.
   - The sentence "A stop between stages before the nightly restart is a candidate for later and does not exist yet". It describes no behaviour.
   - `FACTORY_CLAUDE_HOME` is now given as `<root>/factory/agents`. The code sets it to `$code/agents`, and the old text said only "under `<root>`".
   - The old table of environment variables had no columns for default and example. I added them from the script, and the example values are my own illustrations.
   - I did not add the `\`-quoted default of the model-cost refusal `.` alone. The code also refuses a lone `.`, and the text says "digits with at most one `.`".

   Cross-read and found current: `README.md` (its pointer to *On Cloud Run*), `docs/operator-guide/README.md`, `install.md`, `site.md` (its links to this file's headings) and `machine.md` (the sections this file points to). I did not read `health.md`, `agent-runtime.md`, `work-items.md` or `stops.md` against the code, only that the headings this file names exist there.

   Stale text I saw and did not touch:
   - `docs/decisions.md` line 1560 names the old single-file layout of the operator guide, which is history in the decision log.
   - `docs/runs/` belongs to the human.

   No `docs/decisions.md` entry was written, as criterion 6 says. No findings for the coder: the code agrees with what the old file said.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (5.9 s)
6. factory: started docs-review as vm.
7. reviewer: Docs review, round 0. I read `docs/operator-guide/cloud-run.md` on the branch against the file on `main`, `operator/vm/job-start.sh`, `operator/job/job.sh`, `src/factory/entry/run.py` and `src/factory/machine/application/machine_stop_exit.py`, and against `docs/project-guide/style.md` and the glossary. Every heading the file links to in another document exists. The headings that `site.md` and `README.md` link to are kept. `docs/checked-documents.txt` holds the path. The items dropped on purpose are acceptable as history: the P15/P16/P18/P20 labels, the measurement date, and the "candidate for later" sentence. `FACTORY_CLAUDE_HOME` = `<root>/factory/agents` is correct (`job-start.sh:61,68`).

   Findings:
   1. `docs/operator-guide/cloud-run.md:127`: the bullet "A machine stop that stands for ten minutes ends the execution with status 1" lost its condition. The code ends the process only when the idle shutdown is on and its action is `exit` (`machine.md` *A machine stop in a job*; `src/factory/entry/run.py:56,194`). On `main` the sentence stood under the idle-shutdown bullet. Fix: start the bullet with "With `FACTORY_IDLE_SHUTDOWN_MINUTES` set," and point to *The idle shutdown* in machine.md.
   2. `docs/operator-guide/cloud-run.md:137`: "Every `gcloud run` call carries `--region` too, because Cloud Logging has no region and `logging read` does not take it" gives the wrong cause. Cloud Logging having no region is why `logging read` is the exception, not why `gcloud run` calls carry `--region`. Fix: "Every `gcloud run` call carries `--region` too. `logging read` does not, because Cloud Logging has no region."
   3. `docs/operator-guide/cloud-run.md:57`: the example `/secrets/hosting-token/token` contradicts the code. `job.sh` mounts the token at, and sets `FACTORY_TOKEN_FILE` to, `/secrets/hosting-token` (`operator/job/job.sh:18,98`). Fix: make the example `/secrets/hosting-token`.
   4. `docs/operator-guide/cloud-run.md:100` (with :98): the text says the script prints `job-start: inputs` and then checks the variables. In fact the required-variable, token-file and `RUNC_SHA256` checks run before the `inputs` line is printed (`job-start.sh:45-56`), and the file's own example at :91-93 shows a refusal with no `inputs` line. Fix: say that these checks come before the first step line, and that `inputs` covers the derived settings, the token copy, the transcript check and `PATH`.
   5. `docs/operator-guide/cloud-run.md:115`: "The job's log ends with the last step printed" is false. After the step line, the script prints `job-start: <step>: failed` on standard error, and the job's log carries it too (`job-start.sh:12-19`). Fix: "The job's log shows the last step printed, followed by its failure line" (or keep `main`'s "has the last step printed").
   6. `docs/operator-guide/cloud-run.md:281-297`: the *Messages of `job.sh`* table leaves out `job: operator/vm/job-start.sh holds the line JOB_START_SH_END; the wrapper cannot carry it` (status 1, `operator/job/job.sh:161-162`), and :208 states this refusal without its message. Fix: add the row and quote the message at :208.
   7. `docs/operator-guide/cloud-run.md:3`: this breaks style rule 3 (link a factory word at its first use). The list claims the file uses [round cap] and [cost record], but neither appears in the text. It leaves out `tick` (first used at :125) and `story` (at :121), which are glossary words, and it links `base` again at :21. Fix: drop the word list, and link each glossary word where it is first used: stage, stop, crash, base, work item, tick, story.
   8. `docs/operator-guide/cloud-run.md:5`: this paragraph tells the operator about `make documents` and which blocks the docs check runs. That is the documenter's tooling, not something the operator does (style.md, *The operator guide*: the reader does not read the code). The text above each `sh` block already says where it runs. Fix: remove the paragraph.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's eight findings in `docs/operator-guide/cloud-run.md`, the only file I changed. `make documents` ends with `documents ok (5.9 s)` and prints no line for this file. I did not run `make check`, because I changed only documents.

   1. The machine-stop bullet now starts "With `FACTORY_IDLE_SHUTDOWN_MINUTES` set, a stop of the machine that stands for ten minutes" and points to *The idle shutdown* in machine.md.
   2. The `--region` sentence now reads: every `gcloud run` call carries `--region`; `logging read` does not, because Cloud Logging has no region.
   3. The token path example is now `/secrets/hosting-token`.
   4. The *The steps* intro says the checks of the required variables, the token file and `RUNC_SHA256` come before the first step line. The `inputs` step now says it "derives the other settings", and the rest of that step's text is unchanged.
   5. The failure sentence now says the log shows the last step printed, followed by its failure line.
   6. The `JOB_START_SH_END` refusal message is quoted in the text, and a row for it is added to the *Messages of `job.sh`* table (status 1).
   7. I dropped the word list at the top. Each glossary word is now linked where it first appears: instance, stage, base, crash, work item, story, tick and stop. I removed the second link on `base`.
   8. I removed the paragraph about `make documents` and the `sh` and `console` blocks.

   Cross-read: none beyond round 0.

   Stale text I did not touch: the same as in round 0, namely the line in `docs/decisions.md` and `docs/runs/`.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (5.9 s)
10. factory: started docs-review as vm.
11. reviewer: Docs review, round 1. I read `docs/operator-guide/cloud-run.md` on the branch against the file on `main`, `operator/vm/job-start.sh` (lines 1-140) and `operator/job/job.sh` (its messages, `status` and `log`), and against `docs/project-guide/style.md` and the glossary. All eight round-0 findings are fixed: the idle-shutdown condition is at :125, the `--region` cause at :135, `/secrets/hosting-token` at :55, the order of the checks at :96, the failure line at :113, the `JOB_START_SH_END` message at :206 and :289, the glossary links at first use (instance, stage, base, crash, work item, story, tick, stop) and the `make documents` paragraph is gone. `docs/checked-documents.txt` holds the path. The links from `README.md`, `site.md`, `install.md` and the guide index still point to headings that exist. Every message in the two Reference tables matches `job.sh` and `job-start.sh` word for word. The smaller changes are acceptable: `gcloud run jobs execute <job>` became `sh operator/job/job.sh execute` at :127, and the gcloud call is still named at :213. The P-labels, the measurement date and the "candidate for later" sentence were dropped on purpose as history.

    Findings:
    1. `docs/operator-guide/cloud-run.md:228`: "`log` and `status` pass what they print through `operator/bin/sanitise`" is false. `status` prints its execution lines unsanitised (`printf '%s\n' "$executions"`, `operator/job/job.sh:444`) and passes only the stop line through `sanitise` (`job.sh:451`). `log` sanitises every line (`job.sh:382,384`). `main` had this right. Fix: "`log` passes every line it prints through `operator/bin/sanitise`, and `status` passes the stop line it prints".
    2. `docs/operator-guide/cloud-run.md:139-146` and `:221-224`: these `sh` blocks hold usage synopses with `[--dry-run]`, `[N]` and `NAME`, not bare commands. They also stand under no numbered step. style.md *Examples that are not run* allows an `sh` block only for bare commands under their numbered step. The second block repeats two lines of the first, and the usage `console` example at :150-153 already shows the full grammar. Fix: replace the block at :139-146 with a table of `Command` and `What it does` (create, update, execute, delete, log, status, each with its options), and drop the block at :221-224.
    3. `docs/operator-guide/cloud-run.md:129`: *A free model* is now a `####` subsection of *Starts, restarts and the end of an execution*, but it is about model prices, not starts. On `main` it was a section of its own (`###`), and nothing links to it. Fix: make it `###` again, so it is a sibling of the other sections.
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the reviewer's three findings in `docs/operator-guide/cloud-run.md`, the only file I changed. `make documents` ends with `documents ok (5.7 s)`. I did not run `make check`, because I changed only documents.

    1. Sanitiser sentence (:228 in the reviewer's numbering): it now says `log` passes every line it prints through `operator/bin/sanitise`, and `status` passes the stop line it prints. This matches the reviewer's reading of `job.sh:382,384,444,451`; I did not read those lines again.
    2. The two `sh` synopsis blocks are gone. The first is replaced by a `Command` / `What it does` table with the six commands and their options, followed by a line saying to run each as `sh operator/job/job.sh <command>` on your own machine. The second block, in *Watching the job*, is dropped. The usage `console` example still shows the full grammar.
    3. *A free model* is a `###` section again, a sibling of the other sections.

    Cross-read: nothing beyond the earlier rounds. Stale text I did not touch: the same as before, namely the old-layout line in `docs/decisions.md` and `docs/runs/`, which belongs to the human.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (5.9 s)
14. factory: started docs-review as vm.
