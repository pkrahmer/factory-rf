---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 273
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T16:47:24.438717Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T17:05:43.291998Z'
  stage: acceptance
  run: cd7478727f3f477881c2df41d8913a90
stories: [F0024-S0001, F0024-S0002, F0024-S0003]
outcome: null
---

# Acceptance of Mutation testing per story

## Recommendation

**accepted with stories.** All three stories built what the Scope names. The feature's smoke test drove `make mutants` end to end through the real `MakeProjectCommands` and `command_line` and was green: once complete on a story-form branch, once killed at its time limit. On this acceptance's branch the shortened re-run reached a complete score of 263 killed of 277 in two runs. The findings are smaller than a broken promise. Two rules stated in S0001's Interface have no test (the program name, and the parser's own message in `check_duplicates`). The documents miss the human's later recipe step, a killed report that goes on writing `mutants/`, and the run times measured here. One fact for the human: change 2 (`mutants` as a report in `factory/pipeline.yml`) is not on `main` yet, so the per-story report and the reviewer's reading of it are not live until change 2, and are not shown until change 3.

## 1 Scope

None missing. Each Scope item has a story and the code it names:

- `src/factory/domain/mutants.py`, `src/factory/entry/check_mutants.py`, `src/factory/entry/inputs.py` and `check_duplicates` reading through `read_input`: S0001 (`cbf21db1`).
- `command_line`'s stop note in `src/factory/domain/checks.py`: S0002 (`c96af424`).
- The reviewer's new paragraph in `claude/agents/reviewer.md` and the acceptance reviewer's check 3: S0003. Both texts are in the files exactly; this run's own instructions carry the new check 3, so it reached the image.
- The docs from each story's docs criterion.

No story went outside the scope. `template/` and `demo/` still have the feature-level target (decision 12). `CheckStatus` has no fourth value (decision 3). `factory.adapters.process` is unchanged (decision 4). No story or smoke test made a paid call.

The Goal against what is on `main`:
- The human's change 1 is in: the `Makefile` recipe (`28f5bc0d`), the `CLAUDE.md` *Checks* text, and the `mutants/` permissions (every file there is group-writable).
- The recipe also has one step that `feature.md` does not name: `6dacaef9`, the copy of the files under `src/` that are not Python into `mutants/src` before each run.
- The human's change 2 is not in. `factory/pipeline.yml` still has `check: {time_limit: 15 ...}`, `duplicates: {time_limit: 5}`, no `mutants` report, and `doing: {... reports: [duplicates]}`. So no coder entry carries a `mutants` line yet, and the Goal's "the reviewer reads the story's survivors while the story is still open" waits for change 2. The real check (change 3) is the human's after that.
- This is the planned order, not a gap of the stories.

## 2 Feature smoke test

Green. The walk-through a user of the feature does: a story's coder changes a module, the factory runs the report, the reviewer lists the survivors, and the acceptance re-runs what is left until it is complete.

The story part ran in a throwaway clone under `$TMPDIR`, because a stage may not switch its own branch:
- a bundle of this checkout, cloned;
- HEAD pointed at `work-item/F0024-S9999` with `git symbolic-ref`;
- one comment line appended to `src/factory/entry/inputs.py`;
- a copy of the checkout's `.venv` with its editable path pointed at the clone's `src`, and `UV_NO_SYNC=1`. An offline `uv sync` failed: the cache lacks semgrep's wheels and hatchling.

The script ran the real entry points:

```python
limit = timedelta(seconds=float(sys.argv[1]))
result = MakeProjectCommands(Path.cwd()).run("mutants", time_limit=limit)
print(f"status={result.status} exit={result.exit_status} seconds={result.duration.total_seconds():.0f}")
print(command_line(result))
```

```
--- 1. the report after a story's coder, on work-item/F0024-S9999 with inputs.py changed (limit 600 s)
status=passed exit=0 seconds=439
`mutants`: mutants: 2 killed, 2 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 4 mutant(s) in 1 module(s)
--- 2. the survivors of the story's module, as the reviewer lists them
    factory.entry.inputs.x_read_input__mutmut_1: survived
    factory.entry.inputs.x_read_input__mutmut_3: survived
--- 3. the same report killed at a 3 s limit, MUTANTS_SECONDS=20
status=time_limit exit=None seconds=3
`mutants`: ⠙ Listing all tests  (stopped at its time limit after 3 s)
```

Repeated with `MUTANTS_SECONDS=60`, then `ps` right after the return:

