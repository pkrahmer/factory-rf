---
stage: docs-only
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 611
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-06T23:27:32.508934Z'
  lease_duration: 60
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
---

# The operator guide's the machine reads for the operator

## Description

`docs/operator-guide/machine.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

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
