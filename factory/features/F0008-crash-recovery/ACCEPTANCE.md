---
stage: accept
pr: 99
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0008-S0001, F0008-S0002, F0008-S0003, F0008-S0004]
---
# Acceptance of Crash recovery

## Verdict

**accepted with drafts.** The four stories together do what `FEATURE.md` promised. The feature demo exercises every clause of the Goal's "Done when" with the production `handler_factory` against a real remote, and it is green:

- a kill during an agent run, rerun at the first look by a restart with the same name;
- a boundary error that repeats after a pushed claim and ends at the crash cap;
- an expired lease taken over by a second instance, below and at the cap;
- stale branches of a discarded and of two merged stories, deleted by the tick once the remote allows it.

`make check` is green at 99.15 %. A hand mutation pass over the F0008 code kills 36 of 40 mutants. Two of the four survivors are equivalent; the other two are untested sides of the stale-branch step.

None of the findings is a broken promise:

- one stale sentence in the project guide;
- summaries in `README.md` and the operator guide that do not yet mention crash recovery;
- the two untested sides;
- `_state_of`, which is now copied ten times across `src/factory`.

I propose two drafts.

## 1 Scope

None. Each scope item has its story and its code:

| Scope item | Story | Code |
|---|---|---|
| Recovery handler for `crash`: discard, one commit on the remote head, rerun in the same call through the gate | S0001 | `src/factory/application/recovery.py` (`RecoveryHandler.handle`), `src/factory/domain/recovery.py` |
| `crash` and `expired` registered in `build_handlers`, `RunGate` as the rerun, both removed from `NOT_YET_HANDLED` | S0001, S0003 | `src/factory/entry/wiring.py` (`NOT_YET_HANDLED == ("acceptance_due",)`) |
| Crash cap: ask on the pull request, no rerun until answered; a repeated boundary error ends at the cap | S0002 | `RecoveryHandler._crash_recorded`, `ask_crash_cap`; `post_texts.crash_cap_question` |
| Expired lease of another instance handled as a crash, with its note | S0003 | `RecoveryHandler._note_expiry`; `evaluation.required_claim_status` / `CLAIM_EVENTS` |
| "retrying" only where a retry follows (expiry and stall notes) | S0003 (stall side traced to F0005-S0004) | `post_texts.expiry_note`, `stall_note`; `tests/test_retrying_wording.py` |
| Journal kinds `crash` and `expiry`, written by code | S0001, S0003 | `JournalKind`; `RecoveryHandler._crash_recorded` |
| Tick deletes the branch of a story in `backlog/` or `done/` | S0004 | `delete_stale_branches`, step 4 of `Tick.run` |

Out of scope stayed out:

- The watcher's choice of event is F0006's. F0008 only made `CLAIM_EVENTS` public, at S0003's review, and did not change its behaviour.
- No kill-point matrix (F0011), no second-instance test and no watchdog.
- The resets of `crashes` are used and not rebuilt: `unblock` (F0007) and the forward move (F0005).

## 2 Feature demo

The script is `/tmp/f8demo/demo.py` (md5 `d9e8c390e9af08e0c69a8f1c1a8bbf62`). It uses only real entry points:

- the production `handler_factory(boundaries, name, production_environment())` and a `Tick` per pass;
- a real bare remote with `GitCli` checkouts, two instances named `factory-1` and `factory-2`, each with its own checkout and its own `KillPoints`;
- a human clone (`tests/human_clone.py`);
- `FakeHostingService`, on which the human comments, closes and merges;
- `FakeAgentRuntime` with scripted runs. A killed run has `kill=True` and the instance's `KillPoint.AGENT_RUN` armed. Before it dies it also commits `src/committed.py` locally, as an agent may.

A restart is a new `Boundaries`, `KillPoints` and `Tick` of the same name. The pipeline is intake → doing → approval → done, with the defaults `crash_cap` 2 and `lease_duration` 60. Between steps 1 and 4 the remote has `receive.denyDeletes` set, so every branch deletion is refused.

```bash
uv run python /tmp/f8demo/demo.py; echo "exit $?"
```

