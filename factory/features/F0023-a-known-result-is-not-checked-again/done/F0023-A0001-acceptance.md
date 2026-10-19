---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 269
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T15:24:23.097703Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T16:01:42.952731Z'
  stage: acceptance
  run: 9a0ab49b8d8b4d7296bd2c6789d7296e
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T16:02:29.658784Z'
  stage: done
stories: [F0023-S0001, F0023-S0002]
outcome: accepted
---

# Acceptance of A known result is not checked again

## Recommendation

**accepted with stories.** S0001 and S0002 together build everything in the Scope, and nothing outside it. The feature smoke test, run on factory-rf's own pipeline definition with the human's change 1 applied, is green: the docs stage reused the doing stage's `check` with the journal line the feature promised, it ran `secrets` and `documents`, and the operator guide's count command counted the tree once. `make check` is green and, of the functions the feature added or changed, every mutant was checked; three survivors there are real gaps. Three small stories are proposed: two pin those gaps with tests (no code change expected), and one repairs an operator-guide example that contradicts the guide's own reasoning. None of them is a broken promise. The real check, the human's change 3, is still to come and is the human's.

## 1 Scope

None. Every Scope item has its story, and the code is where `feature.md` puts it:
- `TreeId` is in `src/factory/domain/git.py`.
- `Git.work_tree_id` is in `src/factory/application/git.py`, and `GitCli.work_tree_id`, with a temporary index and `update-index --force-remove --`, is in `src/factory/adapters/git_cli.py`.
- `ProjectCommandDefinition.not_read` and `_not_read_faults`, last in `_RULES`, are in `src/factory/domain/pipeline_definition.py`. `is_inside_checkout` moved there and is imported by `write_paths.py` and `confinement.py`.
- `RECORDS_CONTRACT` is `"1.3"` and the five schemas are regenerated (S0001).
- `src/factory/domain/known_results.py` and `src/factory/application/known_results.py` are new. `src/factory/domain/checks.py` gains `ReusedRun`, `CheckResult.reused` and `command_line`. `Boundaries.result_records` comes last, after `waiter`. `StageFinisher` runs its checks and reports through one `KnownResults` and builds each line with `command_line`. `build_boundaries` points `result_records` at `records/known-results.jsonl` (S0002).

Out of scope holds:
- `ProjectCommands`, `MakeProjectCommands`, `RecordingProjectCommands` and the preflight are untouched.
- `template/factory/pipeline.yml` and the demos' definitions have no `not_read`.
- Nothing prunes the store, and there is no counter or board column.

The Goal is reached up to the human's changes 1 to 3, which `feature.md` keeps for the human. `factory/pipeline.yml` on this branch still has `check: {time_limit: 15}` and no `secrets` command, so factory-rf itself reuses nothing yet. That is expected.

One observation, not a finding. factory-rf's `make check` also depends on something outside the key: `make secrets` scans the files changed against `merge-base HEAD origin/main`, which no tree id holds. Decision 12 covers the docs stage: `secrets` runs there with nothing left out. A reuse across work items (decision 1) can therefore follow a run whose secret scan covered another branch's diff. The contents it read were the same, so I see no hole, but the human may want to know about it.

## 2 Feature smoke test

What a user of the feature does: put factory-rf's planned `not_read` into a pipeline definition, run a story through doing, review and docs, read the journal and the records, and count the runs per tree with the operator guide's command. I wrote this as one pytest module in `$TMPDIR` that uses the repository's fixtures as a plugin, with the real `StageRunner`, `GitCli` on a real bare remote, `MakeProjectCommands`, `JsonLinesRecordLog`, the fake agent runtime and the fake hosting service. These are its steps:

1. It applies the human's change 1 to the real `factory/pipeline.yml` and loads it with `RuamelPipelineDefinitionReader`.
2. It applies the same `check` and docs-stage lines to the test remote's definition. Its Makefile has `lint`, `check`, `test`, `secrets` and `documents`, and each target appends its own name to a log.
3. The coder writes `src/a.py`; the reviewer changes nothing; the documenter writes `docs/guide.md` and `README.md`.
4. It reads the coder's and the documenter's entries from the pushed work item, the Makefile's log and `known-results.jsonl`.
5. It runs the `known-results.jsonl` count command from `docs/operator-guide.md`, with only its path changed, through `bash -c`.

