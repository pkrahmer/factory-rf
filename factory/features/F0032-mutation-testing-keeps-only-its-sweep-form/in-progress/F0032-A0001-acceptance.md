---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 308
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T00:26:18.826872Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T00:31:08.110549Z'
  stage: acceptance
  run: 58f36b6e359d47a1985afd3860a195ea
stories: [F0032-S0001]
outcome: null
---

# Acceptance of Mutation testing keeps only its sweep form

## Recommendation

Accepted. The whole does what `feature.md` promised. `make mutants` has only its sweep form: `MODULES` or `FEATURE`, a fresh `mutants/`, an optional stop and an optional cap on the workers, and mutmut's own listing at the end. The report command, its rules and its tests are gone, and `factory.entry.inputs` stays. The feature's smoke test is green, and so is `make check`. One small documentation repair is proposed, for two operator-guide paragraphs that still read as if `mutants/` could be kept. Three of the human's own changes are still open: changes 4 and 6, which are now due, and change 5, which is optional.

## 1 Scope

None. The Scope's three items each have their part of F0032-S0001, and the story did nothing outside them:
- `src/factory/entry/check_mutants.py` and `src/factory/domain/mutants.py` are removed. Nothing under `src/`, `tests/` (except the new test), `security/`, `pyproject.toml`, the `Makefile` or `CLAUDE.md` names them.
- The two test modules are removed. `tests/entry/test_mutation_report_removed.py` pins both removals and that `factory.entry.inputs` and `factory.entry.check_duplicates` stay.
- The four documents are rewritten (see 5).

The goal also depends on the human's changes 1 to 3, and all three are in:
- The `Makefile`'s `mutants` recipe matches change 1 line for line, with tab-led recipe lines.
- `CLAUDE.md`'s *Checks* bullet matches change 2.
- `factory/features/F0024-mutation-testing-per-story/` has no `backlog/` and no S0004 (change 3).

