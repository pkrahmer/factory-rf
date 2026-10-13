This is not v1.1's baseline run: that run is v1.1 on `factory-demo-todo`, after the build. This is the overnight run in which v1 builds v1.1, with a Claude Code session as the human.

# Morning report, 2026-10-12 overnight

Final (04:55). The night ended at a stop condition of the plan (section 9): no story was left that may run. F0001 (boundaries) is built and accepted: 14 stories merged and archived, each accepted at its first approval, and its feature acceptance merged as **accepted with drafts**. Planning stopped at 01:25 and the cut-off (03:30) passed with only F0001 through Phases 3 and 4, so F0002 to F0011 stay drafted, not built. Night log: `docs/runs/2026-10-12-overnight/night-log.md`.

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
| F0001-S0012 Git wrapper: branches and merge | #12 | 6 | 6.4 | 9 (04:06 to 04:15) | $1.42 | 0 (first-pass) |
| F0001-S0013 Git wrapper: reset, revert, move | #13 | 11 | 8.3 | 14 (04:16 to 04:30) | $2.03 | 1 (reviewer: `move` outside the path rule) |
| F0001-S0014 The hosting-service fake | #14 | 6 | 4.1 | 7 (04:31 to 04:38) | $1.30 | 0 (first-pass) |
| F0001 feature acceptance (acceptor) | #15 | 1 | 7.3 | 9 (04:38 to 04:47) | $2.74 | 0; verdict accepted with drafts, 4 drafts proposed |

Totals: 15 pull requests, 107 agent runs, 93.7 agent minutes, $28.13 (stories $25.39, acceptance $2.74), from the first start at 01:09 to the acceptance at 04:47, with a pause of 55 minutes (02:44 to 03:39) for the usage window.

## Stops

Six questions reached the session; each was answered within the decisions, none twice, and no cap, stall or error occurred.

- S0001, coder at doing: tests used `assert reach(...) is None` against a `-> None` function, red under `mypy --strict`. Answered (a): the tester fixed six lines.
- S0001, reviewer at review: a rule without its failing side for an already armed point. Answered (a): one criterion and one test.
- S0008, coder at doing: a test passed an unknown keyword to a typed pydantic constructor. Answered (a) without a `type: ignore` marker.
- S0009, intake: two behaviours of the Interface without criteria. Answered: write both.
- S0011, coder at doing: random-looking commit ids in a test failed `make secrets`. Answered (a): low-entropy ids, no baseline entry, no pragma.
- S0013, reviewer at review: `move` created folders outside the checkout before git refused. Answered (a): the story's own path rule and a criterion.
- Machine: none. One push of the night log got an empty reply from GitHub at 02:12 and went through on retry. The container ran throughout.

## Fixes made