```text
$ PYTHONPATH=tests uv run pytest -q -s -p conftest -p no:cacheprovider --no-header --rootdir "$TMPDIR/smoke" "$TMPDIR/smoke/test_feature_smoke.py"
1 change-1 definition loads: ['README.md', 'docs/*.md', 'factory/features/*.md', 'factory/features/*.jsonl', 'factory/stops.jsonl', 'planning/*', 'session-logs/*'] | docs checks ['check', 'secrets', 'documents'] | documenter 60 of lease 60
2 stage run: StageReport
2 stage run: StageReport
2 stage run: StageReport
3 stage now: smoke-test
4 coder entry ends:
  `check`: check: green (1.0 s)
4 documenter entry ends:
  `check`: check: green (1.0 s) (not run again: passed on tree 2a916a804b1d at 2026-10-12T12:00:00Z)
  `secrets`: secrets: green (1.0 s)
  `documents`: documents: green (1.0 s)
5 Makefile ran: ['check', 'secrets', 'documents']
6 record: check 2a916a804b1d None passed 0.001681 run
6 record: check 2a916a804b1d None passed 0.0 reused
6 record: secrets 467eae7b52ca None passed 0.001672 run
6 record: documents 467eae7b52ca None passed 0.001554 run
7 operator count: [('2a916a804b1d06260aeb8a87d3e58b24bdbe91f8', 1)]
.
1 passed in 0.37s
```

The test is green. The output shows these results:
- The human's change 1 loads with the code as built. The documenter's 40 minutes plus 15, 3 and 2 come to exactly its `lease_duration` of 60, so the next tick will not stop with `pipeline_definition_invalid`.
- `check` ran once for doing and docs together. The docs stage's line has the form of decision 6, and its tree is the doing stage's.
- `secrets` and `documents` ran on the tree that holds the documenter's files.
- The operator's command counts the real run and not the reuse.

## 3 Mutation score

`make mutants` ran twice; each run printed `mutants: stopped after 540 s; the results below are partial, run it again to go on`. Two runs made little progress on this feature's modules. Of the 540 s of the second run, about 7 minutes went to mutmut's "Listing all tests" and "Running clean tests", and seven mutants were tested in the rest. The modules `make mutants` picks for F0023 include all of `git_cli.py`, `stage.py`, `pipeline_definition.py` and `wiring.py`, which earlier features wrote and whose mutants each run large parts of the suite. I then ran mutmut once more by hand, with the same temporary-folder handling as the target, on the F0023-changed functions the two runs had not reached: `_with_command_lines`, `StageFinisher.__init__`, `GitCli._environment`, `_run` and `_execute`. It ran with `timeout 540` and ended with exit status 124.

Over the 13 modules, from `uv run mutmut results --all true`: **1394 killed, 61 survived, 1222 not checked**, so 1394 of 1455 checked (95.8 %). Every function F0023 added or changed was checked:

| Function | Killed | Survived |
|---|---|---|
| `factory.application.known_results` | 113 | 1 |
| `factory.domain.known_results` | 16 | 1 |
| `GitCli.work_tree_id` | 53 | 3 |
| `GitCli._environment`, `GitCli._run` | 44 | 0 |
| `GitCli._execute` | 26 | 5 |
| `command_line`, `_with_command_lines` | 17 | 0 |
| `StageFinisher._run_checks_and_reports` | 9 | 0 |
| `_not_read_faults`, `is_inside_checkout`, `_is_checkout_pattern` | 19 | 1 |
| `write_paths.py` | 39 | 0 |
| `confinement.py` | 123 | 0 |

The 1222 not checked are older functions of `git_cli.py`, `stage.py`, `pipeline_definition.py` and `domain/git.py` that F0023 did not change. `TreeId` is a type alias and has no mutant.

The survivors, grouped:
- **`GitCli.work_tree_id` without `--`** (`work_tree_id__mutmut_50`, `"--"` → `"XX--XX"`). No test leaves out a path that starts with `-`. I ran that case by hand on today's code and it is right (`True`). This is a missing criterion: **F0023-S0003**.
- **The wired `result_records` and `disk_records` with no model** (`build_boundaries__mutmut_104`, `__mutmut_94`). S0002's criterion 13 test appends through the wired log but reads back through a log it builds itself. A wiring with the wrong model would write its lines and then raise `AttributeError` at the first read. `KnownResults._read` catches only `OSError`, so that error would end a stage run. This is a missing criterion: **F0023-S0004**. `__mutmut_83`, the command records' model, is the same gap, but the log sits inside `RecordingProjectCommands`, where no test can reach it without a code change. It is left out.
- **Equivalent**:
  - `work_tree_id__mutmut_4` and `_5`: the temporary index's file name.
  - `definition_digest__mutmut_4`: `"utf-8"` → `"UTF-8"`.
  - `KnownResults._reuse__mutmut_35`: `targets=[]` dropped, and the field's default is `[]`.
  - `_is_checkout_pattern__mutmut_10`: `"{}"` → `"XX{}XX"`, which would refuse a pattern that holds `X`. No accepted row has one. This is a mutmut artifact; I propose no story.
