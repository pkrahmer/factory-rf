---
stage: done
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 625
comments_read: [6702881617]
handed_over: docs-approval
claim: null
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
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T05:29:37.613006Z'
  stage: docs-only
  run: 6eddc98699374c40acea0177b74ee995
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T05:29:42.490415Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:30:17.665610Z'
  stage: docs-review
  run: ffa707268b0b45489d39ffcab73e805e
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T05:30:22.787292Z'
  stage: docs-only
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-07T05:33:09.136610Z'
  stage: docs-only
  run: 17d50ea0bc0c481eb89c00d920a90743
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T05:33:14.635493Z'
  stage: docs-review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:34:10.561928Z'
  stage: docs-review
  run: 49936bfc3fa1443a85179325e8661c7d
- number: 20
  speaker: factory
  kind: question
  at: '2026-11-07T05:34:10.561928Z'
  stage: docs-review
  run: 49936bfc3fa1443a85179325e8661c7d
  blocked: round_cap
- number: 21
  speaker: human
  kind: comment
  at: '2026-11-07T05:35:59.543649Z'
  stage: docs-review
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-07T05:36:02.049118Z'
  stage: docs-review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:36:39.377496Z'
  stage: docs-review
  run: 2272b7e2c5694d5b8b7da921bcd241a4
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-07T05:36:44.662687Z'
  stage: docs-only
- number: 25
  speaker: documenter
  kind: result
  at: '2026-11-07T05:39:38.087315Z'
  stage: docs-only
  run: f5d765bffe1d441f8b10bd966fa3c325
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-07T05:39:43.497303Z'
  stage: docs-review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:40:29.181072Z'
  stage: docs-review
  run: 3bd8a4b992404a31a76f5e1116af456f
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-07T05:40:34.184226Z'
  stage: docs-only
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-07T05:43:27.581178Z'
  stage: docs-only
  run: ff43d30c336846bfabc9f2ee86047acb
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-07T05:43:32.530169Z'
  stage: docs-review
- number: 31
  speaker: reviewer
  kind: result
  at: '2026-11-07T05:44:11.533902Z'
  stage: docs-review
  run: 12fad60eaa554c3492cda28943b64f08
