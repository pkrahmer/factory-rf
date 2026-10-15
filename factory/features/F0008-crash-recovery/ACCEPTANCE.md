---
stage: accept
pr: 102
blocked: null
comments_seen: 1
round: 0
attempts: 1
stories: [F0008-S0001, F0008-S0002, F0008-S0003, F0008-S0004, F0008-S0005, F0008-S0006]
---
# Acceptance of Crash recovery

## Verdict

**accepted.** This is the second acceptance of Crash recovery. The first one (pull request 99, merged) proposed S0005 and S0006, and both are now merged. The feature still does what `FEATURE.md` promises: the same end-to-end demo is green against the current `main` and prints the same output apart from commit hashes. `make check` is green at 99.54 %. Every finding of the first acceptance is repaired: the stale project-guide sentence, the summaries, the stale-branch sides and the ten `_state_of` copies.

What is left has little weight. Seven call sites of the new `require_state` give up their own error with no test noticing. These are defensive paths that no entry point reaches, but S0006 promised their messages unchanged and nothing pins that. One draft covers them.

## 1 Scope

None. The scope table of the first acceptance still holds; each scope item has its story and its code:

| Scope item | Story | Code |
|---|---|---|
| Recovery handler for `crash`: discard, one commit on the remote head, rerun in the same call through the gate | S0001 | `RecoveryHandler.handle` in `src/factory/application/recovery.py`, `src/factory/domain/recovery.py` |
| `crash` and `expired` registered in `build_handlers`, removed from `NOT_YET_HANDLED` | S0001, S0003 | `src/factory/entry/wiring.py` (`NOT_YET_HANDLED == ("acceptance_due",)`) |
| Crash cap, and a repeated boundary error ending at it | S0002 | `RecoveryHandler.ask_crash_cap`, `post_texts.crash_cap_question` |
| Expired lease of another instance handled as a crash, with its note | S0003 | `RecoveryHandler._note_expiry`, `evaluation.CLAIM_EVENTS` |
| "retrying" only where a retry follows | S0003 | `post_texts.expiry_note`, `stall_note`, `tests/test_retrying_wording.py` |
| Journal kinds `crash` and `expiry` | S0001, S0003 | `JournalKind` |
| Tick deletes the branch of a story in `backlog/` or `done/` | S0004, pinned further by S0005 | `delete_stale_branches`, step 4 of `Tick.run` |

The two new stories came from the first acceptance and are recorded as decision 20 of `FEATURE.md`:

- **S0005** changes only tests and documentation. `git diff` of its merge touches no file in `src/`.
- **S0006** is a refactoring across the modules of F0002, F0004, F0005, F0007 and F0008. It changes no behaviour, and every pre-existing test passes unchanged.

Neither one added scope. Out of scope stayed out: there is no kill-point matrix (F0011), no second-instance test and no watchdog.

## 2 Feature demo

This is the same walk-through as in the first acceptance, rerun on today's `main` (`0ce85f3`). The script is `/tmp/f8acc2/demo.py`, a byte-identical copy (md5 `d9e8c390e9af08e0c69a8f1c1a8bbf62`) of the earlier `/tmp/f8demo/demo.py`. It uses:

- the production `handler_factory(boundaries, name, production_environment())` and a `Tick` per pass;
- a real bare remote with `GitCli` checkouts for two instances, `factory-1` and `factory-2`, each with its own `KillPoints`;
- a human clone;
- `FakeHostingService`;
- `FakeAgentRuntime` with scripted runs. A killed run also leaves an untracked file, a changed sidecar and one local commit.

Between steps 1 and 4, the remote refuses branch deletions (`receive.denyDeletes`).

Compared with the first run, the output differs only in commit hashes. I checked this with `diff` after masking every hex string of 8 or more characters.

```bash
uv run python /tmp/f8acc2/demo.py; echo "exit $?"
```