```
status=time_limit exit=None seconds=3
`mutants`: ⠙ Listing all tests  (stopped at its time limit after 3 s)
 335851  335851       2 timeout 60 uv run mutmut run factory.entry.inputs.*
 335853  335851       2 uv run mutmut run factory.entry.inputs.*
 335856  335851       2 /work/checkout/.venv/bin/python .../repo/.venv/bin/mutmut run factory.entry.inputs.*
```

The acceptance part ran in this checkout, `make mutants` on `work-item/F0024-A0001` (section 3): run 1 partial, run 2 complete.

What the smoke test shows:
- The story form takes exactly the changed module. The last line is `check_mutants`'s, and the journal line is the one decision 10 promised.
- A cold `mutants/` cost 439 s for 4 mutants, close to the 540 s stop.
- A report killed at its limit gets S0002's note. Its last line is a mutmut progress spinner, as S0002's Description expected.
- One contradiction with `feature.md`'s decision 4, which says the factory "waits until `timeout` ends it". The adapter returned at 3 s, and mutmut went on in `timeout`'s own process group. The recipe's temporary folder of each killed run stayed under `$TMPDIR`, as decision 13 predicts.
- In practice this is narrow: on a story's branch mutmut starts within seconds and stops at 540 s, before the 600 s kill. It is listed under 6, and the documents get it in F0024-S0005.

The rule's `rm -rf` of my temporary folder was refused by the run's permission system. The clone, about 1 GB, is left in `$TMPDIR`, which the factory removes after the run. No process was left running.

## 3 Mutation score

`make mutants` on this branch (`FEATURE=F0024`, five modules: `factory.domain.checks`, `factory.domain.mutants`, `factory.entry.check_duplicates`, `factory.entry.check_mutants`, `factory.entry.inputs`).

Run 1, its last line:

```
mutants: partial, 246 killed, 14 survived, 0 timed out, 0 without tests, 17 not checked, 0 other of 277 mutant(s) in 5 module(s)
make: *** [Makefile:111: mutants] Error 1
```

The 17 `not checked` were `factory.domain.checks.x_command_line__mutmut_1` to `_17`. mutmut reset them because S0002 changed `command_line`, and the run had no name for them yet: decision 2's reset at the acceptance, taken in by the next run's list.

Run 2, 12 s:

```
mutants: 263 killed, 14 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 277 mutant(s) in 5 module(s)
```

**Score: 263 killed of 277, complete (not partial), two runs.**

The survivors, read with `uv run mutmut show`, in groups:

- **A. The commands' program name** (rule stated, no test):
  - `check_mutants.x__parser__mutmut_2` and `check_duplicates.x_main__mutmut_2`: `ArgumentParser(prog=None)`.
  - S0001's Interface says "The program name is `check-mutants`". No test looks at argparse's usage line.
  - → F0024-S0004.
- **B. The reasons in the fault lines** (message texts, one rule stated):
  - `check_mutants.x__at_least_one__mutmut_3` and `_6`: `ArgumentTypeError(None)` for `not an integer: 'soon'` and `must be at least 1, not 0`. Criterion 10 checks only the exit status 2.
  - `check_duplicates.x__findings__mutmut_6` and `_7`: `UnreadableInput(None)` and `UnreadableInput(str(None))`. This is a line S0001 wrote, and its Interface says a parse fault keeps "the parser's own message". `test_an_unreadable_input_prints_one_error_line_and_returns_two` checks only the prefix `check-duplicates: `.
  - → F0024-S0004.
- **C. Equivalent, no story:**
  - `inputs.x_read_input__mutmut_1` and `_3`, and `check_duplicates.x__write_baseline__mutmut_5`, `_7` and `_11`: `encoding=None`, `"UTF-8"` or no argument, which is the same in a UTF-8 container. `_write_baseline`'s line predates F0024.
  - `check_mutants.x_main__mutmut_3` and `check_duplicates.x_main__mutmut_34`: `argv` passed as `None`, which argparse reads as `sys.argv[1:]` itself.
  - `mutants.x__parse_line__mutmut_3`: `partition` for `rpartition`. A name can hold no colon, so a line with two `": "` is refused either way, with the same message.

Passed on by the stories' reviews: none. No archived coder entry has a `mutants` line, because change 2 is not in. S0003's reviewer said so in its entry 9. So all three groups are new. `factory.domain.checks` (S0002) and `factory.domain.mutants`'s rules have every other mutant killed.

## 4 What the stories noticed

