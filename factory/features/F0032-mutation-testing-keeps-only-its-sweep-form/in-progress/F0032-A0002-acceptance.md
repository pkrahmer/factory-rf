---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 311
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T00:53:44.892592Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T00:56:40.269560Z'
  stage: acceptance
  run: 8ec7f1c3fdba4b8ebd0fd74cde111307
stories: [F0032-S0001, F0032-S0002]
outcome: null
---

# Acceptance of Mutation testing keeps only its sweep form

## Recommendation

Accepted. The whole does what `feature.md` promised. `make mutants` has only its sweep form, the report command, its rules and its tests are gone, and with F0032-S0002 the operator guide no longer talks about kept stats. The feature's smoke test and `make check` are both green. The open items from the first acceptance (F0032-A0001) are all closed: the human's changes 4, 5 and 6, and the stale line in F0028's draft. No new finding has weight, so no story is proposed.

## 1 Scope

None. The three Scope items are covered by F0032-S0001, as the first acceptance found:
- both modules are removed;
- both test modules are removed, and `tests/entry/test_mutation_report_removed.py` is added;
- the four documents are rewritten.

F0032-S0002 came out of that acceptance's proposal and touched only two paragraphs of `docs/operator-guide.md`, inside the goal's "the documents describe the sweep form". The human's changes are all in:
- Changes 1 to 3: the `Makefile` recipe matches change 1, `CLAUDE.md` *Checks* matches change 2, and F0024 has no backlog left.
- Change 4: F0030's draft, line 36, now uses `MODULES=factory.domain.disk`.
- Changes 5 and 6: commit `01069033` updated the sweep brief, and the playbook's lines 107 and 115 now say "since F0032 every `make mutants` removes `mutants/`". The same commit fixed decision 11's line in F0028's draft.

Nothing Out of scope was touched. `[tool.mutmut]`, `.gitignore`, `command_line`'s suffix, `template/`, the demo and `factory/pipeline.yml` are unchanged by both stories.

## 2 Feature smoke test

The walk-through of someone who runs a sweep. The report command is gone. The command the operator guide gives runs mutmut on the named modules after a fresh `mutants/`, and adds the stop and the cap only when asked. `FEATURE` reads `origin/main`, and `MODULES` wins over it. With neither, the target refuses. The documents state the recipe's own lines and nothing removed. The rules forbid running `make mutants`, so the script reads the recipe with `make -n`. That prints the expanded recipe and executes none of its lines (only the `git log` in `FEATURE_MODULES` runs, read-only). The script was a temporary file, `bash "$d/feature-smoke.sh"` from the repository root:

```
--- 1 the report command is gone, the shared reader stays
/work/checkout/.venv/bin/python3: No module named factory.entry.check_mutants
exit 1
{'factory.entry.check_mutants': False, 'factory.domain.mutants': False, 'factory.entry.inputs': True, 'factory.entry.check_duplicates': True}
--- 2 a sweep by hand, as the operator guide writes it (make -n: printed, not run)
guide: make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2
rm -rf mutants
timeout 7200 uv run mutmut run --max-children 2 factory.application.*
0
--- 3 no stop and no cap unless asked
TMPDIR="$temporary"  uv run mutmut run  factory.domain.disk.* factory.application.*
--- 4 FEATURE from origin/main; MODULES wins
mutmut run  factory.domain.checks.* factory.entry.check_duplicates.* factory.entry.inputs.*
no module under src/factory changed by F0032
mutmut run  factory.domain.disk.*
--- 5 neither: the refusal is the first line
mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012
--- 6 the stop line and the end the guides promise are the recipe's
mutants: stopped after: makefile 1, project guide 1, operator guide 1
mutants: set MODULES or FEATURE: makefile 1, project guide 1, operator guide 0
grep -v ': not checked: makefile 1, project guide 0, operator guide 0
docs/operator-guide.md:0
docs/project-guide/processes-and-checks.md:0
CLAUDE.md:0
tests/entry/test_mutation_report_removed.py
exit 0
```

