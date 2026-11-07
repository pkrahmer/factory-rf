---
stage: docs-approval
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 619
comments_read: [6701199398]
handed_over: docs-approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:26:18.704425Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:26:18.712083Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:26:34.915531Z'
  stage: intake
  run: 28486f415358463cb254047a9233ada2
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T02:26:39.711230Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T02:31:16.047462Z'
  stage: docs-only
  run: 4cad78abdee1490794204e6ab1560f82
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T02:31:21.359561Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:32:15.278255Z'
  stage: docs-review
  run: 962bb58675354edea471f44e5c8eafd2
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T02:32:20.299507Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T02:35:07.179110Z'
  stage: docs-only
  run: 240a1a8b2ad04f7da00fb96d6580e230
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T02:35:12.302164Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:35:51.400402Z'
  stage: docs-review
  run: d9879a24280b4a7db8888f03988eea15
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T02:35:56.481265Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T02:38:36.550245Z'
  stage: docs-only
  run: bf96caf190684cf2843de0361120c0ca
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T02:38:41.382490Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:39:17.259617Z'
  stage: docs-review
  run: 9954e335cd7641ffa358c77127ae6b93
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T02:39:22.327916Z'
  stage: docs-only
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-07T02:42:05.978202Z'
  stage: docs-only
  run: fa6c5c461d394cdeadb84e28fa69255d
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T02:42:11.107489Z'
  stage: docs-review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:43:00.150501Z'
  stage: docs-review
  run: f758a314bc3242da931c6d57c9fc2a8e
- number: 20
  speaker: factory
  kind: question
  at: '2026-11-07T02:43:00.150501Z'
  stage: docs-review
  run: f758a314bc3242da931c6d57c9fc2a8e
  blocked: round_cap
- number: 21
  speaker: human
  kind: comment
  at: '2026-11-07T02:46:51.754632Z'
  stage: docs-review
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-07T02:46:54.533364Z'
  stage: docs-review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:47:31.743321Z'
  stage: docs-review
  run: a600d88e306e4403aa16b84db75ebf1f
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-07T02:47:36.997322Z'
  stage: docs-only
- number: 25
  speaker: documenter
  kind: result
  at: '2026-11-07T02:50:33.581959Z'
  stage: docs-only
  run: 215665b04ea040289ea1de75e4171383
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-07T02:50:38.651074Z'
  stage: docs-review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:51:29.161485Z'
  stage: docs-review
  run: 654a9ca211904f71af5361182f23e77b
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-07T02:51:34.395764Z'
  stage: docs-only
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-07T02:54:16.918055Z'
  stage: docs-only
  run: 51f7747bb5314f87994152e33d1bda36
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-07T02:54:22.403169Z'
  stage: docs-review
- number: 31
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:54:49.091171Z'
  stage: docs-review
  run: b88628f68d8b47c7ac465ed5b1f6890b
---

# The operator guide's index reads for the operator

## Description

