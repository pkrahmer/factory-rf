# The human on the pull request

## Goal

The pull request is the work item's face, and the human's acts on it are all the factory takes from the hosting service. This feature builds every handler of those acts, so that each one is kept through a kill or a failure. The human's comments are copied into the journal by their ids and never by a count. A comment or a close is committed and pushed into the work item before the factory posts, reopens or checks out anything. Questions are recorded, then posted with a key made from the recorded entry, so a repeat or a restart posts nothing twice. A merge archives the story at whatever stage it has reached, with its bill; a close before the approval returns the story to the backlog with the human's text unchanged and its bill empty; a close at the approval sends it back, or asks what to do. An illegal stage change is moved back. An answer ends the wait it answers. The hand-over at the approval is assembled by code from the work item's data and retried from its state until it completes. A handler that cannot do its work raises, so that every event, comment events included, is counted and bounded by the error cap and reported once on the pull request. Done when each handler keeps the human's act through a kill or a failure, none repeats a post, every comment event is bounded by the error cap of three, and a close or a merge found right before an agent run is handled before that run.

## Scope

- The shared plumbing of the handlers: `CannotHandle`, the helpers that take a work item and its pull request number out of an event, and the recorder that resets a branch to the remote's head, commits and pushes a change.
- Comments copied by id: new comments without the factory marker become dated `human` entries of the journal, their ids go into `comments_read`, recorded and pushed before any effect (GH3.1, GH3.2, R22, R34).
- Questions: a recorded question posted with a key made from its journal entry (an agent's, the round cap's, the send-back's and the crash cap's); the attempts-cap question recorded and then posted.
- Merge: the story archived to `done/` at whatever stage, its cost records moved with it, its `done` entry with the bill, its branch deleted after the archive is pushed.
- Discard: a close before the approval returns the story to `backlog/` with the human's text unchanged and deletes its branch; started again, its bill is empty (GH4.3).
- Send-back: a close at the approval recorded first (GH3.3), the pull request reopened as a draft, the reason taken from the journal's data, `round` + 1 within the cap of the stage that hands over to the approval, else the send-back question with its three options.
- `reject`: a stage change that the pipeline definition does not allow is moved back by a commit marked `moved back`, with a keyed correction note (GH3.5).
- Answers and comment events: an answer ends the wait it answers and resets what the sheet says it resets; a comment at an approval is only recorded; every comment event is bounded by the error cap (ST1.1).
- Stops that cannot be done: `duplicate`, `pull_request_lookup` and an `ask` without a pull request are counted errors and reported at the cap (ST3.1, R28).
- The hand-over at the approval: the description assembled by code from fixed sections and the latest `result` entries read by speaker as data, the pull request marked ready, the cost table posted once, `handed_over` recorded last, retried from state and reported at the cap (ST1.2, ST1.3).
- The pull request read before every agent run, with a close or a merge handled first; the handlers of this feature registered in `factory.entry.wiring.build_handlers` (F0006-S0007), the `run` handler gated, and their kinds removed from `NOT_YET_HANDLED`.
- The texts the handlers post or write into the journal, in `factory.domain.post_texts`.

## Out of scope

