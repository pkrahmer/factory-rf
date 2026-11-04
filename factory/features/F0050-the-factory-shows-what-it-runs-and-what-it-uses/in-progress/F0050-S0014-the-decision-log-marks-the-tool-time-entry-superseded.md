---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T23:51:56.738640Z'
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
