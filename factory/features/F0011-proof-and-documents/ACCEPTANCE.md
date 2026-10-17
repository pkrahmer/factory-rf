---
stage: done
pr: 150
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0011-S0001, F0011-S0002, F0011-S0003, F0011-S0004, F0011-S0005]
outcome: accepted
---
# Acceptance of Proof and documents

## Verdict

**accepted with drafts**, as a recommendation. All four scope items are built, and the Goal's "done when" holds when run whole: each of the six kill-point cases, each of the thirteen fault-injection paths and each of the fourteen stop rows has a test that passes. Run in full by the feature demo, all six cases show no violation of their condition list. `python -m factory.entry.check_documents` prints `documents ok`, and `make check` is green. Nothing found breaks a promise. Two findings are worth a story each:

- A hand mutation pass found four survivors. Three are gaps where the document check's tests look at only one row or one list, and the fourth is a `StopRow` limit rule that accepts `"L7\n"` (draft S0006).
- The project guide never tells the next agent about the document check, although `make check` does not run it. It also keeps one stale section name (draft S0007).

## 1 Scope

None. Each scope item maps to stories and code:

| Scope item | Stories | Code and tests |
|---|---|---|
| Six kill-point cases with the crash and stall pass lists and both caps | S0001 | `src/factory/domain/kill_point_cases.py`; `tests/test_kill_points.py`, `tests/proof_support.py`, `tests/domain/test_kill_point_cases.py` |
| Thirteen fault-injection paths, `reject` walked | S0002 (1–6), S0003 (7–13) | `src/factory/domain/fault_paths.py`; `tests/test_fault_paths.py`, `tests/test_fault_paths_7_to_13.py`, `tests/test_fault_paths_table.py` and two domain tests |
| The stop table, one test per row | S0004 | `src/factory/domain/stop_table.py` (14 rows); `tests/test_stop_table.py`, `tests/domain/test_stop_table.py` |
| The four documents and their check | S0005 | `src/factory/domain/documents.py`, `src/factory/entry/check_documents.py`; the four documents pass |

No story went outside the scope. One production change outside F0011's own modules is S0004's change to `RemoteWorkItems.read` (`src/factory/application/work_items.py`, commit 49a4329): a duplicate id is now read from `origin/main`. That is the "defect to fix under `src/`" the Assignment allows, and FEATURE decision 19 records it for the human to confirm.

Out of scope stayed out:

- no baseline run;
- no real container kill;
- the machine stops are proved through `StopService` and a source search, not through their producers (decision 12);
- the document check is neither in the `Makefile` nor a console script.

One reading to be aware of: "a test for each row" is met for the seven health-status rows by one test parametrized over all seven (7 runs, one per reason). The other seven rows each have their own test.

## 2 Feature demo

**Green.** The walk goes the way the operator and the next agent would check the feature's promise:

1. Read the proof as data and check that every test the tables name exists.
2. Run every named test and every kill-point case through pytest and read each one's result from the JUnit report.
3. Play each of the six kill-point cases once more outside pytest with `run_case`. After the restart, check every condition of its class with `violations`. This includes `kill-to-rerun-recorded`, which no test reaches (section 4).
4. Run the document check on the repository, then on a copy with three faults put in: a removed stop row, a `--follow` sentence with a v1 word in the README, and a renamed case in the project guide.