- S0001 coder (entries 7 and 15): the smoke-test blocks were not run, because the permission system refused their `rm -rf` of the temporary folder. The same refusal hit this acceptance. Nobody owns it: the story form prescribes `trap 'rm -rf "$d"' EXIT` for every smoke test, and an agent's own run cannot use it. The smoke tester's runs did run the blocks, through `bash -c`. Listed under 6.
- S0001 reviewer, note 1: the two sides of `--stopped-after`'s "at least 1" are in two test functions. A test-structure note; F0024-S0004 adds the refusals' texts as rows of one test, which brings both sides together.
- S0001 reviewer: `make duplicates` reports 5 new findings, all in `claude_runtime`/`opencode_runtime` and `clock.py`. S0002's reviewer saw the same. These are not this feature's, and are left to the baseline's owner.
- S0001 documenter: the stage forbids reading `feature.md`, so the decision entry *A mutation run's report is a line of its own…* was written from the story alone, and the human may want to compare its wording with decisions 2, 3 and 8. I compared them. The entry agrees, and it names the three rejected alternatives. Nothing to repair.
- S0001 documenter: the stale `CLAUDE.md` sentence on "a second run goes on". It is gone with change 1.
- S0002 documenter: also changed `docs/project-guide/stages.md` (step 4), which the criterion did not name, and the operator guide's "the line has the same form either way". Both are correct.
- S0003 coder: smoke grep 5 waits for the docs. It printed 1 at the smoke test.
- S0003 documenter: none.

## 5 The documentation as a whole

Read `README.md` (no mention of mutants; right for a newcomer), `docs/operator-guide.md` *The mutation report of a story* and point 3 of *What a stage run shows*, `docs/project-guide/processes-and-checks.md` *Mutation testing*, and the three new entries in `docs/decisions.md`. No contradiction between stories was found, and no example that no longer runs: S0001's examples ran here as documented. Gaps:

1. The recipe's step from `6dacaef9`, which copies the files under `src/` that are not Python into `mutants/src`, is in no document. → F0024-S0005.
2. A report killed by the factory's limit returns while mutmut goes on writing `mutants/`, and its temporary folder stays (section 2). The documents say only that the kill "does not reach mutmut". → F0024-S0005.
3. *How long it takes* gives "a fixed 165 s". Today's warm acceptance run took 12 s in all (stats kept in `mutants/mutmut-stats.json`), and a cold story run of 4 mutants took 439 s. → F0024-S0005.
4. Both guides already say that "the factory runs it as a report after the coder (`mutants` in `factory/pipeline.yml`)", and `factory/pipeline.yml` does not have it until change 2. This becomes true with change 2, so no story is proposed for it. If change 2 waits, a reader is told of a report that does not run.

## 6 Decisions taken for the human

To accept or revisit:

1. `feature.md`'s decisions 1 to 18, as written there. They are borne out except decision 4's "the factory waits until `timeout` ends it": the adapter returned at its limit and mutmut ran on (section 2).
   - Options: keep the recipe and only document it (F0024-S0005; my choice, because on a story's branch the 540 s stop comes before the 600 s kill); `timeout --foreground` in the human's recipe, so the kill reaches mutmut; or the gentler stop that decision 4 rejected.
2. The human's change 2 is not on `main` and is due now: S0002 and S0003 are merged, and `self` needs its rebuild first. Change 3 follows.
3. The recipe's extra step `6dacaef9` (not in `feature.md`'s change 1). Accept it as the human's own; S0005 documents it.
4. S0001's reviewer added criterion 12 (`read_input`'s chaining) to the story on its own, from intake's noted gap, and the tester wrote its test. This is within a reviewer's remit, but it is a criterion no human wrote.
5. S0001's coder checks `--stopped-after` in an argparse type function, so 0 and non-integers end through argparse (exit 2, usage line), while `mutation_report` keeps its own `ValueError` for other callers. The domain check is therefore never reached from the command.
6. S0002's coder put the stop note as an early return ahead of the reuse note. A reused result is always `passed`, so the two notes never meet.
7. S0003's documenter marked *Mutation testing is limited to one feature's modules* "Superseded by *Mutation testing per story*" on its date line.
8. The smoke-test form's `trap 'rm -rf "$d"' EXIT` is refused by the permission system in coder and acceptance runs (section 4). A question for the human on `.claude/settings.json` or on the form.

Earlier tests changed: none. All three reviews say "Earlier tests: none", every test file in their diffs has status `A`, and `tests/entry/test_check_duplicates.py` passed unchanged (S0001 criterion 11). No change without a leave.

## 7 The slow checks

