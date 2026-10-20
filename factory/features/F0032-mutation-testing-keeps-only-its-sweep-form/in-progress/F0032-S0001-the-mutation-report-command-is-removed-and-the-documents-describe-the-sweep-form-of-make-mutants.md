---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 307
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T00:16:58.415666Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T00:16:58.421375Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T00:17:13.968258Z'
  stage: intake
  run: 06a65fe7a7a64ffdbebbe4912565c56b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T00:17:34.947766Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T00:19:32.263066Z'
  stage: tests
  run: 5023b3d483074ed3affc9963113d4022
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T00:19:53.171300Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T00:21:43.537094Z'
  stage: doing
  run: 7ec368a30ac243f08d487ea2b945799d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T00:22:04.320707Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T00:22:28.028479Z'
  stage: review
  run: 03dad3a5ff7a4b03a05b95c3f948c355
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T00:22:48.913854Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T00:23:38.659673Z'
  stage: docs
  run: 128f4479dbc540d5a7e7c2862941b481
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T00:23:59.472345Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T00:24:23.494163Z'
  stage: smoke-test
  run: 3f5e3318cedc416c8655be821f523101
---

# The mutation report command is removed and the documents describe the sweep form of `make mutants`

## Description

On 2026-10-19 the human decided that mutation testing runs only as sweeps outside the factory, with `mutants/` made anew for every run (night log, `docs/runs/2026-10-12-overnight/night-log.md`, the row of 22:20). The human's change 1 of this feature rewrites the `Makefile`'s `mutants` recipe into its sweep form before this story starts. Every run removes `mutants/` first. The modules come from `MODULES` given by hand or from `FEATURE`, and an optional `MUTANTS_SECONDS` and `MUTANTS_CHILDREN` set the stop and the workers. The run ends with mutmut's own listing of the mutants it did not kill. The recipe no longer calls `python -m factory.entry.check_mutants`. That command and its rules, `factory.domain.mutants` (F0024-S0001), filtered the survivors of earlier runs out of a kept `mutants/`, named the mutants still to run in it, and marked a run `partial` for the factory's report. A fresh `mutants/` leaves none of those jobs, and no stage and no sweep calls the command. This story removes the two modules and their tests, and makes the documents describe the sweep form. These stay as they are: `factory.entry.inputs`, which `check_duplicates` uses, and its tests; `[tool.mutmut]`; `command_line`'s suffix for a command stopped at its time limit; the template's and the demo's `mutants` recipes; and every other module under `src/`.

## Interface

The coder removes two modules and changes nothing else under `src/factory/`:

- `src/factory/entry/check_mutants.py` (`entry`): removed whole.
- `src/factory/domain/mutants.py` (`domain`): removed whole, with `MutantStatus`, `MutantName`, `MutantResult`, `MutationReport`, `parse_results`, `mutation_report` and `rerun_names`.
- Unchanged: `src/factory/entry/inputs.py` (`read_input`, `UnreadableInput`) and `src/factory/entry/check_duplicates.py`, which imports both from it. No other module imports either removed module.

Tests (the tester writes them):

- `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` (F0024-S0001) are removed whole, under the leave of the feature's decision 9.
- `tests/entry/test_mutation_report_removed.py` (new): one parametrized test over `importlib.util.find_spec`. It reads no source file, so `[tool.mutmut]` needs no new deselected test.
- Unchanged, and they must pass: `tests/entry/test_inputs.py`, `tests/entry/test_check_duplicates.py`, `tests/domain/test_command_line_time_limit.py`, `tests/application/test_stage_time_limited_report.py`, `tests/test_template_makefile.py` and `tests/test_claude_agent_texts_mutants.py`.

## Acceptance criteria

