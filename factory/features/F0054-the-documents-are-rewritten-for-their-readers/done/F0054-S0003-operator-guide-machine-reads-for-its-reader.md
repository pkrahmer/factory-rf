---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 611
comments_read: [6698650455, 6698899316]
handed_over: docs-approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T23:20:58.705028Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T23:20:58.712080Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T23:21:13.433043Z'
  stage: intake
  run: 1d57cf013bc0402d8e8c1c995fd325ad
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T23:21:18.692790Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T23:24:54.815015Z'
  stage: docs-only
  run: 6ffa8165bacc482880b8afb01093848d
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T23:25:00.195437Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:27:27.342341Z'
  stage: docs-review
  run: dd819c82d5974e74990f890afe1e7bde
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T23:27:32.508934Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-06T23:31:34.330677Z'
  stage: docs-only
  run: 4640a3855b5f4dd4afa0d65616ae2ae1
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T23:31:39.635672Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: question
  at: '2026-11-06T23:33:38.384786Z'
  stage: docs-review
  run: 022a0f3263ba45479e6a6ecc2539882e
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-06T23:35:28.001875Z'
  stage: docs-review
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T23:35:30.561856Z'
  stage: docs-review
- number: 14
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:36:16.536395Z'
  stage: docs-review
  run: 5c26794b23ab4c93abe5ee813cb250d5
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-06T23:36:21.776570Z'
  stage: docs-only
- number: 16
  speaker: documenter
  kind: result
  at: '2026-11-06T23:40:03.518581Z'
  stage: docs-only
  run: 397b87d731504610974ef7c266451dd9
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-06T23:40:09.035057Z'
  stage: docs-review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:41:54.427413Z'
  stage: docs-review
  run: 5418eb503e324c33ace0c9a5828eeff1
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-06T23:41:59.922278Z'
  stage: docs-only
- number: 20
  speaker: documenter
  kind: result
  at: '2026-11-06T23:44:48.565823Z'
  stage: docs-only
  run: 4032198f2eda42668b4941f20fb0360f
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-06T23:44:54.182712Z'
  stage: docs-review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:46:57.002803Z'
  stage: docs-review
  run: 650042e664644f2ab8c5d1e4872a433e
- number: 23
  speaker: factory
  kind: question
  at: '2026-11-06T23:46:57.002803Z'
  stage: docs-review
  run: 650042e664644f2ab8c5d1e4872a433e
  blocked: round_cap
- number: 24
  speaker: human
  kind: comment
  at: '2026-11-06T23:48:47.514144Z'
  stage: docs-review
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-06T23:48:50.054657Z'
  stage: docs-review
- number: 26
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:49:36.944606Z'
  stage: docs-review
  run: 390e768268284c12aeb4427c53eb737a
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-06T23:49:42.078044Z'
  stage: docs-only
- number: 28
  speaker: documenter
  kind: result
  at: '2026-11-06T23:52:39.354841Z'
  stage: docs-only
  run: 257325f35d744c73b44cf0fdd051d63b
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-06T23:52:44.357934Z'
  stage: docs-review
- number: 30
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:54:00.782117Z'
  stage: docs-review
  run: abba350ee5cf44ef989ece72fb25e931
- number: 31
  speaker: factory
  kind: done
  at: '2026-11-06T23:57:53.704105Z'
  stage: docs-approval
---

# The operator guide's the machine reads for the operator

## Description

