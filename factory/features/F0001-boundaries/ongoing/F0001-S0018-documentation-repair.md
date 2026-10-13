---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation repair after Boundaries

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Each F0001 story kept its own part of the documentation true. Read as a whole, though, four places are stale or doubled. No code changes, so this story is the documenter's alone. The tester and coder stages have nothing to build.

1. **`docs/project-guide.md`, *Kill points*.**
   - "This story built only the seam. A wrapper calls `kill_points.reach(point)` at its point in its own story; until then nothing reaches a point." This is false now: all four points are reached by their wrappers. It is also ticket language in the docs.
   - The table says `AGENT_RUN` is reached "while an agent runs". The runtime sections say after the run's writes (the fake) and after the last call and the result (`claude -p`).
2. **`README.md`.**
   - The status sentence leaves out the project commands (the make class).
   - It describes the git wrapper as "reading, clone, checkout, commit and push", leaving out branches, merge, reset, revert and move.
   - "Where to look next" calls `docs/operator-guide.md` "not yet written".
3. **`docs/operator-guide.md`, intro.** "Nothing is built yet, so there is nothing to install or configure." Parts are built; what is true is that there is no command to run yet.
4. **`docs/operator-guide.md`, *The agent runtime*.** The last paragraph repeats the stall rule and the unknown cost of a timed-out run from the paragraph before it, and says "story" where `CLAUDE.md`'s vocabulary has "work item".

## Interface

None: documentation only.

## Acceptance criteria

1. The *Kill points* section of `docs/project-guide.md` no longer says that nothing reaches a point. It says that each wrapper in its table reaches its point.
2. The `AGENT_RUN` row says the point is reached after the agent's writes and after the run's last call, as the agent-runtime sections say.
3. `README.md`'s status sentence names the project commands and all of the git wrapper's kinds of operation (reading, writing and pushing, branches and merge, restoring the checkout), and its link to `docs/operator-guide.md` no longer says "not yet written".
4. `docs/operator-guide.md`'s intro says what is built and that there is no command to run yet, instead of "Nothing is built yet".
5. `docs/operator-guide.md`'s *The agent runtime* states the stall rule and the unknown measures of a timed-out run once, and uses "work item", not "story".
6. make check stays green.
7. docs: this story is the documentation change. The documenter cross-reads `README.md` and `docs/` once more for anything else F0001 left stale.

## Demo

```bash
grep -c "until then nothing reaches a point" docs/project-guide.md; grep -c "not yet written" README.md; grep -c "Nothing is built yet" docs/operator-guide.md
```
Expect: three lines, each `0`. grep exits 1 when it counts nothing; that exit is the expected result, not an error.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
