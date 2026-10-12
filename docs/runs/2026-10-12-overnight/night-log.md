# Night log, 2026-10-12

The overnight run of `factory-v2/planning/v1.1/overnight-run-plan.md`: v1 builds v1.1 in this repository, and a Claude Code session acts as the human. One row per act, newest last. Times are local (CEST).

| Time | Act | Pull request | Reason |
|---|---|---|---|
| 23:14 | Section 3 started with the operator present | | plan, section 3 |
| 23:29 | Phase 1: seed committed `3959086` "Set up the repository for the factory" (template fixes and project setup kept apart in the message) | | plan, section 4; brief `planning/overnight/briefs/seed.md` |
| 23:31 | Phase 1 check 1: `make check` green in a fresh clone on the host | | plan, section 4 |
| 23:32 | Phase 1 check 2: v1's container recreated with the image built from `factory` `main` and `REPOS=pkrahmer/factory-rf`; it cloned, ran `uv sync`, passed preflight (`factory-preflight-ok`), and ticks idle with no `waiting for`, `preflight failed` or `dirty` line. Fact: `is ready` is printed only after a `waiting for` line, so its absence is expected | | plan, section 4 |
| 23:33 | Phase 1 check 3: `factory-watch --board` prints a board with no rows | | plan, section 4 |
| 23:34 | Phase 1 check 4: a probe draft passes `factory-check-story` in `/tmp/probe` (no git checkout needed; it reads `factory/TICKET.md` relative to the working folder); a copy without its `Expect:` line fails with exit 1 | | plan, section 4 |
| 23:36 | Section 3 complete; the session goes unattended | | plan, section 3 |

## For the morning

- Decisions in the seed, recorded in `docs/decisions.md`: the package name `factory` and its four layers; the product paths `image/`, `template/`, `claude/` in the coder's write paths; no `mutants` target; the licence allow list extended by `GNU Library or Lesser General Public License (LGPL)` (PyGithub) and `Apache-2.0 OR BSD-3-Clause` (cryptography, through PyJWT and PyNaCl); the project guide in `docs/` so the documenter can keep it true; coverage `fail_under = 90`.
- The documenter's write path `docs/*` also covers `docs/runs/`; only `CLAUDE.md`'s rule keeps stages out of it.
- The old branch `ccr-cf8b451b-yugt27` of `factory-rf` still exists (its deletion was refused by the permission classifier).
- The scratch repository `pkrahmer/factory-night-scratch` (private), used to prove the command forms, is yours to delete.

- Fault paths (`planning/overnight/fault-paths.md`, open questions): whether WE1.1 means five kill points or the six rows of section 7.2; whether a crash after a stage's result (between commit and push, between post and record) raises `crashes`, and on which stage (working reading taken: yes, on the stage in flight); whether a close while the stages work and a merge while the move-back question is open need injection tests; the demo README's own path names were not read.

## Rows after going unattended

| Time | Act | Pull request | Reason |
|---|---|---|---|
| 23:37 | Phase 2 started: skeleton (opus) and fault-path table (opus) in parallel; brief templates for drafting, auditing, improving and the pre-check written | | plan, section 5 |
| 23:39 | Pre-check deviation: one opus subagent per feature plays intake and every later role, instead of sonnet for intake and opus for the rest (simpler, one output per feature) | | plan, section 7 |
| 23:40 | Fault-path table done (`planning/overnight/fault-paths.md`): 13 paths, each walked by one injection test with one kill point; none "mechanism removed"; one extra test for the crash cap. Working readings taken for feature 10's stories: one kill per path; run 1's four further paths only as a note; a crash anywhere in a stage counts on the work item whose latest pushed stage-start commit is in flight; the form check's unit test covers path 1's second half; ST2's rule reads the work item's remote-tracking branch | | decision 007, question 3 |
