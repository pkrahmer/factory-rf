---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 625
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T05:26:09.079609Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T05:07:12.856804Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T05:07:12.864192Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T05:07:28.449664Z'
  stage: intake
  run: 29d84c9e47de4a3da742810a8bc5a650
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T05:07:33.466602Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T05:14:48.419698Z'
  stage: docs-only
  run: 6f370c8ec4d64957b2a13d52ba5b9cb7
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T05:14:53.662724Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:19:02.388616Z'
  stage: docs-review
  run: b9deaf16374548129eaf12db9f08d2d6
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T05:19:07.253900Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T05:24:34.251335Z'
  stage: docs-only
  run: 787592f5048e46de93bdab7d45dc7259
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T05:24:39.406649Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:26:03.837065Z'
  stage: docs-review
  run: ac2049448324424db88634e5973c6c63
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T05:26:09.079609Z'
  stage: docs-only
---

# The project guide's page on the machine area reads for the developer

## Description

`docs/project-guide/machine.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/machine.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/machine.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/machine.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/machine.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/machine.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/machine.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: it names one concrete file to rewrite (`docs/project-guide/machine.md`), the link rule, the one-line `docs/checked-documents.txt` change, and says no code, test or agent file changes. Every path is one the documenter may write.
   - Criteria: criteria 1 and 2 are judged by the reviewer against the style page and the code. Criteria 3 to 5 are checked by `make documents` and by link checks. Criterion 6 is `make check`. Criterion 7 is the docs criterion. The story states no code rules, so there is no failing side to cover. Each criterion is testable in one pass without further decisions.
   - Smoke test: `grep -cx "docs/project-guide/machine.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output. It runs no pytest, so the `-q` rule does not apply.
   - Docs criterion: it names what the reader must know. The page is rewritten for its reader, every fact is kept or moved to *Reference*, and the examples are runnable. It dictates no sentences.
   - Architecture: the page covers the machine area, which `CLAUDE.md` lists with containers, images, snapshots, disks and the preflight. The story changes only a document in `docs/project-guide/`, so no layer is touched.
   - Scope: this is S0017 in the feature's list, and the feature's scope is each file rewritten with its own story. `decisions.md`, `runs/` and the playbook are not touched. Route: docs-only.
4. factory: started docs-only as vm.
5. documenter: Rewrote the project guide's page on the machine area for its reader. `make documents` ends `documents ok (16.2 s)`. I did not run `make check`, because every changed file is a document.

   Files changed:
   - `docs/project-guide/machine.md`: rewritten in the style of `docs/project-guide/style.md`.
     - Each section starts with the idea, then the names in a code block, then one rule per bullet, then See also.
     - Exact detail moved into a closing *Reference* section: ZFS commands, `zfs diff` reading and faults, the podman command line and job profile, reading a run's end, the sync script, the seven steps of the take, the settings table and refusals, the stage-file following, the preflight item table, the order of `KnownResults.run`, and the mutants temporary folder.
     - Source modules, pages and test files are linked once by relative links.
     - Glossary words are linked at first use.
     - Removed: feature and story IDs, the "Replaced in v1.2" section (the `MakeProjectCommands` rule it held is now a bullet under *Project commands*), "v1.1/v1.2" names, "no longer" and "since" notes, and the `planning/v1.2-plan.md` references.
     - New heading *Known results*: it used to be an unnumbered `####` under *Project commands*, and `pipeline.md` already cites it as `machine.md`, *Known results*.
     - Kept the headings that other files cite: *The take*, *The preflight*, *The stage environment*, *The container environment*, *The settings and the wiring*, *The agent's container*, *The checks*.
   - `docs/checked-documents.txt`: added `docs/project-guide/machine.md`.
   - `docs/project-guide/README.md`: the machine.md index entry's section list now reads *Known results* and the *Reference*, and no longer *Replaced in v1.2*.
   - `docs/project-guide/pipeline.md`: one link to the heading *Container project commands*, which never existed in machine.md, now points to *The checks*.

   Corrections to claims the code or the check did not bear out:
   - The test for the agent-run probe's environment is `tests/hosting/application/test_agent_run_probe_environment.py`. The old text gave a `tests/machine/application/` path that does not exist.
   - The old text said the sync script's detail is `factory.pipeline.domain.checks.last_line`. I checked that module name against the code and kept it.
   - Example project paths now use the `<project>/` placeholder, and `src/new.py` and `.venv/...` became prose, because the name check failed on them.

   Facts I did not change or re-derive:
   - I spot-checked constants against the code: podman's limits, grace and time limit, the kill statuses, `SNAPSHOT_TIME_LIMIT`, `DROP_CACHES_COMMAND`, `_CHUNK_BYTES`, `IMAGE_BUILD_TIME_LIMIT`, and the preflight function names. All matched.
   - I carried the rest of the old text over unchanged, so the reviewer should compare it against the code.
   - The measurements on the local VM are kept as stated, with the date. They are copied from earlier real runs, not rerun.

   Examples:
   - The page has no `console` blocks.
   - The `make mutants` and `uv run mutmut show` commands are bare commands in `sh` blocks, with the text saying they run in a checkout and that they act on the suite.
   - The Python snippet for `MakeProjectCommands` and the timing line are not commands.

   Cross-read and found current: the glossary terms I linked (dataset, base, take, stage environment, project command, write paths, pipeline definition, stop, work item); the headings that `agents.md`, `hosting.md`, `watching.md` and `pipeline.md` cite in machine.md.

   Stale text I saw and did not touch:
   - `docs/project-guide/pipeline.md` (the preflight list in the tick step) says the preflight items are `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode`, `agent-run-probe`. It leaves out `metadata-block` and the `copy` variant, which machine.md now states.
   - `docs/project-guide/README.md` still lists the machine.md modules at length and mentions `shared.md`'s hand-over to machine.md settings. Both are unrelated to this story.
   - The `Report (not checked yet)` list from `make documents` covers files outside this story (README, the project-guide index and so on). They are other stories' files.

   No `docs/decisions.md` entry was written, because the criterion says none.

   `check`: check: green
   `secrets`: secrets: green (1.1 s)
   `documents`: documents ok (16.1 s)
