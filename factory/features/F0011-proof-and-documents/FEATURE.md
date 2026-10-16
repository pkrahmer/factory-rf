# Proof and documents

## Goal

Show that v1.1 recovers and says so. Recovery is proven by injection tests at each named kill point, against a real local bare remote and the fake hosting client; each of v1's thirteen fault-injection paths is walked by a named test, `reject` included; every stop that v1 let reach only a log is listed with its destination, a test for each row; and the four documents state what v1.1 does, in the glossary's names, with nothing an item replaced, checked by a command. It is for the operator, who must trust a restart, and for the next agent, who must find the stops and the proof in the documents. Done when each of the six kill-point cases and each of the thirteen fault-injection paths has its passing test, each row of the stop table has its test, and `python -m factory.entry.check_documents` prints `documents ok` on the four documents.

## Scope

- The six kill-point cases of the recovery proof (the tick dies during an agent run; the agent run dies while the tick lives; the tick dies between a commit and its push; between a post and its record; at any other point; the container is lost) as data and as injection tests, with the pass lists of the crash class and of the stall class, and the two caps that repeated failures reach (WE1.1, R36)
- The thirteen fault-injection paths as data and as named injection tests, one kill or one stall each, and `reject` walked (WE1.2, WE1.3)
- The stop table: every stop of v1's limits L11, L19, L26, L30, L33, L55, L58, L64 and L65 with its destination (the health status and the factory log, or the work item's pull request, or none where a rule removed the stop), a test per row (ST3.5)
- The four documents (README, operator guide, project guide, decision log): a document check as a domain function and a command, and the documents written to pass it (WE6.1, WE6.2, WE6.4, WE6.5, R17)

## Out of scope

- The baseline run on the shipped code and its records (WE1.4, WE5), and the end-to-end run's summary and root-cause table
- A real container kill, and a second-instance test
- The producers of the machine stops (the preflight, the health check, the entrypoint): their own features test them; this feature proves where each stop goes
- Document errors that v1.1 did not make wrong
- WE6.3, every story's docs criterion naming its documents: it is checked across the stories, not by a test of this feature
- Wiring the document check into `make check` or adding a console script: the Makefile and `pyproject.toml` are outside the coder's write paths

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Kill-point tests
- S0002 — Fault-injection paths 1 to 6
- S0003 — Fault-injection paths 7 to 13, and reject walked
- S0004 — The stop table
- S0005 — The four documents

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. A kill after a stage's result is pushed (between a post and its record) charges no crash; a kill while a stage is in flight charges one. The table of cases records this as `charges_crash`. (S0001, story text)
2. The restart in every kill-point case advances the manual clock by 5 seconds, and the time from the kill to the rerun's stage-start commit must be exactly that, recorded as a test property; no real time is measured. (S0001, story text)
3. Every interrupted stage in the kill-point cases ends its completed run with a `question`, not a forward move, so that the `crashes` counter is still visible at the end (a forward move resets it). (S0001, story text)
4. "The tick at any other point" is the kill right after the claim's push (`AFTER_PUSH` with `after=0`); the pushes of results and of the human's acts are the paths' kill points. (S0001, story text)
5. The crash cap is reached by two kills in one stage: the first restart reruns, the second restart asks the human. (S0001, story text)
6. Each of the thirteen paths is walked with one kill or one stall, chosen by judgment as `fault-paths.md` proposed; none is mapped to a removing item, because v1.1 keeps every mechanism they exercise. (S0002 and S0003, story text)
7. Path 1's second half (a smoke test without `Expect:`) is walked by the story form check, not by a kill. (S0002, story text)
8. Path 13 (`doing` to `tests` after the human approves a test change) counts no round; the round counter stays 0. (S0003, story text)
9. Path 11 uses a close without a comment, so the send-back question is the post that must appear once. (S0003, story text)
10. The four further paths of v1's run 1 are not rows or tests; the project guide notes where each went. (S0002, story text)
11. The stop table has fourteen rows. A backlog story whose own file names a later stage (L11) is a row with the destination `none`, because the start rule removes the stop. (S0004, story text)
12. A stop of a work item is reported after the error cap of 3 on the same event and state, once; the machine stops are proved through the stop service and by a search that production code names each reason, because their producers belong to F0003, F0006 and F0010. (S0004, story text)
13. The document check is a domain function plus `python -m factory.entry.check_documents`; it is not part of `make check` and has no console script. (S0005, story text)
14. The decision log is exempt from the lists of replaced phrases and v1 words, because it records what was replaced and renamed. (S0005, story text)
15. The operator guide must hold a table row for every stop of the table, and the project guide one for every kill-point case and every fault-injection path; the check finds them by the id or test name in backticks on a line starting with `|` outside code fences. (S0005, story text)
16. Every document except the decision log may keep one section, `## Replaced from v1`, that the two word lists do not read, so that the statements other stories require (no `--follow` mode, v1's leftover files, this repository's own v1 tree) can be written without a finding; the same words anywhere else are findings. (S0005, story text)
17. The thirteen paths are split over two stories (paths 1 to 6, paths 7 to 13) because one story with thirteen end-to-end scenarios is more than a tester's budget and lease allow; the first story creates `FAULT_PATHS` with its six rows and the second appends the other seven. (S0002 and S0003, story text)
18. A path's `case` names the kill point the path arms; the path's own crash charge may differ from the case's `charges_crash`, and the project guide says so. (S0002 and S0003, story text)
19. A second in-progress file of an id that already has a branch is read from the main branch, so that the duplicate reaches the pull request instead of failing every tick. This changes F0006's code (`RemoteWorkItems.read`), not its tests. Taken by the session for the human, to confirm. (S0004, story text)
