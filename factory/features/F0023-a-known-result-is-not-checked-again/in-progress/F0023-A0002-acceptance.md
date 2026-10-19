---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 291
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T22:06:53.618449Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T22:11:56.925225Z'
  stage: acceptance
  run: cef27f092d8545ad9ea1cdabd9c9e5e9
stories: [F0023-S0001, F0023-S0002, F0023-S0003, F0023-S0004, F0023-S0005]
outcome: null
---

# Acceptance of A known result is not checked again

## Recommendation

**accepted.** The five stories together build every Scope item of `feature.md` and nothing outside it. S0003 to S0005 closed the three gaps the first acceptance (F0023-A0001) found: the `--` before left-out paths, the wired logs reading back through themselves, and the operator guide's `not_read` example. The feature smoke test is green; it ran the real wiring, real git and real `make` on factory-rf's own `factory/pipeline.yml`. The human's change 3, the real check, has in effect already happened in the live records. Since change 1, `/state/records/known-results.jsonl` holds 19 real `check` runs and 19 reuses. That is about 955 s of `check` not run, at 51.1 s on average per real run. The docs stages of S0003, S0004 and S0005 end with exactly the three lines `feature.md` promised. `make check` is green. No story is proposed: what is still open is either the human's to edit or belongs to other features.

## 1 Scope

None. Every Scope item has its code where `feature.md` puts it. A0001 checked this item by item for S0001 and S0002, and I found nothing moved since then. S0003 and S0004 each add one test module and change nothing under `src/`:
- S0003: `tests/adapters/test_git_cli_work_tree_dash.py`
- S0004: `tests/entry/test_wiring_record_logs.py`

S0005 changes only `docs/operator-guide.md`. All three fit the Scope's lines on tests and on the operator guide. I checked this with `git diff --name-status` of their merges #288, #289 and #290, leaving out `factory/`.

Out of scope holds:
- The template's and the demos' definitions have no `not_read`.
- The preflight, `ProjectCommands`, `MakeProjectCommands` and `RecordingProjectCommands` are unchanged.
- Nothing prunes the store, and there is no counter or board column.

The Goal is reached. The human's changes 1 and 2 are on `main`: `factory/pipeline.yml` has `check`'s `not_read` and `secrets` among the docs stage's checks, and `CLAUDE.md`'s documenter bullet speaks of the reuse. The `check` time limit is 8, not change 1's 15, by F0024's later change. The "seven targets" sentence of change 2 says six on `main`. That is right since mutation testing became a sweep and `mutants` left the pipeline (`docs/decisions.md`, *Mutation testing runs only as sweeps outside the factory*).

`feature.md`'s *Stories* still lists only S0001 and S0002. S0004's intake pointed this out, and that edit is the human's.

## 2 Feature smoke test

The walk-through a user of the feature does, as one Python script against the real entry points:
- `build_boundaries` with a state directory and an image, and a fake hosting service only.
- `RuamelPipelineDefinitionReader` on the repository's own `factory/pipeline.yml`.
- `KnownResults` over the wired `GitCli`, `RecordingProjectCommands(MakeProjectCommands)` and `JsonLinesRecordLog`.
- `command_line` for the journal lines.

The checkout is a fresh git repository in `$TMPDIR`. Its `Makefile` has `check`, `secrets` and `documents`; each target logs its own name, and goes red while a `fail-<target>` file exists. The script runs these steps:
1. The coder writes `src/b.py`, and the doing stage runs.
2. The reviewer's journal changes, and the documenter writes `docs/guide.md`, `README.md` and `docs/-dash.md` (a dash path). The docs stage runs.
3. A Python file appears under `docs/`.
4. A red `check` runs twice on one tree, then a green one, then a docs stage.
5. The same tree runs under another image.
6. The script reads the wired log back and runs the operator guide's count command (its line 597, with only the path changed) through `bash -c`.

