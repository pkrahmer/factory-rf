---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 553
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T23:51:56.732040Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T23:51:56.738640Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T23:52:16.499354Z'
  stage: intake
  run: 2133abc39b0d4450a7bb9075b5fbd7d0
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T23:52:21.899629Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T23:52:41.912999Z'
  stage: tests
  run: d24fff0d2a5b4e41838826f1417db3a7
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T23:52:47.385323Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T23:55:21.970397Z'
  stage: doing
  run: c4624e32ac144116bed2bf325bf9a82e
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T23:55:27.725279Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T23:55:49.648710Z'
  stage: review
  run: ed0eb3f963904949a7122140e23f2a7d
---

# The decision log marks the old tool-time entry as superseded

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

The decision log still has the F0012 entry "The time per tool command inside a run is not recorded" (`docs/decisions.md:407`). It says that the time of each tool command is not recorded, because the JSON reply of `claude -p` does not carry it. F0050-S0006 made every completed cost record carry `tools`, with the `seconds` of each tool read from the run's transcript, and F0050-S0009 made the Claude Code times come from the `assistant` and `user` lines. The S0006 entry, "The cost record sums up the run's tool calls, without their content" (`docs/decisions.md:1537`), does not say that it supersedes the F0012 entry. So a reader of the log meets two entries that contradict each other. The S0009 documenter saw this and left it alone, as outside that story. This story marks the old entry as superseded, in the form the log already uses for that (a `Superseded by *...*` line). It also names the supersession in the S0006 entry. No code and no test change.

## Interface

- No module under `src/factory/` changes, and no test is written.
- `docs/decisions.md`: the F0012 entry gets one line, `- Superseded by *The cost record sums up the run's tool calls, without their content*: each tool's seconds are read from the run's transcript (F0050-S0006, S0009).`, and its text stays as it is. The S0006 entry gets the sentence `This supersedes *The time per tool command inside a run is not recorded*.` after its Decision.

## Acceptance criteria

1. The F0012 entry "The time per tool command inside a run is not recorded" keeps its text and gains the `Superseded by *The cost record sums up the run's tool calls, without their content*` line, naming F0050-S0006 and S0009.
2. The S0006 entry "The cost record sums up the run's tool calls, without their content" says that it supersedes *The time per tool command inside a run is not recorded*.
3. No other entry of `docs/decisions.md` changes.
4. `make check` stays green.
5. docs: `docs/decisions.md` as criteria 1 to 3 say. `docs/operator-guide.md`, `README.md` and the project guide: none, because they already describe the `tools` field as built.

## Smoke test

```bash
grep -c "Superseded by \*The cost record sums up the run's tool calls" docs/decisions.md
```

Expect: `1`.

```bash
grep -c "This supersedes \*The time per tool command inside a run is not recorded\*" docs/decisions.md
```

Expect: `1`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: a docs-only story. It names `docs/decisions.md` and gives the exact `Superseded by` line for the F0012 entry (line 407). It also gives the exact sentence for the S0006 entry (line 1537), to go after its Decision bullet. I checked that both entries exist and that the S0006 entry has a Decision bullet. No `src/` module changes, so there are no signatures to name.
   - Criteria: 1 and 2 are each testable by grep for the exact line or sentence. Criterion 1 also requires the F0012 text to stay as it is, and criterion 3 requires that no other entry changes. Both can be checked against the committed diff. Nothing in the Interface states a rule with a failing side.
   - Smoke test: both commands are plain `grep -c` calls on `docs/decisions.md` and run as written. Each `Expect:` is a checkable count of `1`. Neither pattern matches anywhere in the log yet, so the counts start at 0 and reach 1 only after the edit.
   - Architecture: the change is only to the decision log, which the documenter stage keeps. It touches no layer and no file in the human's list.
   - Scope: this is S0014 of F0050, which feature.md lists as "from A0002". It adds no code and no new behaviour. It is not in "Out of scope".