````text
== 0. the wiring ==
NOT_YET_HANDLED: ('acceptance_due',)
crash: RecoveryHandler | expired is the same instance: True | rerun is the registered run handler: True RunGate
crash_cap: 2 | lease_duration of coder: 60
== 1. a kill during an agent run; a restart with the same name reruns the stage at its first look ==
tick 1 [09:05]: event=run:F0001-S0001 (remote work-item/F0001-S0001 now eadab750) dispatch=handled agent runs=1
tick 2: KILLED (injected kill at agent-run) during the tick; agent runs 1
   remote after the kill: stage=doing blocked=None attempts=0 crashes=0 claim=factory-1 | stage-start commit db4fae5b
   local checkout of factory-1: [' M factory/features/F0001-demo/in-progress/F0001-S0001-s1.costs.jsonl', '?? src/dead.py', ''] | local commits ahead: 1
   -- restart: a new Tick, same instance name factory-1, 5 minutes later (inside the lease) --
2026-10-14T09:15:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0001-s1.costs.jsonl, src/dead.py
tick 3 [09:15]: event=crash:F0001-S0001 (remote work-item/F0001-S0001 now 7afff361) dispatch=handled agent runs=1
   crash commit: d9b10cfb work item F0001-S0001: crash of stage doing recorded | state at it: stage=doing blocked=None attempts=0 crashes=1 claim=None
   now: stage=approval blocked=None attempts=0 crashes=0 claim=None
   journal 4 factory/started: started doing as factory-1.
   journal 5 factory/crash: crash 1: the run of stage doing ended without a result. Its work is discarded back to commit db4fae5b82c74e5d8d902f08788
   journal 6 factory/started: started doing as factory-1.
   journal 7 coder/result: built.
   dead run's files on any remote branch: dead.py [] committed.py []
   stage-start commit still in history: True
   cost records on the branch: 2 stages: ['intake', 'doing']
   factory posts during the crash tick: 0 (the rerun's own forward move posts nothing either)
tick 4 [09:20]: event=hand_over:F0001-S0001 (remote work-item/F0001-S0001 now 14b0a699) dispatch=handled agent runs=0
   -- the remote refuses branch deletions from now until step 4 --
tick 4b (S1 merged: archived, its branch deletion refused) [09:25]: event=merged:F0001-S0001 (remote work-item/F0001-S0001 now 14b0a699) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0001 failed: rejected
== 2. a boundary error after a pushed claim repeats; it ends at the crash cap, not the error cap ==
2026-10-14T09:30:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 5 [09:30]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now de9f847d) dispatch=handled agent runs=1
2026-10-14T09:35:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 6 (no scripted run: AgentRuntimeError) [09:35]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now 5d86ffab) dispatch=error agent runs=1 error=1x AgentRuntimeError: agent runtime failed: no scripted run is queued
   stage=doing blocked=None attempts=0 crashes=0 claim=factory-1
2026-10-14T09:40:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0002-s2.costs.jsonl
2026-10-14T09:40:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 7 (rerun fails again) [09:40]: event=crash:F0001-S0002 (remote work-item/F0001-S0002 now b7a2ab7a) dispatch=error agent runs=1 error=1x AgentRuntimeError: agent runtime failed: no scripted run is queued
   stage=doing blocked=None attempts=0 crashes=1 claim=factory-1
2026-10-14T09:45:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0002-s2.costs.jsonl
2026-10-14T09:45:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 8 [09:45]: event=crash:F0001-S0002 (remote work-item/F0001-S0002 now 2804ff1b) dispatch=handled agent runs=0
   stage=doing blocked=crash_cap attempts=0 crashes=2 claim=None
   journal 7 factory/crash: crash 2: the run of stage doing ended without a result. Its work is discarded back to commit b7a2ab7a342eedc00b319439c81
   journal 8 factory/question: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the sta
   posts: ['factory: Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied int']
2026-10-14T09:50:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 9 (no rerun until answered) [09:50]: event=idle:- dispatch=handled agent runs=0
2026-10-14T09:55:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 10 [09:55]: event=idle:- dispatch=handled agent runs=0
2026-10-14T10:00:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 11 (the answer) [10:00]: event=comment:F0001-S0002 (remote work-item/F0001-S0002 now cfba4711) dispatch=handled agent runs=0
   stage=doing blocked=None attempts=0 crashes=0 claim=None