The script is `/tmp/f11demo/demo.py`, outside the repository. It uses `tests/proof_support.py` through `PYTHONPATH=tests` and `tempfile.TemporaryDirectory()` for every world and copy.

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 uv run python /tmp/f11demo/demo.py 2>&1 | sed "s|/tmp/tmp[a-z0-9_]*|<tmp>|g"
```

```text
== 1. the proof as data ==
kill-point cases: 6 | fault paths: 13 | stop rows: 14
every path arms a known case: True
stop destinations: {'health_status': 7, 'pull_request': 6, 'none': 1}
named tests: 21 (13 paths + 8 distinct stop tests), missing: []
== 2. the proof run: every named test and every case, through pytest ==
pytest: 94 passed, 4 warnings in 38.43s
   path  1 agent-run-tick  pass
   path  2 commit-push     pass
   path  3 post-record     pass
   path  4 agent-run-dies  pass
   path  5 tick-other      pass
   path  6 agent-run-dies  pass
   path  7 post-record     pass
   path  8 agent-run-dies  pass
   path  9 commit-push     pass
   path 10 tick-other      pass
   path 11 tick-other      pass
   path 12 container       pass
   path 13 agent-run-tick  pass
   stop fetch-failed                 -> health_status pass (7 run(s) of its test)
   stop checkout-restore-failed      -> health_status pass (7 run(s) of its test)
   stop pipeline-definition-invalid  -> health_status pass (7 run(s) of its test)
   stop agent-definition-invalid     -> health_status pass (7 run(s) of its test)
   stop repository-unavailable       -> health_status pass (7 run(s) of its test)
   stop main-branch-failing          -> health_status pass (7 run(s) of its test)
   stop preflight-failed             -> health_status pass (7 run(s) of its test)
   stop duplicate                    -> pull_request  pass (1 run(s) of its test)
   stop pull-request-lookup          -> pull_request  pass (1 run(s) of its test)
   stop ask-without-pull-request     -> pull_request  pass (1 run(s) of its test)
   stop handler-error                -> pull_request  pass (1 run(s) of its test)
   stop hand-over-error              -> pull_request  pass (1 run(s) of its test)
   stop push-rejected                -> pull_request  pass (1 run(s) of its test)
   stop later-stage-in-backlog-file  -> none          pass (1 run(s) of its test)
   kill-point tests: 18 functions, 56 runs, all pass: True
== 3. each case restarted, every condition of its class checked in full ==
2026-10-12T12:00:05Z discarded uncommitted changes: factory/features/F0001-example/in-progress/F0001-S0001-first.costs.jsonl, factory/features/F0001-example/in-progress/F0001-S0001-first.md, src/leak.py
   agent-run-tick  killed at agent-run    stage=intake crashes=1 attempts=0 blocked=question posts=1 violations=[]
   agent-run-dies  killed at None         stage=intake crashes=0 attempts=1 blocked=question posts=2 violations=[]
   commit-push     killed at before-push  stage=intake crashes=1 attempts=0 blocked=question posts=1 violations=[]
   post-record     killed at after-post   stage=intake crashes=0 attempts=0 blocked=question posts=1 violations=[]
   tick-other      killed at after-push   stage=intake crashes=1 attempts=0 blocked=question posts=1 violations=[]
   container       killed at agent-run    stage=intake crashes=1 attempts=0 blocked=question posts=1 violations=[]
== 4. the four documents ==
   repository: documents ok (exit 0)
   broken copy (exit 1):
     README.md: describes a replaced behaviour: '--follow'
     README.md: uses the v1 word 'ticket'
     docs/operator-guide.md: stop 'fetch-failed' has no table row with its destination
     docs/project-guide.md: kill point case 'post-record' has no table row