4. factory: started tests as vm.
5. tester: No test written, because the Interface says so: "No module under `src/factory/` changes, and no test is written." This story only edits `docs/decisions.md`, which the documenter stage keeps. Criteria 1 to 3 fix exact text in that file. The smoke test's `grep -c` commands and the review of the diff check them, so a pytest test pinning the log's wording would go against the Interface.
   - criterion 1: no test, per the Interface (checked by the first smoke-test grep and by the diff)
   - criterion 2: no test, per the Interface (checked by the second smoke-test grep)
   - criterion 3: no test, per the Interface (checked by review of the diff of `docs/decisions.md`)
   - criterion 4: no test of its own (`make check`)
   - criterion 5: no test of its own (docs stage)
   Files created: none. Modules the test runner could not import: none. No test run, since there are no new tests. `make lint` is green. Rejected: a structural test that reads `docs/decisions.md` for the two sentences, because the Interface rules out writing one.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Nothing built: no code change, and the working tree is unchanged. The Interface says no module under `src/factory/` changes. The only file this story edits is `docs/decisions.md`, which is outside the coder's write paths in the pipeline definition (that file belongs to the documenter's `docs/*`), and CLAUDE.md says the coder does not write the decision log. The docs stage makes the two edits from criterion 5: the `Superseded by *The cost record sums up the run's tool calls, without their content*` line under the F0012 entry at `docs/decisions.md:407`, and the `This supersedes *The time per tool command inside a run is not recorded*.` sentence after the Decision of the S0006 entry at `docs/decisions.md:1537`. I checked that both entries are where the description says.

   - Main choice: hand forward with no change and leave the edit to the documenter. Rejected: editing `docs/decisions.md` here. The factory's take would drop that edit as outside the coder's write paths, and CLAUDE.md gives the decision log to the documenter.
   - Refactor step: there is no diff, so there was nothing to refactor.
   - The journal did not change the meaning of the task, so `## Description` was not rewritten.
   - `make test` and `make check` ran green before handing on (`test: green (118.1 s)`, `check: green`, coverage 99.26 %).
   - Noticed, not touched: the log uses two forms for supersession, a plain `Superseded by *...*` sentence (`docs/decisions.md:17`, 397, 874) and a `- Superseded in part by "..."` bullet. The Interface gives the bullet form with italics, which the documenter can follow as written.

   `check`: check: green (not run again: passed on tree 066290bec96a at 2026-11-04T23:41:19Z)
   `duplicates`: duplicates: 4 new, 41 known, 2 gone
8. factory: started review as vm.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. That fits this story. The Interface says no module under `src/factory/` changes and no test is written. The only edit is to `docs/decisions.md`, which only the documenter may write, and criterion 5 hands it to the docs stage.

   1. Acceptance criteria: criteria 1 to 3 are text the docs stage writes in `docs/decisions.md`. The two smoke-test `grep -c` commands and the docs-stage diff check them, so no pytest test is missing. The Interface states no rule with a failing side and no limit. Criterion 4: the journal records `check: green` and test coverage at 99.26 % after the coder (entry 7).
   2. Architecture: nothing under `src/` changes, so no layer or wrapper rule is touched.
   3. Security: no code, no new markers and no new baseline entries.
   4. Quality: there is no code to judge. The `duplicates: 4 new` result in entry 7 cannot come from this branch, since it changes nothing under `src/factory`.
   5. Work item hygiene: the coder's journal entry gives the main choice (hand forward with no change) and what it rejected (editing the decision log outside its write paths). The Description still matches the work, since the edit belongs to the docs stage. The docs criterion names exactly the two edits.
      - Both target entries exist, at `docs/decisions.md:407` and `docs/decisions.md:1537`.
      - The `- Superseded by *...*:` bullet the Interface gives follows the log's existing bullet form for this (for example `docs/decisions.md:152` and `:420`), so the documenter can write it as given.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