2026-10-14T10:05:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 12 [10:05]: event=run:F0001-S0002 (remote work-item/F0001-S0002 now 6c61a201) dispatch=handled agent runs=1
   stage=approval blocked=None attempts=0 crashes=0 claim=None
2026-10-14T10:10:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 13 [10:10]: event=hand_over:F0001-S0002 (remote work-item/F0001-S0002 now 932a2972) dispatch=handled agent runs=0
2026-10-14T10:15:00Z could not delete stale branch work-item/F0001-S0001: rejected
tick 13b (S2 merged) [10:15]: event=merged:F0001-S0002 (remote work-item/F0001-S0002 now 932a2972) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0002 failed: rejected
== 3. an expired lease of another instance: held until 60 minutes, then taken over as a crash ==
2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T10:20:00Z could not delete stale branch work-item/F0001-S0002: rejected
tick 14 [10:20]: event=run:F0001-S0003 (remote work-item/F0001-S0003 now 8b876015) dispatch=handled agent runs=1
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
   journal 5 factory/expiry: expiry 1: the lease of stage doing ran out. Its work is discarded back to commit 1410592837e4ba5a00d163861db3ceb26731462
   journal 6 factory/started: started doing as factory-2.
   last post: The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying.

<!-- factory -->
<!-- factory key=F0001-S0003:expiry:5 -->
   -- factory-1 is back up (a new process, same name), 60 minutes after factory-2's claim --
2026-10-14T12:21:00Z discarded uncommitted changes: factory/features/F0001-demo/in-progress/F0001-S0003-s3.costs.jsonl, src/dead3.py
2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0001: rejected
2026-10-14T12:21:00Z could not delete stale branch work-item/F0001-S0002: rejected
factory-1 tick D [12:21]: event=expired:F0001-S0003 (remote work-item/F0001-S0003 now 1c5cb550) dispatch=handled agent runs=0
   stage=doing blocked=crash_cap attempts=0 crashes=2 claim=None
   journal 6 factory/started: started doing as factory-2.
   journal 7 factory/expiry: expiry 2: the lease of stage doing ran out. Its work is discarded back to commit e3c7f944eafc874e0d7b43f1fb423e1aefab188
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
tick 16 (S3 closed: discard) [12:31]: event=closed:F0001-S0003 (remote work-item/F0001-S0003 now 1c5cb550) dispatch=error agent runs=0 error=1x PushFailed: push of work-item/F0001-S0003 failed: rejected
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
tick 20 (S3 started again) [12:46]: event=run:F0001-S0003 (remote work-item/F0001-S0003 now 4040ac3e) dispatch=handled agent runs=1
   stage=doing blocked=None attempts=0 crashes=0 claim=None | journal records: 3 | cost records: 1
exit 0
````

Green. Each clause of the Goal's "Done when" against this output:

- **No write of the killed run on any branch.** After tick 3, `dead.py` and `committed.py` are on no branch.
- **The stage-start commit and its "started" entry stay.** The stage-start commit is still in history, and journal entry 4 is still there.
- **The dead run's cost records are gone.** The branch holds the 2 cost records `intake` and the rerun's `doing`.
- **The stage reruns at once.** The crash commit has `attempts=0 crashes=1 claim=None`, and the rerun happens in the same tick, inside the lease.
- **A repeated boundary error ends at the crash cap.** Ticks 6–8 run into the cap, ticks 9–10 stay idle, the comment in tick 11 resets `crashes` to 0, and tick 12 reruns.
- **`crash` and `expired` share one `RecoveryHandler`.** It reruns through the registered `RunGate`.
- **An expired lease is held, then taken over.** At 59 minutes the lease is held. At 60 minutes it is taken over with "Retrying." below the cap; at the cap the note has no "Retrying", and the question follows.
- **Stale branches are deleted once the remote allows it.** Refused deletions after two merges and a discard are logged on every tick, and all three branches are deleted in tick 19.
- **A story started again has an empty bill.**
- **No note says "retrying" at a cap.** This holds for the stall notes on both sides of the attempts cap too.