- The acceptance's merge, refusal and hand-over text: F0009. The handlers here handle stories; what they do with an acceptance is not specified.
- Which state raises which event (the watcher's evaluation, the dispatcher and the tick): F0006; F0007 registers its own handlers in F0006's `build_handlers`. F0007 depends on one rule of F0006-S0002's evaluation: `question_posted` compares the post's `n` with the number of the latest `question` record, not of the last record (comments are recorded after a question that waits to be posted); and on F0006-S0005's `last_stage_change`, which the `reject` handler uses to find the change the watcher judged.
- The crash-cap question and the rerun after a crash: F0008. Only the effect of the human's answer on the state is here. F0008 passes its rerun through `RunGate` (S0010).
- Counting comments by author (out of v1.1): the factory's marker alone tells its posts from the human's.
- A comment written while the stages work gets no new meaning (left for v2); it is copied at the next stop, and it answers no question that the factory posts after it (S0007).
- Labels as a projection of the stage: F0005; F0007 writes them again after a send-back and after a move back (S0005, S0006), the only places where the stage changes without a result commit.
- The line of v1's description that says a story is the last of its feature: not kept; the acceptance (F0009) announces a complete feature.

## Stories

- S0001 — The human's comments copied by id
- S0002 — Questions recorded, then posted
- S0003 — A merge archives the story with its bill
- S0004 — A close before the approval discards the story
- S0005 — A close at the approval sends back, recorded first
- S0006 — An illegal stage change moved back
- S0007 — Answers unblock, and comment events are capped
- S0008 — Stops that cannot be done are counted errors
- S0009 — The hand-over at the approval, retried from state
- S0010 — The pull request read before every agent run

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. A comment is the human's when its body carries no factory marker, whoever wrote it; a comment that starts with `factory:` is therefore copied into the journal, which v1 did not do. (S0001, story text)
2. A comment is copied as one journal entry holding its text, with `\r\n` turned into `\n` and the whitespace at its two ends removed (the journal strips every entry), dated with the day it was written (UTC); a comment whose body is blank is marked as read and not copied. (S0001, story text)
3. A recorded question is posted as `<speaker>: <the entry's text>`, so the human sees who asks. (S0002, story text)
4. The attempts-cap question is asked as soon as `attempts` reach the attempts cap; it names the stage, the number of stalls and the last stall, and offers two ways: comment to retry (the attempts go back to 0) or close to discard the story, which says what a close does (the story goes back to the backlog as the human wrote it, its branch and bill are deleted). (S0002, story text)
5. A merge archives the story at whatever stage it has reached, with the entry `done (pull request merged); cost: <the cost line>`; its cost record file moves beside it into `done/`; the pull request gets no post. (S0003, story text)
6. The story's branch is deleted only after the archive is pushed, so a kill between the two leaves the merged branch on the remote, and nothing deletes it later. (S0003, story text)
7. A close before the approval puts the story back in the backlog byte for byte as the human had it, deletes the branch with its journal and bill, and posts nothing; the pull request stays closed. (S0004, story text)
8. A kill or a failure after the story is moved and before its branch is deleted leaves the branch behind; the operator must delete it by hand before the story is started again, or the old branch with its old bill would continue. A branch whose deletion the remote refuses is left the same way, and the handler raises `PushFailed`. (S0003, S0004, story text; see 21)
9. A close at the approval sends the story back to the second stage in the approval's `next`; `round` goes up by one at every send-back, counted against the `round_cap` of the first stage, in the pipeline definition's order, whose first `next` is the approval and that has a `round_cap`. (S0005, story text)
10. The reason of a send-back is any comment copied after the latest `result` entry, whether copied earlier or at the close; the factory does not read what the comment says. (S0005, story text)
11. No reason, or a send-back past the round cap (the cap wins when both hold), gets the send-back question with three options: comment, close again to discard, or mark ready and merge. (S0005, story text)
12. The close is recorded with the day the factory read it, not the day the human clicked. (S0005, story text)
13. If the factory is killed after the pull request was reopened and before the send-back was recorded, the work item is handed over again at the approval and the close has to be repeated; a `set_draft` that fails after the reopen leads to the same. A close already recorded after the latest `result` entry is not recorded twice, whatever comment came in between. (S0005, story text)
14. An illegal stage change is put back by a new commit on the work item's branch, never on the main branch; the journal entry reads `illegal stage change <old> -> <new>, moved back.`; the note on the pull request names the pipeline definition file. (S0006, story text)
15. A comment answers a wait only when it was written after the factory's post of that wait (the pull request holds a factory post keyed to the blocked value and the number of the latest question entry, and the comment's id is greater than the post's id) and its body is not blank; older comments are recorded and the wait stays, so that a comment written while the stages worked never answers a question the human has not seen. Any such comment on a blocked work item answers it. The attempts-cap answer sets `attempts` to 0; the crash-cap answer sets `crashes` to 0; the round-cap and send-back answers change no counter, so the next send-back at the cap asks again, as in v1. A comment at the approval, or on a work item that is not blocked, is only recorded. (S0007, story text)
16. A `duplicate`, a failed pull request lookup and an `ask` without a pull request are retried three times on the same remote state and then reported once on the work item's pull request, which is opened as a draft when there is none and its branch is on the remote with a commit beyond `main`; a work item without such a branch gets a line in the factory log instead (F0006-S0003). (S0008, story text)
17. The pull request description at the approval has the sections Description, Acceptance criteria, Tests, Review, Documentation, Smoke test and Commits, then a closing text; any merge method accepts the story, so the closing text no longer asks for a merge commit; v1's line saying that a story is the last of its feature is dropped. (S0009, story text)
18. The hand-over replaces the whole description, anything the human wrote there included, and posts the cost table once per hand-over. (S0009, story text)
19. The tester, reviewer, documenter and smoke tester are named in the code for the description's sections. (S0009, story text)
20. A close or a merge found right before an agent run is handled first: the story is discarded or archived without that run. (S0010, story text)
21. A kill or a refused deletion between the pushed discard and the deletion of the story's branch leaves the old branch with its closed pull request on the remote; when the human then starts the story again, the old state with the closed pull request is read from that branch, the `RunGate` discards the story again, and GH4.3 (a story started again starts with an empty bill) fails on this path. F0007 builds no cleanup of its own; the option that keeps the human's start and the resume without a human is that F0006's tick deletes the remote branch of any work item whose file is in `backlog/` on `origin/main` (the alternative: F0005-S0002's opening deletes a branch whose recorded pull request is closed, when it opens a started story). It needs a story in F0006 or F0005, for the human to decide. (S0004, audit F0007-1)
22. The handlers that clear a claim (S0003, S0005, S0006) set the field to `None` in the state and do not call `ClaimService.release`, because the service is built for an instance name and a pipeline definition that these handlers do not hold; `tests/test_claim_ownership.py` allows it. (S0003, S0005, S0006, audit F0007-1)
23. The registration of the handlers is F0006's `build_handlers`, by the human's answer to questionnaire 1, Q20 (A); it changes three tests of F0006-S0007 (its criteria 4, 5 and 9 in `tests/entry/test_wiring_handlers.py`), which S0010 names. (S0010, audit F0007-1)
24. After a send-back and after a move back the pull request's label is set again at once (`labels_for` of the new state), so that it does not show the old stage until the next stage finishes; a `set_labels` that fails raises and leaves the recorded change in place. (S0005, S0006, audit F0007-1)