The Out of scope items are untouched: `[tool.mutmut]`, `.gitignore`, `command_line`'s suffix, `template/Makefile`'s `FEATURE`-only recipe, the demo, and `factory/pipeline.yml` (whose only `mutants` mention is F0031's comment).

## 2 Feature smoke test

The walk-through of someone who runs a sweep: the report command is gone; a sweep by hand runs mutmut on the named modules after a fresh `mutants/`, with the stop and the cap only when asked; `FEATURE` reads `origin/main` and `MODULES` wins; with neither the target refuses; and the guide uses the `Makefile`'s own terms. The rules forbid running `make mutants`, so the script reads the recipe with `make -n`. That prints the expanded recipe and executes none of its lines, so mutmut never starts.

```
$ bash feature-smoke.sh
--- 1 the report command is gone, the shared reader stays
/work/checkout/.venv/bin/python3: No module named factory.entry.check_mutants
exit 1
{'factory.entry.check_mutants': False, 'factory.domain.mutants': False, 'factory.entry.inputs': True, 'factory.entry.check_duplicates': True}
--- 2 a sweep by hand (dry run: make -n prints the recipe, executes none of its lines)
modules given by hand: set
rm -rf mutants
timeout 60 uv run mutmut run --max-children 2 factory.domain.disk.* factory.application.*
0
--- 3 no limits unless asked
TMPDIR="$temporary"  uv run mutmut run  factory.domain.disk.*
--- 4 FEATURE from origin/main; MODULES wins
3
if [ -z "" ]; then echo "mutants: no module under src/factory changed by F0032"; exit 0; fi
mutmut run  factory.domain.disk.*
--- 5 neither: the refusal is the first line
if [ -z "" ]; then echo "mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012"; exit 2; fi
--- 6 the documents name the Makefile terms and no removed command
MODULES: makefile 9, guide 3
FEATURE: makefile 6, guide 2
MUTANTS_SECONDS: makefile 4, guide 1
MUTANTS_CHILDREN: makefile 3, guide 1
rm -rf mutants: makefile 1, guide 0
mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012: makefile 1, guide 1
mutants: stopped after: makefile 1, guide 1
tests/entry/test_mutation_report_removed.py
exit 0
```

Green. Here is how to read the output:
- Part 2's `0` counts the old recipe's `check_mutants`, `chmod g+w` and `mutants/src` copy in the expanded recipe: none is left.
- Part 4's `3` is F0024's modules that still exist on `origin/main`: `factory.domain.checks`, `factory.entry.check_duplicates` and `factory.entry.inputs`. The `wildcard` drops the two removed modules, so F0032 itself, which only removed modules, has none.
- The guide says "removes `mutants/` first" in words instead of `rm -rf mutants`.
- The one file that names the removed modules is the test that pins their absence.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- Coder (S0001, entry 7): an ignored `mutants/` from an earlier run still holds copies of the removed modules and the old recipe. It is still present in this checkout. It is untracked and does not affect `make check`, and the next sweep's `rm -rf mutants` removes it. No story.
- Documenter (S0001, entry 11):
  - `docs/operator-playbook.md` still says that `make mutants` removes nested repositories under `mutants/` on exit: line 107 (*Leftovers*, "F0019: `make mutants` now removes nested repositories when it exits") and line 115 (the `repository_unavailable` incident row). The recipe no longer does that. The playbook is the human's file, and the feature's change 6 schedules this repair for after S0001. It is due now (see 6).
  - *Mutation testing per story* in `docs/decisions.md` still describes the story-branch form. It is a history entry, marked superseded, and needs nothing.
- Reviewer (S0001, entry 9): `duplicates: 5 new` does not come from the diff. I ran `make duplicates`: `5 new, 33 known, 3 gone`. The new findings are four similar blocks between `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`call_refusal`, `cleanup_launch`, `version_printed`, the `confine_executable` branch) and the unused class `ManualWaiter` in `src/factory/adapters/clock.py`. The gone ones are `ManualClock`, `advance` and `data` in `work_item_markdown.py`. None of them belongs to F0032, so I propose no story here. They wait for the human: a refresh of `security/duplicates-baseline.txt` (the human's file), or a refactor under the runtimes' features.
- My own observation: the operator guide's *How long it takes* and *A run that never gets past mutmut's stats* still read as if `mutants/` could be kept (see 5). This gets proposed story F0032-S0002.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/processes-and-checks.md` and `docs/decisions.md` from top to bottom for mutation testing.

The project guide's *Mutation testing* matches the recipe on every variable, end line, stop line, the temporary folder and `umask 022`. Its index line no longer names the removed modules and still names `factory.entry.inputs`. `README.md` does not name mutation testing, which is right.

The decision log reads in order. The new entry *The mutants target keeps only its sweep form* is the last one. Each of the three superseded entries names it, and the history entries keep their old wording under their superseded notes.

One finding, in the operator guide, *Mutation testing by sweep*:
- *How long it takes* gives the fixed 165 s twice in one paragraph. It keeps the per-story minutes of F0019 and F0021, and a measurement "with the stats kept in `mutants/mutmut-stats.json`, a run of 31 mutants took 12 s", which `make mutants` can no longer produce. The paragraph then says itself that no run keeps the stats.
- *A run that never gets past mutmut's stats* still gives "a change of `[tool.mutmut]`'s test arguments … or a fresh `mutants/`" as the cause. It says that mutmut "keeps them only when that run ends", and that a larger `MUTANTS_SECONDS` "repairs it". Every run is fresh now, so there is no stuck state to repair.

The advice is still right: a stop below the stats checks nothing. The wording sends an operator looking for a state that cannot occur. It does not mislead about what the target does, so it is not a broken promise. Proposed story F0032-S0002.

Outside the stages' documents, the playbook's lines 107 and 115 still describe the removal of nested repositories (see 4 and 6).

## 6 Decisions taken for the human

To accept or revisit:
1. The recipe makes `mutants/` fresh with `rm -rf mutants`, and every run pays mutmut's stats (feature decision 1).
2. The copy into an existing `mutants/src` goes (decision 2, confirmed by the human).
3. No stop unless `MUTANTS_SECONDS` is given; 540 s is no longer the default (decision 3).
4. `MUTANTS_CHILDREN` is new and optional, one line beyond the task (decision 4).
5. The modules come from `MODULES` or `FEATURE`, `MODULES` wins, there is no story-branch mode, and `FEATURE` is no longer read from a branch (decision 5).
6. `check_mutants` and `factory.domain.mutants` are removed instead of kept for their summary line (decision 6).
7. `factory.entry.inputs` stays, with `check_duplicates` as its one user (decision 7).
8. F0024-S0004 is removed whole instead of trimmed to its `check-duplicates` half (decision 8). It is done: F0024 has no backlog.
9. The template's and the demo's `mutants` recipes keep `FEATURE` only and a kept `mutants/` (decision 10). A project that sweeps would need a later story.
10. In S0001, the coder rejected a re-export shim and made a plain deletion (entry 7). The tester's `git rm` was refused at `.git/index.lock`, so the tester deleted with `rm` and the factory's commit staged the deletion (entry 5).

The human's changes still open:
- Change 4: F0030's draft, `planning/overnight/stories/F0030-…/feature.md` line 36, still runs its real check "on a story-form branch". F0032 has been merged first, so the change is due.
- Change 5 (optional): the sweep brief, `planning/overnight/briefs/mutation-sweep.md`.
- Change 6: `docs/operator-playbook.md` lines 107 and 115. Due now that S0001 is merged.
- Decision 11's stale line in F0028's draft, the "feature acceptance's `make mutants`", is still there.

Earlier tests changed: `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` (F0024-S0001) were deleted under the leave of the feature's decision 9, and the reviewer named that leave for each (S0001, entry 9). No earlier test was changed without a leave.

## 7 The slow checks

Nothing beyond `make check`, which is green: 5,970 tests, coverage 99.14 %. The slowest tests are about 5 s each: `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` and `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`. The feature's own test takes 0.001 s per row. `make duplicates` is a record, not a check (see 4).

Disk: `/work` used stays at 0.5 GB, and `/state` and `/tmp` at 0.0 GB. Free space fell by 0.2 GB on all three at once since the previous record (an acceptance), which is the shared host drive and not the feature. The feature only removed files, so it explains no growth, and there is none to explain.

## 8 Cost

One story, F0032-S0001: 6 runs, 4.0 min, 39 turns, 133,304 tokens in (719,451 more from cache), 13,848 out, $1.15. Nothing stands out. Every stage took a single run, with no rework round and no stall. The longest runs were the tester's (about 2 min) and the coder's (about 2 min), for a deletion and a fifteen-line test.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human: the feature's 14 decisions and the human's changes 1 to 3 settled everything before S0001 started.

## Proposed stories

- F0032-S0002, *The operator guide plans a sweep for a fresh `mutants/` folder only*: rewrites the two operator-guide paragraphs that still speak of kept stats and a run to "repair", so that a sweep's `MUTANTS_SECONDS` is planned for the form that exists. Documents only, one run.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1 Scope: none. S0001 covers all three Scope items: the two modules, the two test modules plus one new test module, and the four documents. The human's changes 1 to 3 are in: the `Makefile` recipe, `CLAUDE.md`, and F0024-S0004 removed. Nothing Out of scope was touched.
   2 Feature smoke test: green. The report command is gone and `factory.entry.inputs` stays. The script read the recipe with `make -n`, which runs none of its lines, so mutmut never started. The dry run shows `rm -rf mutants` before mutmut, `--max-children`/`timeout` only when asked, `FEATURE` read from `origin/main` (F0024 gives 3 modules), `MODULES` winning, and the refusal with neither. The guide uses the `Makefile`'s terms.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: an ignored `mutants/` leftover, which the next sweep removes. The playbook lines 107 and 115 still describe removing nested repositories, which is the human's change 6. `make duplicates` shows 5 new and 3 gone, all in the runtimes and `clock.py`, none from F0032; that is for the human. The operator-guide wording is the reason for S0002.
   5 Documentation: the project guide, the index and the decision log are consistent with the recipe. The operator guide's *How long it takes* and *A run that never gets past mutmut's stats* still speak of kept stats and a run to "repair" (S0002).
   6 Decisions: feature decisions 1 to 10 are listed for the human. Changes 4 (F0030 draft) and 6 (playbook) are due, 5 is optional, and decision 11's F0028 line is still stale. Two earlier test modules were deleted under decision 9, and the reviewer named that leave.
   7 Slow checks: none beyond `make check`, which is green (5,970 tests, 99.14 %; slowest about 5 s, in the runtime time-limit tests). Disk use is unchanged; the 0.2 GB of free space lost is shared by all three mounts on the host drive.
   8 Cost: 1 story, 6 runs, 4.0 min, $1.15. No rework, no stall, 0 questions, 0.0 h waited.