## 3 Mutation score

The project has no `make mutants` target, by the decision "No `mutants` target, no mutmut" in `docs/decisions.md`. As in the first acceptance, I ran a hand pass on a copy of `HEAD` (`/tmp/f8acc2/mut`, from `git archive`):

- **The script** is `/tmp/f8acc2/mutate2.py`. It contains the first acceptance's 40 mutants, re-anchored on today's code (all 40 still apply), plus 12 new ones for S0006: `require_state` itself and the exceptions built at its call sites.
- **Test selection:** mutants 0–39 run against the 19 F0008 test modules, as before. Mutants 40–51 run against the whole `tests/` directory, because the call sites belong to seven features.

```bash
cd /tmp/f8acc2/mut && /work/factory-rf/.venv/bin/python /tmp/f8acc2/mutate2.py
```

**43 of 52 killed.** That is 38 of the 40 F0008 mutants and 5 of the 12 S0006 mutants.

- **The two untested sides of the first acceptance are now killed.** Mutant 37 (backlog winning over done) is killed by `test_an_id_in_the_backlog_and_done_is_logged_as_done`. Mutant 39 (cleanup before the restore) is killed by `test_a_tick_that_ends_at_the_restore_stop_deletes_nothing`. Both tests came with S0005.
- **Survivors 10 and 22 are equivalent, as before.** In 10, the head is resolved from `HEAD` right after the reset to `origin/<branch>`. In 22, the kind guard is shadowed by the status guard, which raises the same `CannotHandle` kind.
- **Survivors 42–46, 49 and 50 form one group: the no-state failing side at seven call sites of `require_state`.**

  | # | Mutant | Survives because |
  |---|---|---|
  | 42 | `RecoveryHandler`'s `_no_state` uses the kind `expired` instead of `crash` | no test passes a stateless snapshot to `ask_crash_cap` |
  | 43 | the same, with another message | the same |
  | 44 | `HandOverHandler`'s message changed | reached only if the branch's file loses its state after the evaluation read it |
  | 45 | `ClaimService.claim`'s message changed | no test claims a stateless document |
  | 46 | `ClaimService.release`'s message changed | no test releases a stateless document |
  | 49 | `TaskComposer.compose` raises `ValueError` instead of `WorkItemFormatError` | no test composes from a stateless document |
  | 50 | `StallService.stall`'s message changed | no test stalls a stateless document |

  `require_state` itself (40, 41), the evaluation (47), the writer's `render` (48) and `target_of` (51) are pinned.

  S0006's Assignment promised that "no exception type or message changes", and its criterion 5 (existing tests pass) was the only pin. For these seven sites that pin does not reach. Line coverage cannot show it either: since S0006, each call site builds its exception *before* `require_state` checks the state, so the line that builds the error runs on every happy path and counts as covered. Before S0006 an untested `raise` in a `_state_of` copy would have been a missed line. I did not measure how much of the rise from 99.15 % to 99.54 % this accounts for.

  Five of the seven sites are reachable through a public method with a stateless document: `claim`, `release`, `ask_crash_cap`, `compose` and `stall`. Their refused side is a missing criterion, which goes into draft F0008-S0007. Mutant 44 is equivalent in practice: its `CannotHandle` is reachable only through a race between the evaluation and the checkout, so it gets no criterion.

## 4 What the stories noticed

The first acceptance collected the items of S0001–S0004. The ones it routed to S0005 and S0006 are done, and the ones it kept without a draft still stand as written there. New from S0005 and S0006:

