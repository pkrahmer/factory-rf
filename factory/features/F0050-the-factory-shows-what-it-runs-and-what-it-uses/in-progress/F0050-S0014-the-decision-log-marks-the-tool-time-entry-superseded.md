---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 553
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-04T23:52:21.899629Z'
  lease_duration: 60
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
