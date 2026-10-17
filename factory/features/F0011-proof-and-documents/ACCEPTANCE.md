---
stage: done
pr: 152
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0011-S0001, F0011-S0002, F0011-S0003, F0011-S0004, F0011-S0005, F0011-S0006]
outcome: accepted
---
# Acceptance of Proof and documents

## Verdict

**accepted**, as a recommendation. This is the feature's second acceptance, run after F0011-S0006 and the human's hand-applied S0007. The Goal's "done when" still holds when run whole:

- each of the six kill-point cases, the thirteen fault-injection paths and the fourteen stop rows has a passing test;
- `python -m factory.entry.check_documents` prints `documents ok`;
- `make check` is green.

Both findings of the first acceptance are closed. Its four mutation survivors are killed, and the documents now name the document check and point the operator to the proof. The one new finding is a test gap of the same kind, not a broken promise: fifteen of the eighteen v1 words and one required section name are not pinned by any test. It goes to draft S0007.

## 1 Scope

None. The scope table of the first acceptance stands (the kill-point cases in S0001, the paths in S0002 and S0003, the stop table in S0004, the document check in S0005), and two changes have been added since:

- **F0011-S0006** stays within the feature's scope, the stop table and the document check. It made one production change, in `src/factory/domain/stop_table.py` (commit cae63fc): `_LIMIT` is `re.compile(r"L[0-9]+")` and is called with `fullmatch`. It added four table-wide tests in `tests/domain/test_documents.py` and `tests/domain/test_stop_table.py`. Its edits to earlier tests are exactly those FEATURE decision 22 allows.
- **S0007, applied by hand by the human** (commit 661deb7), has no story file. It is documentation only:
  - the project guide's *The document check*;
  - the fixed section name "The stops of one work item";
  - a paragraph in the operator guide that points to the proof.

Out of scope stayed out. There is no baseline run and no real container kill, and the document check is still neither in the `Makefile` nor a console script.

## 2 Feature demo

**Green.** The walk is the first acceptance's, with one step added (step 5), run again on today's code:

1. Read the proof as data.
2. Run every named test and every case through pytest, reading each result from the JUnit report.
3. Restart each of the six cases outside pytest with `run_case` and check every condition of its class with `violations`.
4. Run the document check on the repository, then on a copy with faults put in.
5. **New:** run the two proof commands exactly as the operator guide and the project guide print them, which is what a reader of the hand-applied S0007 would do.

The script is `/tmp/f11demo2/demo.py`, outside the repository.

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 uv run python /tmp/f11demo2/demo.py 2>&1 | sed "s|/tmp/tmp[a-z0-9_]*|<tmp>|g"
```

```text
== 1. the proof as data ==
kill-point cases: 6 | fault paths: 13 | stop rows: 14
every path arms a known case: True
stop destinations: {'health_status': 7, 'pull_request': 6, 'none': 1}
named tests: 21 (13 paths + 8 distinct stop tests), missing: []
== 2. the proof run: every named test and every case, through pytest ==
pytest: 94 passed, 4 warnings in 45.95s
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
== 5. the operator's and the agent's proof commands, as the documents give them ==
   operator guide: uv run pytest tests/test_kill_points.py tests/test_fault_paths.py tests/test_fault_paths_7_to_13.py
     -> 72 passed in 42.06s (exit 0)
   project guide: uv run pytest tests/test_fault_paths.py tests/test_fault_paths_7_to_13.py tests/test_fault_paths_table.py tests/domain/test_fault_paths.py tests/domain/test_fault_paths_all_rows.py tests/test_fault_path_names.py
     -> 26 passed in 20.05s (exit 0)