- **`_log_lines` exists four times in the tests** (S0005 coder and reviewer): `tests/application/test_stale_branches.py`, `test_tick.py`, `test_pipeline_loading.py` and `test_tick_stale_branch.py` each read `state/factory.log` the same way. The fourth copy was added by S0005's tester. The CLAUDE.md rule against second copies covers helpers in `src/factory`, and S0005's Interface forbade changing the existing helper. Six more test modules read `factory.log` inline. A shared `log_lines(tmp_path)` beside the `boundaries` fixture in `tests/conftest.py` would remove the copies, but it means changing tests other stories wrote, which needs the human's word. **No draft:** it costs nothing at run time, and the reviewer left it to the human. I name it so that the human can ask for one.
- **Every module now has a private `_no_state()` builder** (S0006 coder): eight small functions that each build an exception. The Interface allowed them, and they are not checks. The coder rejected module-level constants on purpose, because one shared instance raised again would pile up its `__traceback__`. The side effect on coverage is in section 3. No draft beyond S0007.
- **`domain/story_form._check_started` also tests `document.state is None`** (S0006 coder). It returns a finding instead of raising, so it is outside `require_state`'s rule, and the reviewer agreed. No draft.
- **S0005's coder wrote nothing.** The tests passed against the code as it was, so the tester's suite was green from the start. That is the expected shape of a "pin what exists" story; one run (the coder's) did nothing but confirm it.

## 5 The documentation as a whole

I read `README.md`, the operator guide's opening paragraph and its F0008 sections, and the project guide's event kinds, "The stale branch", `NOT_YET_HANDLED`, "The document and its error" (the `require_state` paragraph), the journal's "Imports" bullet and the kill-points section. I grepped `README.md` and `docs/` for `F0008`, `_state_of`, "come with" and "until F0008".

All four findings of the first acceptance are repaired:

- `docs/project-guide.md:486` names only `acceptance_due` as unregistered, in agreement with line 562 and the operator guide's line 565.
- `README.md:3` and `docs/operator-guide.md:3` each name crash recovery, in the same sentence.
- Line 552 states the rule for an id in both `backlog/` and `done/`.
- Line 1389 names F0008's `BEFORE_PUSH` and `AFTER_PUSH` tests and gives F0011 the rest.

`require_state` is documented once, at line 449, together with the search test that enforces it. The journal's exception is explained at line 427, and the two agree. No remaining mention of F0008 is in the future tense. The operator guide's stale-branch log lines (line 447) match what the demo prints.

None.

## 6 Decisions taken for the human

From `FEATURE.md`, still open for the human to accept or revisit. The human merged the first acceptance without revisiting any of them:

- **Decision 15.** A crash-cap question whose post fails for a story that has no pull request in its state is not posted again; the human sees the error report instead. The alternative is to let `AskHandler` open the pull request for a `crash_cap` wait, which would change F0007-S0002.
- **Decision 16.** A lost expiry note is not posted again.
- **Decision 17.** A story moved back to `backlog/` by hand loses its branch, and with it an open pull request, at the next tick.
- **Decision 19.** The stale-branch rule was widened to `done/`, a choice the session took for the human on 2026-10-14. The demo shows it working (ticks 4b, 13b, 19).
- **Decision 20 (new).** S0005 grew S0004's test modules, and S0006 changed modules of five features. Both are built as written.

Taken by the stories, carried from the first acceptance:

- one `RecoveryHandler` for both kinds;
- `CLAIM_EVENTS` made public;
- a `GitError` in the stale-branch step ends the tick with an exception rather than a stop;
- an id in both folders is logged as done (now pinned by S0005);
- a refused deletion is logged on every tick without limit.

New from S0006:

- **One private `_no_state()` builder per module, called before the check** (S0006 coder). The alternative, an exception built only when the state is missing, would need a callable or a lazy argument, which is a change to the Interface `require_state(document, error)`. Accept it, or ask for `require_state(document, make_error)`, which would also let coverage show the untested sides again.

Carried from the F0007 acceptance, still unanswered: item B, a work item branch created by hand is never judged by the move rule.

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: there is no `make mutants` target (by decision; section 3 has the hand pass), no image scan and no SBOM.

## 8 Cost

Six stories cost 43 runs, 129.9 minutes and $13.02, or $2.17 and 7.2 runs per story. The first acceptance cost another $4.25 (its log entry 2).

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0001 | 6 | 19.1 | $2.66 | one pass, no findings |
| S0002 | 6 | 30.4 | $2.19 | one pass; the documenter's background wait loop ran until its time limit |
| S0003 | 10 | 20.3 | $3.22 | two review rounds, each about a second copy (a hand-kept claim map, then a kind constant) |
| S0004 | 9 | 28.6 | $2.39 | one question round trip about an empty `backlog/` directory in a test fixture |
| S0005 | 6 | 10.8 | $1.26 | one pass; tests and docs only, nothing for the coder |
| S0006 | 6 | 20.7 | $1.30 | one pass across 17 call sites, no findings |

The two housekeeping stories are the cheapest of the feature: together $2.56, under a fifth of the total. S0003 still stands out in runs, for the reasons the first acceptance gave.

## Proposed stories

- `drafts/F0008-S0007-the-no-state-refusals-of-require-states-callers.md`: pins the refused side of five public calls that S0006 moved onto `require_state` (`ClaimService.claim` and `release`, `RecoveryHandler.ask_crash_cap`, `TaskComposer.compose`, `StallService.stall`). These are surviving mutants 42, 43, 45, 46, 49 and 50, and line coverage no longer shows the gap. Tests only.

## Log (append only)

1. run expired: the run that held it ended without finishing (lease over or machine restarted)
2. acceptor: accepted; 1 draft proposed; make mutants 43/52 (no target, by the decision in docs/decisions.md; a hand pass over the F0008 code and S0006's require_state call sites)
         1 Scope: none. Every scope item still has its story and its code, as in the first acceptance. S0005 touched only tests and docs, nothing in src/. S0006 was a refactoring across five features with no change in behaviour (FEATURE decision 20). Nothing out of scope was built.
         2 Feature demo: green, exit 0. The same script as the first acceptance (/tmp/f8acc2/demo.py, md5 d9e8c390…), rerun on 0ce85f3, printed the same output apart from commit hashes. It covers: a same-name restart reruns a killed stage at once with no dead write left; a repeated boundary error ends at the crash-cap question, which is then answered; an expired lease is held at 59 min and taken over at 60, with "Retrying." only below the cap; refused stale-branch deletions are logged and later deleted; a restarted story begins with an empty bill. The output is pasted in the report.
         3 Mutation score: 43 of 52 killed. The first acceptance's untested stale-branch sides (37, 39) are now killed by S0005's tests. Survivors 10 and 22 are equivalent, as before. Survivors 42–46, 49 and 50 are one group: at seven require_state call sites the no-state exception (type, kind or message) can change and no test notices. S0006 promised these unchanged, and its eager _no_state() builders hide the gap from line coverage. Five of the sites are reachable through public calls and go into draft S0007; 44 (hand_over) is reachable only through a race.
         4 Noticed: _log_lines is copied four times in the tests (the fourth from S0005's tester). It is outside the CLAUDE.md rule; no draft, named for the human. Each module has a private _no_state() builder (allowed by S0006's Interface). story_form._check_started returns a finding rather than raising, so it is outside the rule. S0005's coder had nothing to do.
         5 Documentation: none. The first acceptance's four findings are repaired (project-guide 486/552/1389, README:3, operator-guide:3). require_state and the journal's exception are documented consistently at project-guide 449 and 427.
         6 Decisions: FEATURE decisions 15, 16, 17 and 19 are still open for the human; decision 20 is built as written. New from S0006: the exception is built before the check (one _no_state() builder per module). The alternative, require_state(document, make_error), would change the Interface. F0007's item B is still unanswered.
         7 Slow checks: none (no mutants target, no image scan, no SBOM).
         8 Cost: 43 runs, 129.9 min, $13.02 ($2.17 per story), plus $4.25 for the first acceptance. S0005 and S0006 together cost $2.56. S0003 still stands out with 10 runs (two review rounds).
         Draft: F0008-S0007 the no-state refusals of require_state's callers. Tests only; it pins claim, release, ask_crash_cap, compose and stall on a document without a state (survivors 42, 43, 45, 46, 49, 50).