```text
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; sed -n 597p docs/operator-guide.md > "$d/count.sh"; mkdir "$d/run"; uv run -q python "$d/smoke.py" "$d/run" "$PWD" "$d/count.sh"; echo "exit=$?"
1 factory-rf's definition loads; check not_read: ['README.md', 'docs/*.md', 'factory/features/*.md', 'factory/features/*.jsonl', 'factory/stops.jsonl', 'planning/*', 'session-logs/*']
  docs stage checks: ['check', 'secrets', 'documents']
2 the coder writes src/b.py; the doing stage
  doing: `check`: check: green (1.0 s)
  make ran: ['check']
3 the reviewer's journal; the documenter writes docs/guide.md, README.md, docs/-dash.md; the docs stage
  docs: `check`: check: green (1.0 s) (not run again: passed on tree fd126fb6595b at 2026-10-19T22:09:32Z)
  docs: `secrets`: secrets: green (1.0 s)
  docs: `documents`: documents: green (1.0 s)
  make ran: ['secrets', 'documents']
4 a Python file under docs/, which lint reads: the docs stage again
  docs: `check`: check: green (1.0 s)
  make ran: ['check']
5 a red check on one tree, run twice; then green; then the docs stage
  doing: `check`: check: red
  make ran: ['check']
  doing: `check`: check: red
  make ran: ['check']
  doing: `check`: check: green (1.0 s)
  make ran: ['check']
  docs: `check`: check: green (1.0 s) (not run again: passed on tree 94a4f14d3f65 at 2026-10-19T22:09:32Z)
  make ran: []
6 another image, the same tree
  doing: `check`: check: green (1.0 s)
  make ran: ['check']
7 the wired log reads back through itself: 10 records, 2 reuses
8 the operator guide's count command: [('039541b696c5f275a99bb61e49ea0f1e58ff3182', 2), ('94a4f14d3f65168089af023ad063237d6c7a8e23', 2), ('fd126fb6595bba6a9cd5f4f3a7e08022cc82b0b8', 1), ('cd5505cc9c6951fbd0f03547c5785267bcc25fa8', 1)]
  project-commands.jsonl lines (real runs only): 8
exit=0
```

Green, and every promise holds:
- The docs stage reuses the doing stage's `check` with decision 6's line. It still runs `secrets` and `documents`, and a left-out dash path keeps the key.
- A `.py` file under `docs/` changes the key, as S0005's sentence in the guide says.
- A red result is not reused: the same tree ran twice red, then green.
- Another image runs again.
- The count command counts real runs only: the red tree twice, the tree run under two images twice. `project-commands.jsonl` has the 8 real runs and no reuse.