````text
== 0. the wiring ==
NOT_YET_HANDLED: ('acceptance_due',)
crash: RecoveryHandler | expired is the same instance: True | rerun is the registered run handler: True RunGate
crash_cap: 2 | lease_duration of coder: 60
== 1. a kill during an agent run; a restart with the same name reruns the stage at its first look ==
tick 1 [09:05]: event=run:F0001-S0001 (remote work-item/F0001-S0001 now 97fb6c8b) dispatch=handled agent runs=1
tick 2: KILLED (injected kill at agent-run) during the tick; agent runs 1
   remote after the kill: stage=doing blocked=None attempts=0 crashes=0 claim=factory-1 | stage-start commit 8fc41691
   local checkout of factory-1: [' M factory/features/F0001-demo/in-progress/F0001-S0001-s1.costs.jsonl', '?? src/dead.py', ''] | local commits ahead: 1
   -- restart: a new Tick, same instance name factory-1, 5 minutes later (inside the lease) --
2026-10-14T09:15:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0001-s1.costs.jsonl, src/dead.py
tick 3 [09:15]: event=crash:F0001-S0001 (remote work-item/F0001-S0001 now 767c2c4c) dispatch=handled agent runs=1
   crash commit: 5069f313 work item F0001-S0001: crash of stage doing recorded | state at it: stage=doing blocked=None attempts=0 crashes=1 claim=None
   now: stage=approval blocked=None attempts=0 crashes=0 claim=None
   journal 4 factory/started: started doing as factory-1.
   journal 5 factory/crash: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit 8fc4169150752bc8c09f95cf49f
   journal 6 factory/started: started doing as factory-1.
   journal 7 coder/result: built.
   dead run's files on any remote branch: dead.py [] committed.py []
   stage-start commit still in history: True
   cost records on the branch: 2 stages: ['intake', 'doing']
   factory posts during the crash tick: 0 (the rerun's own forward move posts nothing either)
tick 4 [09:20]: event=hand_over:F0001-S0001 (remote work-item/F0001-S0001 now f16072d1) dispatch=handled agent runs=0
   -- the remote refuses branch deletions from now until step 4 --
tick 4b (S1 merged: archived, its branch deletion refused) [09:25]: event=merged:F0001-S0001 (remote work-item/F0001-S0001 now f16072d1) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0001 failed: rejected
== 2. a boundary error after a pushed claim repeats; it ends at the crash cap, not the error cap ==
2026-10-14T09:30:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 5 [09:30]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now 6561ed0e) dispatch=handled agent runs=1
2026-10-14T09:35:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 6 (no scripted run: AgentRuntimeError) [09:35]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now e593c040) dispatch=error agent runs=1 error=1x AgentRuntimeError: agent runtime failed: no scripted run is queued
   stage=doing blocked=None attempts=0 crashes=0 claim=factory-1
2026-10-14T09:40:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0002-s2.costs.jsonl
2026-10-14T09:40:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 7 (rerun fails again) [09:40]: event=crash:F0001-S0002 (remote work-item/F0001-S0002 now 32019165) dispatch=error agent runs=1 error=1x AgentRuntimeError: agent runtime failed: no scripted run is queued
   stage=doing blocked=None attempts=0 crashes=1 claim=factory-1
2026-10-14T09:45:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0002-s2.costs.jsonl
2026-10-14T09:45:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 8 [09:45]: event=crash:F0001-S0002 (remote work-item/F0001-S0002 now 9e4827ea) dispatch=handled agent runs=0
   stage=doing blocked=crash_cap attempts=0 crashes=2 claim=None
   journal 7 factory/crash: crash 2: the run of stage doing ended without a result. Its work is discarded back to commit 32019165002a2bd67305daa9096
   journal 8 factory/question: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the sta
   posts: ['factory: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied int']
2026-10-14T09:50:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 9 (no rerun until answered) [09:50]: event=idle:- dispatch=handled agent runs=0
2026-10-14T09:55:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 10 [09:55]: event=idle:- dispatch=handled agent runs=0
2026-10-14T10:00:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 11 (the answer) [10:00]: event=comment:F0001-S0002 (remote work-item/F0001-S0002 now 966458fe) dispatch=handled agent runs=0
   stage=doing blocked=None attempts=0 crashes=0 claim=None
2026-10-14T10:05:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 12 [10:05]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now b805ab83) dispatch=handled agent runs=1
   stage=approval blocked=None attempts=0 crashes=0 claim=None
