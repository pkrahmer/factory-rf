# Crash recovery

## Goal

A crash is the death of the tick or of the container. This feature makes the factory recover from one without a human: the stage that was in flight is discarded and rerun from its pushed stage-start commit with no attempt charged, a `crashes` counter per work item counts it against the crash cap of the pipeline definition (default 2), and at the cap the human is asked on the pull request and the stage does not rerun until answered. A restart with the same instance name reruns the stage at its first look, without waiting out the lease or an idle pause; an instance with another name takes the stage over only when the lease has expired, and handles that expiry as a crash too. The notes the factory posts say "retrying" only where a retry follows. Done when a kill during an agent run leaves no write of that run on any branch, the stage-start commit and its "started" entry stay in history, the discarded cost records are gone, the stage reruns with `attempts` unchanged and `crashes` one higher, the crash cap asks the human and the counter is reset when the stage moves forward, and no stall or expiry note says "retrying" at its cap.

## Scope

- A recovery handler for the `crash` event (own claim found at the first look): uncommitted work, untracked files and unpushed commits of the dead stage thrown away, one commit that records the crash on top of the stage-start commit, a rerun of the stage in the same call (GH2.1, GH2.2, GH2.3, GH1.3, R23, R24)
- The crash cap: the human asked on the pull request at the cap, no rerun until answered, the answer resets `crashes`, a forward move of the stage resets it (GH2.4)
- The expired lease of another instance, handled as a crash by the same handler, with its note (ST1.4)
- The wording of the stall note and the expiry note: "retrying" exactly where the next tick or the same call retries (ST1.4)
- Journal entries of kind `crash` and `expiry`, written by code

## Out of scope

- Deciding which event a work item gets (own claim, held claim, expired claim) and raising `crash` and `expired`: the watcher, F0006
- Claim, lease and expiry functions: F0004
- A stall, which costs an attempt: F0005
- Posting a recorded question again after a kill between its record and its post: the `ask` event's handler, F0007
- The scheduler's pauses and the dispatcher's mapping of event kinds to handlers: F0006 and F0010
- The kill-point tests across all five kill points and the fault-injection paths: F0011
- A second-instance test (dropped, R2) and a watchdog for a dead container

## Stories

- S0001 — A crash discards the stage and reruns it free
- S0002 — The crash cap asks the human
- S0003 — An expired lease, and notes that say retrying only when true

## Decisions taken for the human

1. A crash is charged to the stage whose claim was held when the process died. A kill between one stage's pushed result commit and the next stage's claim holds no claim, so it raises no counter and the next stage starts as usual. (S0001, story text)
2. The rerun happens inside the same call that records the crash, in the tick that finds the dead claim, so a restart with the same instance name reruns at its first look and no idle pause is waited. (S0001, story text)
3. The crash is recorded in one new commit on top of the stage-start commit (claim cleared, `crashes` + 1, a journal entry of kind `crash` written by `factory`); the stage-start commit and its "started" entry are never rewritten or removed. (S0001, story text)
4. A crash of the instance's own stage posts nothing on the pull request; the journal entry is the only record. (S0001, story text)
5. The stage-start commit that the crash entry names is the head of the work item's remote branch, because the factory pushes nothing to that branch between a stage-start push and the stage's result push. (S0001, story text)
6. The human is asked as soon as the count after the crash reaches the crash cap: with the default cap of 2 the first crash reruns and the second asks. (S0002, story text)
7. The crash-cap question names two answers: any comment, which is copied into the journal, resets `crashes` to 0 and lets the stage rerun, and closing the pull request, which discards the story. The text of the comment is never read. (S0002, story text)
8. The question is recorded first (`blocked` is `crash_cap`, a journal entry of kind `question` by `factory`), pushed, and only then posted, once, under a key made of the work item, the kind `crash_cap` and the entry number. (S0002, story text)
9. `crashes` is reset to 0 by a forward move of the stage and by the human's answer to the crash-cap question; a rework move and a stall keep it. (S0002, story text)
10. A pull request opened by a stop gets the title `<work item id>: <story title>`, as in v1. (S0002, story text)
11. The expired lease of another instance is a crash: no attempt is charged and `crashes` is raised. A lease counts as expired when its age is at least `lease_duration` (60 minutes by default), as the lease functions of F0004 define it. (S0003, story text)
12. An expiry posts a note on the pull request (key kind `expiry`); at the crash cap it posts that note, worded without "retrying", and then the crash-cap question. (S0003, story text)
13. The note texts are fixed by the stories: `Retrying.` ends the note below the cap, and the note at the cap says the factory does not rerun the stage and asks instead. The expiry note does not name the instance that lost its lease. (S0003, story text)