```

How the output reads:

- **Charged crashes.** The crash is charged exactly where a stage was in flight. `post-record` charges none, by decision 1.
- **The stall.** It charges one attempt and posts twice: the stall note, then the question.
- **The log line in step 3.** It is the factory log of the `agent-run-tick` restart, which writes to standard output as well.
- **The four warnings.** They come from `record_property` under pytest's default `junit_family` (section 4).
- **The broken copy.** It gives exactly the four findings expected, in the check's order.

## 3 Mutation score

**23 of 27 killed by hand.** The project has no `make mutants` target: `mutmut` is not a dependency, and adding it is the human's call (`planning/overnight/restructure-after-f0011.md`). As in earlier acceptances, I applied 28 single mutations by hand to F0011's production code. Each mutation ran against the tests that cover its module, and each file was restored afterwards. One mutation is equivalent and is not counted: a heading filter in `_missing_sections`. The script is `/tmp/f11demo/mutate.py`.

Killed:

- `kill_point_cases.py`: both validators weakened.
- `stop_table.py`:
  - the reason-against-destination rule weakened;
  - the empty-limits check dropped;
  - one row's limit changed.
- `documents.py`:
  - `all` → `any` in `_has_row`;
  - both word-boundary halves;
  - the exempt section;
  - the decision-log rule;
  - blank text against empty text;
  - letter case of the phrases and of the rows;
  - row prefix `startswith` → `in`;
  - code fences ignored;
  - the destination word dropped from the stop row;
  - `"ticket"` removed from `GLOSSARY_FORBIDDEN`;
  - a required section removed;
  - the last stop row skipped.
- `check_documents.py`: the exit status; the default root.
- `work_items.py`: the duplicate read turned off.
- `kill_point_cases.py`: one row's `charges_crash`.

The four survivors fall into two groups, and both go into draft S0006:

- **The document check's tests check one row and one list.**
  - Removing `"run record"` from `REPLACED_PHRASES` survives. The test runs one case per phrase over the constant itself, so it shrinks along with the list, and nothing pins the tuple the S0005 Interface gives.
  - Checking only `FAULT_PATHS[:12]` survives, and so does checking only `KILL_POINT_CASES[:5]`. The row rules are tested on path 7 and on case `commit-push` only, so a check that skips the last path or the last case passes.
- **The `StopRow` limit rule.**
  - `^L\d+$` → `^L\d+` survives, because no test has a limit with a valid prefix and a trailing extra, such as `L7x`.
  - Checking by hand also showed a real gap. `_LIMIT.match` with `$` accepts `"L7\n"`, because `$` matches before a final newline. The make class has had the same trap fixed with `fullmatch` (F0001-S0017).

Coverage: 99.53 %. One F0011-touched line is uncovered: `src/factory/application/work_items.py:133`, the `missing on origin/main` raise in `_started_document`. It cannot be reached while `read` lists the files from `origin/main`. It is defensive, so no draft.

## 4 What the stories noticed

Collected from the five logs, each with where it goes:

1. **S0001 reviewer, entries 17, 19 and 21, left open by the human's answer in entry 20.** `tests/test_kill_points.py::_rerun_seconds` copies `proof_support`'s claim-commit logic. Because of it, no test reaches the `kill-to-rerun-recorded` condition (the demo's step 3 now has, and it holds for all five crash cases). Also, `_opening_text` returns a `WorkItemDocument`. The human has already assigned both to the housekeeping story in `planning/overnight/restructure-after-f0011.md`, so there is no draft.
2. **S0003 coder (entries 8 and 14) and reviewer (entry 15).**
   - `tests/test_fault_path_names.py` checks only `FAULT_PATHS[:6]`. It is now fully covered by `tests/test_fault_paths_table.py`, which checks all thirteen, so the module is redundant.
   - The private `_rerun` in `tests/proof_support.py` could call the public `rerun`.
   - `tests/test_fault_paths_7_to_13.py::_branch_state` repeats `_state_at`.

   These are test-helper housekeeping of the same kind as item 1. I propose that the human add them to that story's list, not a separate draft.
3. **S0004 documenter, entry 6.** `docs/project-guide.md:988` cites the operator guide section "Stops of one work item". It has been "The stops of one work item" since S0004. Draft S0007.
4. **S0005 reviewer, entry 9.** `sys.argv[1:] if argv is None else argv` in `check_documents.main` repeats what argparse does. It is too small for a story; it belongs with the housekeeping duplicates.
5. **Found by this acceptance's demo.** `test_the_rerun_starts_five_seconds_after_the_kill` calls `record_property("kill_to_rerun_seconds", …)`, which decision 2 calls "recorded as a test property". `make test` writes no JUnit report, so the value goes nowhere. With `--junitxml`, pytest's default `junit_family` (`xunit2`) drops it with a `PytestWarning` (four warnings in the demo). This matters for the telemetry plan, which wants a JUnit report with a time per test: the property only appears with `junit_family=legacy` or `xunit1`. The assertion of 5.0 s is what proves criterion 8, so nothing is wrong today. This is for the human, under 6.
6. **S0003 coder, entry 4.** The cost sidecar beside the work item made two test selections ambiguous, and they were fixed by taking the `.md` file only. `CLAUDE.md`'s Tests rule already names the sidecar. Nothing open.

## 5 The documentation as a whole

I read `README.md` (29 lines), `docs/operator-guide.md` (1,020), `docs/project-guide.md` (1,629) and `docs/decisions.md` (335) from the top, and the document check passes on all four. Three findings, all for draft S0007:

- **The project guide does not mention the document check.** Only the README and the decision log name it. `make check` does not run it, so a later story can add a stop row, a kill-point case or a fault-injection path, or reword a guide, and break `documents ok` without anyone noticing. The next agent finds the tables in the guide but not the rule that keeps them complete.
- **Stale section name.** `docs/project-guide.md:988` cites the operator guide section "Stops of one work item" (item 3 of section 4).
- **The operator is not pointed to the proof.** The Goal names the operator as the reader who "must trust a restart". The operator guide's "A restart during a stage" explains what a restart does but not that it is proved, or where the proof is. The proof is only in the project guide's *Kill points* and *Fault-injection paths* sections.

No contradictions between stories:

- The operator guide's *The stops* table matches `STOP_TABLE` row for row (the check confirms it).
- The kill-point and fault-path sections match the code, including path 5's crash charge differing from its case.
- The decision log entries of S0001 to S0005 agree with each other and with the guides.

Notes that need no story:

- The README and the operator guide still open with a long list of built parts and "under construction". That is still true until the end-to-end run. Rewriting them belongs to that run.
- The project guide is at 1,629 lines. The human's planned split (at about 1,800 lines, or in the housekeeping story) must point `PROJECT_GUIDE` at the index, as the plan already says.

## 6 Decisions taken for the human

From `FEATURE.md` (numbered as there), to accept or revisit:

- **Kill-point cases (S0001).**
  - 1: a kill after the result's push charges no crash.
  - 2: kill to rerun is exactly 5 s on the manual clock. It is "recorded as a test property", but see section 4, item 5.
  - 3: each interrupted stage ends its run with a `question`.
  - 4: "any other point" is `AFTER_PUSH` with `after=0`.
  - 5: the crash cap is reached by two kills in one stage.
- **Fault-injection paths (S0002 and S0003).**
  - 6: one kill or stall per path, by judgment.
  - 7: path 1's second half is walked by the story form check.
  - 8: path 13 counts no round.
  - 9: path 11 uses a close without a comment.
  - 10: the four extra run-1 paths are noted in the project guide, not rows.
  - 17: the paths are split over two stories.
  - 18: a path's crash charge may differ from its case's.
- **The stop table (S0004).**
  - 11: fourteen rows; L11 is a row with destination `none`.
  - 12: a work item's stop is reported once, after the error cap of 3. The machine stops are proved through the stop service and a source search.
- **The document check (S0005).**
  - 13: a domain function plus `python -m`, not in `make check`, no console script.
  - 14: the decision log is exempt from both word lists.
  - 15: the guides' rows are found by the id in backticks on a `|` line outside code fences.
  - 16: one exempt section, `## Replaced from v1`.
