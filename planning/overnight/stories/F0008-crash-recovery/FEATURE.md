# Crash recovery

## Goal

A crash is the death of the tick or of the container. This feature makes the factory recover from one without a human: the stage that was in flight is discarded and rerun from the head of the work item's remote branch (its pushed stage-start commit, unless the human pushed to the branch meanwhile) with no attempt charged, a `crashes` counter per work item counts it against the crash cap of the pipeline definition (default 2), and at the cap the human is asked on the pull request and the stage does not rerun until answered; the human's answer lets the stage rerun with the counter at 0 (F0007-S0007). A restart with the same instance name reruns the stage at its first look, without waiting out the lease or an idle pause; an instance with another name takes the stage over only when the lease has expired, and handles that expiry as a crash too. The handlers of `crash` and `expired` are registered in the production wiring, and every rerun goes through the pull request gate. The notes the factory posts say "retrying" only where a retry follows. The tick deletes the branch that a kill left behind for a story already back in the backlog. Done when a kill during an agent run leaves no write of that run on any branch, the stage-start commit and its "started" entry stay in history, the discarded cost records are gone, the stage reruns with `attempts` unchanged and `crashes` one higher, a boundary error that repeats after a claim ends at the crash cap, the crash cap asks the human, `crash` and `expired` events reach their handler through `factory.entry.wiring.build_handlers`, a stale branch of a discarded story is gone after the next tick, and no stall or expiry note says "retrying" at its cap.

## Scope