Green. How to read some of the lines:
- Part 2's `0` counts what the old recipe had and the new one must not: `check_mutants`, `g+w` and the `mutants/src` copy.
- In part 4, F0024's three modules are the ones that still exist. F0032 itself only removed modules, so it gets the "no module" line.
- Part 6's `not checked` row reads 0 in the project guide because the guide says it in words ("without the `not checked` lines", `docs/project-guide/processes-and-checks.md:175`). The refusal line belongs in the project guide, not in the operator guide.
- The three `:0` counts show that `mutmut-stats.json`, "repairs it", "keeps them only when that run ends", `check_mutants` and `540 s` are gone from the operator guide, the project guide and `CLAUDE.md`. That is S0002's repair.
- The one tracked file under `src`, `tests`, `security`, `pyproject.toml`, `Makefile`, `CLAUDE.md`, `template` and `demo` that still names the removed modules is the test that pins their absence.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001, coder (entry 7): an ignored `mutants/` left from an earlier run. It is still in this checkout, untracked. It does not affect `make check`, and the next sweep's `rm -rf mutants` removes it. No story.
- S0001, documenter (entry 11): the playbook's stale lines. The human has since fixed them (change 6; lines 107 and 115 now name F0032). The *Mutation testing per story* history entry is marked superseded and needs nothing.
- S0001 and S0002, coder and reviewer: `make duplicates` gives `5 new, 33 known, 3 gone` in both stories. With S0002's empty `src/` diff, that confirms the findings are not F0032's. As the first acceptance found, they are the runtimes' similar blocks and `ManualWaiter`. They are left to the human: a baseline refresh, or a refactor under the runtimes' features. No story here.
- S0002, documenter (entry 11): the documenter wrote that "the decision log says the sweep form keeps `MODULES` only" while `CLAUDE.md` and the `Makefile` still take `FEATURE`. That is mistaken. *The mutants target keeps only its sweep form* (`docs/decisions.md:822`) says "the modules come from `MODULES` … or from `FEATURE`; `MODULES` wins", the same as `CLAUDE.md`, the `Makefile` and the project guide. The documenter said it had not checked. No contradiction, no story.
- S0002, coder, tester, reviewer and smoke tester: nothing noticed.

## 5 The documentation as a whole

None. I read `README.md`, `docs/operator-guide.md` (*Mutation testing by sweep*), `docs/project-guide/processes-and-checks.md` (*Mutation testing*), the index line in `docs/project-guide/README.md`, and the mutation entries of `docs/decisions.md`, in order.
- The operator guide states the stats' cost once (165 s on 20 cores, 4.5 to 19 min on two), so the double 165 s and the kept-stats measurement that A0001 found are gone. Its stop paragraph quotes the recipe's stop line exactly.
- The project guide covers both variables, both end lines, the limits, the temporary folder, `umask 022` and the filtered result, each matching the recipe.
- The two guides split the work without contradicting each other: the operator guide gives the sweep's command and its cost, the project guide the full variables, and each points to the other.
- The decision log's new entry is the last on mutation, and the three superseded entries name it.
- `README.md` does not mention mutation testing, which is right.

## 6 Decisions taken for the human

To accept or revisit (feature decisions; none came from a question during the stories):
1. `rm -rf mutants` before every run, so every run pays mutmut's stats (decision 1).
2. The copy into an existing `mutants/src` goes (decision 2, confirmed by the human).
3. No stop unless `MUTANTS_SECONDS` is given; 540 s is not the default (decision 3).
4. `MUTANTS_CHILDREN`, new and optional (decision 4).
5. `MODULES` or `FEATURE`, with `MODULES` winning; no story-branch mode (decision 5).
6. `check_mutants` and `factory.domain.mutants` are removed rather than kept for a summary line (decision 6).
7. `factory.entry.inputs` stays, with `check_duplicates` as its one user (decision 7).
8. F0024-S0004 is removed whole (decision 8).
9. The template's and the demo's recipes keep `FEATURE` only and a kept `mutants/` (decision 10). A project that sweeps would need a later story.
10. Choices recorded in the journals:
    - S0001: a plain deletion, with no re-export shim (coder, entry 7).
    - S0001: the tester deleted with `rm` after `git rm` was refused at `.git/index.lock` (entry 5).
    - S0002: the coder left the operator guide to the documenter, although it was the story's only change (entry 7), so the documents stayed with the documenter as `CLAUDE.md` *Docs* says.