2026-10-14T10:10:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 13 [10:10]: event=hand_over:F0001-S0002 (remote work-item/F0001-S0002 now 38e27dc4) dispatch=handled agent runs=0
2026-10-14T10:15:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 13b (S2 merged) [10:15]: event=merged:F0001-S0002 (remote work-item/F0001-S0002 now 38e27dc4) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0002 failed: rejected
== 3. an expired lease of another instance: held until 60 minutes, then taken over as a crash ==
2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0002: rejected
tick 14 [10:20]: event=run:F0001-S0003 (remote work-item/F0001-S0003 now 5a1bffdc) dispatch=handled agent runs=1
2026-10-14T10:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T10:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
tick 15 (factory-1 dies): KILLED (injected kill at agent-run) during the tick; agent runs 1
   stage=doing blocked=None attempts=0 crashes=0 claim=factory-1 | claimed at 10:21
2026-10-14T10:51:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T10:51:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-2 tick A (+30 min) [10:51]: event=idle:- dispatch=handled agent runs=0
   stage=doing blocked=None attempts=0 crashes=0 claim=factory-1
2026-10-14T11:20:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T11:20:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-2 tick B (+29 min, 59 min after the claim) [11:20]: event=idle:- dispatch=handled agent runs=0
   stage=doing blocked=None attempts=0 crashes=0 claim=factory-1
2026-10-14T11:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T11:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-2 tick C (+1 min: the lease is 60 min old; the rerun dies too): KILLED (injected kill at agent-run) during the tick; agent runs 1
   stage=doing blocked=None attempts=0 crashes=1 claim=factory-2
   journal 4 factory/started: started doing as factory-1.
   journal 5 factory/expiry: expiry 1: the lease of stage doing ran out. Its work is discarded back to commit 2c87f2338fb10510f4d2fd44de3e7bdbd6cd78e
   journal 6 factory/started: started doing as factory-2.
   last post: The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying.

<!-- factory -->
<!-- factory key=F0001-S0003:expiry:5 -->
   -- factory-1 is back up (a new process, same name), 60 minutes after factory-2's claim --
2026-10-14T12:21:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0003-s3.costs.jsonl, src/dead3.py
2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-1 tick D [12:21]: event=expired:F0001-S0003 (remote work-item/F0001-S0003 now e6723183) dispatch=handled agent runs=0
   stage=doing blocked=crash_cap attempts=0 crashes=2 claim=None
   journal 6 factory/started: started doing as factory-2.
   journal 7 factory/expiry: expiry 2: the lease of stage doing ran out. Its work is discarded back to commit e075f83b79328ac927bb8c91e4d2df8de2057c4
   journal 8 factory/question: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the sta
   post: The run that held this stage ended without finishing: its lease expired (crash 2 of 2). The factory does not rerun it and asks you instead.

<!-- factory -->
<!-- factory key=F0001-S0003:expiry:7 -->
   post: factory: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story 
2026-10-14T12:26:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T12:26:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-1 tick E [12:26]: event=idle:- dispatch=handled agent runs=0
   stall notes (F0005) at both sides of the attempts cap, for comparison:
      Stalled (attempt 1 of 2): the agent gave no valid decision and entry. Retrying on the next tick.
      Stalled (attempt 2 of 2): the agent gave no valid decision and entry. The attempts cap is reached; the factory asks you next.
== 4. stale branches: a refused deletion after a discard and after a merge; the tick deletes them ==
2026-10-14T12:31:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T12:31:00Z could not delete stale branch work-item/F0001-S0002: rejected
tick 16 (S3 closed: discard) [12:31]: event=closed:F0001-S0003 (remote work-item/F0001-S0003 now e6723183) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0003 failed: rejected
   on main: S3 in backlog: True | S1, S2 in done: [True, True]
   remote branches: ['main', 'work-item/F0001-S0001', 'work-item/F0001-S0002', 'work-item/F0001-S0003']