The live records are the human's change 3 at a larger scale. I counted the factory's own `/state/records/known-results.jsonl` (136 lines since 16:06 UTC):
- 19 real `check` runs and 19 reuses. All but two of the reuses are at docs stages. The two at 19:12:49 and 20:33:39 are doing stages after a review send-back that changed no code.
- About 955 s of `check` were not run, against 51.1 s on average per real run.
- The docs entries of S0003, S0004 and S0005 end with `` `check`: check: green (not run again: passed on tree … at …) ``, `` `secrets`: secrets: green (… s) `` and `` `documents`: documents ok ``, the form change 3 expected.
- Tree `3523d622cd0b` ran twice, at 21:45:24 (S0004) and 21:56:48 (S0005), because the image changed between them (`3440796c…` to `6f096063…`, a rebuild of `self`). Decision 4 intends exactly that, and step 4 of change 3 names it.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0004, coder and documenter.** The command records' log inside `RecordingProjectCommands` is still not read back through the wiring. The story left it out on purpose, because reaching the log would take a code change. A wrong model there would only lose telemetry: nothing reads `project-commands.jsonl` to decide anything. No story.
- **S0004, intake and documenter.** `feature.md`'s *Stories* lists only S0001 and S0002. That edit is the human's.
- **S0005, intake and coder.** The guide's factory-rf block showed `time_limit: 15`, while `main` holds `8`. The documenter copied `8`, and the block now matches `factory/pipeline.yml:10`. Resolved.
- **S0003, tester.** The tester could not show that the new test kills the `--` mutant without writing under `src/`. The coder did it by hand: three of the four rows fail without `--`. Resolved.
- **Carried from A0001 and still open, not F0023's.** `make duplicates` reports `5 new` in every coder entry of S0003 to S0005: F0020's runtime pairs and `ManualWaiter`. In the live records, all 21 `duplicates` runs have the status `failed`. So that report is never a known result and always runs, about 3 s each. That is harmless, but it will stay so until the human accepts those findings into `security/duplicates-baseline.txt` or a story removes them.
- **Carried from A0001.** `make secrets` scans the files changed against the merge-base with `origin/main`, which the key does not hold. Decision 12 covers the docs stage. No new evidence.
- **Mine.** `docs/operator-playbook.md:67` (the human's file) says "the docs stage may log" the reused line. The live records show a doing stage after a send-back logging it too (19:12:49, 20:33:39). The playbook's rule ("that line is a pass") holds for both, so this is a wording note for the human, not a story.

## 5 Documentation

None. I read `README.md`, `docs/operator-guide.md` (*The records* with *The known results*, *The pipeline definition*, *What a stage run shows*), `docs/project-guide/processes-and-checks.md` (*Known results*), `stages.md` (`StageFinisher.finish`, `ProjectCommandDefinition`), `git-and-hosting.md` and `docs/decisions.md` (*A known result is not checked again* and the mutation entries after it). They agree with the code and with each other:
- A0001's contradiction is gone. The example is now `check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}`, the guide adds the sentence that a linter reads every source file in every folder, and the factory-rf block and the `secrets` warning are in the present tense. Smoke step 4 shows the behaviour the guide now describes.
- The count command at `docs/operator-guide.md:597` runs as written; the smoke test ran it.
- `docs/decisions.md`'s F0024 decision 7, "a complete [mutants] result is a known result like any report", is superseded by the sweep entry right after it, which says so. That is not stale.

## 6 Decisions taken for the human

The 18 decisions of `feature.md` stand as A0001 listed them for the human to accept or revisit. In short:
- The key: command, tree without `not_read`, definition digest and image; no commit, no stage, reuse across work items.
- `not_read` as patterns left out.
- The tree as the factory's commit would record it.
- What invalidates a known result; no expiry.
- A failed result is never reused, and the last real run decides.
- A reuse is recorded, never silenced.
- A store of its own, never pruned.
- Checks and reports reused; the preflight untouched.
- Only the factory's own runs are known.
- `result_records` optional and last.
- `work_tree_id` as the twenty-fourth git operation.
- factory-rf's `not_read`, with `secrets` at the docs stage.
- The template and the demos unchanged.
- Records contract `1.3`.
- The leaves to change earlier tests.
- How F0023 meets F0020, F0021 and F0022.
- What only the real run shows.
- The human's answers of the morning.

Taken since A0001, in S0003 to S0005:
- **S0003, coder.** Kept `update-index --force-remove -- <paths>`, and rejected passing the paths through `--stdin -z`.
- **S0004, story.** Left the `RecordingProjectCommands` log out of the read-back criterion rather than change code to expose it.
- **S0004, intake.** Accepted a story that `feature.md`'s *Stories* does not list, and left that edit to the human.
- **S0005, criterion 3.** The guide's factory-rf line follows `factory/pipeline.yml` on `main` (`time_limit: 8`), not change 1's text (`15`).
- **The human's answer** in S0002 (question 1, option a) is the feature's only one. A0001 listed it.

Earlier tests changed: none in S0003 to S0005. Each merge adds one new test file or none (status `A`), and each reviewer says so. A0001 listed the earlier tests changed by S0001 and S0002, each under decision 15 or the standing leave. No earlier test was changed without a leave.

## 7 Slow checks

Nothing is offered beyond `make check`: no image scan and no SBOM, and `make mutants` runs by sweep only (check 3). `make check` is green as I found it: `test: green (40.9 s)`, coverage 99.12 %, `check: green`.

From `.reports/junit.xml`, 6005 tests take 467.2 s summed over the workers. The slowest are not F0023's:
- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`, 5.0 s
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, 5.0 s
- two `test_opencode_sudo_time_limit` rows, 4.5 s each

The new tests are fast: `test_git_cli_work_tree_dash` has 4 rows in 0.16 s, and `test_wiring_record_logs` 2 rows in 0.01 s.

Disk is unchanged from the start record to now: `/work` 970.4 GB free and 0.5 GB used, `/state` 0.0 GB used, `/tmp` 0.0 GB used. There is no growth to explain.

## 8 Cost

The stories cost 45 runs, 41.4 min, 327 turns, 1,193,545 tokens in (7,633,656 more from cache), 130,333 out and $12.32.

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 | 14 | 15.4 | $4.91 |
| S0002 | 13 | 16.2 | $4.87 |
| S0003 | 6 | 3.5 | $0.93 |
| S0004 | 6 | 3.6 | $0.85 |
| S0005 | 6 | 2.7 | $0.77 |

S0001 and S0002 stand out, as the two stories that built the feature. Their extra runs were rework rounds that changed only tests (A0001, check 8). S0003 to S0005 each took one run per stage, with no rework, at under a dollar each, as tests-only or docs-only stories should.

The feature pays for itself in factory time, not in dollars. The roughly 16 minutes of `check` the live records show not run cost no model, and those docs stages still ran their agents.

Human interventions: 1 question answered (question 1), 0.0 h waited. It was S0002's coder (journal entry 7): criterion 12's test asserted a `` `check`\n `` that `stall_note` never renders, and the human chose option (a). S0002 is the story that needed the human most, and only that once.

## Proposed stories

None. Every open item is either the human's to edit (`feature.md`'s *Stories*, the playbook's wording, the duplicates baseline) or belongs to other features (F0020's `make duplicates` findings).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   1. Scope: no finding. All Scope items of the five stories are built, and nothing outside the Scope. S0003 to S0005 added two test modules and repaired one passage of the operator guide, which closes all three proposals of A0001. Out of scope holds. The human's changes 1 and 2 are on `main`. `feature.md`'s *Stories* still lists only S0001 and S0002; that edit is the human's.
   2. Feature smoke test: green. I ran a Python script against the real `build_boundaries`, git and `make` on factory-rf's own `factory/pipeline.yml`:
      - The docs stage reused the doing stage's `check` with the promised line, and still ran `secrets` and `documents`. A dash path left out kept the key.
      - A `.py` file under `docs/` reran `check`.
      - A red result was never reused, and another image ran again.
      - The operator guide's count command counted only real runs.
      - The live `known-results.jsonl` shows change 3 in effect: 19 real `check` runs and 19 reuses, about 955 s of `check` not run.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the `RecordingProjectCommands` log is not read back through the wiring (left out on purpose). F0020's 5 `make duplicates` findings mean every `duplicates` run (21 of 21) has the status `failed`, so that report is never reused; about 3 s each. Still open from A0001: the merge-base of `make secrets` is not part of the key. The playbook says only "the docs stage" logs the reused line, but a doing stage after a send-back does too. No story for any of them.
   5. Docs: no finding. A0001's contradiction in the `not_read` example is gone, the count command runs as written, and the guide, the project guide and the decision log agree with the code.
   6. Decisions: the 18 decisions of `feature.md` stand as listed. Taken since A0001:
      - S0003 kept `--` and rejected `--stdin -z`.
      - S0004 left the `RecordingProjectCommands` log out of its criterion.
      - S0004's intake accepted a story `feature.md` does not list.
      - S0005 copied `time_limit: 8` from `main`.
      S0003 to S0005 changed no earlier test.
   7. Slow checks: nothing beyond `make check`, which is green (test 40.9 s, coverage 99.12 %). The slowest tests take 5.0 s and are not F0023's. Disk is unchanged since the start record.
   8. Cost: 45 runs, 41.4 min, $12.32. S0001 and S0002 come to $4.91 and $4.87, with rework that changed only tests. S0003 to S0005 cost under $1 each, with no rework. 1 human question (S0002's stall-note assertion), answered with 0.0 h waited.
