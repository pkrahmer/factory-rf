---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 517
comments_read: [6600797229, 6600934999]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T09:51:33.739546Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T09:51:33.745787Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T09:51:54.289216Z'
  stage: intake
  run: 28839d9776b046faba41c27c450a5bdd
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T10:10:08.388809Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T10:10:11.460227Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T10:10:32.358678Z'
  stage: intake
  run: 83bb70814b0f44ad86b47677651f442d
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T10:10:38.148874Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T10:11:21.122942Z'
  stage: tests
  run: b6e60bf8d07a4bf4a6442fa40a57c740
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T10:11:27.431229Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-03T10:13:28.503581Z'
  stage: doing
  run: be5a9f1ffb95456da52fddac167a66f6
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-03T10:17:23.578368Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T10:17:26.495365Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-03T10:17:40.702360Z'
  stage: doing
  run: fb4d77df05654c32b86401d4ba5d1a47
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-03T10:17:46.465259Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-03T10:18:10.623798Z'
  stage: tests
  run: dea8a093ada94a0e898ce74cc12610d3
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-03T10:18:16.476868Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-03T10:21:41.329723Z'
  stage: doing
  run: 1dc419bbe7664e41b778dc9225f2a5b7
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-03T10:21:47.428670Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-03T10:22:19.013194Z'
  stage: review
  run: f83ef321f2a34a99bfb6651f260655cb
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-03T10:22:24.938817Z'
  stage: docs
- number: 21
  speaker: documenter
  kind: result
  at: '2026-11-03T10:23:03.915685Z'
  stage: docs
  run: 0e9ca5373274405b9b75416aa1c4dc44
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-03T10:23:09.644429Z'
  stage: smoke-test
- number: 23
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T10:23:30.992751Z'
  stage: smoke-test
  run: 84d4ed1a153148d18b654d6a127d5fa3
---

# The guide's advice on the job and on the probe follows the defaults and the died line

<!-- proposed by feature acceptance of 2026-11-03; the human added part B on 2026-11-03 (decision 24) -->

## Description

S0014 gave `job.sh` the example's sizes as its defaults (decision 21): 4 CPUs, 16Gi, a task timeout of 86400 seconds (24 hours) and 30 idle minutes. S0015 made a `died` run leave its text in the factory log. Three passages of `docs/operator-guide.md` were written before both and now advise against what the factory does:

- *On Cloud Run*, *What the job needs*, **Size**: "Eight vCPUs and 16 GiB of memory at least". The default and the example's `SITE_CPU=4` give half of that, so an operator who keeps the default reads that their job is below the minimum, and one who trusts the guide changes a value the human chose.
- The same list, **The task timeout**: "Set the timeout shorter than the schedule's interval: 23 hours for a daily schedule". The default is now 24 hours, the interval itself, and the passage does not say that a job on a daily schedule must set `SITE_TIMEOUT` below the default.
- *The probe of the agent run*: a flag the pinned `claude` rejects makes "every real run ... end `died` with no text that says why". Since S0015 the factory log names each such run with its text (*A provider's spend limit*, the paragraph *A run that ends `died`*).

This story corrects the three passages so that they say what the factory does (part A). It changes no default: the defaults are the human's (decision 21).

**Part B: the job keeps one image in memory.** The job mounts podman's storage as a tmpfs (`vm/job-start.sh`, step `storage`), so every image byte counts against the job's memory, which is 16Gi by default now. The step `image` builds the stage image (about 2.4 GB on vm) with podman's layer cache, which leaves the build's intermediate images in that tmpfs beside the final one. Nothing in an execution needs them: the image is built once per execution and never rebuilt in it. Part B builds without the layer cache and removes the unused untagged images right after the build, so that only the tagged stage image and its base stay in memory. On a machine, every rebuild leaves the previous stage image untagged; on vm 104 images and 26 GB had piled up by 2026-11-03. The guide's rebuild routine therefore gains the same prune.

## Interface

Part A: none; the documenter changes `docs/operator-guide.md`.

Part B, `vm/job-start.sh`, step `image`: the build passes `--layers=false`, and after a successful build the step runs `podman $JOB_PODMAN_OPTIONS image prune -f`, whose failure fails the step as a failed build does. It never removes a tagged image. Nothing else in the script changes.

Tests: a new text test over `vm/job-start.sh` (the step `image` holds the build with `--layers=false`, followed by the prune, in that order), beside the existing tests of the script.

## Acceptance criteria

1. (B) The step `image` of `vm/job-start.sh` builds with `--layers=false` and then runs `podman $JOB_PODMAN_OPTIONS image prune -f`, in that order; a step without either, or with them in the other order, fails its row.
2. (B) The prune line of the step `image` ends with `|| failed image`, as the build line does, so that its failure fails the step.
3. (B) The prune line of the step `image` has neither `-a` nor `--all`, so that it never removes a tagged image.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`:
   - *What the job needs*, **Size**: says that the job gets 4 vCPUs and 16 GiB of memory unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and that memory is the limit to raise first, because the root file system, the tmpfs of the image layers, the checkout, the base copy and the workspace all count against it. The words "Eight vCPUs" and "at least" go. The rest of the bullet (the plain base copy, about 1.6 s per GiB for a reset) stays.
   - **The task timeout**: says that the default, 86400 seconds, is the platform's maximum of 24 hours and equals a daily schedule's interval, so a job executed every night sets `SITE_TIMEOUT` below it, such as `23h`. The sentence on two executions that must never overlap stays.
   - *The probe of the agent run*: the parenthesis after "a flag the pinned `claude` rejects" says that every real run would end `died`, each with its line `run <run id> of <work item> (<stage>) died: <text>` in the factory log, instead of "with no text that says why".
   - **Size** also says that the stage image, about 2.4 GB, sits in the job's memory because podman's storage is a tmpfs, and that the job removes the build's leftovers (part B).
   - *The rebuild after a merge*: after the image is built, `podman image prune -f` as the factory's user removes the previous stage image and the build's leftovers. It removes only untagged images that no container uses, so another instance's tagged image and a running container are safe. The guide says that the next build is slower without the cache.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'Eight vCPUs' docs/operator-guide.md; grep -c 'no text that says why' docs/operator-guide.md
```
Expect: `0`, then `0`

```bash
sed -n '/^### What the job needs/,/^### The environment/p' docs/operator-guide.md | grep -c 'SITE_TIMEOUT'
```
Expect: a number of at least `1`

```bash
grep -c -- '--layers=false' vm/job-start.sh; grep -c 'image prune -f' vm/job-start.sh
```
Expect: `1`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface, step `image`: "whose failure fails the step as a failed build does" is a stated rule, but no criterion tests its failing side. Criterion 1 only checks that the text holds the build with `--layers=false` and then the prune. Options: (a) add a criterion that the prune is followed by `|| failed image`, the way the build line is (I would choose this); (b) drop the clause from the Interface.
   2. Interface: "It never removes a tagged image" has no criterion. `image prune -f` without `-a` already has that property. Options: (a) add a criterion that the prune line has no `-a` or `--all` flag (I would choose this); (b) delete the sentence, because podman guarantees it.
   3. Criterion 2 ("Nothing under `src/`, `operator/`, `image/`, `template/` or `claude/` changes, and under `vm/` only `vm/job-start.sh`") cannot be tested by one test function. It would need a diff against `main`, and the Tests section defines no such helper. Options: (a) remove it, because the write paths already confine the coder (I would choose this); (b) say which test checks it and how.
   4. Interface, the Interface's "Nothing else in the script changes": no criterion backs it. It is covered by item 3 only as far as the file is concerned. If you keep it, say whether it is a criterion or a description only. I would treat it as a description.
4. 2026-11-03 human: Your choices on all four:
   1. (a): a criterion that the prune line ends with `|| failed image`, as the build line does.
   2. (a): a criterion that the prune line has no `-a` and no `--all`.
   3. (a): remove criterion 2; the write paths confine the coder.
   4. A description only, no criterion.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
5. factory: started intake as vm.
6. intake: accepted
   - Interface: Part A names no module (the documenter edits `docs/operator-guide.md`). Part B names `vm/job-start.sh`, step `image`, with the exact flag `--layers=false` and the exact command `podman $JOB_PODMAN_OPTIONS image prune -f`. The story is concrete enough. "Nothing else in the script changes" is a description only, as the human said in journal entry 4, item 4.
   - Criteria: carried in from the human's answer (journal entry 4). Item 1 became criterion 2: the prune line ends with `|| failed image`, which is the failing side of the Interface's failure rule. Item 2 became criterion 3: the prune line has no `-a` and no `--all`, which backs "never removes a tagged image". Item 3 removed the old criterion 2, the diff-scope one, because it could not be tested by one test function. The closing `make check` and `docs:` criteria are now 4 and 5. Criterion 1 covers the order of build and prune, with a row for each missing part and for the reversed order. The docs criterion lists each passage and its wording. The smoke test checks the guide's text with `grep`.
   - Smoke test: the commands are runnable. None runs pytest, so the `-q` rule does not apply. Each `Expect:` line is checkable: `0`, then `0`; at least `1`; `1`, then `1`; `documents ok`.
   - Architecture: Part B stays in the VM's start script, and Part A is documentation only. Nothing touches the layers in `src/factory`.
   - Scope: the story is listed in the feature's scope and stories (S0018, decision 24). It changes no default, and it touches nothing in the feature's Out of scope.
7. factory: started tests as vm.
8. tester: Wrote the text tests for part B over `vm/job-start.sh`. They sit beside the script's existing tests and read the uncommented script from the line `step image` to the next `step` line. Part A is documentation only, and criteria 4 and 5 are the checks and the documenter's job, so no test covers them.

   - criterion 1: tests/test_vm_job_start_image.py::test_the_image_step_builds_without_layers_and_then_prunes. One parametrized test with four rows: the script itself must hold. Three variants built from the script's own step must fail: without `--layers=false`, without the prune line, and with the prune before the build.
   - criterion 2: tests/test_vm_job_start_image.py::test_a_failed_prune_fails_the_image_step. There is at least one line with `podman $JOB_PODMAN_OPTIONS image prune -f`, and every such line ends with `|| failed image`.
   - criterion 3: tests/test_vm_job_start_image.py::test_the_prune_never_removes_a_tagged_image. Parametrized over `-a` and `--all`; neither may be a word of the prune line.

   Files created: tests/test_vm_job_start_image.py. It reuses `JOB_START` and `lines_with` from tests/vm_support.py and `_uncommented` from tests/dockerfile_support.py. No earlier test file changed.

   Import problems: none. The test reads the script as text.

   One run, `uv run pytest -q tests/test_vm_job_start_image.py`: 4 tests fail for the right reason and 3 pass. The failing ones are the `the-script` row of criterion 1, criterion 2, and both rows of criterion 3; each fails because the step has no `--layers=false` build and no prune line yet. The 3 that pass are the variants of criterion 1 that must fail its rule. `make lint` is green.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: An earlier test conflicts with the Interface. I stopped here because changing that test needs your word.

    What I built (left in the working tree): the step `image` in `vm/job-start.sh` now builds with `--layers=false`. Right after the build it runs `podman $JOB_PODMAN_OPTIONS image prune -f || failed image`. That line has no `-a` or `--all` and has its own `# shellcheck disable=SC2086`, as the build line does. I put the prune straight after the build, before the image-id line, so the leftovers go as soon as the build is done. The new tests in `tests/test_vm_job_start_image.py` pass.

    The contradiction: `make check` is red on `tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options[given]` and `[default]`. Both compare the build's argv exactly, as `[*JOB_PODMAN_OPTIONS, "build", "--network=host", "-f", "vm/Dockerfile", ...]`. The Interface requires `--layers=false` in that build, so the exact list can no longer match. From the failed run:
    ```
    E   AssertionError: assert [['--runtime=...k=host', ...]] == [['--runtime=...', '-f', ...]]
    E     At index 0 diff: [..., 'build', '--layers=false', '--network=host', '-f', 'vm/Dockerfile', ...] != [..., 'build', '--network=host', '-f', 'vm/Dockerfile', ...]
    ```
    (tests/test_vm_job_start.py:377, the `assert builds == [...]`). The prune itself does not trip this test: it collects only the podman calls with `build` in their argv.

    The standing leave in `CLAUDE.md` covers only moving shared helpers, so changing this test needs your word. Options:
    (a) The tester adds `"--layers=false",` after `"build",` in that expected argv, and the test still checks the same build. I would choose this.
    (b) Drop `--layers=false` from the Interface and criterion 1 and keep only the prune. The cache's intermediate images would then be removed by the prune anyway, because they are untagged, but the build would still write them to the tmpfs first, so peak memory would be higher.

    If you choose (a), I end the next round with `tests` and name exactly that change.

    Refactor: not done yet. I do it once `make check` is green.

    Noticed but not touched: nothing else.
11. 2026-11-03 human: (a). The tester has leave to add `"--layers=false",` right after `"build",` in the expected argv of `tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options`, and nothing else in that module. The test keeps its name and its rows.

    — Kumpel, for the human who owns this project
    <!-- kumpel -->
12. factory: started doing as vm.
13. coder: The human's answer (entry 11, option (a)) calls for one test change. In `tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options`, add `"--layers=false",` right after `"build",` in the expected build argv. Change nothing else in that module. The test keeps its name and its rows `given` and `default`.

    What I built: the code part of part B is already committed on the branch from the last round. In `vm/job-start.sh`, step `image`, the build now passes `--layers=false` (line 155). The next line runs `podman $JOB_PODMAN_OPTIONS image prune -f || failed image`, without `-a` or `--all` and with its own shellcheck disable (line 157). I changed no code this round.

    Main choice: the prune comes straight after the build and before the image-id line, so the leftovers are gone as soon as the build is done. I rejected putting it at the end of the step: then a failure to write the image id would leave the leftovers in the tmpfs.

    Still open: `make check` stays red on that one test until the tester changes it. The refactor pass and the final `make check` come in the next doing round, once the test is changed.

    The journal's answer adds no criterion and does not change the Description's meaning. It only allows that one test change.

    Noticed but not touched: nothing.
14. factory: started tests as vm.
15. tester: I made the one test change the human approved in entry 11, as the coder named it in entry 13.

    - Changed: `tests/test_vm_job_start.py::test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options`. In the expected build argv, I added `"--layers=false",` right after `"build",`. Nothing else in the module changed. The test keeps its name and its rows `given` and `default`.
    - Why: the Interface requires the step `image` to build with `--layers=false`, so the old exact argv could no longer match the build. The human chose option (a) in entry 11.
    - Files changed: tests/test_vm_job_start.py, which an earlier story wrote; the human gave leave in entry 11. I created no files. No module failed to import.
    - Mapping for the criteria (unchanged from entry 8):
      - criterion 1: tests/test_vm_job_start_image.py::test_the_image_step_builds_without_layers_and_then_prunes
      - criterion 2: tests/test_vm_job_start_image.py::test_a_failed_prune_fails_the_image_step
      - criterion 3: tests/test_vm_job_start_image.py::test_the_prune_never_removes_a_tagged_image
    - One run, `uv run pytest -q tests/test_vm_job_start.py`: all 42 tests pass. `make lint` is green.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: `make check` is green now that the tester made the approved change to `tests/test_vm_job_start.py` (entry 15). I changed no code this round.

    What I built (part B), all in `vm/job-start.sh`, step `image`:
    - The build passes `--layers=false` (line 155).
    - The next line runs `podman $JOB_PODMAN_OPTIONS image prune -f || failed image`, with no `-a` or `--all`. It has its own `# shellcheck disable=SC2086`, as the build line does (line 157).

    Main choice: the prune runs right after the build and before the image-id line, so the build's leftovers leave the tmpfs as soon as the build is done. I rejected putting it at the end of the step: then a failure to write the image id would leave the leftovers in memory.

    Refactor: I read the diff (two lines in `vm/job-start.sh`) and found nothing to change.

    The journal changed nothing in the Description. Entry 11 only allowed the one test change, so the Description stays as it is.

    Part A and the docs criterion are the documenter's (`docs/operator-guide.md`).

    Noticed but not touched: nothing.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
18. factory: started review as vm.
19. reviewer: no findings

    What I checked:
    - Group 1, acceptance criteria. Criterion 1 is `tests/test_vm_job_start_image.py::test_the_image_step_builds_without_layers_and_then_prunes`. Its row `the-script` holds, and the rows `without-no-layers`, `without-prune` and `prune-before-build` each fail the rule, as the criterion asks. Criterion 2 is `test_a_failed_prune_fails_the_image_step`: there is at least one prune line, and every prune line ends with `|| failed image`. Criterion 3 is `test_the_prune_never_removes_a_tagged_image`, with one row for `-a` and one for `--all`. The Interface's rules are its failure rule (criterion 2) and its never-tagged rule (criterion 3). The human said in entry 4 that "Nothing else in the script changes" is a description only, so it needs no test. Entry 17 records that the factory's `make check` was green after the coder and that `duplicates` found 0 new.
    - Group 2, architecture: the diff touches only `vm/job-start.sh` and the tests. No layer is involved.
    - Group 3, security: the prune line uses no string-built command, and no suppression marker was added. The new `# shellcheck disable=SC2086` repeats the build line's own disable for the same reason, and that reason is stated beside it.
    - Group 4, quality: `vm/job-start.sh:155-157` holds the build with `--layers=false` and then `podman $JOB_PODMAN_OPTIONS image prune -f || failed image`, without `-a`. The test module reuses `JOB_START` and `lines_with` from `tests/vm_support.py`. It also reuses `_uncommented` from `tests/dockerfile_support.py`, as `tests/test_vm_job_start.py` already does. There is no existing helper that cuts one step out of the job start script, because `step_texts` covers `setup.sh` only, so the new `_image_step` copies nothing.
    - Group 5, work item hygiene: the journal explains the main choice and what was rejected (the prune runs right after the build, not at the end of the step). It also records the human's leave for the test change. The Description matches what was built. The docs criterion lists every guide passage the documenter must change, including what part B adds.

    Earlier tests:
    - tests/test_vm_job_start.py: changed under the human's leave in journal entry 11. The only change is `"--layers=false",` added after `"build",` in the expected argv of `test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options`, which keeps its name and its rows `given` and `default`.
20. factory: started docs as vm.
21. documenter: Changed `docs/operator-guide.md` only, in four places:
    - *On Cloud Run*, *What the job needs*, **Size**: "Eight vCPUs ... at least" is gone. It now says the job gets 4 vCPUs and 16 GiB unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and that memory is the limit to raise first (root file system, image layers, checkout, base copy and workspace all count against it). It also says the 2.4 GB stage image sits in memory because podman's storage is a tmpfs, and that the job builds without the layer cache and removes the build's untagged leftovers. The plain base copy and the 1.6 s per GiB remain.
    - **The task timeout**: says the default 86400 s is the platform maximum and equals a daily interval, so a nightly job sets `SITE_TIMEOUT` below it, such as `23h`. The sentence on overlapping executions stays.
    - *The probe of the agent run*: the parenthesis now says every real run would end `died`, each with its line `run <run id> of <work item> (<stage>) died: <text>` in the factory log.
    - *The rebuild after a merge*: added `podman image prune -f` after the build in the command block, plus a paragraph. It removes the previous stage image and the build's leftovers, only untagged images no container uses, so another instance's tagged image and running containers are safe. It also says the next build is slower without the cache.

    The code matches the Interface: `vm/job-start.sh` lines 155-157 hold the build with `--layers=false` and then the prune ending `|| failed image`, with no `-a`.

    I ran `uv run python -m factory.entry.check_documents`; it printed `documents ok`. I did not run `make check`, because only a document changed. I did not run the guide's rebuild commands, since they need the VM.

    Cross-read and found current: the *The job profile* and *The site file* keys table (`SITE_TIMEOUT` default 86400 (24 hours)) and the paragraph *A run that ends `died`*.

    Stale text I noticed and did not touch: none that relates to this story. One grammar slip at `docs/operator-guide.md` in the probe paragraph, "A state directory that cannot be written fail it", predates this story.

    `check`: check: green (not run again: passed on tree 5940cd35f228 at 2026-11-03T10:20:06Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
22. factory: started smoke-test as vm.
23. smoke-tester: Ran the four smoke-test commands from the repository root, as written and in order. All four outputs met their `Expect:` lines. No findings.

    1. `grep -c 'Eight vCPUs' docs/operator-guide.md; grep -c 'no text that says why' docs/operator-guide.md`
    ```
    0
    0
    ```
    Met (`0`, then `0`).

    2. `sed -n '/^### What the job needs/,/^### The environment/p' docs/operator-guide.md | grep -c 'SITE_TIMEOUT'`
    ```
    1
    ```
    Met (at least `1`).

    3. `grep -c -- '--layers=false' vm/job-start.sh; grep -c 'image prune -f' vm/job-start.sh`
    ```
    1
    1
    ```
    Met (`1`, then `1`).

    4. `uv run python -m factory.entry.check_documents`
    ```
    Bytecode compiled 4164 files in 47ms
    documents ok
    ```
    Met (`documents ok`; the first line is uv's own output).

    Checked against the acceptance criteria: I read `git diff origin/main` for `vm/job-start.sh` and `docs/operator-guide.md`. The smoke test contradicts no criterion.
    - Criteria 1–3: in `vm/job-start.sh`, the step `image` runs the build with `--layers=false` (line 155) and then `podman $JOB_PODMAN_OPTIONS image prune -f || failed image` (line 157). The prune line has no `-a` and no `--all`.
    - Criterion 4: I did not run `make check` again. Entry 17 records it green after the coder. The documenter changed only `docs/operator-guide.md`.
    - Criterion 5:
      - **Size**: now says 4 vCPUs and 16 GiB unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and that memory is the limit to raise first. It also says the 2.4 GB stage image sits in memory because podman's storage is a tmpfs, and that the job removes the build's leftovers. The plain base copy and the 1.6 s per GiB stay.
      - **The task timeout**: says the default of 86400 seconds equals a daily interval, so a nightly job sets `SITE_TIMEOUT` below it, such as `23h`. The sentence on overlapping executions stays.
      - *The probe of the agent run*: the parenthesis now names the line `run <run id> of <work item> (<stage>) died: <text>`.
      - *The rebuild after a merge*: gains `podman image prune -f` with the paragraph the criterion asks for, including that the next build is slower.
      - The diff touches no other passage.

    Note, not a finding: the guide's manual rebuild command still runs `podman build` without `--layers=false`. The criterion asks only for the prune there, so the guide matches the story.

    Open: nothing.