1. The report command and its rules are gone, and the shared reader stays (rows of one parametrized test, each a module name and whether `importlib.util.find_spec(name)` finds it): `factory.entry.check_mutants`, not found (`None`); `factory.domain.mutants`, not found; `factory.entry.inputs`, found; `factory.entry.check_duplicates`, found.
2. The earlier tests named in the Interface as unchanged pass with their names and their checks as they are, and `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` no longer exist.
3. `make check` stays green.
4. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*, as F0031 left it, is rewritten for the sweep form, in the `Makefile`'s own terms. No stage and no agent runs `make mutants`, and sweeps do. Every run removes `mutants/` first, so mutmut makes it anew, copies the other files under `src/` afresh and runs its stats again; nothing is kept between runs. The modules come from `MODULES` (dotted modules or packages, each run by its pattern `<name>.*`, for example `MODULES='factory.domain.disk factory.application'`) or from `FEATURE=<id>` (the modules the feature's story commits on `origin/main` changed, which needs a checkout with its history). `MODULES` wins when both are given. With neither, it prints `mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012` and fails; with no module changed by the feature, it prints `mutants: no module under src/factory changed by <id>` and exits 0. `MUTANTS_SECONDS` stops mutmut by `timeout` after that many seconds (no stop when unset), and the run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`. `MUTANTS_CHILDREN` passes `--max-children`, because mutmut's default is every core the machine reports, also in a container limited to fewer. The recipe keeps its own `TMPDIR` from `mktemp -d`, its `EXIT` trap that removes that folder, and `umask 022`. It ends with `uv run mutmut results` without the `not checked` lines, which then lists only this run's mutants that mutmut did not kill (and none that a stop left unreached). To read one survivor: `uv run mutmut show <name>`. The story-branch form, the `--names` rerun, the reason of the two users of one group for `chmod -R g+w mutants`, the removal of `.git` folders, the copy into an existing `mutants/src`, and "`mutants/` holds the latest run of each module" go. The subsection *The report of a mutation run* goes whole. `docs/project-guide/README.md`, the index line of `processes-and-checks.md`, no longer names `factory.domain.mutants`, `factory.entry.check_mutants` or *The report of a mutation run*, and still names `factory.entry.inputs`. `docs/operator-guide.md`, *Mutation testing by sweep* (F0031's): the target stays for the sweeps, and `check_mutants` is no longer named there. It gives a sweep's command, `make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2`, and says that every run pays mutmut's stats: 165 s on 20 cores; 4.5 to 19 minutes on two cores in the sweeps of 2026-10-19. *How long it takes* no longer says that the recipe stops mutmut after 540 s or that the largest runs end `partial`. *A run that never gets past mutmut's stats* says that a `MUTANTS_SECONDS` below the stats checks no mutant, and its example `make mutants MUTANTS_SECONDS=1500` gains `MODULES=<module>`. After the story, neither `docs/operator-guide.md` nor `docs/project-guide/` names `check_mutants` or `factory.domain.mutants`. `docs/decisions.md`: an entry *The mutants target keeps only its sweep form*, dated with the story, from the feature's decisions 1 to 7. Its decisions are a fresh `mutants/` by `rm -rf mutants`, `MODULES` or `FEATURE`, no stop unless asked, `MUTANTS_CHILDREN`, and the report command removed with `factory.entry.inputs` kept. Its reasons are the human's decisions of 2026-10-19 and that a fresh `mutants/` leaves the command no job. It rejects keeping `check_mutants` for its summary line, refusing a run while `mutants/` exists, and 540 s as the default stop. *A mutation run's report is a line of its own, and a partial run is never complete*, *make mutants runs under a temporary root of its own* and *Mutation testing runs only as sweeps outside the factory* (whose decision says that `factory.entry.check_mutants` stays for the sweeps) each get a line naming the new entry. `README.md`: none, it does not name mutation testing.

## Smoke test

```bash
uv run -q python -c "import importlib.util as u; print([u.find_spec(m) is None for m in ('factory.entry.check_mutants', 'factory.domain.mutants', 'factory.entry.inputs')])"
```
Expect: `[True, True, False]` (the two modules are gone, the shared reader stays)

```bash
ls src/factory/entry/check_mutants.py src/factory/domain/mutants.py tests/entry/test_check_mutants.py tests/domain/test_mutants.py 2>&1 | grep -c 'No such file'
grep -c -F -e check_mutants -e factory.domain.mutants docs/operator-guide.md docs/project-guide/processes-and-checks.md docs/project-guide/README.md Makefile CLAUDE.md || true
```
Expect: `4`, then five lines, `docs/operator-guide.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/README.md:0`, `Makefile:0`, `CLAUDE.md:0`

```bash
p=docs/project-guide/processes-and-checks.md
for s in 'mutants: set MODULES or FEATURE' 'mutants: stopped after' 'MUTANTS_CHILDREN' 'uv run mutmut show'; do grep -qF -e "$s" "$p" && echo found || echo "missing: $s"; done
grep -qF 'make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2' docs/operator-guide.md && echo found || echo 'missing: the sweep command'
grep -c -F 'The report of a mutation run' "$p" docs/project-guide/README.md || true
```
Expect: five lines `found`, then two lines, `docs/project-guide/processes-and-checks.md:0` and `docs/project-guide/README.md:0` (the guide describes the sweep form, the operator guide gives the sweep's command, and the report's subsection is gone; no command here runs `make mutants`)

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: it names the two modules to remove (`src/factory/entry/check_mutants.py`, `src/factory/domain/mutants.py`, with their seven public names) and the modules that stay (`factory.entry.inputs`, `check_duplicates`). It adds no new behaviour. It lists the tests removed (under the leave of the feature's decision 9), the one new test module and the earlier tests that must pass unchanged.
   Criteria: criterion 1 is one parametrized test over `find_spec` with four rows. Two rows are "not found" and two are "found", so both sides of the removal are covered. Criterion 2 is checkable, since the two test files must be absent and the six named tests must pass. Criterion 3 is `make check`. The docs criterion carries the documenter's work. It is checkable by the smoke test's greps. It has no new rules or failing sides of its own, because the rules it describes (the refusal with no `MODULES` or `FEATURE`, the stop line) belong to the human's Makefile change 1 and are not changed by this story.
   Smoke test: the three blocks are runnable with `uv run`, `ls` and `grep` and make no paid calls. Each `Expect:` line gives exact output to compare. The second block assumes the human's changes 1 and 2 (Makefile, CLAUDE.md) are already in. That is a precondition the feature names, not a gap in the story.
   Architecture: it removes a domain module and an entry module and leaves the layer order alone. It writes no new code under `src/`. `factory.entry.inputs` stays with its one remaining user.
   Scope: it matches the feature's Scope list, including the four documents and the removal of the two test modules. It touches nothing in the feature's Out of scope list (`inputs`, `[tool.mutmut]`, `command_line`'s suffix, the template and the demo recipes, `pipeline.yml`).
4. factory: started tests as self.
5. tester: I wrote the one new test module and removed the two earlier test modules, as the Interface says.

   - criterion 1: tests/entry/test_mutation_report_removed.py::test_the_mutation_report_is_removed_and_the_input_reader_stays. It has four rows over `importlib.util.find_spec`: `factory.entry.check_mutants` not found, `factory.domain.mutants` not found, `factory.entry.inputs` found, `factory.entry.check_duplicates` found.
   - criterion 2: I wrote no new test for this one. I deleted `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` from the working tree under the leave of the feature's decision 9. `git rm` was refused (`.git/index.lock` Permission denied), so I used a plain `rm` and the factory's commit stages the deletion. The six named earlier tests stay as they are and pass now: `test_inputs`, `test_check_duplicates`, `test_command_line_time_limit`, `test_stage_time_limited_report`, `test_template_makefile` and `test_claude_agent_texts_mutants`.
   - criterion 3: `make check`, the coder's job.
   - criterion 4 (docs): the documenter's job; no test.

   Files created: tests/entry/test_mutation_report_removed.py. Files deleted: tests/entry/test_check_mutants.py, tests/domain/test_mutants.py. I changed no other earlier test file.

   `make test`: the test runner could import every module. The report-command and report-rules rows fail on purpose because the two modules still exist; the coder removes `src/factory/entry/check_mutants.py` and `src/factory/domain/mutants.py`. Every other test passes. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/entry/test_mutation_report_removed.py::test_the_mutation_report_is_removed_and_the_input_reader_stays[report-rules]
6. factory: started doing as self.
7. coder: I removed `src/factory/entry/check_mutants.py` and `src/factory/domain/mutants.py` whole, as the Interface says. Nothing else under `src/` imported them: a search of `src/`, `security/` and `pyproject.toml` found no other user, and no contract schema comes from them. I left `src/factory/entry/inputs.py` and `check_duplicates.py` untouched. `make check` is green: `check: green`, coverage 99.14 %. The new test `tests/entry/test_mutation_report_removed.py` passes on all four rows.

   Main choice: a pure deletion. I rejected keeping `factory.entry.inputs` only through a re-export or any other shim, because the Interface keeps it as it is with `check_duplicates` as its one user.

   Refactor: the diff only deletes files, so nothing needed changing.

   The journal did not change the meaning of the task, so I left the Description alone. The four documents in criterion 4 are the documenter's work and I did not touch them.

   Noticed, not touched: an ignored `mutants/` folder left from an earlier mutmut run still holds copies of the removed modules, their tests and the old `Makefile` recipe. It is not tracked, and it does not affect `make check`. The next sweep's `rm -rf mutants` removes it.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` and the work item. The diff removes `src/factory/domain/mutants.py` and `src/factory/entry/check_mutants.py` whole. It removes their two test modules and adds `tests/entry/test_mutation_report_removed.py`. It touches nothing else under `src/`, and `inputs.py` and `check_duplicates.py` are unchanged.
   - Criterion 1: one parametrized test with four rows over `importlib.util.find_spec`. The two "not found" rows (`check_mutants`, `domain.mutants`) and the two "found" rows (`inputs`, `check_duplicates`) cover both sides of the removal. The test reads no source file, so `[tool.mutmut]` needs no new deselected test.
   - Criterion 2: the two test files are gone. The six earlier test modules named in the Interface are not in the diff, so they are unchanged. The coder's `make check` (entry 7) ran them green.
   - Criterion 3: entry 7 records `check: green`.
   - Leftover references: a search outside `factory/`, `docs/` and `planning/` finds no other mention of `check_mutants` or `factory.domain.mutants`. That covers `src/`, `tests/`, `security/`, `pyproject.toml`, the `Makefile` and `CLAUDE.md`, so no baseline entry or mutmut setting points at a removed file.
   - Architecture, security, quality: the diff only deletes code, and the one new test module has a module docstring and typed parameters. It adds no markers that silence a check and no new helper. The `duplicates: 5 new` record cannot come from this diff: a deletion adds no similar or dead code.
   - Work item hygiene: the coder's entry gives the main choice, a plain deletion, and what was rejected, a re-export shim. The Description matches what was built. Criterion 4 still describes the documenter's work on the four documents.

   Earlier tests:
   - `tests/domain/test_mutants.py` (deleted): the human's leave, decision 9 in the feature's `feature.md`, which the story's Interface names.
   - `tests/entry/test_check_mutants.py` (deleted): the human's leave, the same decision 9 in the feature's `feature.md`, named in the story's Interface.
