---
stage: docs
pr: 20
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
2. intake: accepted
   - Interface: "None: documentation only". There is no comment stating behaviour and no rule with a failing side, so steps 3's requirements are vacuous.
   - Criteria: 1 to 5 each name one file and one checkable wording change (the stale phrases can be found with grep, and the replacements are named). 6 and 7 are the two closing criteria. 7 is open-ended ("anything else F0001 left stale"), but it is the documenter's standing docs criterion and not a build decision.
   - Demo: one runnable grep line. Its Expect line is checkable: three lines, each `0`, and the exit status 1 is explained.
   - Architecture: no code, layers or dependencies change. Only `README.md` and `docs/` are touched, and the documenter's lane covers them.
   - Scope: documentation repair across F0001's stories, listed as S0018 in FEATURE.md. Decision 21 says the repair runs through the pipeline. It is not in "Out of scope".
   - Note for the next stage: the assignment says there is nothing for the tester and coder to build.
3. tester: no tests written; this is a documentation-only story.
   - The Interface is "None: documentation only", and the Assignment says the tester and coder stages have nothing to build. Criteria 1 to 5 are wording changes in `README.md`, `docs/project-guide.md` and `docs/operator-guide.md`. Their check is the Demo's grep line, which the documenter and the demo stage run.
   - Rejected: pytest tests that grep the docs for phrases. Tests would then pin documentation prose, which is the documenter's to word. Nothing in the criteria asks for that, and it would break the rule that tests do not name tickets or criteria.
   - Criterion mapping: 1 to 5 go to the documenter and the Demo grep; 6 is `make check`, unchanged by this stage; 7 is the documenter's cross-read.
   - Files created: none. Modules the test runner could not import: none, since no new tests exist. `make lint` is green.
   - Next: the coder stage has no code to write and can hand straight on to the documenter.

   `make lint`: lint: green
   `make test`: test: green
4. coder: no code written; this is a documentation-only story.
      - Built: nothing. The Interface is "None: documentation only". The Assignment says the tester and coder stages have nothing to build, and the tester wrote no tests, so `make test` has no failing tests to implement against.
      - Rejected: editing `README.md`, `docs/project-guide.md` and `docs/operator-guide.md` here. `CLAUDE.md` gives those files to the documenter stage ("the coder does not write them"), and criteria 1 to 5 and the cross-read in 7 belong to that stage.
      - Refactor: not applicable. The branch has no diff outside `factory/`.
      - Checked: `make check` is green on the unchanged branch (coverage 99.49 %).
      - Open: everything in criteria 1 to 5 and 7 is still to do, all of it for the documenter. The review stage has no code diff to read.

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the ticket, so there is no code, test, architecture or security surface to review.
      - Acceptance criteria: 1 to 5 are wording changes in `README.md`, `docs/project-guide.md` and `docs/operator-guide.md`. `CLAUDE.md` gives those files to the documenter stage, which comes after this one. Their check is the Demo's grep line, run by the documenter and the demo stage. The Interface is "None: documentation only", so no rule has a failing side that would need a test. I agree with the tester's decision not to pin documentation prose in pytest.
      - Criterion 6: the coder's entry records `make check` green on the unchanged branch (coverage 99.49 %).
      - Ticket hygiene: the tester's and coder's entries give the main decision (nothing to build) and what was rejected. `Assignment` still matches, since the work it describes is the documenter's and none of it is done yet. Criterion 7 still says what the documenter must do.
      - Open for the documenter: all of criteria 1 to 5, and the cross-read of `README.md` and `docs/` in 7. The demo stage then checks the grep line: three lines, each `0`.
