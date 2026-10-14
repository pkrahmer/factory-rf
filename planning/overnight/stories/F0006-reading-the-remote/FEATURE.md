# Reading the remote

## Goal

Every tick of the factory fetches first, reads every work item from the remote-tracking refs only, decides in four tiers what is to be done, and hands the one resulting event to its handler through a dispatcher that counts errors per event and remote state and reports once at the cap. The local checkout follows the remote and is disposable. Done when a hand push to a remote branch is seen past a stale local branch, a failed fetch is a reported repository stop, a rejected push is judged from the remote's state with at most one report, a fresh clone continues every work item, an event kind without a handler is a counted error, no merge method is misread as an illegal stage change, the watcher's command line has no `--follow`, and every event kind built so far has a handler in the production wiring.

## Scope

- Reading work items (R18): the stories in `in-progress/` on `origin/main`, each with its state from its own remote branch, never from a local branch or the work tree; plain id order; a started story without a branch is at the first stage with initial counters, whatever its file says (ST6.1)
- The evaluation: four tiers, one event per evaluation, waiting work items holding back new work, at most one pull request lookup, the claim tier through the claim service, the attempts-cap question, `run`, `idle`, two work items with one id
- The dispatcher and the tick status (R28, SI2.4): every event kind has a handler or raises as a counted error; errors counted per event and remote state; the cap reported once; a push to the work item's remote branch retries (GH5.4)
- The tick: fetch first, a failed fetch a repository stop (GH5.3); load and validate the pipeline definition; restore the checkout to the remote, with the local branches of the work items deleted; after a rejected push the remote's state judged, with at most one report (GH5.2); a fresh clone continues every work item (GH5.5); the tick reads and writes no run record and no lock, and v1's leftover files change nothing (GH1.5)
- The move rule: an illegal stage change judged after the pull request's state is read, so no merge method is misread (ST2.3); every stage change the factory makes itself is legal under the pipeline definition (ST2.4)
- The command line: evaluate once and print the event and the board of features and work items; no `--follow` (SI3.1) and no `factory-last-line` file (SI3.2)
- The production wiring (questionnaire 1, Q20): the handlers of `idle` and `run` registered in `factory.entry.wiring`. The `run` handler wraps F0005's `StageRunner` and gets the agent run's environment with `PATH` and `HOME` (F0005 decision 23). A test checks that every event kind built so far has a handler.

## Out of scope

- The handlers of the human's acts (comments, questions, merge, close, `reject`, the hand-over): feature F0007
- The handlers of a crash and of an expired lease: feature F0008
- The acceptance's derivation and its column on the board: feature F0009
- The preflight and its place after the fetch, and the scheduler loop with its pauses: feature F0010
- Completing `build_boundaries` from the instance settings: F0010-S0001

## Stories

The order is the story numbers. A later number may start first if it is the only one moved to `ongoing/`.

- S0001 — Work items read from the remote-tracking refs
- S0002 — The watcher's evaluation in four tiers
- S0003 — The dispatcher and the tick status
- S0004 — The tick: fetch first, then the remote's state
- S0005 — The move rule reads the pull request first
- S0006 — The watcher's command line
- S0007 — The production wiring of the dispatcher

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken.