- **Older than F0023, in functions it did not change** (49):
  - In `git_cli.py`: the exact arguments of `GitError` in `_execute`, `_failed_push`, `_merge_diverged`, `discard` and `delete_remote_branch`, and one in `_is_unreachable`.
  - In `stage.py`: `_stall_red` and `AfterAgent._stall` (`stage_start` and `pull_request` set to `None`), `StageRunner.run`, `_description`, `_masked`, and `StageFinisher.__init__`'s `ClaimService` arguments.
  - In `wiring.py`: `machine_log`, `read_hosting_token`, `repository_name`, `_read_utf8`, `boundaries_from_environment` and others.
  - In `contract_schema`: `indent=2` of the JSON. The committed-schema comparison is a structural test that mutmut leaves out.

  These belong to the features that wrote those functions, and I propose no story for them here.

## 4 What the stories noticed

- **S0001, coder (entries 7, 11, 15, 19, 23).** `update-index` gets every left-out path in one argument list, and a very large `left_out` could reach the system's limit on argument length. For factory-rf this means a few hundred Markdown paths, far below the limit. A failure would be a `GitError`, which `KnownResults` logs before it runs the command, so the cost is one run. No story.
- **S0001, coder.** The `_changed` test helper is still copied in `tests/adapters/test_pipeline_rules.py`, `test_pipeline_strict_values.py` and `test_pipeline_stage_moves.py`. The copies are older than F0023. The tester may move them under the standing leave the next time a new test needs one. No story.
- **S0001 and S0002, coder.** `make duplicates` reports 5 new findings: four similar-code pairs between `claude_runtime` and `opencode_runtime`, and the unused `ManualWaiter` in `adapters/clock.py`. None of them is in a module F0023 changed, and I reran it today with the same result. They belong to F0020's modules. No story here; the human may want one there.
- **S0002, coder (entries 7, 10, 14, 18, 22).** The comment "the record is telemetry" appears in both `KnownResults._append` and `RecordingProjectCommands.run`. Both are true, so this is cosmetic.
- **S0002, coder (entry 22).** `tests/application/test_preflight_run.py` keeps its own `_raising`, typed for `ProjectCommandError`. It is not a copy of the shared one.
- **S0002, documenter.** The operator guide's sentence that nothing reads `project-commands.jsonl` "to decide anything" is still true of that file.
- **S0001, reviewer.** `TreeId` repeats `CommitId`'s pattern, as the Interface prescribes. Not a finding.
- **Mine.** `/session-logs/` is git-ignored, so the `session-logs/*` entry in the human's change 1 `not_read` is redundant. It is harmless and keeps the intent visible.

## 5 Documentation

I read `README.md`, `docs/operator-guide.md` (*What a stage run shows*, *The records* with *The known results*, *The pipeline definition*, *The records contract*), `docs/decisions.md` (*A known result is not checked again*) and `docs/project-guide/` (`processes-and-checks.md`, `stages.md`, `git-and-hosting.md`, `watching.md`, `work-items.md`, `README.md`). They agree with the code and with each other, with one exception. The operator guide's count command runs as written: the smoke test above ran it.

**Finding (F0023-S0005).** The two `not_read` examples in *The pipeline definition* contradict each other:
- S0001's documenter wrote `lint: {time_limit: 10, not_read: ["factory/*", "docs/*"]}`, which leaves whole folders out of `lint`.
- S0002's documenter wrote, a few paragraphs further on, that factory-rf leaves out only Markdown and JSON Lines files because `make lint` reads every Python file wherever it lies.

An operator who copies the first example lets a reused `lint` miss a Python file under `docs/`. That is the silenced check decision 2 rules out. The same section says in the future tense that factory-rf's docs stage "will run `secrets`", which goes stale with the human's change 1. I do not count this as a contradiction between documentation and behaviour that misleads a user about what the factory does, since the code is right. It is a bad example, and a story fixes it.