- **Taken by the session for the human, still to confirm.**
  - 19: S0004 changed F0006's `RemoteWorkItems.read`, so that a second in-progress file of an id is read from `origin/main`.
  - 20: S0003's tester changed S0002's tests to remove the duplicated `world`, `work_item` and `_rerun`.
  - 21: `tests/entry/test_watch.py`'s follow-mode search skips `src/factory/domain/documents.py` and its `.pyc` by name.

From the story logs:

- **S0001, entry 5.** Two test helpers contradicted built behaviour, and they were fixed in `tests/proof_support.py`, not in `src/`. `GitCli.show_file` keeps raising for a missing ref, and the reader keeps refusing a text without front matter.
- **S0001, entry 20.** Past the send-back cap, v1's "one more round" answer could not work. The story went forward with two group-4 findings open, and they were moved to the housekeeping story. The human's plan records the v1 cap behaviour as something to check in v1.1.
- **S0003, entry 5.** The cost sidecar stays beside the work item, and tests select the `.md` file.

Open questions this acceptance does not decide:

- **(a)** Wire the document check into `make check`, or into the docs stage's checks in `factory/stages.yml`. Both are the human's files. Draft S0007 only documents the command for agents.
- **(b)** Whether `record_property` should keep reporting the kill-to-rerun time once a JUnit report exists, which means `junit_family = "legacy"` in `pyproject.toml`, or drop the claim of decision 2.
- **(c)** The replaced-phrase list is fixed in code: a behaviour that a later item replaces is only flagged if a story adds it to `REPLACED_PHRASES`. This is a property of the design, not a defect.

## 7 The slow checks

- Nothing beyond `make check`: no image scan, no SBOM, no `make mutants` target (section 3).
- The one check this feature adds outside `make check` is `python -m factory.entry.check_documents`. Run on the repository during this acceptance, it printed `documents ok`.
- `make check` was green as I found it (`check: green`, coverage 99.53 %).