Earlier tests changed:
- `tests/entry/test_check_mutants.py` and `tests/domain/test_mutants.py` (F0024-S0001) were deleted in S0001 under feature decision 9, which the reviewer named for each (S0001, entry 9).
- S0002 changed no test.

No earlier test was changed without a leave.

## 7 The slow checks

There is nothing beyond `make check` (and `make mutants`, which is check 3's). `make check` is green: 5,973 tests, coverage 99.14 %. The slowest tests in `.reports/junit.xml`:
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s
- `tests/adapters/test_opencode_sudo_time_limit.py::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[status-1-past-the-limit]`: 4.5 s

The feature's own test takes 0.001 s per row.

Disk: unchanged since the previous record (the start of this acceptance). `/work` has 970.2 GB free and 0.5 GB used, `/state` and `/tmp` have 970.2 GB free and 0.0 GB used. There is no growth to explain.

## 8 Cost

Two stories: 12 runs, 7.3 min, 67 turns, 231,173 tokens in (1,120,331 more from cache), 20,970 out, $1.94.
- F0032-S0001: 6 runs, 4.0 min, $1.15.
- F0032-S0002: 6 runs, 3.3 min, $0.79.

Neither stands out. Every stage took a single run, with no rework round and no stall. S0002's coder, tester and reviewer had no code to handle and each ended quickly, so the story's cost is mostly the fixed price of six stages for a four-line document change. A story that only changes documents could skip the code stages, but that is a question for the pipeline (`factory/pipeline.yml`, the human's file), not for this feature.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human: the feature's decisions and the human's changes settled everything before the stories started.

## Proposed stories

None. Every noticed item is either closed, the human's own (the `make duplicates` baseline), or mistaken (the S0002 documenter's remark on `FEATURE`).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. S0001 covers all three Scope items. S0002 repaired the two operator-guide paragraphs and stayed within the goal. The human's changes 1 to 6 are all in: the Makefile, CLAUDE.md, F0024-S0004, the F0030 draft, the sweep brief and the playbook. The stale line in the F0028 draft is fixed too. Nothing Out of scope was touched.
   2 Feature smoke test: green. The script read the recipe with `make -n`, so mutmut never started. The report command is gone and `inputs`/`check_duplicates` stay. The operator guide's sweep command expands to `rm -rf mutants`, then `timeout 7200 … --max-children 2 factory.application.*`. There is no stop or cap unless asked. `FEATURE` reads origin/main (F0024 gives 3 modules, F0032 none), `MODULES` wins, and with neither the target refuses. The kept-stats wording is gone from both guides and `CLAUDE.md`.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the ignored `mutants/` leftover is still there, and the next sweep removes it. `make duplicates` reports 5 new findings in both stories, but none come from F0032: they are the human's baseline or the runtimes' features. The playbook lines are fixed by the human. The S0002 documenter said the decision log keeps `MODULES` only; that is mistaken, because `docs/decisions.md:822` names `MODULES` or `FEATURE`, the same as `CLAUDE.md` and the `Makefile`.
   5 Documentation: none. The operator guide gives the stats' cost once and quotes the recipe's stop line. The project guide matches the recipe on every variable and end line. The decision log entries are in order. `README.md` rightly does not mention mutation testing.
   6 Decisions: feature decisions 1 to 8 and 10 are listed for the human, with the journals' choices: a plain deletion, `rm` after the refused `git rm`, and the coder leaving the docs to the documenter. Two earlier test modules were deleted under decision 9, and the reviewer named that leave. No test was changed without a leave.
   7 Slow checks: nothing beyond `make check`, which is green: 5,973 tests, 99.14 %. The slowest tests take about 5 s, in the runtime time-limit tests. Disk is unchanged since the start record.
   8 Cost: 2 stories, 12 runs, 7.3 min, $1.94 (S0001 $1.15, S0002 $0.79). No rework and no stall. S0002 is mostly the fixed cost of six stages for a four-line document change. 0 questions, 0.0 h waited.