- To stories, before the build: F0001 went through three rounds of audit and pre-check (`planning/overnight/audits/F0001-*`, `precheck/F0001-*`): split from 11 to 14 stories; the handling tables give every changed criterion old and new.
- To stories, at night through answers: S0001 criterion 16, S0009 two criteria, S0013 one rule and criterion (each in the story's journal).
- To the seed: `CLAUDE.md` allows exactly four markers in `src/factory/adapters/process.py` (R5; `docs/decisions.md`); `pyproject.toml` got the six console scripts (`b131f1e`); `CLAUDE.md` Tests got three lines learned from the questions (no value of a `-> None` call; refused fields through `type[BaseModel]`; low-entropy hex test values). All three tighten; none loosens a check.
- To v1: none. No v1 defect was seen.

## Decisions the session took

- Decision 007 (`factory-v2/planning/decisions/007-overnight-defaults.md`): the four open questions, all defaults, answered by you before the night (accepted).
- The working answers in `planning/overnight/skeleton-answers.md`: to the skeleton's 16 questions, the interface sheet's 14, cross-check 1's three blockers, and F0001's rounds 1 and 2. One was a mistake and was corrected the same hour: `--permission-prompts none` was dropped on an auditor's word, then restored from v1's book.
- The seed's choices (`docs/decisions.md`): package `factory` with four layers, product paths `image/`, `template/`, `claude/` in the coder's write paths, no `mutants`, the licence entries for PyGithub (LGPL) and cryptography, the project guide in `docs/`.
- No answer was added to F0001's `## Decisions taken for the human` at night: every answer closed a story's own rule.
- Setup commits: the console scripts. Write paths widened at night: none. Stories held back or discarded: none. Acceptances closed: none.
- Deviations from the plan, each in the night log: all 14 F0001 drafts committed to `drafts/` before all had passed (so the feature would not fall complete after S0001); only passed stories were started; the pre-check run by one opus agent per feature and, in round 3, together with the narrow re-audit; planning stopped at 01:25 to leave the usage window to the build.

## Figures against run 4

| Figure | Run 4 | Tonight (F0001) |
|---|---|---|
| cost per first-pass story | $1.16 on average | $1.63 on average (8 first-pass stories: S0002 to S0006, S0010, S0012, S0014) |
| agent minutes per first-pass story | 2 to 4 | 4.1 to 8.1, 5.9 on average |
| clock minutes per first-pass story | 7 to 9 | 7 to 11, 8.9 on average |
| acceptance cost | $0.87 to $1.59 | $2.74 (one acceptance over 14 stories) |
| total | $15.89, 59 runs, 8 stories, 3 acceptances | $28.13, 107 runs, 14 stories, 1 acceptance |

Conditions: run 4 ticked every 2 minutes fixed; tonight the pause started at 15 seconds and doubled to 120. The session answered questions within about a minute of their post and approved within about two minutes of the pull request turning ready. Tonight's stories were larger: 21 criteria on average (14 to 26), against run 4's largest of 26. The dollars are Claude Code's list prices under a subscription login.

## Usage

- 23:17: 5-hour window 1%, weekly 53%.
- 00:46: 57%. 02:03: 83%. 02:44: 93%, starts held until the window reset at 03:30.
- 03:39: 0% after the reset. 04:48: 15%, weekly 66% (the weekly window resets at 05:00).

## What needs the operator

- **F0001-S0015 before any feature that pushes.** `GitCli.push("--force")` reads a branch name starting with `-` as an option and really force-pushes (the acceptance report's one finding of weight). No caller exists yet. S0015 and the other three proposed drafts (S0016 negative measures in a reply; S0017 four untested failing sides; S0018 documentation repair) are in `factory/features/F0001-boundaries/drafts/`; start them, or edit them first.
- The acceptance report's open points: the hosting protocol is wider than R10's list (`find_open_pull_request`, `set_draft`, `set_description`); `set_labels` reads label names internally beside R10's "never read back".
- The interface sheet (`planning/overnight/interfaces.md`, with its amendments at the end) and the working answers (`planning/overnight/skeleton-answers.md`): the stories of F0002 to F0011 rest on them.
- F0002 to F0011: drafted (65 stories), cross-checked once (`cross-check-1.md`: three blockers answered, should-fixes open), not audited or pre-checked. F0010's draft has placeholders for the image digest and package versions and ships no stage texts.
- Decision 007 to confirm (accepted on your answers before the night).
- The traceability's morning observations: ST3.3, ST5.1, WE3.1, WE3.3, WE3.4 (`planning/overnight/traceability.md`).
- The `mutants` decision (left out of the seed; the acceptor read branch coverage instead).
- The items v1 could not build tonight: WE1.4, WE4, WE5 and R35's rewrite.
- The fault-path table's open questions (`planning/overnight/fault-paths.md`).
- Housekeeping: delete the scratch repository `pkrahmer/factory-night-scratch`; the old branch `ccr-cf8b451b-yugt27` of `factory-rf` still exists; the heartbeat job in this session is stopped; v1's container keeps running on `factory-rf` and idles (nothing is in `ongoing/`); `factory` is on `main` with the pre-push hook, and the image is tagged `factory:night-base-2026-10-12` (the old one `factory:pre-night-2026-10-05`).
