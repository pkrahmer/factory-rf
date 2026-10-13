This is not v1.1's baseline run: that run is v1.1 on `factory-demo-todo`, after the build. This is the overnight run in which v1 builds v1.1, with a Claude Code session as the human.

# Morning report, 2026-10-12 overnight

A running file: every push of the night log updates it. Status at the last update (02:45): F0001 has 9 of 14 stories merged and archived (S0001 to S0009), all accepted at the first approval. Starts are held at 93% of the 5-hour window until its reset at 03:30; S0010 is next. Planning stopped at 01:25: F0002 to F0011 are drafted and cross-checked once, not audited.

## Done

| Story | Pull request | Agent runs | Agent minutes | Clock minutes (start to archive) | Cost | Answers |
|---|---|---|---|---|---|---|
| F0001-S0001 Kill points in the wrappers | #1 | 14 | 5.4 | 12 (01:09 to 01:21) | $2.41 | 2 (coder: test vs mypy; reviewer: a missing failing side) |
| F0001-S0002 Hosting-service interface and DTOs | #2 | 6 | 4.3 | 7 (01:25 to 01:31) | $1.37 | 0 (first-pass) |
| F0001-S0003 PyGithub client and its one error type | #3 | 6 | 8.1 | 11 (01:32 to 01:43) | $1.54 | 0 (first-pass) |
| F0001-S0004 The process wrapper | #4 | 6 | 4.3 | 7 (01:43 to 01:50) | $1.19 | 0 (first-pass) |
| F0001-S0005 Git wrapper: fetch and refs | #5 | 6 | 7.6 | 10 (01:51 to 02:01) | $2.27 | 0 (first-pass) |
| F0001-S0006 Git wrapper: clone, checkout, commit, push | #6 | 6 | 6.3 | 9 (02:02 to 02:11) | $1.95 | 0 (first-pass) |
| F0001-S0007 Project commands and the make class | #7 | 8 | 4.9 | 9 (02:12 to 02:21) | $1.78 | 0 |
| F0001-S0008 Agent-runtime interface, DTOs and fake | #8 | 9 | 6.1 | 10 (02:22 to 02:32) | $1.96 | 1 (coder: a test vs the pydantic mypy plugin) |
| F0001-S0009 The `claude -p` runtime: call and result | #9 | 7 | 6.5 | 11 (02:33 to 02:44) | $2.02 | 1 (intake: two criteria the Interface implied) |
| F0001-S0010 The `claude -p` runtime: resume and version | #10 | 6 | 5.9 | 11 (03:39 to 03:50) | $2.00 | 0 (first-pass) |
| F0001-S0011 Git wrapper: history and work tree | #11 | 9 | 8.2 | 14 (03:51 to 04:05) | $2.15 | 1 (coder: test commit ids flagged by detect-secrets) |

## Stops

- S0001, coder at doing: tests used `assert reach(...) is None` against a `-> None` function, red under `mypy --strict`. Answered (a), the tester fixed six lines; `CLAUDE.md` got a test rule to prevent it.
- S0001, reviewer at review: a rule without its failing side for an already armed point. Answered (a), one criterion and one test added.
- S0008, coder at doing: a test passed an unknown keyword to a typed pydantic constructor. Answered (a) without a marker; `CLAUDE.md` got a second test rule.
- S0009, intake: two behaviours of the Interface without criteria. Answered: write both.
- S0011, coder at doing: random-looking commit ids in a test failed `make secrets`. Answered (a) low-entropy ids; `CLAUDE.md` got a third test rule.

## Fixes made

None yet.

## Decisions the session took

- Decision 007 (`factory-v2/planning/decisions/007-overnight-defaults.md`): the four open questions, all defaults, answered by the operator (accepted).
- The seed's choices: see the night log, "For the morning".

## Figures against run 4

| Figure | Run 4 | Tonight |
|---|---|---|
| cost per first-pass story | $1.16 on average | |
| agent minutes per first-pass story | 2 to 4 | |
| clock minutes per first-pass story | 7 to 9 | |
| acceptance cost | $0.87 to $1.59 | |
| total | $15.89, 59 runs, 8 stories, 3 acceptances | |

Conditions: run 4 ticked every 2 minutes fixed; tonight the pause starts at 15 seconds and doubles to 120. Dollars are Claude Code's list prices under a subscription login.

## Usage

- Start (23:17): 5-hour window 1% used, resets 03:30; weekly 53% used, resets 05:00.
- 00:46: 5-hour window 57%, weekly 61%.
- 02:03: 83%, weekly 64%. 02:11: 85%. 02:32: 90%. 02:44: 93%, starts held until the 03:30 reset.

## What needs the operator

- The interface sheet (`planning/overnight/interfaces.md`), once written.
- Decision 007 to confirm.
- The items v1 cannot build tonight: WE1.4, WE4, WE5 and R35's rewrite.
- The `mutants` decision (left out of the seed).
- The working answers in `planning/overnight/skeleton-answers.md`, taken by the session.
- The traceability (`planning/overnight/traceability.md`) and its morning observations: ST3.3, ST5.1, WE3.1, WE3.3, WE3.4.