```

How the output reads:

- **Steps 1 to 4** read as they did in the first acceptance:
  - a crash is charged exactly where a stage was in flight, and `post-record` charges none (decision 1);
  - the stall charges one attempt and posts twice;
  - the broken copy gives exactly the four expected findings.
- **The four warnings** are still the `record_property` warnings under junit's `xunit2` family. They are now in the human's housekeeping list (section 4).
- **Step 5:** the operator guide's new command runs green, and so does the project guide's command for the paths.

## 3 Mutation score

**31 of 37 killed by hand.** The project still has no `make mutants` target, because `mutmut` is a dependency the human has not yet granted (`planning/overnight/restructure-after-f0011.md`, item 1.3). The pass is again by hand, with the script `/tmp/f11demo2/mutate.py`. It applies one textual mutation at a time, runs the tests covering the module, and restores the file afterwards; the working tree was clean after the run.

The pass has 38 mutations:

- the first acceptance's 28, with M2 rewritten for the new code;
- three new mutations of the limit rule (M29 to M31);
- seven new mutations of the document check's constants (M32 to M38).

M20, a heading filter in `_missing_sections`, is equivalent as before and is not counted.

Killed:

- **The four survivors of the first acceptance**, now closed by S0006:
  - M18: `"run record"` removed;
  - M23: `FAULT_PATHS[:12]`;
  - M27: `KILL_POINT_CASES[:5]`;
  - M2: `fullmatch` → `match`.
- **The new limit mutations:**
  - M29: `[0-9]` → `\d`, killed by `"L٣"`;
  - M30: `+` → `*`, killed by `"L"`;
  - M31: `L` → `[Ll]`, killed by `"l7"`.
- **M28:** `STOP_TABLE[:13]`.
- **M37:** the `none` destination's words changed.
- **Everything the first pass killed**, still killed.

Survivors, one group, all in `src/factory/domain/documents.py` and all going to draft S0007:

```text
M32  SURVIVED  '"max_rounds",' -> ''  [150 passed]
M33  SURVIVED  '"promote",' -> ''  [150 passed]
M34  SURVIVED  '"stages.yml",' -> ''  [150 passed]
M35  SURVIVED  '"control surface",' -> ''  [150 passed]
M36  SURVIVED  '("Kill points", "Fault-injection paths")' -> '("Kill points",)'  [148 passed]
M38  SURVIVED  '"ongoing/",' -> ''  [150 passed]
```

- **`GLOSSARY_FORBIDDEN`:** only `ticket`, `lane` and `drafts/` are reached by any test. The S0005 Interface fixes all eighteen entries.
- **`PROJECT_GUIDE_SECTIONS`:** the section tests are parametrized over the constant itself. They shrink with it, which is why 148 tests ran instead of 150. `OPERATOR_GUIDE_SECTIONS` is held only because two tests happen to name `"Install"`.

I checked by hand that today's code already gives the one expected finding for each of the eighteen entries on its own (`18 entries, mismatches: []`). The draft therefore pins behaviour and needs no code change.

Coverage is unchanged at 99.53 %.

## 4 What the stories noticed

The first acceptance's six items, and what became of each:

- **Items 1, 2, 4 and 5** are in the human's housekeeping list (commit 7c0cc91, `planning/overnight/restructure-after-f0011.md`):
  - the copy in `_rerun_seconds` and `_opening_text`;
  - the redundant `tests/test_fault_path_names.py`;
  - `_rerun` calling `rerun`, and `_branch_state`;
  - the argv redundancy in `check_documents.main`;
  - `record_property` under `xunit2`.

  Nothing for a draft.
- **Item 3, the stale section name**, is fixed by the hand-applied S0007.
- **Item 6** was closed already.

From F0011-S0006's log:

- **The tester (entry 3)** chose not to check the accepted rows' `.limits`, because that would need a `type: ignore`. `isinstance` is checked instead. This is a sound reading of the test rules, and nothing is open.
- **The coder (entry 4)** noticed nothing else.
- **The reviewer (entry 5)** noted that the human's own plan commits came in through the merge of main and were not reviewed. That is correct, and nothing is open.
- **The documenter (entry 6)** saw nothing stale.

## 5 The documentation as a whole

I read `README.md` (29 lines), `docs/operator-guide.md` (1,022), `docs/project-guide.md` (1,641) and `docs/decisions.md` (335), concentrating on what changed since the first acceptance. `check_documents` prints `documents ok`.

What changed is consistent:

- **The document check is described three times, and the three agree:**
  - the project guide's new *The document check* (around line 1607);
  - the README's paragraph;
  - the decision-log entry of F0011-S0005.

  All three give the same sections, the same table-row rule, the exempt section, and the statement that `make check` does not run it.
- **S0006's paragraph on `STOP_TABLE` and `StopRow`** (`docs/project-guide.md:990`) matches the code: a reason exactly when the destination is the health status, and each limit `L` and ASCII digits, compared as the whole text.
- **The operator guide's new pointer to the proof** (in *A restart during a stage*) names a command that runs green (demo step 5). It also names the two project-guide sections that hold the tables.

One small finding, for draft S0007's docs criterion: `docs/project-guide.md:1617` gives the reason `make check` does not run the check as "(F0011, decision 13)". That is a feature file's decision number, which a reader of the guide cannot resolve from `docs/`. The lasting reason is in the decision log's entry of 2026-10-17 (F0011-S0005), and the guide should point there.

Notes from the first acceptance that still need no story:

- the "under construction" opening of the README and the operator guide belongs to the end-to-end run;
- the project guide's planned split, now at 1,641 lines, must repoint `PROJECT_GUIDE`. That is in the human's plan.

## 6 Decisions taken for the human

The first acceptance listed FEATURE decisions 1 to 21 with their sources, and the human merged it, so I do not repeat them here. Still open, or new:

- **Taken by the session for the human, to confirm** (FEATURE.md still says "to confirm" for these):
  - 19: S0004's change to F0006's `RemoteWorkItems.read`;
  - 20: S0003's tester changing S0002's tests;
  - 21: the `test_watch.py` exemption of `documents.py`.
- **22 (new, S0006):** S0006's tester was given leave to move the `X7` row into the new limit test, and to remove the `absent` row from three S0005 tests in `tests/domain/test_documents.py`. I checked the result: the moved row is in `test_a_limit_is_the_whole_text_l_and_ascii_digits`, and the three `absent` cases are now covered for every row by the `test_every_*` tests. Nothing was lost.
- **New, taken by the human outside the pipeline:** S0007 was applied by hand rather than run as a story, so its text had no review or demo stage. This acceptance read it (section 5) and ran its command (demo step 5); one reference repair is proposed.
- **Open questions that remain the human's:**
  - **(a)** Wire the document check into `make check` or into the docs stage's checks in `factory/stages.yml`. The table-wide tests now catch a missing row in the tests' own texts, but not in the real documents; only the command does that.
  - **(b)** The `junit_family` setting for the kill-to-rerun property. It is already in the housekeeping list.
  - **(c)** Grant `mutmut` for a `make mutants` target (item 1.3 of the plan). This feature's two acceptances needed 66 hand mutations between them.

## 7 The slow checks

- Nothing beyond `make check`: no image scan, no SBOM, and no `make mutants` target (section 3).
- `make check` was green as I found it (`check: green`, total coverage 99.53 %).
- The document check outside `make check` prints `documents ok`.

## 8 Cost

The six stories cost 60 runs, 150.1 min and $17.75. The first acceptance is not included; it cost 1 run, 15.7 min and $2.79.

| Story | Runs | Minutes | Cost |
|---|---|---|---|
| S0001 | 19 | 50.1 | $6.68 |
| S0002 | 6 | 12.2 | $1.64 |
| S0003 | 14 | 35.1 | $3.81 |
| S0004 | 6 | 14.3 | $2.13 |
| S0005 | 9 | 23.2 | $2.41 |
| S0006 | 6 | 15.2 | $1.08 |

- **S0006 is the cheapest story of the feature.** It went through every stage once with no send-back and no question: a pre-checked draft (commit 207ad38), a two-line code change, and the human's leave for the test edits given in advance as decision 22.
- **S0001 still stands out** at 38 % of the cost, for the reasons the first acceptance gave:
  - a round lost to test helpers that contradicted built code;
  - three review rounds;
  - v1's send-back cap loop.
- **The hand-applied S0007** cost the factory nothing, and its text was checked only here.

## Proposed stories

- `drafts/F0011-S0007-document-check-word-list-and-sections-pinned.md`: the six mutation survivors. It pins `GLOSSARY_FORBIDDEN` and both section tuples exactly as the S0005 Interface gives them, and tests every v1 word on its own. No code change is expected. Its docs criterion repoints the project guide's "F0011, decision 13" to the decision log.

## Log (append only)

1. acceptor: accepted; 1 draft proposed; make mutants 31/37 (there is no make mutants target, so this is a hand pass: 38 mutations, 1 equivalent and not counted)
   1 Scope: none. F0011-S0006 (limit rule `fullmatch` with `L[0-9]+`, cae63fc, and four table-wide tests) and the human's hand-applied S0007 (661deb7, documentation only) both stay within scope. Out of scope stayed out.
   2 Feature demo: green. All 94 named tests and kill-point runs pass. All 6 cases replay through `run_case` with no violations. `documents ok`, and the broken copy gives exactly the 4 expected findings. New step 5: the proof commands printed in the operator guide and the project guide run green (72 and 26 passed).
   3 Mutation score: 31/37. All four survivors of the first acceptance are now killed, along with three new limit mutants (`\d`, `*`, `[Ll]`). The 6 survivors are all in documents.py: 5 entries of `GLOSSARY_FORBIDDEN` can be removed unnoticed (tests reach only `ticket`, `lane` and `drafts/`), and so can `Fault-injection paths` from `PROJECT_GUIDE_SECTIONS`, because its tests are parametrized over the constant. All go to draft S0007.
   4 Noticed: the first acceptance's items are in the human's housekeeping list (7c0cc91) or fixed by S0007-by-hand. S0006's log leaves nothing open.
   5 Documentation: consistent. The document check is described the same way in the README, the project guide and the decision log. S0006's StopRow paragraph matches the code. The operator's proof pointer runs. One small finding: project-guide.md:1617 cites "F0011, decision 13" instead of the decision log entry; this goes into S0007's docs criterion.
   6 Decisions: 19–21 are still to confirm. 22 (S0006's test edits) was checked, and nothing was lost. S0007 was applied by hand without review or demo; this acceptance checked it. Open for the human: wire the check into make check or stages.yml; junit_family; grant mutmut.
   7 Slow checks: none beyond make check (green as found, 99.53 %). There is no mutants target. The document check prints documents ok.
   8 Cost: 60 runs, 150.1 min, $17.75. S0006 is the cheapest story ($1.08, 6 runs, no send-back): it was pre-checked, needed a two-line fix, and had the test leave given in advance. S0001 is still 38 % of the cost, for the reasons the first acceptance gave.
2. done (pull request merged); cost: 2 runs, 26.4 min, 82 turns, 216k tokens in (5666k more from cache), 59k out, $4.03