- Nothing beyond `make check` and `make mutants`: factory-rf has no image scan or SBOM target.
- `make check` was green as I found it: `test: green (42.0 s)`, coverage 99.07 %, `check: green`.
- From `.reports/junit.xml`: 5,927 tests, 461.3 s summed over the workers. The slowest are two 5.0 s tests: `tests.adapters.test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` and `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`. Next is `tests.test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[accepted]` at 3.6 s. None is this feature's.
- The feature's 66 tests take 0.68 s together; the slowest is `test_a_report_stopped_at_its_time_limit_says_so_in_the_entry` at 0.56 s.
- Disk:
  - At the previous record (`disk start`): /work 978.3 GB free, 0.5 GB used; /state 978.3 GB free, 0.0 GB used; /tmp 978.3 GB free, 0.0 GB used.
  - Now (`disk acceptance`): 978.2 GB free and the same used figures.
  - Used is unchanged on every mount. The 0.1 GB of free space is shared with the host, so it is not the feature's. No unexplained growth.
  - `mutants/mutmut-stats.json` is 26 MB in the checkout, within /work's 0.5 GB.

## 8 Cost

- `Cost of the stories`: 23 runs, 18.6 min, 155 turns, 558,849 tokens in (3,152,408 more from cache), 68,036 out, $5.40.
- S0001 stands out with 10 runs, 10.0 min and $3.03, more than half of the cost. Its journal says why: the review of round 0 found that criterion 1's two sides were two test functions, and added criterion 12. That took a coder round that only handed over (entry 11), a tester round and a second coder and review round.
- S0002: 6 runs, 3.7 min, $1.07.
- S0003: 7 runs, 4.9 min, $1.30. One extra docs run after a stall: `make documents` refused the v1 word "ticket" in `processes-and-checks.md` (entry 12).
- `Human interventions of the stories`: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `backlog/F0024-S0004-the-fault-lines-of-check-mutants-and-check-duplicates-are-pinned.md`: tests for survivor groups A and B. The program name in both commands, the reasons of `--stopped-after`'s refusals, and `check_duplicates`'s parse-fault message, which S0001's Interface states and no test notices breaking. No code change.
- `backlog/F0024-S0005-the-documents-describe-the-mutation-report-as-it-runs.md`: the documentation repair of section 5, items 1 to 3. The recipe's copy of the files under `src/` that are not Python, a killed report whose mutmut goes on writing `mutants/`, and the warm and cold run times measured here.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed; make mutants 263/277
   1 Scope: every Scope item has its story and its code. The human's change 1 is on `main`, plus `6dacaef9`, a recipe step `feature.md` does not name. Change 2 (`mutants` as a report in `factory/pipeline.yml`) is not on `main` yet, so the per-story report is not live until it is applied.
   2 Smoke test: green. In a clone on `work-item/F0024-S9999`, `MakeProjectCommands.run("mutants")` followed by `command_line` gave `` `mutants`: mutants: 2 killed, 2 survived, ... of 4 mutant(s) in 1 module(s) `` (439 s, cold `mutants/`). Killed at 3 s, the line ended `(stopped at its time limit after 3 s)`, but mutmut kept running in `timeout`'s own process group, against `feature.md`'s decision 4.
   3 Mutants: complete after 2 runs, 263 killed of 277. Run 1 was partial with 17 `command_line` mutants not checked; mutmut had reset them, as decision 2 expects. New groups: program name (A) and fault reasons (B), both to F0024-S0004; the rest are equivalent (C). No review had passed any on as notes, because no coder entry has a `mutants` line yet.
   4 Noticed: the permission system refuses the `trap 'rm -rf "$d"' EXIT` that the smoke-test form prescribes, in coder runs and in this run. Everything else noticed was handled or not this feature's.
   5 Docs: the copy of the non-Python files under `src/` (`6dacaef9`), a killed report that keeps writing `mutants/`, and the run times measured here (fixed 165 s documented; 12 s warm and 439 s cold measured) are missing; F0024-S0005 adds them. Both guides already name a `mutants` report that only change 2 adds.
   6 Decisions: `feature.md` decisions 1 to 18 hold, except decision 4's claim that the factory waits for mutmut. Also for the human: change 2 is due, the `6dacaef9` step, criterion 12 added by S0001's reviewer, argparse's check of `--stopped-after`, and the refused `rm -rf` trap. No earlier test was changed.
   7 Slow checks: none beyond `make check` (green as I found it, 99.07 %) and `make mutants`. The slowest tests take 5.0 s and none is the feature's; its 66 tests take 0.68 s. Disk used is unchanged on every mount.
   8 Cost: 23 runs, 18.6 min, $5.40. S0001 cost $3.03 of it, after a review round on test structure that added criterion 12. S0003 needed one extra docs run after a stall on the word "ticket". 0 questions to the human, 0.0 h waited.