2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0002: rejected
2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0003: rejected
tick 17 (deletion still refused) [12:36]: event=idle:- dispatch=handled agent runs=0
2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0001: its story is done
2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0002: its story is done
2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0003: its story is back in the backlog
tick 19 [12:41]: event=idle:- dispatch=handled agent runs=0
   remote branches: ['main']
   factory-1 log, stale-branch lines:
      2026-10-14T09:30:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T09:35:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T09:40:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T09:45:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T09:50:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T09:55:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:00:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:05:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:10:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:15:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T10:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T10:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T12:26:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T12:26:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T12:31:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T12:31:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0001: rejected
      2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0002: rejected
      2026-10-14T12:36:00Z could not delete stale branch work-item/F0001-S0003: rejected
      2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0001: its story is done
      2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0002: its story is done
      2026-10-14T12:41:00Z deleted stale branch work-item/F0001-S0003: its story is back in the backlog
tick 20 (S3 started again) [12:46]: event=run:F0001-S0003 (remote work-item/F0001-S0003 now 159f6cb7) dispatch=handled agent runs=1
   stage=doing blocked=None attempts=0 crashes=0 claim=None | journal records: 3 | cost records: 1
exit 0
````

Green. Against the Goal's "Done when":

- **A kill during an agent run leaves no write of that run on any branch.** In tick 2 the run left `src/dead.py` untracked, a changed sidecar and one local commit `src/committed.py`. After tick 3, neither file is on any remote branch.
- **The stage-start commit and its "started" entry stay.** The stage-start commit is an ancestor of the branch, and journal entry 4 is still there.
- **The discarded cost records are gone.** The branch holds 2 cost records, `intake` and the rerun's `doing`, and none from the dead run.
- **The stage reruns with `attempts` unchanged and `crashes` one higher.** The crash commit holds `attempts=0 crashes=1 claim=None`. The rerun happens in the same tick (agent runs=1, 5 minutes after the claim, inside the lease). Its forward move resets `crashes` to 0. Nothing is posted.
- **A boundary error that repeats after a claim ends at the crash cap.** In ticks 6–8, two `AgentRuntimeError`s after pushed claims become crash 1 and crash 2. Crash 2 records and posts the crash-cap question. Ticks 9–10 are idle, the comment in tick 11 resets `crashes` to 0, and tick 12 reruns.
- **The crash cap asks the human.** At step 2 the answer is a comment; at step 3 the answer is a close (tick 16), which discards the story.
- **`crash` and `expired` reach their handler through `build_handlers`.** Step 0 shows one `RecoveryHandler` for both kinds, with the registered `RunGate` as its rerun, and `NOT_YET_HANDLED` is `('acceptance_due',)`.
- **An expired lease.** At 30 and 59 minutes, `factory-2` is idle and the claim is untouched. At 60 minutes it records `expiry 1`, posts "… (crash 1 of 2). Retrying." and reruns. That rerun dies too. `factory-1`, back up, finds `factory-2`'s claim expired: `expiry 2`, the note without "Retrying" ("The factory does not rerun it and asks you instead."), and then the question.
- **A stale branch of a discarded or merged story is gone after the next tick.** While deletions are refused, the merge (ticks 4b, 13b) and the discard (tick 16) each count one `PushFailed`. The cleanup logs `could not delete …: rejected` every tick. The first tick after the refusal is lifted (tick 19) deletes all three branches. S3 started again has 3 journal records and 1 cost record: an empty bill (GH4.3).
- **No stall or expiry note says "retrying" at its cap.** This holds for the expiry notes above and for the stall notes at 1 and 2 of 2.

## 3 Mutation score

There is no `make mutants` target, by the decision "No `mutants` target, no mutmut" (`docs/decisions.md`). As at F0007, I ran a hand pass instead:

- 40 mutants (`/tmp/f8demo/mutate.py`, md5 `9b6bf2819bb8b87abe46d4fc3ac45aa4`);
- over `domain/recovery.py`, the crash and expiry texts in `domain/post_texts.py`, `CLAIM_EVENTS`, `application/recovery.py`, and the cleanup step of `application/tick.py`;
- each mutant run on a copy (`/tmp/f8mut`) against the 19 test modules of F0008 and its neighbours (recovery, stale branches, tick, wiring, the crash-cap comment test, the retrying search and the journal-reading search).

```bash
cd /tmp/f8mut && /work/factory-rf/.venv/bin/python /tmp/f8demo/mutate.py
```