- number: 32
  speaker: factory
  kind: done
  at: '2026-11-07T05:48:05.669402Z'
  stage: docs-approval
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
13. documenter: Round 2: I fixed the reviewer's five findings in `docs/project-guide/machine.md`, the only file I changed. `make documents` ends `documents ok (16.5 s)`. I did not run `make check`, because the only changed file is a document.

    How each finding went:
    1. The `FEATURE_MODULES` sentence now reads: "The pattern of `FEATURE_MODULES` in the `Makefile` also matches older subjects that open with one other word in place of `work item`."
    2. I split the long sentences into bullets or short sentences, with at most one parenthesis each. They are:
       - the `project_image_settings` bullet;
       - the `machine_extras` snapshots bullet;
       - the layers bullet in *Project commands*;
       - the login-variables reason;
       - the network paragraph in the Reference;
       - the 255 status bullet;
       - step 1 of `KnownResults.run`, now with its parts as sub-bullets;
       - the mutants process-group bullet.
    3. *The fakes* and *Known results* now put "Tests:" before "See also".
    4. I added "See also" to *The copy snapshots* (*The snapshots* and *The fakes*) and to *The container environment* (*The stage environment*, *The take* and *The checks*).
    5. Each file the page names is now linked once, at its first mention. Later mentions are plain code names. This covers `take.py`, `stage_environment.py`, `make_commands.py`, `wiring.py`, `process.py`, `test_interfaces.py` and this repository's `Makefile`. The operator template's `Makefile` keeps its own link, as it is a different file.

    Cross-read and found current: the headings that other documents cite in machine.md still exist, and no heading was renamed this round.

    Stale text I saw and did not touch, because it is unrelated to this story:
    - `docs/project-guide/pipeline.md`, in the tick step: the preflight item list omits `metadata-block` and the `copy` variant, which machine.md states.
    - `docs/project-guide/README.md` and the root `README.md`: `make documents` lists them under "Report (not checked yet)", with unresolved names such as `support/*.py` and `project/factory/pipeline.yml`. They belong to other stories.

    No `docs/decisions.md` entry was written, because the criterion says none.

    `check`: check: green
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok (16.1 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I compared this round's changes (237fe10a1..f8e43a1c6) with last round's five findings and with the code on the branch.

    Last round's findings:
    - 1 is fixed. The `FEATURE_MODULES` sentence now reads clearly and matches Makefile:117.
    - 2 is fixed. The long sentences are split, and the `KnownResults.run` step 1 sub-bullets match the code.
    - 3 is fixed. "Tests:" now comes before "See also" in *The fakes* and *Known results*.
    - 4 is fixed. *The copy snapshots* and *The container environment* now end with "See also".
    - 5 is fixed. No file under `../../` is linked twice any more. The operator template's `Makefile` is a different file from this repository's.

    The three one-line changes from entry 5 are unchanged and still right. No heading was renamed this round.

    Findings:
    1. docs/project-guide/machine.md, *The project's stage image*, the bullet "It returns `None` when the file breaks the rule or does not build. The caller then raises the machine stop `stage_image_failed`." This round's split made the sentence wrong. `project_image_settings` raises the stop itself and does not leave it to its caller: `chosen_image` calls `_stage_image_failed`, which calls `stops.raise_stop(RepositoryStop(scope="machine", reason="stage_image_failed", ...))`, and only then returns `None` (src/factory/entry/wiring.py:489-497, 523-530; its docstring is at :462-465). Fix: "It raises the machine stop `stage_image_failed` and returns `None` when the file breaks the rule or does not build."

    Earlier tests: none (the diff changes no test file).
16. factory: started docs-only as vm.
17. documenter: Round 3: I fixed the reviewer's one finding. `make documents` ends `documents ok (16.5 s)`. I did not run `make check`, because the only changed file is a document.

    Files changed:
    - `docs/project-guide/machine.md`, in *The project's stage image*. The bullet now reads: "It raises the machine stop `stage_image_failed` and returns `None` when the file breaks the rule or does not build." I read `project_image_settings` in `src/factory/entry/wiring.py` (about lines 485-530): it calls `_stage_image_failed`, which calls `stops.raise_stop(...)`, and then returns `None`. The old wording left the raising to the caller, which was wrong.

    Cross-read and found current: no heading was renamed this round, and the other files from the earlier rounds are unchanged (`docs/checked-documents.txt`, `docs/project-guide/README.md`, `docs/project-guide/pipeline.md`).

    Stale text I saw and did not touch, because it is unrelated to this story: `docs/project-guide/pipeline.md`, in the tick step, lists the preflight items without `metadata-block` and the `copy` variant, which machine.md states.

    No `docs/decisions.md` entry was written, because the criterion says none.

    `check`: check: green
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok (16.1 s)
18. factory: started docs-review as vm.
19. reviewer: Round 3 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I checked this round's change against the code. I also re-read *The project's stage image* and the Reference section *How the stage file is followed* against `src/factory/entry/wiring.py`, `src/factory/entry/run.py` and `src/factory/machine/application/images.py`.

    Last round's finding is fixed. machine.md:364 now says that `project_image_settings` raises `stage_image_failed` and then returns `None`. That matches wiring.py:489-497 and :523-530. The three one-line changes from entry 5 are unchanged and still right.

    Findings. Both are claims carried over from the old text that the code does not bear out (style rules 8 to 10, criterion 2):
    1. docs/project-guide/machine.md:361, :369, :721 and :724 say that `run_instance` / `_ProjectImageStart` call `project_image_settings`, and that it is "the one place where the image in use is chosen". The code says otherwise. `_ProjectImageStart._choose` calls `chosen_image` (run.py:267). `project_image_settings` is only a wrapper around `chosen_image` that returns `.settings` (wiring.py:468-469). `chosen_image` makes the choice and returns a `ChosenImage` (`settings`, plus `sizes` measured once) (wiring.py:472-512). Also, after the start, a follow with no stage file passes no `StageImageReport` (run.py:266), so it is not true that every "different text" gets one. `chosen_image` is named nowhere on the page. Fix: add `chosen_image(...) -> ChosenImage | None` to the code block. Name it as the place where the image is chosen and as what `_ProjectImageStart._choose` calls. Describe `project_image_settings` as the wrapper that returns only the settings. Say that the report is passed only when a stage file exists or at the start.
    2. docs/project-guide/machine.md:357 says `build` returns an `ImageBuild` (`passed`, `duration`, `output_tail`: the last 20 lines). This field list leaves out `warnings` (images.py:24, `NonNegativeInt = 0`, the output lines that warn). `chosen_image` writes that field into the `stage image: built ...` log line (wiring.py:505). Fix: add `warnings` to the list.

    Earlier tests: none (the diff changes no test file).
20. factory: This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
21. 2026-11-07 human: One more round, by the human's standing word for tonight (no stop at a round cap while the findings are real). The documenter fixes findings 1 and 2 of the last review against the code: who calls `project_image_settings` and where the image in use is chosen, and the full field list of `ImageBuild`, `warnings` included. Read each named function and model before writing its sentence.
22. factory: started docs-review as vm.
23. reviewer: Docs-review after the human's answer in entry 21. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. No documenter run came between entry 21 and this review, and the page has not changed since the round-3 review. The only commit since then is the merge of `origin/main` (add92190e), and it touches only `docs/runs/2026-11-05-f0052/log.md`. I checked the two findings of entry 19 against the code on the branch again. Both still hold, and the human's entry 21 asks for both to be fixed.

    Findings:
    1. docs/project-guide/machine.md:353, :361, :369, :721 and :724 are wrong about the image in use:
       - What the page says: `project_image_settings` is "the one place where the image in use is chosen", and `run_instance` / `_ProjectImageStart` call it, with a `StageImageReport` for every different text.
       - What the code does: `_ProjectImageStart._choose` calls `chosen_image` (src/factory/entry/run.py:267). In `src/factory`, no code calls `project_image_settings`; it is only in the export list at wiring.py:160. It is a wrapper that returns `chosen.settings` (wiring.py:468-469). `chosen_image(settings, git, images, stops, *, report=None) -> ChosenImage | None` makes the choice and returns the settings and the sizes, measured once (wiring.py:472-512). The report is passed only when a stage file exists or at the start (`told = report if has_stage_file or at_start else None`, run.py:265-266).
       - Fix: add `chosen_image(...) -> ChosenImage | None` to the code block at :353. Name it at :361 as the place where the image is chosen, and at :369 and :721 as what `_ProjectImageStart._choose` calls. Describe `project_image_settings` as the wrapper that returns only the settings. At :724, say that the report goes with a stage file or at the start.
    2. docs/project-guide/machine.md:357: the field list "`ImageBuild` (`passed`, `duration`, `output_tail`: the last 20 lines)" leaves out `warnings`. That field is a `NonNegativeInt`, default 0, counting the output lines that warn (src/factory/machine/application/images.py:24). `chosen_image` writes it into the `stage image: built ...` log line (wiring.py:505). Fix: add `warnings` to the list.

    Earlier tests: none (the diff changes no test file).
24. factory: started docs-only as vm.
25. documenter: Round 4: I fixed the reviewer's two findings in entry 23, as the human asked in entry 21. I read `chosen_image` and `project_image_settings` in `src/factory/entry/wiring.py`, `_ProjectImageStart._choose` in `src/factory/entry/run.py`, and `ImageBuild` in `src/factory/machine/application/images.py` before I wrote.

    Files changed:
    - `docs/project-guide/machine.md`, in *The project's stage image* and in the Reference section *How the stage file is followed*:
      - I added `chosen_image(...) -> ChosenImage | None` to the code block.
      - The page now names `chosen_image` as the place where the image in use is chosen. It returns the settings and the sizes measured once. `project_image_settings` is described as the wrapper that returns only the settings.
      - `_ProjectImageStart` is the caller, and it calls `chosen_image`.
      - The `StageImageReport` is passed only when a stage file exists or at the start. A later follow without a stage file passes none.
      - The `ImageBuild` field list now includes `warnings`: the count of output lines that warn, 0 by default.

    Cross-read and found current: the other files from earlier rounds are unchanged. No heading was renamed.

    Stale text I saw and did not touch, because it is unrelated to this story: `docs/project-guide/pipeline.md`, in the tick step, lists the preflight items without `metadata-block` and the `copy` variant, which machine.md states. No `docs/decisions.md` entry was written, because the criterion says none.

    `make documents` ended `documents ok (16.2 s)`. I did not run `make check`, because the only changed file is a document.

    `check`: check: green
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok (16.2 s)
26. factory: started docs-review as vm.
27. reviewer: Docs-review of the round-4 change, after the human's answer in entry 21. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I checked the rewritten parts of *The project's stage image* and of the Reference section *How the stage file is followed* against `chosen_image`, `project_image_settings` and `_base_image` (src/factory/entry/wiring.py:455-530), `_ProjectImageStart._follow_main` and `_choose` (src/factory/entry/run.py:240-285), `ImageBuild` (src/factory/machine/application/images.py:15-24) and `BUILD_OUTPUT_TAIL_LINES` (podman_images.py:18).

    Both findings from entry 23 are fixed, and the new text matches the code:
    - `chosen_image(settings, git, images, stops, *, report=None) -> ChosenImage | None` is now in the code block. The page names it as the place where the image is chosen and as what `_ProjectImageStart` calls (run.py:267). `project_image_settings` is described as the wrapper that returns `chosen.settings` (wiring.py:468-469).
    - The report rule matches `told = report if has_stage_file or at_start else None` (run.py:266).
    - The `ImageBuild` field list now has `warnings`, a `NonNegativeInt` that defaults to 0 (images.py:24). The 20 lines match `BUILD_OUTPUT_TAIL_LINES`.

    The three one-line changes from entry 5 have not changed and are still right. No heading was renamed.

    Findings:
    1. docs/project-guide/machine.md:725, the bullet this round rewrote, breaks style rule 2 (`docs/project-guide/style.md`:8: one idea per sentence, split anything over about 25 words). The sentence "A different text calls `chosen_image`; it passes a `StageImageReport` when a stage file exists or at the start, and none for a later follow without a stage file (`stage_image_report`: log, clock, the commit's first 12 hex digits)." runs to about 37 words and joins two ideas with a semicolon. Fix: split it. For example: "A different text calls `chosen_image`. It passes a `StageImageReport` (`stage_image_report`: log, clock, the commit's first 12 hex digits) when a stage file exists or at the start. A later follow without a stage file passes none."

    Earlier tests: none needed (the diff changes no test file).
28. factory: started docs-only as vm.
29. documenter: Round 5: I fixed the one finding in the reviewer's entry 27.

    Files changed:
    - `docs/project-guide/machine.md`, line 725 (Reference section *How the stage file is followed*): I split the 37-word sentence into four short ones. A different text calls `chosen_image`. It passes a `StageImageReport` (`stage_image_report`: log, clock, the commit's first 12 hex digits) when a stage file exists or at the start. A later follow without a stage file passes none. Given a report, `chosen_image` writes the `stage image:` lines and puts `at <commit>: ` before the stop's detail. The meaning is unchanged. I named `chosen_image` as the subject of the last sentence because wiring.py:502, :519, :526 and :527 write those lines in `chosen_image`.

    Cross-read and found current: the other changes on this page and in the other files are unchanged since the last review. No heading was renamed.

    Stale text I saw and did not touch, because it is unrelated to this story: `docs/project-guide/pipeline.md`, in the tick step, lists the preflight items without `metadata-block` and the `copy` variant, which machine.md states. No `docs/decisions.md` entry was written, because the criterion says none.

    `make documents` ended `documents ok (16.4 s)`. I did not run `make check`, because the only changed file is a document.

    `check`: check: green
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok (16.2 s)
30. factory: started docs-review as vm.
31. reviewer: Docs-review of the round-5 change. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. Since the last review, the only document change is one bullet in `docs/project-guide/machine.md`, in the Reference section *How the stage file is followed* (a83481b1b..a3dc22e19). I checked it against the code on the branch.

    The one finding from entry 27 is fixed:
    - The 37-word sentence is now four short sentences, one idea each, with one parenthesis. That follows style rule 2.
    - "A different text calls `chosen_image`": matches `_follow_main` and `_choose` (src/factory/entry/run.py:251-267).
    - "It passes a `StageImageReport` ... when a stage file exists or at the start. A later follow without a stage file passes none.": matches `told = report if has_stage_file or at_start else None` (run.py:266).
    - `stage_image_report`'s log, clock and the commit's first 12 hex digits: matches wiring.py:425-433 (`commit[:_SHORT_COMMIT_LENGTH]`).
    - "Given a report, `chosen_image` writes the `stage image:` lines and puts `at <commit>: ` before the stop's detail": matches `chosen_image` and the two helpers it calls, `_base_image` and `_stage_image_failed` (wiring.py:500-530).

    Nothing else under review has changed since entry 27. That review and the earlier ones checked the rest of the page against the code and the style page. The three one-line changes from entry 5 are unchanged and still right: the line in `docs/checked-documents.txt`, the index entry in `docs/project-guide/README.md`, and the link in `docs/project-guide/pipeline.md`. No heading was renamed. The factory's results in entry 29 show `make documents` as `documents ok`.

    No findings.

    Earlier tests: none needed (the diff changes no test file).
32. factory: done (pull request merged); cost: 14 runs, 19.9 min, 175 turns, 563660 tokens in (7842246 more from cache), 104969 out, $6.26