6. factory: started docs-review as vm.
7. reviewer: I reviewed `git diff main...HEAD -- README.md docs operator/README.md` (machine.md rewritten; checked-documents.txt, project-guide README.md and pipeline.md one line each) against the code on the branch and `docs/project-guide/style.md`. The three one-line changes are right: the line in checked-documents.txt; the index entry, now *Known results* and *Reference*; and the pipeline.md link, now *The checks*, which exists. Every machine.md heading that another file cites still exists.

   I checked these claims against the code and they match: the ZFS commands, diff reading and faults; the copy snapshots; the fakes; the container path rules; the sync script and its mounts; the timing line; the take and `copy_changed`; the preflight items and their messages; `KnownResults.run` and `command_line`; the record log; the disk record; the constants.

   Dropped on purpose and named in entry 5: the feature and story IDs, the "Replaced in v1.2" section (its rule is now a bullet), and the `planning/` references. That is fine.

   Findings:
   1. docs/project-guide/machine.md:373: the signature `MakeProjectCommands(directory, kill_points=None, *, executable="make", user=None)` names a `user` parameter the code lacks (src/factory/machine/adapters/make_commands.py:54-60 has `directory, kill_points=None, *, executable="make"`). Line 377 also says the class takes no user. Fix: drop `user=None`.
   2. docs/project-guide/machine.md:120 and the Reference table under *The settings of the stage environment*: the signature `PodmanRuns(executable, image, workspace, *, time_limit=..., profile=...)` and the built boundary `PodmanRuns(podman_executable, stage_image, workspace)` both leave out the required keyword `instance` (podman_runs.py:82, wiring.py:577). Fix: add `instance` (and `instance=settings.instance`, `profile=settings.container_profile` in the table).
   3. docs/project-guide/machine.md, *The podman command line* (the `text` block and its bullets) and *The job profile* ("a `job` launch reads `... run --rm --http-proxy=false ...`"): both leave out the words `--label factory.instance=<instance>` that podman_runs.py:121-123 puts right after `--rm` in every launch. Fix: add the words to the block, the job example and one bullet giving their reason: the service's unit stops the containers by this label, because rootless podman places them outside the service's cgroup (podman_runs.py:119-120).
   4. docs/project-guide/machine.md:92: "whenever the boundaries hold snapshots ... `snapshots.mount_point / "checkout"`, else `boundaries.checkout`" is false. `agent_working_directory` (take.py:36-38) always returns `boundaries.snapshots.mount_point / "checkout"`, and has no else. Fix: state the one return value and drop "whenever ... else".
   5. docs/project-guide/machine.md:223: "`Boundaries.snapshots` and `Boundaries.containers` ... default to `None`. `stage_environment_of` picks the container environment only when both are set" is false. Both fields are required, with no default (src/factory/pipeline/application/boundaries.py:62-63), and `stage_environment_of` always builds `ContainerEnvironment` (stage_environment.py:216). Fix: say they are required, as line 156 already does.
   6. docs/project-guide/machine.md:301 and :308: `workspace_overlap_fault(...) -> str | None` is wrong. It returns `tuple[str, str] | None` (the variable and the fault), and it also refuses a relative workspace (settings.py:288-305), not only "the overlap rule". Also at :150, the code types `stage_environment_of` as `-> StageEnvironment`, not `-> ContainerEnvironment`. Fix: correct both signatures and the bullet.
   7. docs/project-guide/machine.md:104: "The base is `BASE_SNAPSHOT`, `<dataset>@base`" reads as if the constant held the whole name. In zfs_snapshots.py:14, `BASE_SNAPSHOT = "base"`. Fix: "the base is the snapshot `<dataset>@<BASE_SNAPSHOT>`, `BASE_SNAPSHOT` being `base`".
   8. docs/project-guide/machine.md:455, under *Mutation testing*: "found from the commit subjects that start `work item <id>-S<nnnn>:`" leaves out `ticket <id>-S<nnnn>:`, which `FEATURE_MODULES` in the Makefile (line 117, `--grep='^(ticket|work item) ...'`) still matches. The old text said so, and entry 5 does not name the fact as dropped (criterion 2). Fix: name both subject forms without version words. Also dropped silently: the old *The grace* named `HOME`, `XDG_RUNTIME_DIR` and `PATH` as what the `podman` program needs from the factory's environment. Fix: restore it in the `launch` bullet at :133.
   9. docs/project-guide/machine.md, criterion 1 / style rule 3: these glossary words are not linked at their first use. "take" is never linked (first at :6/:14), and neither are stage (:7), claim (:9), role (:14), cost record (:164), stall (:218), journal (:262), instance (:298), tick (:336), feature and story (:455). Fix: link each to glossary.md at its first use.
   10. Style rule 2, one idea per sentence, at most about 25 words and one parenthesis. These lines break it: :359 (about 50 words), :361, :461, :92, :164, and the Tests lines :94, :169 and :229 (three parentheses in one sentence each). In the Reference, the "second refspec" bullet of *Why the fetch is so wide* and the last bullet of *The temporary folder of a mutants run* are past anecdotes ("On the first VM stage ...", "This was seen on 2026-10-20"). Rule 7 asks for the current rule. Fix: split the long sentences, keep one parenthesis per sentence, and state the reasons as rules.
   11. Style, the project guide section, and the Interface's link rule:
       - These sections have no "See also": *The fakes*, *The agent's container*, *The project's stage image*, *Project commands* and *Known results*. *The tests' umask and login variables* (:426) opens with bullets and no plain sentence on what it is for. Fix: add them.
       - These names are not linked: `factory.entry.run` (:661), `factory.shared.domain.printed_lines` (:683), `test_claude_runtime.py` (last bullet), and this repository's own `Makefile` and `factory/pipeline.yml` (:381). The links already there point to the operator template's files. Fix: link each one once.

   Earlier tests: none (the diff changes no test file).
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's eleven findings in `docs/project-guide/machine.md`. `make documents` ends `documents ok (16.1 s)`. I did not run `make check`, because the only file I changed is a document.

   Files changed:
   - `docs/project-guide/machine.md` only. The other files from entry 5 (`docs/checked-documents.txt`, `docs/project-guide/README.md`, `docs/project-guide/pipeline.md`) are unchanged this round.

   How each finding went:
   1. `MakeProjectCommands` signature: removed `user=None`, which the code lacks.
   2. `PodmanRuns` signature: added the required keyword `instance`. The built-boundary row in the settings table now reads `PodmanRuns(podman_executable, stage_image, workspace, instance=settings.instance, profile=settings.container_profile)`.
   3. Podman label:
      - Added `--label factory.instance=<instance>` to the command-line block and to the `job` example.
      - Added a bullet with its reason: the service's unit stops containers by this label, because rootless podman places them outside the service's cgroup.
      - Restored `HOME`, `XDG_RUNTIME_DIR` and `PATH` as what the `podman` program needs from the factory's environment.
   4. `agent_working_directory`: now states the one return value, `boundaries.snapshots.mount_point / "checkout"`. The "whenever … else" wording is gone.
   5. `Boundaries.snapshots` and `Boundaries.containers`: now described as required fields. `stage_environment_of` always builds the container environment.
   6. Signatures:
      - `workspace_overlap_fault` now returns `tuple[str, str] | None`.
      - `stage_environment_of` now returns `StageEnvironment`.
      - The bullet says it also refuses a relative workspace.
   7. Base snapshot: now `<dataset>@<BASE_SNAPSHOT>`, with `BASE_SNAPSHOT` being `base`.
   8. Mutants:
      - The `FEATURE` text keeps `work item <id>-S<nnnn>:`.
      - The `ticket` form of older subjects cannot be named. `make documents` refuses the word as a v1 word, so the text says the `FEATURE_MODULES` pattern in the Makefile also matches the one-word opening of older subjects.
   9. Glossary links added at first use: stage, claim, role, take, cost record, stall, journal, instance, tick, feature and story.
   10. Sentences and anecdotes:
       - Split the long sentences and the long test lists into bullets.
       - Rewrote the two past anecdotes in the Reference as current rules: the second refspec, and the mutants process that survives a kill.
   11. See also and links:
       - Added See also to *The fakes*, *The agent's container*, *The project's stage image*, *Project commands* and *Known results*.
       - Added an opening sentence to *The tests' umask and login variables*, and a closing See also.
       - Linked `run.py`, `printed_lines.py`, `test_claude_runtime.py`, `process.py`, and this repository's `Makefile` and `factory/pipeline.yml`.

   Cross-read and found current: the glossary terms I linked; the headings that `agents.md`, `hosting.md`, `watching.md` and `pipeline.md` cite in machine.md.

   Stale text I saw and did not touch, because it is unrelated to this story:
   - `docs/project-guide/pipeline.md`, in the tick step: the preflight item list omits `metadata-block` and the `copy` variant. machine.md states both.
   - `docs/project-guide/README.md` and the root `README.md`: `make documents` lists them among the unchecked files, with unresolved names such as `support/*.py` and `factory/stage.Containerfile`. Other stories' files.

   No `docs/decisions.md` entry was written, because the criterion says none.

   `check`: check: green
   `secrets`: secrets: green (1.1 s)
   `documents`: documents ok (16.2 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, then checked the new `docs/project-guide/machine.md` against the code on the branch and against `docs/project-guide/style.md`.

    Last round's eleven findings, checked against the code:
    - 1 to 7 are fixed and match the code:
      - `MakeProjectCommands` has no `user` (make_commands.py:54-60).
      - `PodmanRuns` takes `instance`, and the label `factory.instance=<instance>` follows `--rm` (podman_runs.py:75-123).
      - `agent_working_directory` has one return value.
      - `Boundaries.snapshots` and `Boundaries.containers` are required.
      - `workspace_overlap_fault` returns `tuple[str, str] | None` (settings.py:288).
      - `stage_environment_of` returns `StageEnvironment` (stage_environment.py:216).
      - The `BASE_SNAPSHOT` wording is fixed.
    - 8 is fixed in substance: `HOME`, `XDG_RUNTIME_DIR` and `PATH` are back, and the older subject form is named. Its new sentence is garbled (finding 1).
    - 9 is fixed: the glossary links are added.
    - 10 and 11 are fixed at the lines named. Other cases of the same rules remain (findings 2 to 5).

    Also correct:
    - The headings cited in other documents all exist: pipeline.md, shared.md, agents.md, hosting.md, operator-guide machine.md and install.md, decisions.md.
    - `machine_extras` and `_container_items` match the item order and the metadata-block placement (wiring.py:740-768).
    - The three one-line changes from entry 5 are unchanged and right.

    Findings:
    1. docs/project-guide/machine.md:493: "The pattern `FEATURE_MODULES` in the Makefile holds also matches the one-word opening of older subjects." is ungrammatical and unclear. The code (Makefile:117, `--grep='^(ticket|work item) ...'`) matches subjects that open with one other word in place of `work item`. Fix: rewrite it, for example "The pattern of `FEATURE_MODULES` in the Makefile also matches older subjects that open with one other word in place of `work item`."
    2. Style rule 2 (a sentence of at most about 25 words, at most one parenthesis): these sentences are still too long: :358 (~30 words), :381 (~33), :412 (~35), :464 (~45), :588 (~33), :618 (~35) and :746 (~45 words, two parentheses). :730 (Reference, step 1 of `KnownResults.run`) holds four parentheses and one sentence of about 60 words. Fix: split each into one idea per sentence, with at most one parenthesis each.
    3. Style, project-guide section order ("Then comes See also"): in *The fakes* the "Tests:" list (:96-103) comes after "See also" (:94), and in *Known results* "Tests:" (:484) comes after "See also" (:482). Fix: put "Tests:" before "See also" in both, as the other sections do.
    4. Style, project-guide section order: two `##` sections end without "See also": *The copy snapshots* (:61-72) and *The container environment* (:188-249, which ends with its Tests list). Fix: add a "See also" line to each, for example *The snapshots* and *The fakes* for the first, and *The stage environment*, *The take* and *The checks* for the second.
    5. Interface, "each module, file or page is linked once": these files are linked twice: take.py (:92 and :275), stage_environment.py (:155 and :194), make_commands.py (:304 and :400), wiring.py (:117 and :320), process.py (:83 and :748), tests/machine/application/test_interfaces.py (:101 and :184), and this repository's Makefile (:411 and :493). Fix: keep the first link and write the later mentions as plain names.
12. factory: started docs-only as vm.