**36 of 40 killed.** Every mutant of the crash count, the cap boundary (`>=` against `>`, `<` against `<=`), the texts, the discard, the claim release, the expiry note and its key, the guards, `ask_crash_cap`'s refusals, key, prefix and pull-request recording, and the stale-branch rules was killed by a test named after its criterion.

The four survivors:

| # | Mutant | Reading |
|---|---|---|
| 10 | the head named in the entry is `resolve("HEAD")` instead of `resolve("origin/<branch>")` | equivalent: `check_out` has just reset the local branch to the remote head |
| 22 | the kind guard removed | equivalent in effect: the next guard raises `CannotHandle` with the same kind (`claim is own, not None`), and only the reason differs |
| 37 | backlog takes precedence over done for an id in both folders | **untested side**: the coder chose "done" for a case the Interface left open (S0004 entries 4 and 8). No criterion or test pins it, and the project guide does not state it |
| 39 | the cleanup moved before the restore, inside the stop's `try` | **untested side**: S0004's criterion 12 ("a tick that ends at a repository stop deletes nothing") is tested only with `pipeline_definition_invalid`. A `checkout_restore_failed` stop would delete branches under this mutant. The Interface's "a repository stop of an earlier step ends the tick before it" covers the restore too, and CLAUDE.md asks for both sides |

37 and 39 form one small group: the stale-branch step's untested sides. They go into the housekeeping draft F0008-S0005.

## 4 What the stories noticed

Collected from the coder, reviewer and documenter entries of S0001–S0004:

- **The stale `NOT_YET_HANDLED` sentence (S0002 documenter: "the project guide's `NOT_YET_HANDLED` text (`expired` as F0008's) is unrelated").** S0003 registered `expired` but did not fix it. `docs/project-guide.md:484` still says `build_handlers` registers every kind "except `expired` and `acceptance_due` … `expired` belongs to F0008". This contradicts line 560 of the same guide and the code. → draft F0008-S0005.
- **`_state_of` is now defined ten times** (`grep -rn "def _state_of" src/factory`): `recovery.py` (added in S0002), `claims.py`, `stage.py`, `stalls.py`, `journal.py`, and `closed.py`, `questions.py`, `comments.py`, `reject.py`, `hand_over.py` in `handlers/`. The F0007 acceptance counted five and expected a story here to share one "in passing". Instead S0002's reviewer praised the new copy for "replacing three duplicated checks". CLAUDE.md counts a second copy of a helper as a finding. → draft F0008-S0006.
- **`AskHandler._post` looks up `last_record(kind="question")` without the speaker filter that `ask_crash_cap` uses** (S0002 coder and reviewer). The two agree as long as the crash-cap question is the work item's last question. While the item is blocked no role can ask, so they do. No draft.
- **Unreachable typing guards:** `_remote_head`'s `None` branch (S0001) and `_note_expiry`'s `expiry is None` (S0003). Both reviewers accepted them as type narrowing. No draft.
- **`ask_crash_cap` raises `CannotHandle` with the kind `crash` also when it is reached from an `expired` event** (S0003 round 1, allowed by the reviewer). The reason names the work item, so nothing is lost. No draft.
- **The `"unreachable"` outcome of the stale-branch deletion has no test** (S0004 coder). The code treats it as `"rejected"`, and no criterion names it. I add it to the S0005 draft beside mutants 37 and 39, because it is the same function's untested side.
- **S0004's test fixture had an empty `backlog/` directory** after `human.start`. The human answered option (a), a `mkdir` in the test (entry 5). That cost one question round trip, the "fixture against an earlier rule" pattern of F0007.
- **S0002's documenter started a background wait loop**, which ran until its time limit. CLAUDE.md forbids that. It did not affect the result. A cost remark only (section 8).
- **S0001's documenter:** the kill-points section says the recovery tests "come with F0008, F0011". F0008 has come: `test_recovery_crash.py` arms `BEFORE_PUSH`. → wording in draft S0005.

## 5 The documentation as a whole

I read `README.md`, the operator guide's opening paragraph and its F0008 sections ("A stale branch is deleted by the tick", the merge and discard failure bullets, "An event that keeps failing", "A restart during a stage", "The crash cap", "An expired lease", "Claims, leases and the clock"). In the project guide I read the event kinds, the tick, "The stale branch", "The handlers of the events" with the crash, cap and expiry paragraphs, and the kill points. In `docs/decisions.md` I read its three new F0008 entries. The behaviour the demo shows matches the operator guide line by line: texts, counts, the 59/60-minute edge, the refused deletion as a log line every tick, and `PushFailed` on the merge and the discard with the branch left for the tick.