`CLAUDE.md` still names six targets and still describes the documenter's check without the reuse. Both are the human's change 2.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:
1. The key is the command, the work tree without `not_read`, the SHA-256 of the whole definition, and the image. It holds no commit and no stage, and it reuses results across work items.
2. `not_read` is a list of patterns left out, matched like write paths. `/`, `~`, a `..` segment, `{` and `}` are refused.
3. The tree is what the factory's commit would record. Ignored files do not count, and a tracked file that `.gitignore` matches does.
4. The key changes with a read file, a merge that brings one, any definition value, or a new image. There is no expiry. A rebuild changes the image id only when a layer before the `image-id` step changes (`image/Dockerfile`; the operator guide says so for the preflight stamp).
5. A failed result is never reused, and the last real run of a key decides.
6. A reuse is a record and a journal line, never a line in `project-commands.jsonl`.
7. The store is `records/known-results.jsonl` per instance and is never pruned.
8. Checks and reports are reused, and the preflight's probe is untouched.
9. An agent's own `make check` is not a known result.
10. `Boundaries.result_records` is optional and comes last.
11. `work_tree_id` is the twenty-fourth git operation.
12. factory-rf's `not_read` names only `.md` and `.jsonl` files, `secrets` runs at the docs stage, and `documents` gets 2 minutes. These are pending as the human's change 1.
13. The template and the demos stay as they are.
14. The records contract goes to `1.3`.
15. The leaves to change earlier tests.
16. How F0023 meets F0020, F0021 and F0022.
17. What only the real run shows.

From the journals:
- **S0002, the human's answer (entry 8, option a).** The red-check test asserts `` "`check`." in note.body ``, and `stall_note` stays as it is. The test was this story's own.
- **S0001, coder.** Left-out paths are removed with `update-index --force-remove --` (literal paths). Rejected: `rm --cached` with `:(literal)` pathspecs, and a second `GitCli` per call.
- **S0002, coder.** The definition digest is computed once, in `KnownResults.__init__`.
- **S0001, tester.** In criterion 3 the files are committed before each row runs. In criterion 4 the checkout has a staged file, an unstaged edit and an untracked file. Criterion 7's type rows check only that the fault names `not_read`.
- **S0001, reviewer.** Added criterion 9 (a `~` not at the start, and `..` inside a segment) as accepted rows.

Earlier tests changed, each with its leave. I checked the list against the F0023 commits' `git diff-tree`, and there is no other change:
- **Decision 15 (S0001):**
  - `tests/application/test_git_interface.py`: `work_tree_id` added, renamed `_twenty_four_`.
  - `tests/application/test_interfaces.py`: renamed `_twenty_four_`.
  - `tests/domain/test_contract.py`: one `"1.3"`.
  - `tests/domain/test_contract_provider_limit.py`: two `"1.3"`.
- **Decision 15 (S0002):** `tests/domain/test_checks.py`: renamed `_generic_eight` and gains `"reused"`.
- **Standing leave to move a shared helper:**
  - `tests/git_support.py`: `pipeline_outcome`.
  - `tests/domain/test_tool_paths.py`, `tests/adapters/test_pipeline_rules.py`, `tests/adapters/test_pipeline_strict_values.py` and `tests/adapters/test_pipeline_stage_moves.py`: `_outcome` replaced (S0001).
  - `tests/application/test_recording_project_commands.py`: `_raising` → `tests/project_command_support.py` (S0002).

No earlier test was changed without a leave.

## 7 Slow checks

Nothing is offered beyond `make check` and `make mutants`: no image scan and no SBOM. `make check` is green as I found it (`test: green (47.3 s)`, coverage 99.08 %, `check: green`).