`docs/operator-guide/machine.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example, or is marked for the VM, GitHub or a model, or, when it acts on a real machine or a cloud account and no run can be copied, stands in an `sh` block of bare commands (no `$ `, no output) under its numbered step, with the text above it saying where it runs. That rule is added to `docs/project-guide/style.md`, *Runnable examples*, as one short paragraph. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/machine.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/machine.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/machine.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/machine.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/machine.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names one concrete document (`docs/operator-guide/machine.md`) and `docs/checked-documents.txt`; both are paths the documenter may write, and it states no code, test or agent file changes, so the docs route fits.
   Criteria: 1 and 2 are judged by the reviewer against `docs/project-guide/style.md` and the code, as the docs route intends. 3 is checkable by `make documents` printing `documents ok` plus the list entry. 4 is checkable by following links. 5 is `make check`. The Interface states no behaviour or rule beyond the document rewrite, so no failing-side criterion is missing.
   Smoke test: `grep -cx "docs/operator-guide/machine.md" docs/checked-documents.txt` is runnable, and `Expect: 1` is checkable. It runs no pytest.
   Docs criterion: criterion 6 names what the reader must know (criteria 1 to 4) and quotes no sentences to write.
   Architecture: documents only, no code, so CLAUDE.md's layers are not touched. Operator-guide docs sit in the documenter's write paths.
   Scope: this is S0003 of F0054, listed in `feature.md`. It touches nothing in the feature's Out of scope (`decisions.md`, `docs/runs/`, `operator-playbook.md`, no behaviour change).
4. factory: started docs-only as vm.
5. documenter: I rewrote `docs/operator-guide/machine.md` in place and did not rebuild it from scratch. `make documents` ends with `documents ok (2.0 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/machine.md`:
     - It now opens with the reader (an operator of an instance), links the glossary at the first use of the factory's words, and says that the `console vm` blocks are listed and not run.
     - I removed the history and the planning references: "v1.2", "F0042", "F0043 decision 10", "decisions of 2026-10-24", "question 7 of planning/v1.2-plan.md", "the plan's measure", the `planning/cloud-sandbox/` and `planning/overnight/` paths, "unchanged", "as before", "no longer" and "a later version may use rsync". Three sentences were reworded for the same reason: "A machine set up before this change", "The old name `--ref`" and "as `vm` was".
     - The measured seconds for the job overlay became "about" figures. I made these up by rounding, but they come from the old text: 601 s → about ten minutes, 182 s → about three, 199 s → about three, 107 s → about two.
     - I turned every `bash` block into a `console vm` block with `$ ` prefixes. Their commands were not run: they need the VM, the cloud or the operator's own computer. They show no output, so I invented none.
     - Project paths now use the `<project>/` placeholder (`<project>/factory/stage.Containerfile`, `<project>/factory/agents/`), and the `factory.image` label is written `factory.image=<ref>`, so the name check passes.
   - `docs/checked-documents.txt`: added `docs/operator-guide/machine.md`.

   I kept every heading that another file, `operator/vm/setup.sh` or a test points to: *The machine*, *The service*, *The two passes*, *The rebuild after a merge*, *On GCP, step by step* (with its step numbers 6, 8 and 11), *The idle shutdown*, *The job profile*, *The metadata server in a job*, *The code and the project apart*, *The image on the cost records*, *Without ZFS* and *The steps* (with its steps 14 and 16). So no link needed a change.

   I did not add a *Reference* section, and I dropped no name, command, setting or rule. The option table, the layout table and the environment-file table stay where they are.

   I did not restructure the stage-image-failed stop into the three parts "what you see / what it means / what you do". The text covers all three but not under those labels. The reviewer may ask for that.

   I spot-checked these against the code or scripts:
   - the pins `2.1.318` and `1.19.5` in `operator/vm/Dockerfile`;
   - the `--ref` refusal in `operator/vm/setup.sh`;
   - `--pids-limit=4096` and `--memory=4g` in `podman_runs.py`;
   - the settings names in `settings.py`.

   I did not re-verify every other claim line by line.

   Cross-read and found current: `docs/operator-guide/README.md` and the links to `machine.md` headings in `install.md`, `health.md`, `cloud-run.md`, `agent-runtime.md`, `stops.md` and `docs/project-guide/machine.md`.

   Stale text I saw and did not touch (outside this story):
   - `docs/operator-guide/agent-runtime.md:181` names `planning/cloud-sandbox/`, a path the name check does not find.
   - The other files in the `Report (not checked yet)` list, such as `health.md` and `pipeline.md`, have name findings. They belong to other stories.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (2.2 s)
6. factory: started docs-review as vm.
7. reviewer: I reviewed `git diff main...HEAD -- README.md docs operator/README.md` (`docs/operator-guide/machine.md`, `docs/checked-documents.txt`) against the code on the branch, the criteria and `docs/project-guide/style.md`. I checked these claims against the code and found them true: the label `factory.image` (`operator/vm/Dockerfile:45`), the `--ref` refusal and the `setup: done` and `setup: local` lines (`operator/vm/setup.sh:76,476,477`), `FACTORY_CLAUDE_HOME` (`setup.sh:427`), the preflight item names (`src/factory/machine/application/preflight.py:65-74`), and the `stage image:`, `idle shutdown:` and `machine stop: standing for` log lines (`src/factory/entry/wiring.py:502-526`, `src/factory/entry/run.py:274`, `src/factory/pipeline/application/idle_shutdown.py:9`, `src/factory/machine/application/machine_stop_exit.py:51`). The diff mostly removed history. It did not rewrite the file for its reader, so criterion 1 is not met.

   1. `docs/operator-guide/machine.md:5`, and every `console vm` block (103, 129, 225, 242, 303, 309, 340, 378-486, 557, 566, 578, 586, 602, 611): wrong: the style guide says a `vm` block comes from a real run that the text above names, and rule 6 wants each command followed by what it prints. Entry 5 says none of these commands was run, none shows output, and line 5 stretches `vm` to "the cloud or your own computer", which covers the `gcloud` blocks and the job-only `mkdir` at 103. Fix: delete line 5. Make every block a runnable `console` example where the check container can run it (for example `uv run pytest tests/vm/test_stage_image.py`, or `sh operator/vm/setup.sh --help` if it runs in the checkout fixture), or copy it from a real VM run with its output and name that run above it. Where neither is possible, ask the human how such commands are to be shown.
   2. `docs/operator-guide/machine.md:209-215` (the stop `stage_image_failed`) and `:95` (a failed `metadata-block` raises `preflight_failed`): wrong: the style guide says every stop has three parts, what you see, what it means, what you do, and entry 5 itself says these are not split. Fix: write each stop in those three labelled parts.
   3. `docs/operator-guide/machine.md:572-617` (*The rebuild after a merge*), `:143-151` (*Update the pins*), `:555-562` (turning the idle shutdown on and off), `:301-314` (installing a unit that differs): wrong: each is a task written as prose with several command blocks, but the style guide wants numbered steps, one action and its command per step. Fix: rewrite each as numbered steps and keep the headings that other files link to.
   4. `docs/operator-guide/machine.md:246-259`: wrong: the option table is headed `Option | Default | Meaning`, but the style guide and the Description want settings tables headed `Name`, `What it does`, `Default`, `Example`. Fix: rebuild it with those four columns and an example per option.
   5. `docs/operator-guide/machine.md:576`: wrong: `see "If the factory dies while a stage runs"` names no heading in any document (it is a sentence at `docs/operator-guide/work-items.md:219`), which breaks criterion 4. Fix: `see *A restart during a stage* in [work-items.md](work-items.md)` (the heading at `work-items.md:217`), as line 582 already does.
   6. `docs/operator-guide/machine.md:236`: wrong: `(see *The hosting-service token*)` points to a heading that is not in this file; it is at `docs/operator-guide/health.md:7`. Fix: add `in [health.md](health.md)`.
   7. `docs/operator-guide/machine.md:320`: wrong: "without it the unit starts as before" is a changelog phrase (rule 7), and entry 5 says "as before" was removed. Fix: "without it the unit reads `factory.env` alone".
   8. `docs/operator-guide/machine.md:148-149`: wrong: "`2.1.318` at the time of writing" and "`1.19.5` at the time of writing" date the text instead of stating what is true now (rule 7). Fix: say the current default is in `operator/vm/Dockerfile`, linked, or give the value without the hedge.
   9. `docs/operator-guide/machine.md:328`: wrong: `SnapshotError` names a class, and the operator guide says to name no module or class. Fix: say what the operator sees when the drop fails (the stage does not start, plus the log line or stop it produces).
   10. `docs/operator-guide/machine.md:115,133,137,240,338` and the blocks at 129, 242, 304: wrong: no file of the repository is linked, though rule 8 says to link a repository file by a relative link and to link the file a block shows once, above the block. This covers `operator/vm/Dockerfile`, `operator/vm/job-start.sh`, `tests/vm/test_stage_image.py`, `operator/vm/setup.sh`, `operator/vm/factory.service` and `operator/vm/git-credential-factory`. Fix: link each once at its first use (`[setup.sh](../../operator/vm/setup.sh)`).
   11. `docs/operator-guide/machine.md:233`: wrong: `factory/pipeline.yml`, `factory/story-form.md` and `factory/feature-form.md` are paths in the project but have no placeholder, while the same sentence writes `<project>/factory/agents/` (rule 8). Fix: start each with `<project>/`.
   12. `docs/operator-guide/machine.md:28,176,476,507`: wrong: the glossary words claim (28, "claims"), cost record (176), crash (476) and role (507) are not linked at their first use, which criterion 1 and rule 3 require; line 3 links only seven words. Fix: link each at its first use, or add them to the list on line 3.
   13. `docs/operator-guide/machine.md:60,141,211,231,540,551` and `:19,66,511`: wrong: the first group of lines holds sentences of 40 to 90 words, and the second group holds sentences with two parentheses each (rule 2: about 25 words, at most one parenthesis per sentence). Fix: split them, and move the second parenthesis of each into its own sentence.
   14. `docs/operator-guide/machine.md:111`: wrong: "uses the item `zfs` and `dataset`" is ungrammatical. Fix: "uses the items `zfs` and `dataset`".
   15. `docs/operator-guide/machine.md:109`: wrong: "slower than the 0.2 s that `rsync` measured" quotes a measurement the reader cannot place, since nothing says what took 0.2 s (rule 5). Fix: "much slower than `rsync`", or say what was measured.

   Dropped on purpose (criterion 2), against `main`: the sentence on a VM that the prototype of `planning/overnight/gcp-runbook-2026-10-24.md` had prepared, and "A later version may use `rsync`". Both are history, and dropping them is right. No *Reference* section was added. I found no name, command, setting or rule dropped besides these two.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's 15 findings in `docs/operator-guide/machine.md`. The last line of `make documents` is `documents ok (2.1 s)`. I did not run `make check`, because I changed only documents. `docs/checked-documents.txt` is unchanged and still lists the file (the smoke test prints `1`).

   Files changed:
   - `docs/operator-guide/machine.md`: all 15 findings, in the order below.

   Findings:
   1. Every `console vm` block is now a plain `sh` block, which `make documents` never runs. They show no output. I have no real VM run to copy from, so I claim none. Line 5 now says the `sh` blocks are not run and the `console` blocks are. I added two `console` examples that `make documents` runs: `sh operator/vm/setup.sh --help | head -n 1` and the `--ref` refusal.
   2. The `preflight_failed` stop from `metadata-block` and the `stage_image_failed` stop now have the three labelled parts (what you see, what it means, what you do).
   3. These tasks are now numbered steps, and their headings are kept: *Update the pins*, installing a unit that differs (in *The two passes*), turning the idle shutdown on and off, and *The rebuild after a merge*.
   4. The option table of the script now has the columns Name, What it does, Default and Example.
   5. The `work-items.md` reference is now *A restart during a stage*.
   6. The `health.md` link for the hosting-service token is added.
   7. "starts as before" is now "reads `factory.env` alone".
   8. The "at the time of writing" version numbers are replaced by a pointer to the Dockerfile.
   9. `SnapshotError` is gone; the text now says the stage does not start and the factory log names the failed command.
   10. Repository files are linked once at their first use: `Dockerfile`, `job-start.sh`, `setup.sh`, `factory.service`, `git-credential-factory` and `test_stage_image.py`.
   11. The `pipeline.yml`, `story-form.md` and `feature-form.md` paths now start with `<project>/`.
   12. The glossary words claim, cost record, crash and role are linked in the opening list.
   13. I split the long sentences and the double parentheses at the places the reviewer named.
   14. "the items `zfs` and `dataset`".
   15. "the 0.2 s that `rsync` measured" is now "much slower than `rsync` would be".

   Open, for the human: finding 1 offered two routes, a `console` block that runs or a copy of a real VM run. For the `gcloud`, `sudo` and `podman build` commands neither is possible here. I used unrun `sh` blocks without output. If the human wants these shown another way, for example as `console vm` blocks copied from a real VM run, say so. The style guide says nothing about commands that cannot run and have no real run.

   I cross-read these again and found them current: `docs/operator-guide/README.md`, and the links to `machine.md` headings in `install.md`, `health.md`, `cloud-run.md`, `agent-runtime.md`, `stops.md` and `docs/project-guide/machine.md`. I kept every heading that another file links to.

   Stale text I did not touch, because it is outside this story:
   - `docs/operator-guide/agent-runtime.md:181` names `planning/cloud-sandbox/`.
   - `docs/operator-guide/stops.md:235` is a very long paragraph.
   - The other files in the `Report (not checked yet)` list have name findings. They belong to other stories.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (2.3 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md` (`docs/operator-guide/machine.md`, `docs/checked-documents.txt`) and judged them against the code, the criteria and `docs/project-guide/style.md`. The round-0 fixes are in. The two links (`work-items.md` *A restart during a stage*, `health.md` *The hosting-service token*) resolve. I checked these claims against the code and found them true: `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i` and `Restart=always`/`RestartSec=15` (`operator/vm/factory.service:15-17`), the drop-caches command (`src/factory/machine/adapters/zfs_snapshots.py:16`), and `FACTORY_IDLE_SHUTDOWN_MINUTES` default `0` with blank read as off (`src/factory/shared/domain/settings.py:176,512-523`). `make documents` passes (entry 9).

    Question for the human. No stage can settle it.

    The Description says: "Every command the file shows is a runnable example or is marked for the VM, GitHub or a model". The style guide says a `vm` block "comes from a real run, and the text above it says where it ran". In round 1 the documenter turned every VM, cloud and own-computer command into an unrun `sh` block with no output (`machine.md:5`; for example 115, 141, 247, 264, 341, 378, 416-524, 596-605, 610, 628, 636-665). Such a block is neither runnable nor marked, so the Description is not met. No agent can copy a real run of `gcloud projects create`, `sudo sh setup.sh` or `podman build`. The options I see:
    - (A) Allow unrun command blocks for commands that need a real machine or a cloud account, and amend this story's Description to say so. The wording would be: "...or, when it acts on a real machine or cloud account and no run can be copied, stands in an `sh` block of bare commands without `$ ` and without output, and the text above it says where it runs." The style guide's own operator-guide example already shows unrun commands under numbered steps. A later story could put the rule into `style.md`.
    - (B) Keep the Description. The human runs the commands on `factory-vm`, and the documenter copies each into a `console vm` block with its output and names the run. One-time commands such as the project, budget and VM creation cannot be run again for this.
    - (C) Put the commands inline in the numbered steps (`run \`...\``), with no blocks. This avoids the rule rather than meeting it.

    I would choose (A).

    Whichever you choose, the documenter's next round must also fix these findings:
    1. `docs/operator-guide/machine.md:116,142,248,265,379-381,417-424,429-432,437-439,444-445,450-454,467-471,477-481,488-491,496-499,505-509,516-517,523-524,612` against `:170,342,348-349,597,604,628,638-644,654-655,663-665`: the `sh` blocks mix two forms. Some prefix every command with `$ `, some do not. Line 5 says they show no output, so the `$ ` lines read like transcripts with their output missing. Fix: use one form in every unrun block, the one your answer names (bare commands under (A)).
    2. `machine.md:3`: the sentence is about 60 words long, and its list is broken: "...[stop] and [work item], [claim], [cost record], [crash] and [role]" has two "and"s. Fix: one list with one final "and", split into two sentences (rule 2).
    3. `machine.md:68`: the first sentence is about 45 words long and holds two parentheses, "(`--network=host`)" and "(reachable from host-network and bridge containers, ...)" (rule 2). Fix: split it, and make the reachability note its own sentence.
    4. `machine.md:21,119,149` (last sentence)`,153,198,253,307` (step 5)`,315` (step 13)`,330,370,376,484,549,585,589`: each of these lines still holds a sentence of about 40 to 70 words. Line 549 also has two parentheses in its first sentence (rule 2: about 25 words, at most one parenthesis). Fix: split each into sentences of one idea.
    5. `machine.md:388-408` (the environment file's variables): this is a settings table, but it is headed `Variable | Value`, while the Description and the style guide want `Name`, `What it does`, `Default`, `Example`. Fix: rebuild it with those four columns. Use the value the script writes as the default, and add what each variable does or a link to its row in `install.md` *Configuration*.
    6. `machine.md:597` (*The idle shutdown*, "Turning it on and off", step 1): the step runs `sudo sh operator/vm/setup.sh --device /dev/sdb ...` from a checkout on the VM. `machine.md:651` says "Root runs nothing from `/srv/factory/vm/factory`", and the rebuild runs `sudo sh setup.sh` from your own copy with the first run's arguments (`:663-664`). Fix: tell the reader to run their copied `setup.sh` with the arguments of the first run plus `--idle-shutdown 30`, as in step 5 of *The rebuild after a merge*.
    7. `machine.md:473`: the reference `(see *The script*, "The two passes")` mixes italics and quotes, while every other reference in the file is one italic heading. Fix: `(see *The two passes*)`.

    Criterion 2: I found no name, command, setting or rule dropped beyond the two history sentences that round 0 already named. No *Reference* section was added.
12. 2026-11-06 human: (A), and the rule goes into the style page in this story, so that the later pages of the rewrite meet it without asking: a command that acts on a real machine or a cloud account, where no run can be copied, stands in an `sh` block of bare commands, without `$ ` and without output, under its numbered step, and the text above it says where it runs. A command an agent can run stays a `console` block with its output; one copied from a real run stays `console vm` with the run named. The documenter adds this to `docs/project-guide/style.md`, *Runnable examples* (one short paragraph, by the style page's own rules), and this story's Description counts as amended by this answer.
    And yes to findings 1 to 7 as you wrote them: bare commands in every unrun block, the long sentences split, the environment file's table in the four columns, the copied `setup.sh` with the first run's arguments for the idle shutdown, and one italic heading per reference.
13. factory: started docs-review as vm.
14. reviewer: Round 1 docs-review, after the human's answer in entry 12. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. Since entry 11 the branch has only factory commits and a merge of `main`. Neither touches `docs/operator-guide/machine.md` or `docs/project-guide/style.md`, so the documents are the ones entry 11 reviewed. The human chose (A) and confirmed findings 1 to 7, so they all still stand. The answer also adds one piece of work: the rule goes into `style.md`.

    description corrected: "Every command the file shows is a runnable example or is marked for the VM, GitHub or a model." -> "Every command the file shows is a runnable example, or is marked for the VM, GitHub or a model, or, when it acts on a real machine or a cloud account and no run can be copied, stands in an `sh` block of bare commands (no `$ `, no output) under its numbered step, with the text above it saying where it runs. That rule is added to `docs/project-guide/style.md`, *Runnable examples*, as one short paragraph." (entry 12: "this story's Description counts as amended by this answer").

    1. `docs/project-guide/style.md:16-` (*Runnable examples*): wrong: the paragraph the human asked for in entry 12 is missing. Fix: add one short paragraph, written by the style page's own rules. It says: a command that acts on a real machine or a cloud account, where no run can be copied, stands in an `sh` block of bare commands, without `$ ` and without output, under its numbered step, and the text above it says where it runs. A command an agent can run stays a `console` block with its output. A command copied from a real run stays a `console vm` block with the run named.
    2. `docs/operator-guide/machine.md:116,142,248,265,379-381,612` and the other `$ `-prefixed `sh` blocks from entry 11 finding 1 (417-524 and the rest): wrong: unrun `sh` blocks still put `$ ` before their commands, against entry 12's bare-command form. Fix: remove `$ ` from every line of every `sh` block.
    3. `docs/operator-guide/machine.md:5`: wrong: one blanket sentence ("commands for the VM, the cloud or your own computer") stands in for the per-block statement that entry 12 requires. Fix: in the text above each `sh` block, say where its commands run (on the VM as root, on your own computer with `gcloud`, and so on). Then cut line 5 down to what the blocks are, or remove it.
    4. `docs/operator-guide/machine.md:3`: wrong: the sentence is about 60 words, and its list has two "and"s ("...[stop] and [work item], [claim], ... and [role]"). Fix: make one list with one final "and", and split it into two sentences (rule 2).
    5. `docs/operator-guide/machine.md:68`: wrong: the sentence is about 45 words with two parentheses. Fix: split it, and give the reachability note its own sentence.
    6. `docs/operator-guide/machine.md:21,119,149,153,198,253,307,315,330,370,376,484,549,585,589`: wrong: each line holds a sentence of about 40 to 70 words, and line 549 also has two parentheses (rule 2). Fix: split each one into sentences of one idea.
    7. `docs/operator-guide/machine.md:388-408`: wrong: the environment file's settings table is headed `Variable | Value`. Fix: use the columns `Name`, `What it does`, `Default`, `Example`. The value the script writes is the default. Say what each variable does, or link to its row in `install.md` *Configuration*.
    8. `docs/operator-guide/machine.md:597`: wrong: the idle-shutdown step runs `sudo sh operator/vm/setup.sh` from a checkout on the VM, which contradicts `:651` ("Root runs nothing from `/srv/factory/vm/factory`") and the rebuild at `:663-664`. Fix: tell the reader to run their copied `setup.sh` with the first run's arguments plus `--idle-shutdown 30`, as step 5 of *The rebuild after a merge* does.
    9. `docs/operator-guide/machine.md:473`: wrong: `(see *The script*, "The two passes")` mixes italics and quotes. Fix: `(see *The two passes*)`.

    Criterion 2: unchanged from entries 7 and 11. Nothing was dropped except the two history sentences, and no *Reference* section was added.
15. factory: started docs-only as vm.
16. documenter: Round 2: I applied the human's answer (A) and the reviewer's findings from entries 11 and 14. The last line of `make documents` is `documents ok (5.7 s)`. I did not run `make check`, because I changed only documents. `docs/checked-documents.txt` is unchanged and still lists the file.

    Files changed:
    - `docs/project-guide/style.md`: *Runnable examples* has the one new paragraph in the human's words. A command on a real machine or a cloud account, where no run can be copied, stands in an `sh` block of bare commands under its numbered step, and the text above it says where it runs. An `sh` block is never run. A command an agent can run stays a `console` block, and one copied from a real run stays `console vm`.
    - `docs/operator-guide/machine.md`:
      - Entry 14, findings 2 and 3: every `sh` block is now bare commands without `$ `. Line 5 now says what the blocks are, and the text above blocks that lacked a place now says where the commands run (the sandbox for the base directory, the VM for `setup.sh`, the `systemctl` commands, and so on).
      - Entry 14, finding 4, and entry 11, finding 2: I rewrote the intro list in the glossary sentence as one list with one final "and". I also split the long sentences and double parentheses at the places named. These are the first sentence at 21, the lines before 119, 149 and 153, the lines at 198, 253, 307, 315, 330, 370, 376 and 484, and the ones at 549, 585 and 589.
      - Entry 14, finding 5, and entry 11, finding 3: the reachability note about the metadata server is its own sentence.
      - Entry 14, finding 7: the table of the environment file is now Name, What it does, Default and Example.
      - Entry 14, finding 8: the idle-shutdown step now runs the copied `setup.sh` with the first run's arguments plus `--idle-shutdown 30`. The "turn it off" sentence says the same.
      - Entry 14, finding 9: the reference is now `(see *The two passes*)`.
      - Extra: the `uv run pytest tests/vm/test_stage_image.py` step is now a `console` block that `make documents` runs. Its output is `...` and `<n> passed in <seconds>s`.

    I cross-read these again and found them current: `docs/operator-guide/README.md`, and the links to `machine.md` headings in `install.md`, `health.md`, `cloud-run.md`, `agent-runtime.md`, `stops.md` and `docs/project-guide/machine.md`. I kept every heading that another file links to.

    Not in the stage's checks: I did not re-measure every other long sentence in the file. I split those the reviewer named and those I met while editing.

    Stale text I did not touch, because it is outside this story:
    - `docs/operator-guide/agent-runtime.md:181` names `planning/cloud-sandbox/`.
    - `docs/operator-guide/stops.md:235` is a very long paragraph.
    - The files in the `Report (not checked yet)` list have name findings. They belong to other stories.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (5.8 s)
17. factory: started docs-review as vm.
18. reviewer: Round 2 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, which covers `docs/operator-guide/machine.md`, `docs/project-guide/style.md` and `docs/checked-documents.txt`. I judged them against the code, the criteria, the human's answer in entry 12 and `docs/project-guide/style.md`.

    The fixes from entries 11 and 14 are in:
    - `style.md:73` holds the human's paragraph in one short paragraph.
    - No `sh` block has a `$ ` prefix.
    - Line 3 has one list with one final "and".
    - Line 68 is split.
    - The environment table at `machine.md:402-422` has the four columns.
    - The idle-shutdown step at `:609-613` runs the copied `setup.sh` with the first run's arguments.
    - Line 473's reference is one italic heading.

    I checked the new environment table against `operator/vm/setup.sh:417-439`: every name and default the script writes is there, including `FACTORY_ZFS` with `--sudoers` (`setup.sh:243-245`). Its "What it does" column agrees with `install.md` *Configuration*. Entry 16 says `make documents` printed `documents ok`.

    1. `docs/operator-guide/machine.md:89`: wrong: the probe's `curl` command stands in an indented code block. That is neither a `console` example nor an `sh` block, and line 107 tells the reader to run it by hand. Fix: make it a fenced `sh` block, with the text above saying it runs in a container of the stage image.
    2. `docs/operator-guide/machine.md:471,500,507,516` (steps 6, 9, 10 and 11 of *On GCP, step by step*): wrong: the text above each `sh` block does not say where it runs, which `style.md:73` and entry 12 require. Line 426 covers only steps 1 to 5. Fix: open step 6 with "On your own computer", and steps 9, 10 and 11 with "On the VM from your own account" or "On the VM as `factory`", as steps 7 and 8 do.
    3. `docs/operator-guide/machine.md:167,171,540,599,648`: wrong: commands the reader is to run stand inline in prose, against rule 6 and the `sh`-block rule. They are `podman pull`/`podman inspect` (167), `opencode models anthropic` (171), `gcloud compute instances start` (540), `grep 'idle shutdown' …` (599), and `sudo install …` with `sudo systemctl daemon-reload` (648). Fix: put each in an `sh` block under its step, with where it runs. At 540, point to *Starting the machine again*. At 648, point to steps 1 to 3 of *The two passes* instead of repeating them.
    4. `docs/operator-guide/machine.md:584`: wrong: `(see "The factory log and the health status file" in [health.md](health.md))` uses quotes, not one italic heading (entry 12: "one italic heading per reference"). Fix: `(see *The factory log* in [health.md](health.md))`, the heading at `health.md:104`.
    5. `docs/operator-guide/machine.md:268,307,311,320,321,322,336,368,374,376,544,560,584,601,603,605`: wrong: each line still holds a sentence of about 35 to 55 words, against rule 2 (about 25 words). Lines 320, 321 and 322 (steps 8, 9 and 10 of *The steps*) also hold two parentheses in one sentence, against rule 2's limit of one. Fix: split each into sentences of one idea, with at most one parenthesis per sentence. For example, give each step's mode and owner a sentence of its own.

    Criterion 2: unchanged from entries 7, 11 and 14. Nothing was dropped except the two history sentences, and no *Reference* section was added. Criterion 4: the links I followed (`health.md`, `work-items.md`, `stops.md`, `install.md`, the repository files) resolve.
19. factory: started docs-only as vm.
20. documenter: Round 3: I fixed the five findings of entry 18 in `docs/operator-guide/machine.md`. The last line of `make documents` is `documents ok (5.6 s)`. I did not run `make check`, because I changed only documents.

    Files changed:
    - `docs/operator-guide/machine.md`:
      1. The metadata probe's `curl` command was an indented block. It is now a fenced `sh` block, and the text above it says it runs in a container of the stage image.
      2. Steps 6, 9, 10 and 11 of *On GCP, step by step* now open with where they run: your own computer, the VM from your own account, or the VM as `factory`.
      3. Commands that stood inline in prose are now `sh` blocks under their steps. They are `podman pull` and `podman inspect` and `opencode models anthropic` in *Update the pins*, and the `grep 'idle shutdown'` command, which is a new step 3 of *Turning it on and off*. The inline `gcloud compute instances start` now points to *Starting the machine again*. The inline `sudo install` and `daemon-reload` now point to steps 1 and 2 of *The two passes*.
      4. The reference to the factory log in `health.md` is now one italic heading, *The factory log*.
      5. I split the sentence of the helper's `git-credential-factory` bullet and the sentence about a failed cache drop. I also rewrote the parentheses of steps 8, 9 and 10 of *The steps* so that each sentence holds at most one.

    I did not check every sentence in the file by hand. A script found no sentence over 36 words outside code blocks and tables after my edits. It splits at `;` and `:`, so a long sentence with those marks would not show.

    Cross-read and found current: `docs/project-guide/style.md` (the new paragraph from the last round), and the links to `machine.md` headings in the other operator-guide files. I kept every heading that another file links to.

    Stale text I saw and did not touch, because it is outside this story:
    - `docs/operator-guide/agent-runtime.md:181` names `planning/cloud-sandbox/`.
    - `docs/operator-guide/stops.md:235` is a very long paragraph.
    - `make documents` reports `docs/project-guide/work.md:13: factory/agents does not exist` in its report-only list.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (5.8 s)
21. factory: started docs-review as vm.
22. reviewer: Round 3 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, which covers `docs/operator-guide/machine.md`, `docs/project-guide/style.md` and `docs/checked-documents.txt`. I also read the round-3 change on its own (`git diff cb6b6a25c 42070ae1c`). I judged the documents against the code, the criteria, the human's answer in entry 12 and `docs/project-guide/style.md`.

    Findings 1 to 4 of entry 18 are fixed:
    - `machine.md:89-91` is a fenced `sh` block, and the text above says where it runs. The command matches `METADATA_PROBE_COMMAND` in `src/factory/machine/domain/containers.py:31-41`.
    - Steps 6, 9, 10 and 11 of *On GCP, step by step* say where they run.
    - The inline commands that entry 18 named are now `sh` blocks, or point to *Starting the machine again* and to steps 1 and 2 of *The two passes*.
    - `:595` points to *The factory log*, the heading at `health.md:104`.

    Finding 5 of entry 18 is only partly fixed. Steps 8 to 10 (`:331-333`), the helper bullet (`:279`) and the failed cache drop (`:387`) are split. The other lines that entry 18 named still hold sentences far over about 25 words. Entry 20 says why: its script split sentences at `:` and `;`. I went through every sentence outside the code blocks and tables, and the list below is all of them that I found. A sentence of about 30 words or less, I left alone.

    1. `docs/operator-guide/machine.md:318`: wrong: the sentence "A missing required option, … prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2" is about 45 words (rule 2). Fix: put the five refused inputs in a short list, then say in its own sentence what the script prints and that it exits 2.
    2. `machine.md:347`: wrong: "Place all three files, …, readable by `factory`, and run the same command again: steps 1 to 11 report `found` and the rest completes" is about 33 words and holds two ideas (rule 2). Fix: one sentence for placing the files, and one for the second run and what it reports.
    3. `machine.md:377` and `:379`: wrong: "Every run rewrites `factory.env` … (the Claude Code and opencode versions and the opencode model ids), and writes it only when its text differs" is about 34 words. "For values the script does not know (…), make a second file …" is about 37 words (rule 2). Fix: split each, and give the parenthesis its own sentence.
    4. `machine.md:385`: wrong: "After the rollback the file has the snapshot's size but may still read the newer page: a file the stage made shorter reads as zero bytes past its end, and git's stat cache calls it clean, so the sync does not repair it" is about 45 words (rule 2). Fix: split it into three sentences: what the file reads, what git's stat cache does, and that the sync does not repair it.
    5. `machine.md:137`, `:198`, `:242` and `:341`: wrong: each line holds a sentence of about 33 to 42 words (rule 2). They are "It holds no user of its own … and mounts the dataset", "Without the file, every container runs in the base image, … only when it configures none)", "It has no file of the repository, … as `operator/vm/Dockerfile` does" and "The script writes the files … root's `/dev/stdin`". Fix: split each into sentences of one idea.
    6. `machine.md:555`: wrong: "Take the steps of *On GCP, step by step* from step 6 on, without `gcloud`: copy …, run it …, place the three secrets, run the script again, build the image, start the service" is about 50 words. It is also a task written as prose (rule 2, and the operator guide's numbered steps). Fix: say in one sentence that steps 6 to 11 apply without `gcloud`, and make what differs a short numbered list or its own sentences.
    7. `machine.md:571`, `:595`, `:612`, `:614` and `:616`: wrong: each line holds a sentence of about 38 to 42 words (rule 2). They are the read-only mounts bullet, "The time from the start of a stage … `take` is the copy back", "With `FACTORY_IDLE_SHUTDOWN_ACTION=exit` the factory, … ends the job's execution", "On a VM a machine stop waits … with other settings" and "The setup script gives `factory` the right … both from the same run". Fix: split each at its `:` or `;` into sentences of one idea, with at most one parenthesis each.
    8. `machine.md:491`, `:612` and `:647`: wrong: commands the reader is to run still stand inline in prose. That is against rule 6 and the `sh`-block rule at `style.md:73`, the same kind of finding as entry 18 finding 3, and I missed these three in round 2. They are `ls -l /dev/disk/by-id/ | grep google` (491), `gcloud run jobs execute <job>` (612), and `gcloud compute resource-policies create instance-schedule` with `gcloud compute instances add-resource-policies` (647). Fix: put each in an `sh` block and say above it where it runs. At 647, write it as numbered steps for making the schedule and attaching it.
    9. `machine.md:539-551` (step 12 of *On GCP, step by step*): wrong: one step holds three actions in two places: wait for the board, stop the instance on the VM, and stop the VM on your own computer. The operator guide's rule is one action and its command per step (`style.md`, *The operator guide*). Fix: split it into steps 12 to 14. No other file links to a step number above 11.

    Criterion 2: unchanged from entries 7, 11, 14 and 18. Nothing was dropped except the two history sentences, and no *Reference* section was added. Criterion 3: entry 20 says `make documents` printed `documents ok`, and the file is on `docs/checked-documents.txt`. Criterion 4: the links I followed resolve. They are `health.md` *The factory log*, *The preflight's items* and *Transcripts*, `stops.md` *The stops*, `work-items.md` *A restart during a stage*, and the repository files. The `style.md` paragraph at `:73` is unchanged since round 2 and holds the human's rule.
23. factory: This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
24. 2026-11-06 human: One more round, by the human's standing word for tonight (no stop at a round cap while the findings are real). The documenter fixes findings 1 to 8 of the last review as written. Before it ends, it counts the words of every sentence it changed with a short script and splits each one over about 25 words, so that rule 2 needs no further round.
25. factory: started docs-review as vm.
26. reviewer: Round 0 docs-review, after the human's answer in entry 24. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`.

    The documenter has not run since entry 22. Entry 24 answered the question at the round cap, and that answer restarted this docs-review stage, not docs-only. `git log` shows that `docs/operator-guide/machine.md`, `docs/project-guide/style.md` and `docs/checked-documents.txt` last changed in 42070ae1c, the commit entry 22 reviewed. `git diff --stat 42070ae1c HEAD` over `README.md`, `docs`, `operator`, `agents` and the code these documents describe shows only `docs/runs/2026-11-05-f0052/log.md`, which is the human's file. So nothing the findings rest on has moved.

    I read each line entry 22 named again. Every finding still stands at the same line. Entry 24 tells the documenter to fix findings 1 to 8 of entry 22 as written, and to count the words of every sentence it changes with a short script, splitting each one over about 25 words. Below are those eight findings, restated so the documenter can work from this entry.

    1. `docs/operator-guide/machine.md:318`: wrong: "A missing required option, … prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2" is about 45 words (rule 2). Fix: put the five refused inputs in a short list, then say in a sentence of its own what the script prints and that it exits 2.
    2. `machine.md:347`: wrong: "Place all three files, …, readable by `factory`, and run the same command again: steps 1 to 11 report `found` and the rest completes" is about 33 words with two ideas (rule 2). Fix: one sentence for placing the files, and one for the second run and what it reports.
    3. `machine.md:377` and `:379`: wrong: "Every run rewrites `factory.env` … (the Claude Code and opencode versions and the opencode model ids), and writes it only when its text differs" is about 34 words, and "For values the script does not know (…), make a second file …" is about 37 (rule 2). Fix: split each, and give the parenthesis its own sentence.
    4. `machine.md:385`: wrong: "After the rollback the file has the snapshot's size but may still read the newer page: … so the sync does not repair it" is about 45 words (rule 2). Fix: split it into three sentences: what the file reads, what git's stat cache does, and that the sync does not repair it.
    5. `machine.md:137`, `:198`, `:242` and `:341`: wrong: each holds one sentence of about 33 to 42 words (rule 2). They are "It holds no user of its own … and mounts the dataset", "Without the file, every container runs in the base image, … only when it configures none)", "It has no file of the repository, … as `operator/vm/Dockerfile` does" and "The script writes the files … root's `/dev/stdin`". Fix: split each into sentences of one idea.
    6. `machine.md:555`: wrong: "Take the steps of *On GCP, step by step* from step 6 on, without `gcloud`: copy …, run it …, place the three secrets, run the script again, build the image, start the service" is about 50 words, and it is a task written as prose (rule 2, and the operator guide's numbered steps). Fix: one sentence saying that steps 6 to 11 apply without `gcloud`, then what differs as a short numbered list or as sentences of its own.
    7. `machine.md:571`, `:595`, `:612`, `:614` and `:616`: wrong: each holds one sentence of about 38 to 42 words (rule 2). They are the read-only mounts bullet, "The time from the start of a stage … `take` is the copy back", "With `FACTORY_IDLE_SHUTDOWN_ACTION=exit` the factory, … ends the job's execution", "On a VM a machine stop waits … with other settings" and "The setup script gives `factory` the right … both from the same run". Fix: split each at its `:` or `;` into sentences of one idea, with at most one parenthesis each.
    8. `machine.md:491`, `:612` and `:647`: wrong: commands the reader is to run still stand inline in prose, against rule 6 and the `sh`-block rule at `style.md:73`. They are `ls -l /dev/disk/by-id/ | grep google` (491), `gcloud run jobs execute <job>` (612), and `gcloud compute resource-policies create instance-schedule` with `gcloud compute instances add-resource-policies` (647). Fix: put each in an `sh` block, with the text above saying where it runs. At 647, write it as numbered steps: make the schedule, then attach it.

    What I left out on purpose: finding 9 of entry 22 says step 12 of *On GCP, step by step* (`machine.md:539-551`) holds three actions. I did not repeat it, because entry 24 limits this round to findings 1 to 8. If the human wants step 12 split into steps 12 to 14, it stays open for a later round.

    Criteria 2 to 4 are unchanged from entry 22:
    - Criterion 2: nothing was dropped except the two history sentences that entry 7 named, and no *Reference* section was added.
    - Criterion 3: the file is on `docs/checked-documents.txt`, and entry 20 says `make documents` printed `documents ok`.
    - Criterion 4: the links that entry 22 followed still resolve. No linked file changed since that review.
27. factory: started docs-only as vm.
28. documenter: Round 1 docs-only, after the human's answer in entry 24. I fixed findings 1 to 8 of entry 22, as entry 26 restated them. The last line of `make documents` is `documents ok (5.8 s)`. I changed only documents, so I did not run `make check`.

    Files changed:
    - `docs/operator-guide/machine.md`, the only file I touched:
      1. Setup script, the refused inputs: the five refused inputs are a list, and one sentence says what the script prints and that it exits 2.
      2. Secrets: placing the three files and the second run are separate sentences.
      3. `factory.env` and `factory.local.env`: both sentences are split, and each parenthesis is its own sentence.
      4. Page cache after the rollback: split into what the file reads, what git's stat cache does, and that the sync does not repair it.
      5. The base-image paragraph, the user-less container, the `Dockerfile` build and the files written as `factory`: each sentence is split into sentences of one idea.
      6. Without `gcloud`: one sentence says that steps 6 to 11 apply, and a short numbered list names what differs.
      7. The read-only mounts bullet, the `take` timing, the exit action in a job, the machine stop in a job and the right to `poweroff`: all are split.
      8. The three inline commands are now `sh` blocks with the place named above each:
         - The `ls -l /dev/disk/by-id/ | grep google` command is in step 7 of *On GCP, step by step*, and runs on the VM.
         - `gcloud run jobs execute <job>` runs on your own computer.
         - The schedule is now two numbered steps, make the schedule and attach it. The placeholders `<schedule>`, `<region>`, `<cron expression>` and `<timezone>` are mine; the old text named only the two commands. I did not run these commands, because they act on a cloud account. The flags `--vm-start-schedule` and `--timezone` are from my knowledge of `gcloud`, not from a run.

    Entry 24 asked me to count the words of every sentence I changed with a script. I ran it over the added lines and split at `.`, `:` and `;`. Two sentences remain, at 26 and 27 words: the opening of *In a job* and the opening of *The right*. I left them as about 25 words.

    Cross-read: the headings that other files link to are unchanged. The *Starting the machine again* heading is the same, and the numbering of steps 1 to 11 of *On GCP, step by step* is unchanged.

    Not done: finding 9 of entry 22, which would split step 12 of *On GCP, step by step* into steps 12 to 14. Entry 24 limited this round to findings 1 to 8, and the human can open it in a later round.

    Stale text I saw and did not touch, because it is outside this story:
    - `make documents` reports `docs/project-guide/work.md:13: factory/agents does not exist` in its report-only list.
    - `docs/operator-guide/agent-runtime.md:181` names `planning/cloud-sandbox/`.
    - `docs/operator-guide/stops.md:235` is a very long paragraph.

    `check`: check: green
    `secrets`: secrets: green (0.7 s)
    `documents`: documents ok (5.9 s)
29. factory: started docs-review as vm.
30. reviewer: Round 1 docs-review, after the human's answer in entry 24 and the documenter's entry 28. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, which covers `docs/operator-guide/machine.md`, `docs/project-guide/style.md` and `docs/checked-documents.txt`. I also read this round's change on its own (`git diff 42070ae1c HEAD -- docs/operator-guide/machine.md`). I judged the documents against the code, the criteria, the human's answers in entries 12 and 24, and `docs/project-guide/style.md`.

    no findings

    All eight findings of entry 22, as entry 26 restated them, are fixed:
    1. *The script* (`machine.md:318-326`): the five refused inputs are now a list. One sentence says the script prints `setup.sh: <what is wrong>` and the usage, and exits 2. This matches `operator/vm/setup.sh:69-85`.
    2. *The two passes*: placing the files and the second run are now separate sentences.
    3. *The environment file*: both long sentences are split, and each parenthesis became a sentence of its own.
    4. *The page cache after a rollback*: split into what the file reads, what git's stat cache does, and that the sync does not repair it.
    5. Lines 137, 198, 242 and 341 are now split into sentences of one idea.
    6. *On any Ubuntu 24.04 VM*: one sentence says steps 6 to 11 apply without `gcloud`, and a numbered list follows. `--device` taking a disk or a file matches `setup.sh:12,172`.
    7. The read-only mounts bullet, the `take` timing, *In a job*, *A machine stop in a job* and *The right* are split.
    8. The three inline commands are now `sh` blocks, and the text above each says where it runs: `ls -l /dev/disk/by-id/ | grep google` in step 7 on the VM, `gcloud run jobs execute <job>` and the two schedule steps on your own computer. This follows the rule the human gave in entry 12 (`style.md`, *Examples that are not run*).

    I looked at every sentence this round changed. None is much over about 25 words, and none holds more than one parenthesis. The longest are the openings of *In a job* and *The right*, at about 26 words. No heading changed, so the links from other files still resolve (criterion 4). The file is on `docs/checked-documents.txt`, and entry 28 says `make documents` printed `documents ok` (criterion 3). The factory checks that again after this stage.

    The flags of the two `gcloud compute` schedule commands (`--region`, `--vm-start-schedule`, `--timezone`, `--resource-policies`) are not in this repository's code. Entry 28 says they come from the documenter's knowledge of `gcloud`, not from a run. They act on a cloud account, so the human's rule in entry 12 lets them stand as bare commands in an `sh` block. They also match `gcloud`'s documented flags as far as I know them. So I did not count them as a finding.

    Still open, on purpose: finding 9 of entry 22 (step 12 of *On GCP, step by step*, `machine.md:551-563`, holds three actions). Entry 24 limited the round to findings 1 to 8, so I left it out again. The human can still ask for it in a later story.

    Criterion 2: unchanged from entries 7 to 22. Nothing was dropped apart from the two history sentences named in entry 7, and no *Reference* section was needed.
31. factory: done (pull request merged); cost: 13 runs, 17.6 min, 143 turns, 601651 tokens in (5075896 more from cache), 103116 out, $6.21