Findings:

1. **`docs/project-guide.md:484` contradicts the code and line 560** (see 4). An agent who reads the event kinds first is told that `expired` has no handler.
2. **The summaries of what is built do not mention crash recovery.** `README.md`'s first paragraph and the operator guide's opening list the handlers of the human's acts and stop there. Neither says that a restart reruns a dead stage, that an expired lease is taken over, that the crash cap asks, or that the tick deletes stale branches. This is the gap the F0007 acceptance found for its own handlers (its finding 3).
3. **The stale-branch rule for an id in both `backlog/` and `done/`** (logged as done) is in the code's comment only. It belongs in "The stale branch" next to the log lines it chooses between.
4. **The kill-points section's "come with the recovery features (F0008, F0011)"** is now half past. It should say that F0008's tests arm `BEFORE_PUSH` and that F0011 covers all four points.

None of them misleads the operator: the operator guide's own F0008 sections are correct. All four go into draft F0008-S0005.

The README's commands behave as written: `make check` ends with `check: green`, and `factory-run` and `factory-health` are still declared and not built, as the README says.

## 6 Decisions taken for the human

`FEATURE.md`'s decisions 1–19 were built as written. Decisions 1–4, 6–9, 11–14, 17 and 19 are visible in the demo. Decisions 5, 10, 15, 16 and 18 are pinned by the stories' tests: S0001 criterion 15, S0002 criteria 10–11, S0003 criterion 14, and the `ALLOWED` change. To accept or revisit:

- **Decision 15.** A crash-cap question whose post fails for a story without a pull request is not posted again; the human sees the error report instead. The alternative is to let `AskHandler` open the pull request for a `crash_cap` wait, which changes F0007-S0002. Still open.
- **Decision 16.** A lost expiry note is not posted again; the stage reruns on the next tick.
- **Decision 17.** A story moved back to `backlog/` by hand loses its branch (and with it an open pull request) at the next tick. A start before the first tick after a kill still finds the old branch.
- **Decision 19**, the widening to `done/`, was taken by the session for the human on 2026-10-14 and built in S0004. The demo shows it working (ticks 4b, 13b, 19). Confirm it.

Decisions the stories took, recorded in their logs and in `docs/decisions.md`:

- **One `RecoveryHandler` for `crash` and `expired`** (S0003 coder), rather than an `ExpiryHandler`.
- **`CLAIM_EVENTS` made public, with its inverse `required_claim_status`** (S0003, at review), so the handler's guard and the evaluation read one map.
- **The cap is decided once**, in the recorded document. `handle` branches on the pushed `blocked` (S0002 coder).
- **The cleanup is its own tick step, outside `_restore`.** A `GitError` there (for example, `remote_branches` failing) ends the tick with an exception, not with the stop `checkout_restore_failed` (S0004 coder; project guide, the tick). Accept it, or ask for a stop.
- **An id in both `backlog/` and `done/` is logged as done** (S0004 coder). This is an anomaly case. The S0005 draft pins today's choice.
- **A refused deletion is logged on every tick, without limit** (S0004 Interface). A remote that permanently protects `work-item/*` branches fills the factory log with one line per branch per tick. Today the operator guide's answer is "lift the refusal". Revisit only if that proves noisy.

Carried from the F0007 acceptance, still unanswered: item B, a work item branch created by hand is never judged by the move rule. It stands by default.

## 7 The slow checks

None. The project has no slow check beyond `make check`: no `make mutants` target (by decision; section 3 has the hand pass), no image scan and no SBOM.

## 8 Cost

The four stories cost 31 runs, 98.4 minutes and $10.46: $2.62 and 7.8 runs per story, against F0007's $1.88 and 7.1 (78 runs, $20.69 for eleven stories, one of them documentation only).

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0001 | 6 | 19.1 | $2.66 | one pass, no findings |
| S0002 | 6 | 30.4 | $2.19 | one pass; the documenter's background wait loop ran until its time limit, which explains most of the minutes |
| S0003 | 10 | 20.3 | $3.22 | two review rounds, each with one quality finding: the hand-kept `_REQUIRED_STATUS` map typed `str`, then the `CannotHandle` kind in `_remote_head` |
| S0004 | 9 | 28.6 | $2.39 | one question: the test fixture's empty `backlog/` directory (entries 4–7), a round trip coder → human → tester → coder |