From `.reports/junit.xml`: 5859 tests, 442.5 s summed over the workers. The slowest are `test_claude_runtime_resume::…[resume ended by the time limit]` and `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s each), then `test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]` (3.3 s). None of these is F0023's. F0023's 133 tests take 6.9 s together, the slowest being `test_stage_known_results` rows at 0.5 to 0.6 s.

`make mutants` is the slow check that did not fit: two 540-second runs and one targeted run, and 1222 mutants of older functions in the touched modules are still unchecked. About 7 of each run's 9 minutes go to mutmut's clean test run. Narrowing `make mutants` to the changed functions would be a `Makefile` change, which is the human's.

Disk: `/work` 978.5 GB free, 0.5 GB used, at acceptance and at the previous record (start), and `/state` and `/tmp` are unchanged too. There is no growth to explain.

## 8 Cost

The stories cost 27 runs, 31.6 min, 237 turns, 897,344 tokens in (6,331,263 more from cache), 107,186 out and $9.78.

| Story | Total | Coder | Tester | Reviewer | Documenter | Smoke tester | Intake |
|---|---|---|---|---|---|---|---|
| S0001 | 14 runs, 15.4 min, $4.91 | 5 runs, $1.50 | 3 runs, $1.06 | 3 runs, $1.67 | $0.25 | $0.30 | $0.14 |
| S0002 | 13 runs, 16.2 min, $4.87 | 5 runs, $1.57 | 3 runs, $1.53 | 2 runs, $1.14 | $0.28 | $0.21 | $0.14 |

Neither story stands out. Both spent most of their extra runs on rework rounds that changed only tests:
- S0001 went to round 2: a copied parse helper (review entry 9) and the missing accepted rows of criterion 9 (entry 17).
- S0002 went to round 1: two copied test helpers (entry 16).

In each story three of the five coder runs changed no code and only named the tester's change or confirmed `make check`.

Human interventions: 1 question answered (question 1), 0.0 h waited. It was S0002's coder (entry 7): criterion 12's test asserted a `` `check`\n `` that `stall_note` never renders. The human chose option (a) the same morning. S0002 is the story that needed the human most, and only once.

Not part of the stories' cost: none of F0023's own docs stages reused anything, because factory-rf's `not_read` is the human's change 1, still to come.

## Proposed stories

- `F0023-S0003-the-git-wrapper-leaves-out-a-path-that-starts-with-a-dash.md`: pins the `--` before the left-out paths (survivor `work_tree_id__mutmut_50`). Tests only.
- `F0023-S0004-the-wired-known-results-and-disk-records-read-back-what-they-write.md`: reads the wired `result_records` and `disk_records` back through themselves (survivors `build_boundaries__mutmut_94` and `_104`). Today a wrong model would end a stage run instead of costing one run. Tests only.
- `F0023-S0005-the-operator-guide-s-not-read-example-leaves-out-only-what-lint-does-not-read.md`: repairs the operator guide's `not_read` example, which contradicts its own reasoning about `make lint`, and the future tense that the human's change 1 makes stale. Documentation only; start it after change 1.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 3 stories proposed; make mutants 1394/1455 (1222 mutants of older functions in the touched modules not reached; every function F0023 added or changed was checked)

   1. Scope: no finding. Both stories built every Scope item and nothing outside it, and Out of scope holds. The Goal is reached up to the human's changes 1 to 3. One observation: `make secrets` also depends on the merge-base with `origin/main`, which the key does not hold. Decision 12 covers this at the docs stage.
   2. Feature smoke test: green. I ran a story through doing, review and docs with the real `StageRunner` and git, on factory-rf's own definition with the human's change 1 applied. The definition loads, and the documenter's 40 + 15 + 3 + 2 minutes come to exactly its 60-minute lease. The docs stage reused `check` with the promised line. `secrets` and `documents` ran. The operator guide's count command printed one run for the tree.
   3. Mutants: 61 survived. Two groups are real gaps: no test leaves out a path that starts with `-` (S0003), and the wired `result_records` and `disk_records` are never read back through themselves, so a wrong model would end a stage run (S0004). 5 are equivalent and 49 are in older functions. `make mutants` stopped after 540 s twice, with about 7 of its 9 minutes spent on mutmut's clean run. I ran a third, targeted pass by hand on the changed functions it had not reached.
   4. Noticed: the `update-index` argument length (harmless, costs one run), the `_changed` test-helper copies, F0020's 5 `make duplicates` findings, a repeated comment, and the redundant `session-logs/*` entry (that folder is git-ignored). No story for any of them.
   5. Docs: one finding (S0005). The operator guide's first `not_read` example leaves whole folders out of `lint`, against its own later reasoning that `make lint` reads every Python file. The guide also says in the future tense that the docs stage "will run `secrets`", which goes stale once the human's change 1 is on `main`. `CLAUDE.md` is still pending as the human's change 2.
   6. Decisions: the 18 from `feature.md`, the human's answer (a) in S0002, and the coders' and testers' defaults are listed in the report. Ten earlier test files were changed, each under decision 15 or the standing leave. None was changed without a leave.
   7. Slow checks: nothing beyond `make check` and `make mutants`. `make check` is green (test 47.3 s). The slowest tests take 5.0 s, and F0023's 133 tests take 6.9 s together. Disk did not change since the start record.
   8. Cost: 27 runs, 31.6 min, $9.78, split evenly ($4.91 and $4.87). The rework rounds changed only tests; three of each story's five coder runs changed no code. There was 1 human question (S0002, the stall-note assertion), answered with 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 37.3 min, 67 turns, 174174 tokens in (6923992 more from cache), 44911 out, $3.68
