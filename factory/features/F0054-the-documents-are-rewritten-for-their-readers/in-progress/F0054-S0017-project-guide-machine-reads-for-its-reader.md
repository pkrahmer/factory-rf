---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 625
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T05:14:53.662724Z'
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