`docs/operator-guide/README.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it changes only `docs/operator-guide/README.md` and `docs/checked-documents.txt`, both under `docs/*`, so the story takes the docs route. It names no code, test or agent file, and says that none changes. Links to changed headings are covered.
   - Criteria: criteria 1 and 2 are judged by the reviewer against the style guide and the code, which is how the feature's decision 2 defines them for this route. Criterion 3 is checked by `make documents` printing `documents ok` and by the list entry. Criterion 4 is a link check. Criterion 5 is `make check`. The Interface's one-line list entry and its heading-link rule are covered by criteria 3 and 4. No rule here has a failing side that needs its own criterion.
   - Smoke test: `grep -cx "docs/operator-guide/README.md" docs/checked-documents.txt` is runnable and has no pytest options. Its `Expect: 1` is checkable against the output.
   - Docs criterion: it names what the reader must know (criteria 1 to 4), not sentences to write. It says `docs/decisions.md` gets no change.
   - Architecture: it touches no code, so the layers are not affected. It leaves out the playbook, `decisions.md` and `docs/runs/`, which `CLAUDE.md` keeps for the human.
   - Scope: it is S0011 of F0054 and matches the story list in `feature.md`. It is not in "Out of scope".
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/operator-guide/README.md`: rewritten for the operator.
     - It now opens with what the guide is for and what the machine is, then a numbered "Where to start" list, then a table of the ten topic files, then a pointer to `decisions.md`.
     - The two "Replaced" sections are gone, with their feature and story IDs and version names (style rules 1 and 7). The facts that are still true are in a new *Reference* section at the end: the containers are the only stage environment; the three required variables; a setting file that holds an unread variable is harmless; the container runs as `factory` with `--userns=keep-id` and mounts the dataset only; the token stays on the host; the agent's home is `home/` and the rollback clears it; the take, and the journal line `The factory left out changes outside the write paths: ...`; a pipeline definition with `tool_paths` is refused; the stage image and the credential helper paths; `factory-watch` has no follow mode; and where the planning history is kept (the tag `planning-history-2026-10-19`).
     - I checked these claims against the code: `src/factory/machine/application/stage_environment.py`, `src/factory/machine/adapters/podman_runs.py`, `src/factory/work/domain/decisions.py`, `src/factory/pipeline/domain/pipeline_definition.py` (every model is `extra="forbid"`), `src/factory/shared/domain/settings.py`, `operator/vm/setup.sh` and `src/factory/entry/wiring.py`. I did not run `tool_paths` through the loader. "Refused" rests on the `extra="forbid"` models and on the old text.
     - Each glossary word is linked at its first use.
   - `docs/checked-documents.txt`: added `docs/operator-guide/README.md`.
   - `README.md` (line 28): it pointed to *Replaced in v1.2* in the guide's index, which no longer exists. It now says the guide's index is `docs/operator-guide/README.md`. This is the link fix the Interface asks for (criterion 4).

   Dropped on purpose, for the reviewer (criterion 2):
   1. The document check (`REPLACED_PHRASES` and `GLOSSARY_FORBIDDEN` in `src/factory/shared/domain/documents.py`) flags outside an exempt section `factory-last-line`, `factory-run.json`, `factory-tick.lock` and `stage table`. The check blocked them as `describes a replaced behaviour`, so I left them out. The three v1 files in `.git/` and the `factory-last-line` file are no longer named; the follow-mode statement stays without the literal option name.
   2. Pure history of removed things, which the code no longer has and style rule 7 forbids: `factory-confine`/Landlock, the `agent` user and its `sudo` chain, `FACTORY_AGENT_USER`, `factory.entry.leftovers`, `factory.entry.fresh_home`, the checkout seal and the `nested_repository` stop, `UndoService`, the Docker image and compose file, `docker exec`, and the records contract rising to `3.0`. The decision log already records the replacement (`docs/decisions.md`, the "Replaced in v1.2" entry). The story says `docs/decisions.md` gets no change, so I wrote nothing there.
   3. The v1.1 pointer (tag `v1.1`) and the "v1.2" and "v1.1" names.

   `make documents` ends with `documents ok (13.6 s)`. The file has no `console` example blocks, so none ran. I did not run `make check`, because I changed only documents.

   Cross-read and found current: the links from `work-items.md` and `health.md` to the index, and the other nine files of the guide, which link back to `README.md` as a whole.

   Stale text seen, not touched:
   - `README.md` (root) still has a "Replaced from v1" section and v1.1 history in "How it is built". It is not this story's.
   - `docs/project-guide/README.md` line 21 and `docs/project-guide/shared.md` line 97 describe the document check's exemption of the *Replaced* sections. They are still accurate for the code. They would change only if a later story removes those exemptions.
   - `docs/project-guide/machine.md` and `agents.md` have "Replaced in v1.2" sections, and the *Not checked yet* report lists unresolved names in the project guide. These belong to the stories for those files.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.7 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch and `docs/project-guide/style.md`. These parts hold: the four-column file table, the "Where to start" steps, the glossary links at first use, the `README.md:28` link fix, the `docs/checked-documents.txt` line, the journal line (`src/factory/work/domain/decisions.py:19`), the credential helper path (`operator/vm/setup.sh:402`, `src/factory/entry/wiring.py:169`), the refusal of `tool_paths` (`extra="forbid"` in `src/factory/pipeline/domain/pipeline_definition.py`) and the planning-history tag. I accept the list of things dropped on purpose in entry 5 under criterion 2: they are removed behaviour, which style rule 7 keeps out of the guide.

   Findings:
   1. `docs/operator-guide/README.md`, *What the stage environment is*, bullet 1: "an instance without `FACTORY_DATASET`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` is refused" is false for `FACTORY_DATASET`. `src/factory/shared/domain/settings.py:165` requires it only "with zfs", and `FACTORY_SNAPSHOTS=copy` runs without it. Fix: name `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` as required, and `FACTORY_DATASET` as required when the snapshots are `zfs`.
   2. `docs/operator-guide/README.md`, *What the stage environment is*, bullet 2: "runs as the user `factory` with `--userns=keep-id`" holds only for the VM. On the Cloud Run job profile `src/factory/machine/adapters/podman_runs.py:47-52` gives `--http-proxy=false --network=host` and no `--userns=keep-id`, and `cloud-run.md` documents that job. Fix: say this is the VM's container, and that a Cloud Run job runs without the user namespace.
   3. `docs/operator-guide/README.md`, *What the stage environment is*, bullet 2: "mounts the dataset only" is false. `src/factory/agents/adapters/agent_launch.py:206` also mounts the login files read-only at their own paths. The sync container also mounts the checkout's `.git` and the agent home read-only (`src/factory/machine/application/stage_environment.py:188-191`). Fix: say the dataset is the only writable mount, and the login files are mounted read-only.
   4. `docs/operator-guide/README.md`, *Options that do not exist*: "an option for it is unknown" is vague and reads as a note about a removed option (style rules 1 and 7). `src/factory/entry/watch.py:72-73` builds an argument parser with no arguments, so `factory-watch` takes no option but `--help`. Fix: state the current truth, "`factory-watch` takes no options; it refuses any option but `--help`", and drop the heading's "do not exist" framing.
   5. `docs/operator-guide/README.md`, *Reference*, opening line: "for the operator who knows an older setup or an older option" frames the section as history, against style rules 1 and 7. Fix: say what the section holds, for example "How the stage environment works and what the instance refuses".
8. factory: started docs-only as vm.
9. documenter: Round 1: fixed the reviewer's five findings, all in `docs/operator-guide/README.md`, section *Reference*. I read the cited code only as the reviewer's findings quote it. I did not open it myself.
   1. Opening line: now "How the stage environment works and what the instance refuses." (no framing as history).
   2. Bullet 1 of *What the stage environment is*: `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` are required. `FACTORY_DATASET` is required when the snapshots are `zfs`, and with `FACTORY_SNAPSHOTS=copy` the instance runs without a dataset.
   3. Bullet 2 of the same section: `--userns=keep-id` and the user `factory` are now stated for the VM. A Cloud Run job runs without the user namespace, with a pointer to `cloud-run.md`.
   4. Same bullet: the dataset is the only writable mount, and the login files are mounted read-only at their own paths. I left out the sync container's read-only mounts of the checkout's `.git` and the agent home, which the reviewer also named.
   5. The heading *Options that do not exist* is now *Command-line options*: "`factory-watch` takes no options but `--help`; it has no follow mode."

   `make documents` ends with `documents ok (13.7 s)`. I changed only documents, so I did not run `make check`.

   Cross-read and found current: the rest of the operator guide README and the link fix in the root `README.md`, as in entry 5. I noticed no new stale text beyond the items entry 5 already lists.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.6 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1. I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch and `docs/project-guide/style.md`.

    All five findings of entry 7 are fixed:
    - the `FACTORY_DATASET` condition (`src/factory/shared/domain/settings.py:165`);
    - the VM-only `--userns=keep-id` and the Cloud Run job profile (`src/factory/machine/adapters/podman_runs.py:47-52`);
    - the dataset as the only writable mount and the login files mounted read-only (`src/factory/agents/adapters/agent_launch.py:205`);
    - `factory-watch` taking only `--help` (`src/factory/entry/watch.py:72-73`);
    - the *Reference* opening line.

    Leaving out the sync container's read-only mounts is acceptable. The bullet is about the agent's container. The `README.md:28` link fix and the `docs/checked-documents.txt` line still hold. The list of things dropped on purpose in entry 5 stays accepted under criterion 2.

    Findings:
    1. `docs/operator-guide/README.md`, *What the stage environment is*, bullet 1: the bullet lists the settings without which the instance is refused, and it says "with `FACTORY_SNAPSHOTS=copy` it runs without a dataset". It leaves out that copy snapshots require `FACTORY_SNAPSHOT_BASE` (`src/factory/shared/domain/settings.py:168`, `required="with copy"`). An operator who switches to `copy` would expect to need nothing else. Fix: add "and one without `FACTORY_SNAPSHOT_BASE` when the snapshots are `copy`".
    2. `docs/operator-guide/README.md`, *What the stage environment is*, bullets 2 and 7: style rule 8 says a file of the repository is linked by a relative link. "(see `cloud-run.md`)" names the file in backticks with no link. So do `operator/vm/Dockerfile`, `operator/vm/git-credential-factory` and `operator/vm/setup.sh`. `docs/operator-guide/machine.md:129` already links `[Dockerfile](../../operator/vm/Dockerfile)` this way. Fix: write `[cloud-run.md](cloud-run.md)`, `[Dockerfile](../../operator/vm/Dockerfile)`, `[setup.sh](../../operator/vm/setup.sh)` and `[git-credential-factory](../../operator/vm/git-credential-factory)`. Leave the installed path `/usr/local/bin/git-credential-factory` in backticks.
12. factory: started docs-only as vm.
13. documenter: Round 2: fixed the reviewer's two findings from entry 11, both in `docs/operator-guide/README.md`, section *Reference*, *What the stage environment is*.
    1. Bullet 1 now also says an instance is refused without `FACTORY_SNAPSHOT_BASE` when the snapshots are `copy`. I checked this against `src/factory/shared/domain/settings.py:168` (`required="with copy"`).
    2. Bullets 2 and 7 now use relative links: `[cloud-run.md](cloud-run.md)`, `[Dockerfile](../../operator/vm/Dockerfile)`, `[git-credential-factory](../../operator/vm/git-credential-factory)` and `[setup.sh](../../operator/vm/setup.sh)`. The installed path `/usr/local/bin/git-credential-factory` stays in backticks.

    `make documents` ends with `documents ok (13.6 s)`. I changed only documents, so I did not run `make check`.

    Cross-read and found current: the rest of the guide's README and the earlier fixes (as in entries 5 and 9).

    Stale text seen, not touched: only the items already listed in entry 5. They belong to other stories.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (13.8 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2. I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch and `docs/project-guide/style.md`.

    Both findings from entry 11 are fixed:
    - Bullet 1 now says an instance is refused without `FACTORY_SNAPSHOT_BASE` when the snapshots are `copy`. This matches `src/factory/shared/domain/settings.py:168` (`required="with copy"`). `FACTORY_DATASET` "with zfs" (line 165) and `FACTORY_WORKSPACE`/`FACTORY_STAGE_IMAGE` (`_YES`, lines 166 and 169) also hold.
    - Bullets 2 and 7 now link `cloud-run.md`, `operator/vm/Dockerfile`, `operator/vm/git-credential-factory` and `operator/vm/setup.sh` with relative links. All four files exist. The installed path stays in backticks.

    These still hold: the `README.md:28` link fix, the `docs/checked-documents.txt` line, the earlier round's facts, and the list of things dropped on purpose in entry 5 (accepted under criterion 2).

    Findings:
    1. `docs/operator-guide/README.md:39`, the sentence that starts "The stage environment is the containers; an instance without `FACTORY_WORKSPACE`…" and ends "…(with `FACTORY_SNAPSHOTS=copy` it runs without a dataset).": the round-2 addition makes it about 42 words with three conditions. That breaks style rule 2 (split a sentence of more than about 25 words), and rule 4 (common case first) suffers too. Fix: split it into short sentences with the same facts. For example: "The stage environment is the containers. An instance without `FACTORY_WORKSPACE` or `FACTORY_STAGE_IMAGE` is refused. With `zfs` snapshots it also needs `FACTORY_DATASET`. With `FACTORY_SNAPSHOTS=copy` it needs `FACTORY_SNAPSHOT_BASE` instead and runs without a dataset."
16. factory: started docs-only as vm.
17. documenter: Round 3: fixed the reviewer's one finding from entry 15, in `docs/operator-guide/README.md`, section *Reference*, *What the stage environment is*, bullet 1. The long sentence is now four short ones with the same facts. An instance without `FACTORY_WORKSPACE` or `FACTORY_STAGE_IMAGE` is refused. With `zfs` snapshots it also needs `FACTORY_DATASET`. With `FACTORY_SNAPSHOTS=copy` it needs `FACTORY_SNAPSHOT_BASE` instead and runs without a dataset. Those conditions were checked against the code in round 2.

    `make documents` ends with `documents ok (13.5 s)`. I changed only documents, so I did not run `make check`.

    Cross-read and found current: the rest of the guide's README and the earlier fixes, as in entries 5, 9 and 13.

    Stale text seen, not touched: only the items entry 5 lists. They belong to other stories.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (13.6 s)
18. factory: started docs-review as vm.
19. reviewer: Round 3. I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch and `docs/project-guide/style.md`.

    The finding from entry 15 is fixed. Bullet 1 of *What the stage environment is* is now four short sentences with the same facts. These still hold: the facts of rounds 1 and 2, the `README.md:28` link fix, the `docs/checked-documents.txt` line, and the list of things dropped on purpose in entry 5 (accepted under criterion 2).

    Earlier rounds missed a gap in criterion 1. The criterion says each factory word is linked to the glossary at its first use. Style rule 3 says the same. I checked every term in `docs/project-guide/glossary.md` against the file:

    Findings:
    1. `docs/operator-guide/README.md`: three linked words are not linked at their first use.
       - "dataset" is first used unlinked at line 5 ("on one ZFS dataset"), but linked only at line 40.
       - "stage environment" is first used unlinked at line 35 ("How the stage environment works"), but linked only at line 39.
       - "pipeline definition" is first used unlinked at line 27 (the `pipeline.md` row), but linked only at line 44.
       Fix: move each link to the first use: `[dataset](../project-guide/glossary.md)` at line 5, `[stage environment](...)` at line 35, `[pipeline definition](...)` at line 27. Then remove the later links.
    2. `docs/operator-guide/README.md`, the file table (lines 26-29), bullet 5 of *What the stage environment is* (line 43) and *This repository's own history* (line 53): these glossary words are never linked.
       - In the table: "stalls" (line 26), "story" (line 27), "work item" (line 28), "feature", "acceptance", "approval", "lease" and "claims" (line 29).
       - At line 43: "role", "write paths" and "journal".
       Fix: link each one to `../project-guide/glossary.md` at its first use in the file. Later uses stay plain.
20. factory: This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
21. 2026-11-07 human: One more round, by the human's standing word for tonight. The documenter fixes findings 1 and 2 of the last review: each glossary word is linked at its first use in the file, also in the file table and the two sections named, and only there. Before it ends, it lists the glossary words the page uses and checks each first use by script.
22. factory: started docs-review as vm.
23. reviewer: Round 0 after the human's answer (entry 21). I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch, `docs/project-guide/style.md` and `docs/project-guide/glossary.md`.

    No documenter run came between the human's answer (entry 21) and this review (entry 22). The last commit that changed `docs/operator-guide/README.md` is 62973866a, the round-3 documenter commit. So the file is as entry 19 reviewed it, and both findings of entry 19 are still open. The human's answer asks the documenter to fix them, so I send the work item to `docs-only`.

    These still hold: the facts checked in earlier rounds (the settings in bullet 1 against `src/factory/shared/domain/settings.py:165-169`, the container boundary, the take's journal line, `tool_paths`, the relative links, `factory-watch`). The `README.md:28` link fix and the `docs/checked-documents.txt` line also hold. The list of things dropped on purpose in entry 5 stays accepted under criterion 2.

    Findings:
    1. `docs/operator-guide/README.md` lines 5, 27 and 35: three glossary words are linked later than their first use (style rule 3, criterion 1). "dataset" is first used at line 5 ("one ZFS dataset") but linked at line 40. "pipeline definition" is first used at line 27 (the `pipeline.md` row) but linked at line 44. "stage environment" is first used at line 35 but linked at line 39. Fix: put each link `../project-guide/glossary.md` at the first use and make the later use plain.
    2. `docs/operator-guide/README.md` lines 26, 27, 28, 29 and 43: these glossary words are never linked. In the table: "stalls" (26), "story" (27), "work item" (28), and "feature", "acceptance", "approval", "lease" and "claims" (29). At line 43: "role", "write paths" and "journal". Fix: link each one to `../project-guide/glossary.md` at its first use in the file, and only there. As entry 21 asks, list the glossary words the page uses and check each first use by script before ending.
24. factory: started docs-only as vm.
25. documenter: Round after the human's answer (entry 21): I fixed findings 1 and 2 of the last review. I changed one file, `docs/operator-guide/README.md`. Every glossary word is now linked to `../project-guide/glossary.md` at its first use in the file, and only there. I changed no other file.

    - **Moved earlier (finding 1):** "dataset" is linked at line 5, "pipeline definition" at line 27 (the `pipeline.md` row) and "stage environment" at line 35. I made the later uses plain.
    - **Linked for the first time (finding 2):**
      - In the file table: "stalls", "story", "work item", "feature", "acceptance", "approval", "lease" and "claims".
      - In the *Reference* section: "role" and "journal". I linked "write paths" at its first real use, in the `tool_paths` bullet. Its earlier mention is inside the quoted journal message, `The factory left out changes outside the write paths: ...`. I did not link inside that code span, because a link there would change the quoted text.
    - **Check by script, as the human asked:**
      - The script listed each glossary term the page uses (instance, stop, stage, dataset, feature, journal, lease, pipeline definition, role, stall, story, take, work item, write paths, base, acceptance, approval, claim, stage environment).
      - It found the first line where each appears and whether a link sits on it. Every first use is linked, except "write paths", whose first appearance is the quoted message.
      - I did not list "round", "tick", "attempts cap", "round cap", "backlog", "cost record", "crash", "project command" and "round" in that check, because the page does not use them as the glossary defines them.
    - **Verification:** `make documents` ends with `documents ok (13.5 s)`. I changed only documents, so I did not run `make check`.
    - **Cross-read:** I read the rest of the page again against the earlier rounds and found it current.
    - **Stale text not touched:** only the items listed in entry 5. They belong to other stories.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (13.7 s)
26. factory: started docs-review as vm.
27. reviewer: Round 1 after the human's answer (entry 21). I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch, `docs/project-guide/style.md` and `docs/project-guide/glossary.md`.

    Both findings from entry 23 are fixed. I went through every term in the glossary against `docs/operator-guide/README.md`. Each term the page uses is linked at its first use and only there: instance and stop (line 3); stage and dataset (line 5); stall (26); pipeline definition and story (27); work item (28); feature, acceptance, approval, lease and claim (29); stage environment (35); base (41); take, role and journal (43). "write paths" is first linked at line 44. Its earlier mention on line 43 is inside the quoted journal message in a code span, so it stays unlinked. I accept that: the quote must keep its exact text, and a code span holds no links.

    These still hold: the settings in bullet 1 (`src/factory/shared/domain/settings.py:165-169`), the container boundary, the take's journal line, `tool_paths`, the relative links, `factory-watch`, the `README.md:28` link fix and the `docs/checked-documents.txt` line. The list of things dropped on purpose in entry 5 stays accepted under criterion 2.

    Findings:
    1. `docs/operator-guide/README.md:5`: the line says "An instance runs on a VM with ZFS and rootless Podman, and every stage runs in throwaway containers on one ZFS dataset". The code and the guide itself say otherwise. `src/factory/shared/domain/settings.py:98` and `:168` allow `FACTORY_SNAPSHOTS=copy`, which needs no ZFS. `docs/operator-guide/machine.md:111-113` (*Without ZFS*) and `cloud-run.md:73` run an instance in a Cloud Run job without ZFS. Line 39 of this same file says that with `copy` the instance "runs without a dataset". Fix: keep the common case first and add the other one. For example: "An instance usually runs on a VM with ZFS and rootless Podman, where every stage runs in throwaway containers on one ZFS dataset. It can also run without ZFS, in a Cloud Run job ([cloud-run.md](cloud-run.md))." Keep the dataset link at its first use.
28. factory: started docs-only as vm.
29. documenter: Fixed the reviewer's one finding from entry 27. I changed one file, `docs/operator-guide/README.md`, line 5. The sentence now says an instance "usually" runs on a VM with ZFS and rootless Podman, where every stage runs in throwaway containers on one ZFS dataset. It adds that an instance can also run without ZFS, in a Cloud Run job, with a link to `cloud-run.md`. The common case stays first. The dataset and stage links stay at their first use. I checked the claim against `docs/operator-guide/machine.md` (*Without ZFS*) and the reviewer's code references (`FACTORY_SNAPSHOTS=copy`). `make documents` ends with `documents ok (13.6 s)`. I changed only documents, so I did not run `make check`.

    Cross-read and found current: the rest of the guide's README and the earlier fixes, as in entries 5, 9, 13 and 25.

    Stale text seen, not touched: only the items entry 5 lists. They belong to other stories.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (13.6 s)
30. factory: started docs-review as vm.
31. reviewer: Round 2 after the human's answer (entry 21). I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the code on the branch, `docs/project-guide/style.md` and `docs/project-guide/glossary.md`.

    The finding from entry 27 is fixed. `docs/operator-guide/README.md:5` now gives the usual case first: a VM with ZFS and rootless Podman, where every stage runs in throwaway containers on one ZFS dataset. It then says an instance can also run without ZFS, in a Cloud Run job, and links `cloud-run.md`. This matches `docs/operator-guide/machine.md:111-113` (*Without ZFS*: `FACTORY_SNAPSHOTS=copy`, with `FACTORY_DATASET` and `FACTORY_ZFS` not read) and `docs/operator-guide/cloud-run.md:73` (`FACTORY_SNAPSHOTS` is `copy`). It also agrees with bullet 1 of *What the stage environment is* (line 39). The links to dataset and stage are still at their first use, and the sentence stays under about 25 words.

    These still hold:
    - Every glossary word is linked at its first use and only there, as checked in entry 27.
    - The settings in bullet 1 match `src/factory/shared/domain/settings.py:165-169`.
    - The container boundary, the take's journal line, `tool_paths`, the relative links and `factory-watch` all still hold.
    - The headings that "Where to start" names exist: "The machine" (`machine.md:7`), "Configuration" (`install.md:39`) and "The stops" (`stops.md:7`).
    - The `README.md:28` link fix and the `docs/checked-documents.txt` line are in place.
    - Entry 5's list of things dropped on purpose stays accepted under criterion 2.

    Criteria 1 to 4 and the docs criterion are met.

    no findings