1. A branch whose tip is an ancestor of `origin/main` is still read as the work item's branch. v1 skipped such branches; here the listing comes from `in-progress/` on `origin/main`, so an archived story is never listed, and a story merged by a merge commit but not yet archived must keep its state to be seen as merged. A story whose branch was deleted before its archive (for example by a hosting setting) is read as new; the operator guide must say so (S0001 criterion 20). The related case of an agent run on a story the human already merged stays open (cross-check 1, finding 10). (S0001, story text)
2. A story whose file is missing on its work item branch, or whose front matter cannot be read, stops the reading with `WorkItemFormatError` naming the path; a story whose stage the definition lacks makes the evaluation raise `ValueError`. The tick does not catch either: no repository stop reason exists for them, and the error shows on every tick until a human repairs the file (S0004 criterion 19). Alternative for the human: add a repository stop reason `work_item_unreadable` to `factory.domain.stops`, raised by the tick with the path and cleared by the first tick that reads every work item. (S0001, S0004, story text)
3. A work item waits for the human when `blocked` is set or its stage is an approval. Only the first waiting work item in id order gets the tick's one pull request lookup (v1's limit, kept). The lookup is one `get_pull_request` and, when the pull request is open, one `list_comments`. (S0002, story text)
4. A waiting work item whose pull request is open and has nothing new yields `idle` and holds back all new work. A claim held by another instance within its lease is also `idle`; v1's `busy` is gone. (S0002, story text)
5. A recorded question counts as posted when the pull request holds a factory comment keyed with the work item, a kind equal to `blocked`, and the number of the last journal entry. The stages that block a work item must therefore make the asking entry the last journal entry (features F0005, F0007, F0008 must key their posts that way). (S0002, story text)
6. A waiting work item without a pull request yields `ask`; the handler of F0007 turns that into a counted error (ST3.1). (S0002, story text)
7. The first work item in id order that carries a claim decides the claim tier: an own claim is `crash`, an expired one `expired`, a held one `idle`. (S0002, story text)
8. An error count is kept per event and the work item's remote state. A success clears the event's counts. At three errors one report is posted on the pull request, keyed to the first 12 characters of the remote state, and the event is not tried again on that state; a new commit on the work item's branch is a new state and starts the count again. The report text says so. A failed report does not change the count. (S0003, story text)
9. An event without a work item (`idle`, a feature's acceptance) has no pull request to report on: at the cap one line goes to the factory log, if the dispatcher was given a log (the tick gives it the factory log). The report of a work item without a pull request opens its draft pull request first; the dispatcher does not record the opened number in the work item. When that cannot be done because the work item has no branch on the remote (the stop service refuses a pull request without a commit beyond `main`), the report is a log line too and the event is marked reported, so that the failure is not retried for ever. (S0003, story text)
10. The tick runs in this order and ends at the first repository stop: fetch, load the pipeline definition, restore the checkout, evaluate, dispatch. Each repository stop is cleared by the first tick on which its cause is gone; the stop for an invalid definition is raised and cleared by the loader, never by the tick. The restore discards uncommitted changes and untracked files, keeps ignored paths, deletes the local branches `work-item/<id>` of the work items the remote knows (a local branch of a work item that has left the remote stays, since `Git` cannot list local branches), and writes one line naming what it discarded. (S0004, story text)
11. The tick keeps no lock and no memo file; v1.1 has no run record (questionnaire 1, Q3), and v1's leftover files in `.git/` change nothing. It keeps its tick status in memory across ticks and builds its dispatcher after each load, from a handler factory, because the handlers take the loaded definition. (S0004, story text)
12. A stage change is judged only on the work item's own branch and only in the last commit beyond `origin/main` that touched the work item's file. A merge commit, a first commit, the opening commit (whose parent is the text on `origin/main`) and an unreadable previous version are never a change. The factory's own correction is recognised by the journal kind `move_back`, not by the commit message. A change from an approval stage to `done` is legal even when its `next` does not list `done`. The stage-change record of the move rule is called `FactoryMove`, because `StageMove` is F0005-S0006's decision. (S0005, story text)
13. `factory-watch` does not fetch: it shows the remote as the last tick left it, and it loads the pipeline definition at the head commit of `origin/main`, which raises or clears no stop. It prints one event line, a blank line and the board, and exits 0 once the pipeline definition loads. A feature appears on the board when it has at least one story file; its title is the first heading of its `feature.md`, else its directory name. Until F0010-S0001 wires the instance settings, `main` called without boundaries exits 2 with a line that says so; a request for `--follow` exits 2 from the argument parser before anything else. (S0006, story text)
14. A capped event holds back all new work, like a waiting work item: after the report on a `run` event, every tick evaluates the same first runnable work item and the dispatcher answers `capped`, so no other work item runs until the human pushes to that work item's branch. Alternative for the human: skip a capped work item in tier 4. (S0004 criterion 20, S0002, story text)
15. `Event` validates its shape: no work item for `idle` and `acceptance_due`, one for every other kind, and a feature for `acceptance_due` and for no other kind. The evaluation validates every stage against the definition before it calls `role_of` or `position`, which settles the question F0003 left to its first caller. (S0002, story text)
16. The production wiring grows with each feature (questionnaire 1, Q20). This feature registers `idle` and `run` in `factory.entry.wiring.build_handlers`; the constant `NOT_YET_HANDLED` lists the kinds still without a handler, and a later feature that registers one removes its kinds from the constant and edits no test of this feature. The agent run's environment is a `PATH` (the directory of the running interpreter's scripts, so `factory-guard` is found) and a `HOME`; F0010 scrubs it and probes both. The sheet's amendment names `build_dispatcher`; the tick builds the dispatcher itself, so the wiring function is `build_handlers`, with `handler_factory` for the tick. (S0007, story text)