## 8 Cost

The five stories cost 54 runs, 134.9 min and $16.67, or $3.33 per story on average.

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 19 | 50.1 | $6.68 |
| S0002 | 6 | 12.2 | $1.64 |
| S0003 | 14 | 35.1 | $3.81 |
| S0004 | 6 | 14.3 | $2.13 |
| S0005 | 9 | 23.2 | $2.41 |

**S0001 stands out at 40 % of the cost**, and its log says why:

- It lost one round to two test helpers that contradicted behaviour already built: `show_file` on a missing ref, and a front-matter-less commit on `main`. That is the test-data rule `CLAUDE.md` gained on 2026-10-16 because of it.
- Three review rounds tightened criterion 7 and criterion 11 (the first tick, all six cases).
- Two more rounds went to v1's cap loop: past the cap, "one more round" sends back and asks again. The human ended it in entry 20.

**S0003 is second.** It needed two questions, the sidecar selection and the duplicated helpers, and the second was answered with leave to change S0002's tests.

**S0002 and S0004 went through without a send-back**, at 6 runs each.

## Proposed stories

- `drafts/F0011-S0006-document-check-and-stop-limits-pinned-in-full.md`: the four mutation survivors. It pins `REPLACED_PHRASES` exactly, tests the row rules over every case, path and stop rather than one example each, and refuses a `StopRow` limit with a trailing newline or extra characters (`fullmatch`).
- `drafts/F0011-S0007-documentation-after-the-proof.md`: the project guide gets the document check and when to run it, its stale section name is fixed, and the operator guide's restart section points to the proof.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants 23/27 (there is no make mutants target, so this is a hand pass: 28 mutations, 1 equivalent and not counted)
   1 Scope: none. All four scope items are built (S0001 the kill-point cases and both caps, S0002/S0003 the 13 paths, S0004 the 14 stop rows, S0005 the document check). Out of scope stayed out. S0004's change to F0006's `RemoteWorkItems.read` is a defect fix, recorded as decision 19. The 7 health-status rows share one test parametrized over all 7.
   2 Feature demo: green. Every named test passes (94 passed). All 6 cases replayed through `run_case` show no violations of their full condition lists, `kill-to-rerun-recorded` included. The check prints `documents ok`, and on a copy with three faults put in it gives exactly the 4 expected findings.
   3 Mutation score: 23/27 killed. The survivors: `REPLACED_PHRASES` is not pinned; the row rules are tested only for case `commit-push` and path 7 (the last case or last path can be skipped); the `StopRow` limit pattern without `$` passes. Checking by hand also showed `"L7\n"` is accepted (`match` with `$`). All go to draft S0006.
   4 Noticed: S0001's open findings (`_rerun_seconds` copy, dead check, `_opening_text`) are already in the human's housekeeping plan. Proposed additions to that plan: the redundant `tests/test_fault_path_names.py`, `_rerun` calling `rerun`, `_branch_state`, and the argv redundancy in `check_documents.main`. `record_property` reaches no report: it is dropped under junit xunit2. The stale guide reference goes to S0007.
   5 Documentation: no contradictions. The project guide never mentions the document check, which `make check` does not run. `project-guide.md:988` names the old section "Stops of one work item". The operator guide's restart section does not point to the proof. All three go to draft S0007.
   6 Decisions: FEATURE decisions 1–18 listed for review. Decisions 19–21, taken by the session for the human, are still to confirm. Log answers: S0001 entries 5 and 20, S0003 entry 5. Open for the human: wiring the check into `make check` or `stages.yml`; junit_family for the kill-to-rerun property.
   7 Slow checks: none beyond `make check` (green as found, 99.53 %). There is no mutants target. The document check prints `documents ok`.
   8 Cost: 54 runs, 134.9 min, $16.67. S0001 is 40 % of it ($6.68, 19 runs): a round lost to test helpers that contradicted built code, three review rounds tightening criteria 7 and 11, and v1's send-back cap loop. S0003 is next ($3.81, two questions).
2. done (pull request merged); cost: 1 runs, 15.7 min, 52 turns, 147k tokens in (4276k more from cache), 38k out, $2.79
