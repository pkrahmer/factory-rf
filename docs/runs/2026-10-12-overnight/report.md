This is not v1.1's baseline run: that run is v1.1 on `factory-demo-todo`, after the build. This is the overnight run in which v1 builds v1.1, with a Claude Code session as the human.

# Morning report, 2026-10-12 overnight

A running file: every push of the night log updates it. Status at the last update (01:10): Phase 1 done. Phase 2 done: 11 features, 79 stories drafted (F0001 now 14), skeleton, interface sheet, traceability and cross-check 1 committed under `planning/overnight/`. Phase 3/4 for F0001 in its third round; F0001-S0001 started at 01:09. Later features not yet audited (usage kept for the build).

## Done

| Story | Pull request | Agent runs | Agent minutes | Clock minutes (start to archive) | Cost | Answers |
|---|---|---|---|---|---|---|
| F0001-S0001 Kill points in the wrappers | #1 | 14 | 5.4 | 12 (01:09 to 01:21) | $2.41 | 2 (coder: test vs mypy; reviewer: a missing failing side) |
| F0001-S0002 Hosting-service interface and DTOs | #2 | 6 | 4.3 | 7 (01:25 to 01:31) | $1.37 | 0 (first-pass) |
| F0001-S0003 PyGithub client and its one error type | #3 | 6 | 8.1 | 11 (01:32 to 01:43) | $1.54 | 0 (first-pass) |
| F0001-S0004 The process wrapper | #4 | 6 | 4.3 | 7 (01:43 to 01:50) | $1.19 | 0 (first-pass) |
| F0001-S0005 Git wrapper: fetch and refs | #5 | 6 | 7.6 | 10 (01:51 to 02:01) | $2.27 | 0 (first-pass) |

## Stops

- S0001, coder at doing: tests used `assert reach(...) is None` against a `-> None` function, red under `mypy --strict`. Answered (a), the tester fixed six lines; `CLAUDE.md` got a test rule to prevent it.
- S0001, reviewer at review: a rule without its failing side for an already armed point. Answered (a), one criterion and one test added.

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

## What needs the operator

- The interface sheet (`planning/overnight/interfaces.md`), once written.
- Decision 007 to confirm.
- The items v1 cannot build tonight: WE1.4, WE4, WE5 and R35's rewrite.
- The `mutants` decision (left out of the seed).
- The working answers in `planning/overnight/skeleton-answers.md`, taken by the session.
- The traceability (`planning/overnight/traceability.md`) and its morning observations: ST3.3, ST5.1, WE3.1, WE3.3, WE3.4.