- A recovery handler for the `crash` event (own claim found at the first look): uncommitted work, untracked files and unpushed commits of the dead stage thrown away, one commit that records the crash on top of the remote's head, a rerun of the stage in the same call through the pull request gate (GH2.1, GH2.2, GH2.3, GH1.3, R23, R24)
- The registration of `crash` (S0001) and `expired` (S0003) in `factory.entry.wiring.build_handlers`, with the registered `run` handler (F0007's `RunGate`) as the rerun, and their removal from `NOT_YET_HANDLED` (questionnaire 1, Q20)
- The crash cap: the human asked on the pull request at the cap, no rerun until answered (GH2.4); the path of a boundary error that repeats after a pushed claim and ends at the cap (F0005 decision 8)
- The expired lease of another instance, handled as a crash by the same handler, with its note (ST1.4)
- The wording of the stall note and the expiry note: "retrying" exactly where the next tick or the same call retries (ST1.4)
- Journal entries of kind `crash` and `expiry`, written by code
- The deletion of the remote branch of a story whose file is back in `backlog/` on `origin/main`, by the tick (S0004; F0007 decision 21)

## Out of scope

- Deciding which event a work item gets (own claim, held claim, expired claim) and raising `crash` and `expired`: the watcher, F0006
- Claim, lease and expiry functions: F0004
- A stall, which costs an attempt: F0005
- Posting a recorded question again after a kill between its record and its post: the `ask` event's handler, F0007
- The scheduler's pauses: F0010; the dispatcher and `build_handlers`: F0006 (this feature registers its two kinds there)
- The reset of `crashes` on a forward move: F0005-S0007 (F0005 decision 17); its reset by the answer to the crash-cap question: F0007-S0007 (`unblock`)
- The kill-point tests across all five kill points and the fault-injection paths: F0011
- A second-instance test (dropped, R2) and a watchdog for a dead container
- The branch of a merged story that a kill left behind (F0007 decision 6): not cleaned up; see decision 17

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — A crash discards the stage and reruns it free
- S0002 — The crash cap asks the human
- S0003 — An expired lease, and notes that say retrying only when true
- S0004 — A discarded story's stale branch is deleted by the tick

## Decisions taken for the human

1. A crash is charged to the stage whose claim was held when the process died. A kill between one stage's pushed result commit and the next stage's claim holds no claim, so it raises no counter and the next stage starts as usual (the `run` event of F0006-S0002, tier 4). This answers fault-paths' open question 3 (questionnaire 1, Q5). (S0001, story text)
2. The rerun happens inside the same call that records the crash, in the tick that finds the dead claim, so a restart with the same instance name reruns at its first look and no idle pause is waited. The rerun is the registered `run` handler, F0007's `RunGate`, so a story whose pull request the human closed or merged meanwhile is discarded or archived, not run. (S0001, story text)
3. The crash is recorded in one new commit on top of the remote's head (claim cleared, `crashes` + 1, a journal entry of kind `crash` written by `factory`); the stage-start commit and its "started" entry are never rewritten or removed. (S0001, story text)
4. A crash of the instance's own stage posts nothing on the pull request; the journal entry is the only record. (S0001, story text)
5. The discard goes back to the head of the work item's remote branch, and the crash entry names that head (`Its work is discarded back to commit <head>.`). The head is the stage-start commit, because the factory pushes nothing to the branch between a stage-start push and the stage's result push, unless the human pushed to the branch during the stage (the rejected result push of F0005 decision 8); then it is the human's commit, which stays in the history. The discard never removes a commit that the remote holds. (S0001, story text)
6. The human is asked as soon as the count after the crash reaches the crash cap: with the default cap of 2 the first crash reruns and the second asks. (S0002, story text)
7. The crash-cap question names two answers: a non-blank comment written after the question's post (F0007 decision 15), which is copied into the journal and, through `unblock`, resets `crashes` to 0 and lets the stage rerun, and closing the pull request, which discards the story. The text of the comment is never read. (S0002, story text)
8. The question is recorded first (`blocked` is `crash_cap`, a journal entry of kind `question` by `factory`), pushed, and only then posted, once, under a key made of the work item, the kind `crash_cap` and the entry number; its body is the one F0007's `ask` handler posts (`factory: ` and the entry's text). (S0002, story text)
9. `crashes` is reset to 0 by a forward move (F0005 decision 17) and by the human's answer to the crash-cap question (F0007 decision 15); a rework move and a stall keep it. The cap therefore counts the crashes since the last forward move, which can span two stages after a rework. (S0002, story text)
10. A pull request opened by a stop gets the title `<work item id>: <story title>`, as in v1. (S0002, story text)
11. The expired lease of another instance is a crash: no attempt is charged and `crashes` is raised. A lease counts as expired when its age is at least `lease_duration` (60 minutes by default), as the lease functions of F0004 define it. (S0003, story text)
12. An expiry posts a note on the pull request (key kind `expiry`); at the crash cap it posts that note, worded without "retrying", and then the crash-cap question. (S0003, story text)
13. The note texts are fixed by the stories: `Retrying.` ends the note below the cap, and the note at the cap says the factory does not rerun the stage and asks instead. The expiry note does not name the instance that lost its lease. (S0003, story text)
14. A boundary error after a pushed claim leaves the claim (F0005 decision 8); the next tick handles it as a crash, so an error that repeats on the rerun reaches the crash cap and asks the crash-cap question, and the error cap does not apply to it. (S0002, story text)
15. A crash-cap question whose post fails for a story without a pull request in its state (every first stage: F0005 decision 7 records the number only in the stage's next commit) leaves a recorded `crash_cap` wait with no pull request in the state. F0007's `ask` handler cannot open a pull request (it raises `CannotHandle`), so the question is not posted again; the human sees the error report of F0007 decision 16 instead. Alternative for the human: let the `ask` handler open the pull request for a `crash_cap` wait, a change to F0007-S0002. (S0002, audit F0008-1)
16. A lost expiry note is not posted again: the note is posted after the expiry commit is pushed, and a kill or a failure between the two loses the note and keeps the expiry, as with the stall note (F0005 decision 10). Below the cap the next tick then runs the stage as usual. (S0003, audit F0008-1)
17. A kill or a refused deletion between a discard's pushed move and the deletion of the story's branch leaves the old branch with its closed pull request, and a story started again would continue from it with its old bill (GH4.3 fails; F0007 decision 21). This feature builds the first option of that decision as S0004: the tick, after its restore and before the evaluation, deletes the remote branch of every work item whose story file is in `backlog/` on `origin/main` and not also in `in-progress/`. The window that remains is a start by the human before the first tick after the kill. Deleting a branch closes a pull request that is still open on it, so a story the human moved back to the backlog by hand loses its branch the same way. The branch of a merged story that a kill left behind (F0007 decision 6) is not deleted; the same step could cover stories in `done/`. Alternative for the human: F0005-S0002's opening deletes a branch whose recorded pull request is closed, when it opens a started story. The close sentence of the crash-cap question depends on this decision, as the attempts-cap question's does. (S0004, audit F0008-1)