10. factory: started docs as self.
11. documenter: I rewrote the mutation-testing documents for the sweep form. I found no finding for the coder: the `Makefile` recipe, the Interface and the removed modules agree.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`: *Mutation testing* is rewritten in the `Makefile`'s own terms.
      - Nothing is kept between runs: `rm -rf mutants`, mutmut's stats run again, and the other files under `src/` are copied afresh.
      - It covers `MODULES` and `FEATURE` (`MODULES` wins), the two end lines, `MUTANTS_SECONDS` with its stop line, `MUTANTS_CHILDREN`, the `TMPDIR`/`EXIT` trap/`umask 022`, and the result without the `not checked` lines, plus `uv run mutmut show <name>`.
      - *The report of a mutation run*, the story-branch form, `--names`, `chmod -R g+w mutants`, the `.git` removal and "`mutants/` holds the latest run" are gone.
    - `docs/project-guide/README.md`: the index line for `processes-and-checks.md` no longer names `factory.domain.mutants`, `factory.entry.check_mutants` or the removed subsection. It still names `factory.entry.inputs`.
    - `docs/operator-guide.md`, *Mutation testing by sweep*:
      - `check_mutants` is gone.
      - The sweep command `make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2` is added.
      - Every run pays the stats: 165 s on 20 cores, 4.5 to 19 minutes on two cores.
      - The 540 s stop and the `partial` ends are gone.
      - The stats-wall paragraph says a `MUTANTS_SECONDS` below the stats checks no mutant, and its example now has `MODULES=<module>`.
    - `docs/decisions.md`:
      - New entry *The mutants target keeps only its sweep form*, dated 2026-10-20, from the feature's decisions 1 to 7. It has the decisions, the reasons and the three rejected options.
      - One line naming the new entry is added to each of: *A mutation run's report is a line of its own, and a partial run is never complete*, *make mutants runs under a temporary root of its own*, and *Mutation testing runs only as sweeps outside the factory*. The last one now says that `check_mutants` is removed and the target stays.
      - The F0017 line says the temporary root stays and that `chmod` and the `.git` removal go.

    `README.md`: nothing to change, it does not name mutation testing.

    Checks I ran: a grep of `docs/operator-guide.md`, `docs/project-guide/`, `Makefile` and `CLAUDE.md` finds no `check_mutants`, `factory.domain.mutants` or *The report of a mutation run*. I did not run the examples, because they run `make mutants` and the story says no stage runs it. I checked every variable, end line and stop line against the `Makefile` recipe by reading it. I did not run `make check`, because I changed only documents. The factory's checks decide.

    Cross-read and found current: `docs/project-guide/agents.md`, `watching.md`, `git-and-hosting.md` and `write-guard.md`. Their mentions of mutation are unrelated or still true, for example the commit-prefix sentence in `watching.md`.

    Stale text I noticed and left, because it is not mine to fix:
    - `docs/operator-playbook.md` (the human's file): the incident table rows at lines 115 and 117 mention `mutants/seed/.git` and `make mutants` running under `umask`. They are history and mostly still true. The `chmod`/`.git` handling they describe is gone from the recipe.
    - `docs/decisions.md`, *Mutation testing per story*: its text still describes the story-branch form and `chmod -R g+w mutants`. It is a history entry, already marked superseded, and the new entry says what replaced it.
    - The decision log has no stale-but-unrelated text that I noticed.

    `check`: check: green (not run again: passed on tree 8e7782634823 at 2026-10-20T00:20:55Z)
    `secrets`: secrets: green (1.6 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: I ran the three blocks from the repository root, exactly as written and in order. All three met their `Expect:` lines, and there are no findings.

    Block 1:
    ```
    [True, True, False]
    ```
    Met: `[True, True, False]`. Both removed modules are gone and `factory.entry.inputs` is still there.

    Block 2:
    ```
    4
    docs/operator-guide.md:0
    docs/project-guide/processes-and-checks.md:0
    docs/project-guide/README.md:0
    Makefile:0
    CLAUDE.md:0
    ```
    Met: `4`, then the five files, each with a count of `:0`.

    Block 3:
    ```
    found
    found
    found
    found
    found
    docs/project-guide/processes-and-checks.md:0
    docs/project-guide/README.md:0
    ```
    Met: five `found` lines, then both files at `:0`.

    I compared the output with the acceptance criteria and found nothing that contradicts them:
    - Criterion 1: matches block 1. The `check_duplicates` row is not in the smoke test; the tester's parametrized test `tests/entry/test_mutation_report_removed.py` covers it.
    - Criterion 2: the two old test files are gone (block 2's `4`).
    - Criterion 3: no smoke-test command runs `make check`, and I did not run it either. Entry 7 records `check: green`, and the factory checks it again.
    - Criterion 4: beyond what the greps check, I looked at a few more of its points:
      - The index line for `processes-and-checks.md` still names `factory.entry.inputs`.
      - `docs/decisions.md` has the new entry *The mutants target keeps only its sweep form*, and the three earlier entries each name it.
      - The operator guide gives 165 s on 20 cores and 4.5 to 19 minutes on two cores, and has the example `make mutants MODULES=<module> MUTANTS_SECONDS=1500`. It no longer mentions a 540 s stop or a `partial` end.

    As the work item says, no command ran `make mutants`. I changed no files.