S0003 stands out in runs. Both of its findings came from a second copy of something: the reversed claim map, then the kind constant. That is the same pattern as the `_state_of` copies that draft S0006 removes. S0004's extra runs are the fixture pattern the F0007 acceptance saw three times.

## Proposed stories

- `drafts/F0008-S0005-housekeeping-after-crash-recovery.md`: covers the four documentation findings of section 5 and the stale-branch step's three untested sides (mutants 37 and 39, and the `unreachable` outcome).
- `drafts/F0008-S0006-one-helper-for-a-work-items-state.md`: replaces the ten private `_state_of` copies, and three inline checks of the same shape, with one domain function `require_state`, keeping every exception and message. This is a CLAUDE.md finding that two acceptances have now passed over.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 36 of 40)
      1 Scope: none. Every scope item has its story and its code: RecoveryHandler for crash and expired (S0001, S0003), the crash cap (S0002), the expiry note and the retrying wording (S0003), delete_stale_branches as tick step 4 (S0004). NOT_YET_HANDLED is ('acceptance_due',). Nothing out of scope was built.
      2 Feature demo: green, exit 0. /tmp/f8demo/demo.py (md5 d9e8c390…) uses the production handler_factory, two instances on a real bare remote, the fake hosting service and a scripted runtime with kill points. It shows: a kill during an agent run, rerun at the first look by a same-name restart, with no dead write on any branch, the stage-start commit kept, the dead cost record gone, attempts 0 and crashes 1; a repeated AgentRuntimeError after pushed claims ending at the crash-cap question, then answered; an expired lease held at 59 min and taken over at 60, with "Retrying." below the cap and the no-retry note plus the question at it; refused deletions after two merges and one discard, logged every tick, all three branches deleted once allowed; a restart with an empty bill. Output pasted.
      3 Mutation score: no make mutants target. A hand pass of 40 mutants over the F0008 code killed 36. Two survivors are equivalent (resolve HEAD after the reset; the kind guard shadowed by the status guard). Two are untested sides of the stale-branch step: an id in both backlog and done is logged as done, and a checkout_restore_failed stop deletes nothing. Both go into the S0005 draft. make check is green at 99.15 %.
      4 Noticed: the stale project-guide sentence S0002's documenter saw was not fixed by S0003; _state_of is now defined ten times (the S0002 reviewer praised the new copy); AskHandler's question lookup has no speaker filter, harmless while blocked; two unreachable typing guards; the unreachable deletion outcome is untested; S0002's documenter ran a background wait loop.
      5 Documentation: four findings, none misleading the operator. docs/project-guide.md:484 says expired is not registered, contradicting the code and line 560. The README and operator-guide summaries do not mention crash recovery. The backlog/done tie rule is undocumented. The kill-points wording is half past. All four go into S0005.
      6 Decisions: FEATURE decisions 1–19 were built as written. Still for the human: decision 15 (a lost crash-cap question without a pull request is not reposted), decision 17's hand-moved-story side effect, and confirmation of decision 19 (the widening to done/, taken by the session). Taken by the stories: one RecoveryHandler for both kinds, CLAIM_EVENTS made public, a GitError in the cleanup is uncaught (not a stop), the tie logged as done, a refused deletion logged every tick without limit. F0007's item B is still unanswered.
      7 Slow checks: none (no mutants target, no image scan, no SBOM).
      8 Cost: 31 runs, 98.4 min, $10.46 ($2.62 per story). S0003 stands out with 10 runs: two review rounds, each about a second copy (a hand-kept claim map, then a kind constant). S0004 had 9 runs, from one fixture question (an empty backlog/ directory) answered by the human.
      Drafts: F0008-S0005 housekeeping after crash recovery (the four doc repairs and the three untested sides of the stale-branch step); F0008-S0006 one helper for a work item's state (require_state replaces ten _state_of copies and three inline checks, every exception and message kept).
