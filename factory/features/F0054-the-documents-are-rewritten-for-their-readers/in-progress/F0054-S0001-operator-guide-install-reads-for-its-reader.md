---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 608
comments_read: [6696943013]
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
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T21:49:58.313569Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T21:52:45.619599Z'
  stage: docs-review
  run: 0391712758604a539dbb58f2f409895f
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T21:52:51.055560Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-06T21:55:59.789288Z'
  stage: docs-only
  run: 666f74ff0552425ba93f9442865d21ab
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T21:56:07.350507Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-06T21:58:12.182786Z'
  stage: docs-review
  run: bc42d74bba66402a8b4f86b23e1e021a
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T21:58:17.600265Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: question
  at: '2026-11-06T21:58:55.440004Z'
  stage: docs-only
  run: 79de3ed9565f48d08a1ae1b34d66225e
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-06T22:00:45.151843Z'
  stage: docs-only
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
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` (`docs/operator-guide/install.md`, `docs/checked-documents.txt`) against the work item, the old file on `main`, `docs/project-guide/style.md` and the code: `src/factory/shared/domain/settings.py`, `src/factory/entry/run.py`, `src/factory/entry/wiring.py`, `src/factory/entry/watch.py`, `src/factory/pipeline/application/scheduler.py`, `operator/vm/setup.sh` and `docs/project-guide/glossary.md`.

   What holds:
   - `make documents` ends `documents ok (1.8 s)`, with no finding on install.md (criterion 3).
   - Every link from another document to a section of install.md still resolves: *Configuration*, "When the process refuses to start", "The loop and its pauses" and "The checkout is cloned when it is missing". Nothing linked to the removed heading "A repository URL with a password is refused" (criterion 4).
   - These agree with the code: the settings defaults, every refusal text, the exit statuses 0, 1 and 2 (run.py:303-327), the pauses of 30 to 120 s (scheduler.py:19-20) and the VM's values (setup.sh:415-436).

   Findings:
   1. docs/operator-guide/install.md:31: the order of faults is wrong. `read_settings` reads `FACTORY_SNAPSHOTS` (settings.py:345) and a relative `FACTORY_SNAPSHOT_BASE` (settings.py:346) before the faults of `FACTORY_WORKSPACE` (settings.py:348). This line also contradicts the order the Reference gives at line 231. Fix: state the code's order once and make the other place point to it.
   2. docs/operator-guide/install.md:231: this order is wrong too. A relative `FACTORY_SNAPSHOT_BASE` (settings.py:346) comes before the workspace faults, not after them. `FACTORY_CLAUDE_HOME` (settings.py:354) is read before `FACTORY_TRANSCRIPT_DIR` (settings.py:355-359), and the line leaves it out. Fix: list the order as settings.py:337-359 reads it.
   3. docs/operator-guide/install.md:231: the line names the function `read_settings`. The style page's operator-guide section says "Name no module or class", and the journal (entry 5) claims the name was dropped. Fix: write "the factory reads" instead.
   4. docs/operator-guide/install.md:209-211 and :223-225: the `make mutants` commands are in `sh` blocks. These are neither runnable examples nor marked `console vm` with the real run they were copied from. The Description requires one or the other, and so does the Documents check. Fix: make each a `console vm` block copied from a real sweep, with the text above saying where it ran, or ask how to show a command that no run backs.
   5. docs/operator-guide/install.md:13 and :17: `uv sync` and `make check` are indented blocks with no info string. They are neither runnable nor marked, and they show no output (style rule 6, and the Description's rule on commands). Fix: write `console` blocks. The `make check` block is skipped as `suite` and expects `...` then `check: green`. `uv sync` becomes a runnable block with `...`, or a `console vm` block from a real run.
   6. docs/operator-guide/install.md:19: step 3 names no command. The style page says each step is one action with its command, and its own example gives one. Fix: add `sudo sh operator/vm/setup.sh --device <disk> --repository-url <url>` (usage at setup.sh:11).
   7. docs/operator-guide/install.md (whole file): the old file's line 58 was dropped without being named as dropped (criterion 2). It said that `operator/vm/setup.sh` prepares the VM with the dataset and the stage image, and that the preflight checks them (see "The preflight's items" in health.md). It is neither in the new text nor in *Reference*. Fix: restore it in step 3 or in *Reference*.
   8. docs/operator-guide/install.md: some glossary words are not linked at their first use (criterion 1, style rule 3): "work items" at :9, "dataset" and "base" at :83, "stage environment" at :195, "role" at :199 and "acceptance" at :205. Fix: link each to `../project-guide/glossary.md` at its first use.
   9. docs/operator-guide/install.md:52, :115, :142 and :239: "boundaries" is a private word of the code (`Boundaries`). It is not in the glossary, and the style page says to use no other private words (rule 3). Fix: say "when `factory-run` starts" or "before it builds anything".
   10. docs/operator-guide/install.md:43, :31 and :115 break style rule 2. Line 43 has two parentheses in one sentence. The sentence at :115 has about 35 words and the one at :31 about 30. Fix: split them.

   Open, outside this story's diff: `docs/project-guide/shared.md` still says the operator guide has no `Default` column and no refusal table, which is now false. The documenter named this too, so it is for the story of that file or for the human.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's findings 1 to 10 in `docs/operator-guide/install.md`, except finding 4, which I handled differently (see below). `make documents` ends `documents ok (1.8 s)`. I ran no `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/install.md`: the fixes below. `docs/checked-documents.txt` is unchanged.

   Findings by number:
   1. *Configuration* no longer states an order of faults. It points to *The order of faults* in the *Reference*, which is now the only place.
   2. *The order of faults* now follows `settings.py:337-359`:
      - the repository, the instance, `FACTORY_CHECKOUT`, `FACTORY_STATE`, the image identity file, `FACTORY_SNAPSHOTS`, and a relative `FACTORY_SNAPSHOT_BASE`;
      - then the workspace faults;
      - then the `FACTORY_SNAPSHOT_BASE`, `FACTORY_CLAUDE_HOME` and `FACTORY_TRANSCRIPT_DIR` faults, in that order;
      - then the other variables.
   3. The name `read_settings` is gone; the text says "the factory reads".
   4. Not done as the finding asks, because I have no real sweep to copy. The two `make mutants` commands are now inline code in prose. The text says they are not run in the documents and that no real sweep backs them. `uv sync` is a `console vm` block. I ran `uv sync` on this machine, which is the instance `vm`, and copied its last two lines (`Resolved 107 packages in 3ms`, `Bytecode compiled 4164 files in 49ms`); this is the output of a second run. `make check` is a `console` block that the check skips as `suite`. Open question for the reviewer or the human: is inline code acceptable for a command with no real run behind it?
   5. Both blocks have an info string now. They sit at column 0 instead of indented under their steps, because an indented fence made the check crash (`documents.py:681`, `ValueError: zip() argument 2 is longer than argument 1`). That crash on indented fences is a bug in the check, for the coder. It is outside this story.
   6. Step 3 now gives `sudo sh operator/vm/setup.sh --device <disk> --repository-url <url>`, taken from the usage in `setup.sh`.
   7. I restored the dropped sentence. Step 3 says the setup prepares the VM with the dataset and the stage image, and that the preflight checks them, with the link to "The preflight's items" in `health.md`.
   8. I linked "work items", "base", "dataset", "stage environment", "role" and "acceptance" to the glossary at their first use.
   9. "Boundaries" is gone. The text now says "when `factory-run` starts".
   10. I split the sentences of the `FACTORY_MIN_FREE_GB` row and of the `missing` refusal row. The parenthesis in the `FACTORY_MIN_FREE_GB` row is removed.

   Cross-read and found current: the links from `stops.md`, `machine.md` and the other operator-guide files to the headings of `install.md`. I kept all four of those headings.

   Stale text that is not mine to fix:
   - `docs/operator-guide/README.md` still has the "Replaced in v1.2" and "Replaced from v1" sections.
   - `docs/project-guide/shared.md` says the operator guide has no `Default` column and no refusal table, which is false now.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (1.9 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 docs review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/install.md` and `docs/checked-documents.txt`. I checked them against the old file on `main`, against `docs/project-guide/style.md`, and against the code in `src/factory/shared/domain/settings.py`, `src/factory/entry/wiring.py`, `operator/vm/setup.sh` and `uv.lock`.

    What holds:
    - Round 0's findings 1 to 3 and 5 to 10 are fixed.
    - *The order of faults* (install.md:235) now matches settings.py:337-359.
    - The refusal texts match settings.py, including `cannot read <path>: <reason>` and `<path> is empty` (settings.py:643-645), and wiring.py:235 has `names no owner/name on a host`.
    - The `console vm` block for `uv sync` says where it ran. Its `Resolved 107 packages` matches the 107 packages in `uv.lock`.
    - The headings that other files link to are all kept (criterion 4).
    - `docs/checked-documents.txt` has the line (criterion 3).

    Findings:
    1. docs/operator-guide/install.md:27: the code contradicts two claims about `operator/vm/setup.sh`.
       - It does not build the stage image. The script has no build step, and its last line says `setup: done: build the stage image and start factory@<instance>` (setup.sh:476).
       - It does not "make the VM". It prepares a fresh Ubuntu 24.04 machine (setup.sh:2-6).
       - The sentence is also about 34 words long (style rule 2).
       - Fix: say that setup.sh prepares the machine (the packages, the ZFS pool and dataset, the factory's checkout and its virtual environment, `image-id`, `factory.env` and the systemd unit). Then add a step that builds the stage image, pointing to "The stage image" in machine.md, before the instance starts.
    2. docs/operator-guide/install.md:37 and :124: "Every path is absolute" and the refusal row "A path variable holds a relative path" claim more than the code does.
       - `FACTORY_TOKEN_FILE`, `FACTORY_CLAUDE_LOGIN_FILE` and `FACTORY_API_LOGIN_FILE` are read with `_optional_path` (settings.py:370-372) and are never refused when relative.
       - Only checkout, state, agent home, image id file, provider file, CA bundle and snapshot base (settings.py:222-234, 606-630), plus workspace and transcript dir (settings.py:279, 298), are refused.
       - Fix: name in the row the variables that the refusal covers, and drop or narrow the sentence at :37.
    3. docs/operator-guide/install.md:215-217 and :229: the two `make mutants` commands are still shown as inline code. They are neither runnable nor marked `console vm` with a real run (the Description's rule on commands, and the Documents check).
       - "A sweep's command is:" ends in a colon that nothing follows.
       - "It is not run in the documents, and no real sweep backs it" speaks about the docs check, not to the operator.
       - No stage can make a real sweep: only the human starts one.
       - Fix: remove the two meta sentences and the dangling colon. Then end the docs-only stage with `question` to the human, offering three options:
         - (a) the human pastes a real sweep's output for a `console vm` block;
         - (b) the human accepts an inline command in prose for a command that only the human's sweeps run, as the style page's own Install example writes `setup.sh` inline;
         - (c) a form the human names.
    4. docs/operator-guide/install.md:62: the old file pointed from `FACTORY_API_LOGIN_FILE` to "The agent's API key" (agent-runtime.md:40). The old file's login-token row also pointed to "The agent's login token" (agent-runtime.md:30). Both pointers are dropped, and the journal does not name that as on purpose (criterion 2). Fix: add "See "The agent's API key" in [agent-runtime.md](agent-runtime.md)" to the row at :62, and name "The agent's login token" in the row at :61.
    5. docs/operator-guide/install.md:190: "A checkout that has a `.git` is kept as it is: the factory does not check it, …" is about 30 words (style rule 2). Fix: split it after "kept as it is".

    Open, outside this diff: `docs/project-guide/shared.md` still says the operator guide has no `Default` column and no refusal table. That is now false. It belongs to that file's story or to the human.
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the reviewer's findings 1, 2, 4 and 5 in `docs/operator-guide/install.md` and part of finding 3. `make documents` ends `documents ok (1.8 s)`. I ran no `make check`, because I changed only documents. Finding 3 needs the human's decision (question below).

    Files changed:
    - `docs/operator-guide/install.md`: the fixes below. `docs/checked-documents.txt` is unchanged.

    Findings by number:
    1. Step 3 now says what `setup.sh` does, from its header (setup.sh:2-6): it prepares a fresh Ubuntu 24.04 machine (the packages, the ZFS pool and dataset, the factory's checkout with its virtual environment, `image-id`, `factory.env` and the systemd unit). It no longer says it builds the stage image or "makes the VM". The long sentence is split. A new step 4 builds the stage image and points to "The stage image" in `machine.md`. The old steps 4 and 5 are now 5 and 6.
    2. "Every path is absolute" became "The path variables named in *The refusals* must be absolute". The refusal row now lists what it covers: the checkout, the state directory, the workspace, the transcript folder, the agent home, the image identity file, the provider file, the CA bundle and the snapshot base. It says the token file and the two login files are not checked for it.
    3. In part. I removed the dangling colon and the two meta sentences ("It is not run in the documents, and no real sweep backs it"). The two `make mutants` commands are now plain inline code in prose, and they are not runnable and not marked `console vm`.
    4. The login-token row points to "The agent's login token" and the API-key row to "The agent's API key", both in `agent-runtime.md`.
    5. The sentence about a checkout with a `.git` is split after "kept as it is".

    Question for the human, on finding 3: no stage can run a mutation sweep, because only the human starts one, so I have no real run to copy into a `console vm` block. How should the two `make mutants` commands (the sweep command and the `MUTANTS_SECONDS` example) be shown? The options:
    - (a) You paste a real sweep's output, and I make each command a `console vm` block from it.
    - (b) You accept an inline command in prose, as it stands now and as the style page's own Install example writes `setup.sh` inline. This is the one I would choose.
    - (c) A form you name.
    With (b) the story can go on to `docs-review` as it is.

    Cross-read and found current: the links from `stops.md`, `machine.md`, `health.md` and `agent-runtime.md` to the headings of `install.md`. I kept all four of those headings.

    Stale text that is not mine to fix:
    - `docs/operator-guide/README.md` still has the "Replaced in v1.2" and "Replaced from v1" sections.
    - `docs/project-guide/shared.md` says the operator guide has no `Default` column and no refusal table, which is false now.
    - `docs/operator-guide/agent-runtime.md:57` names "F0043" and links to install.md's "The stage environment" under *Configuration*, a heading that I could not find in the new file. The link text was already there before this story, but check it. The reviewer or the story for that file should look at it.

    Found in the check, for the coder and not part of this story: the documents check crashes on a fenced block that is indented under a numbered step (`documents.py:681`, `ValueError: zip() argument 2 is longer than argument 1`). So the blocks in `install.md` sit at column 0.
14. 2026-11-06 human: (b): the two `make mutants` commands stay inline in the prose. A sweep is started only by the human, so there is no run to copy, and an inline mention is no example the check runs. Go on to `docs-review`.
    The crash on a fenced block indented under a numbered step is a fault in the code; it becomes its own story, outside this one. Keep the blocks at column 0 here. The stale texts you named belong to the stories of those files.
