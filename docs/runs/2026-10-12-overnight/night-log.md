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
