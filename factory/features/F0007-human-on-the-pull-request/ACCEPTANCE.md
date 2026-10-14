---
stage: accept
pr: 92
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0007-S0001, F0007-S0002, F0007-S0003, F0007-S0004, F0007-S0005, F0007-S0006, F0007-S0007, F0007-S0008, F0007-S0009, F0007-S0010]
---
# Acceptance of The human on the pull request

## Verdict

**accepted with drafts.** The ten stories together do what `FEATURE.md` promised. Every scope item has its story and its code, and the feature demo is green: the production `build_handlers` on a real remote takes a story through comments, a question, a failed and repeated hand-over, two send-backs, an answer, a merge, a discard with a restart, the attempts cap, a move back, a merge found by the run gate and a counted duplicate, with no post repeated. `make check` is green at 99 %.

One finding is worth a story, and it breaks no promise:

- **Stale documentation.** The operator guide still says in three places that the `ask` and `comment` handlers are not registered, and the project guide still says the closed handler does nothing at an approval. Both contradict the code. They mislead only about what is wired: no command runs ticks before F0010, so no operator acts on them yet. That is why I did not judge it "not accepted".

The hand mutation pass killed 50 of 52, and the two survivors are equivalent mutants. One product question stays open for the human (section 6, A).

## 1 Scope

None. Each scope item of `FEATURE.md` has its story and its code:

| Scope item | Story | Code |
|---|---|---|
| Shared plumbing: `CannotHandle`, the event's target, the recorder | S0001 | `domain/errors.py`, `application/handlers/recording.py` |
| Comments copied by id | S0001 | `application/handlers/comments.py` (`CommentCopier`) |
| Questions recorded, then posted; the attempts-cap question | S0002 | `application/handlers/questions.py`, `post_texts.attempts_cap_question` |
| Merge archives with the bill | S0003 | `application/handlers/merged.py`, `domain/archive.py` |
| Discard before the approval | S0004 | `ClosedHandler._discard` |
| Send-back at the approval | S0005 | `ClosedHandler._send_back`, `domain/send_back.py` |
| `reject` moved back | S0006 | `application/handlers/reject.py` |
| Answers and capped comment events | S0007 | `CommentHandler`, `domain/answers.py` |
| Stops that cannot be done | S0008 | `application/handlers/lookups.py`, the `ask` stop in `questions.py` |
| Hand-over from state | S0009 | `application/handlers/hand_over.py`, `domain/hand_over.py` |
| Pull request read before every run; the wiring | S0010 | `application/handlers/run_gate.py`, `entry/wiring.build_handlers` |
| The texts | all | `domain/post_texts.py` |

The demo shows every "Done when" clause (section 2):

- **The act is kept through a failure.** In step 3 a hand-over fails and is completed from state. The kill points are covered by the stories' tests, for example S0002 criterion 14 and S0005's kill cases.
- **No post repeats.** Ticks 5 and 11 are idle with the post count unchanged, and one cost table is posted after the failed attempt.
- **Every event is bounded by the error cap of three.** Step 11 shows it. S0007 proves it for `comment` and `ask` through the dispatcher.
- **A close or a merge right before a run is handled first.** Steps 7 and 10 show it, with 0 agent runs.

Out of scope stays out:

- The handlers do nothing specific to an acceptance (F0009).
- `crash`, `expired` and `acceptance_due` are still in `NOT_YET_HANDLED`.
- Labels are written again only after a send-back and after a move back.

One small difference from the scope: the scope puts "the texts the handlers post" in `factory.domain.post_texts`, but `HAND_OVER_CLOSING` and the section titles live in `factory.domain.hand_over`. S0009's Interface placed them there, and the human's answer in S0009 (entry 5) confirmed that module for the journal reading. It is not a finding.

## 2 Feature demo

The script is `/tmp/f7demo/demo.py` (md5 `171e909241458a727503d764181f0a8d`, 323 lines). It builds on the F0006 acceptance's harness, with the same seed, `boundaries()` and `show()`. It uses:

- the production `handler_factory` and `production_environment()`, and a `Tick` per pass;
- a real bare remote with a human clone (`tests/human_clone.py`) and `GitCli`;
- `FakeHostingService` for the pull requests, on which the human comments, closes and merges;
- `FakeAgentRuntime` with scripted results.

The pipeline is intake → doing (`round_cap: 1`) → approval (`next: [done, doing]`), with `attempts_cap: 2`. The tick labels skip 7 and 29: those are gaps in my numbering, not ticks.

```bash
uv run python /tmp/f7demo/demo.py; echo "exit $?"
```

````text
== 0. the wiring ==
NOT_YET_HANDLED: ('crash', 'expired', 'acceptance_due')
registered: {'idle': 'IdleHandler', 'run': 'RunGate', 'comment': 'CommentHandler', 'ask': 'AskHandler', 'merged': 'MergedHandler', 'closed': 'ClosedHandler', 'reject': 'RejectHandler', 'hand_over': 'HandOverHandler', 'duplicate': 'DuplicateHandler', 'pull_request_lookup': 'PullRequestLookupHandler'}
== 1. S0001 starts; the human comments while the stage works; the agent asks ==
tick 1: stopped=None event=run:F0001-S0001 at 8ee389d2 (after the tick, remote work-item/F0001-S0001 at 3fadd759) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=0
tick 2: stopped=None event=run:F0001-S0001 at 3fadd759 (after the tick, remote work-item/F0001-S0001 at 8ff2e490) dispatch=handled
   stage=doing blocked=question round=0 attempts=0 handed_over=None comments_read=[] claim=None
== 2. the comments are copied by id; the question is posted once; a later comment answers ==
tick 3: stopped=None event=comment:F0001-S0001 at 8ff2e490 (after the tick, remote work-item/F0001-S0001 at 2e5744a6) dispatch=handled
   stage=doing blocked=question round=0 attempts=0 handed_over=None comments_read=[1, 2, 3] claim=None
   journal: (5, 'coder', 'question', 'shall hello() take a name?')
   journal: (6, 'human', 'comment', 'Please keep it short.')
   journal: (7, 'human', 'comment', 'factory: this looks like a factory post but has no marker')
tick 4: stopped=None event=ask:F0001-S0001 at 2e5744a6 (after the tick, remote work-item/F0001-S0001 at 2e5744a6) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=1
   last factory post: coder: shall hello() take a name?
tick 5: stopped=None event=idle:- dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=1
tick 6: stopped=None event=comment:F0001-S0001 at 2e5744a6 (after the tick, remote work-item/F0001-S0001 at ab7c931e) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[1, 2, 3, 5] claim=None
   journal: (8, 'human', 'comment', 'No name, keep it plain.')
== 3. the hand-over, failing once, completed from state ==
tick 8: stopped=None event=run:F0001-S0001 at ab7c931e (after the tick, remote work-item/F0001-S0001 at d7b67114) dispatch=handled
tick 9 (post_comment fails): stopped=None event=hand_over:F0001-S0001 at d7b67114 (after the tick, remote work-item/F0001-S0001 at d7b67114) dispatch=error
   count: ('hand_over:F0001-S0001', 'd7b67114', 1, False, 'HostingServiceError: hosting service post_comment failed: injected failure')
   stage=approval blocked=None round=0 attempts=0 handed_over=None comments_read=[1, 2, 3, 5] claim=None | #1 state=open draft=False labels=['stage:approval'] factory posts=1
tick 10: stopped=None event=hand_over:F0001-S0001 at d7b67114 (after the tick, remote work-item/F0001-S0001 at d99985ee) dispatch=handled
   stage=approval blocked=None round=0 attempts=0 handed_over=approval comments_read=[1, 2, 3, 5] claim=None | #1 state=open draft=False labels=['stage:approval'] factory posts=2
   description sections: ['## Description', '## Acceptance criteria', '## Tests', '## Review', '## Documentation', '## Smoke test', '## Commits']
tick 11: stopped=None event=idle:- dispatch=handled
   #1 state=open draft=False labels=['stage:approval'] factory posts=2
== 4. a close at the approval with a reason sends back within the cap ==
tick 12: stopped=None event=closed:F0001-S0001 at d99985ee (after the tick, remote work-item/F0001-S0001 at c2f64c84) dispatch=handled
   stage=doing blocked=None round=1 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7] claim=None | #1 state=open draft=True labels=['stage:doing'] factory posts=2
   journal: (11, 'human', 'comment', 'Rename the module, please.')
   journal: (12, 'human', 'close', 'closed the pull request.')
   journal: (13, 'factory', 'send_back', 'sent back to doing, round 1.')
== 5. a close without a comment past the cap asks; the answer unblocks ==
tick 13: stopped=None event=run:F0001-S0001 at c2f64c84 (after the tick, remote work-item/F0001-S0001 at 72fd5a79) dispatch=handled
tick 14: stopped=None event=hand_over:F0001-S0001 at 72fd5a79 (after the tick, remote work-item/F0001-S0001 at 454fbcee) dispatch=handled
tick 15: stopped=None event=closed:F0001-S0001 at 454fbcee (after the tick, remote work-item/F0001-S0001 at 1fc9dacd) dispatch=handled
   stage=doing blocked=send_back round=2 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7] claim=None | #1 state=open draft=True labels=['stage:doing'] factory posts=3
tick 16: stopped=None event=ask:F0001-S0001 at 1fc9dacd (after the tick, remote work-item/F0001-S0001 at 1fc9dacd) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=4
   last factory post: factory: This story has now been sent back 2 times, more than 1. What should happen? 1. Comment what should ch
tick 17: stopped=None event=comment:F0001-S0001 at 1fc9dacd (after the tick, remote work-item/F0001-S0001 at a2ce2640) dispatch=handled
   stage=doing blocked=None round=2 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7, 10] claim=None
== 6. a merge archives the story with its bill ==
tick 18: stopped=None event=run:F0001-S0001 at a2ce2640 (after the tick, remote work-item/F0001-S0001 at 55a35457) dispatch=handled
tick 19: stopped=None event=hand_over:F0001-S0001 at 55a35457 (after the tick, remote work-item/F0001-S0001 at 261ce6d5) dispatch=handled
tick 20: stopped=None event=merged:F0001-S0001 at 261ce6d5 (after the tick, remote work-item/F0001-S0001 at (deleted) dispatch=handled
   on main: ['done', 'F0001-S0001-s1.md'] stage done | last entry: done (pull request merged); cost: 5 runs, 10.0 min, 25 turns, 500 tokens in (0 more from cache), 100 out, $0.50
   cost records beside it: True | files in done/: ['factory/features/F0001-demo/done/F0001-S0001-s1.costs.jsonl', 'factory/features/F0001-demo/done/F0001-S0001-s1.md']
   branch on remote: None | new posts on the merged PR: 0
== 7. a close before the approval discards (found by the run gate); a restart starts with an empty bill ==
tick 21: stopped=None event=run:F0001-S0002 at e7fa9c8e (after the tick, remote work-item/F0001-S0002 at 63048d6b) dispatch=handled
tick 22: stopped=None event=run:F0001-S0002 at 63048d6b (after the tick, remote work-item/F0001-S0002 at (deleted) dispatch=handled
   agent runs in tick 22: 0
   back in backlog byte for byte: True | branch on remote: None | #2 state=closed draft=True labels=['stage:doing'] factory posts=0
tick 23: stopped=None event=run:F0001-S0002 at 91605e3e (after the tick, remote work-item/F0001-S0002 at dac011d7) dispatch=handled
   cost records after the restart: 1 | pull request: 3
== 8. the attempts cap: recorded, posted, answered ==
tick 24: stopped=None event=run:F0001-S0002 at dac011d7 (after the tick, remote work-item/F0001-S0002 at 4d4d1988) dispatch=handled
tick 25: stopped=None event=run:F0001-S0002 at 4d4d1988 (after the tick, remote work-item/F0001-S0002 at e32443a1) dispatch=handled
   stage=doing blocked=None round=0 attempts=2 handed_over=None comments_read=[] claim=None
tick 26: stopped=None event=ask:F0001-S0002 at e32443a1 (after the tick, remote work-item/F0001-S0002 at af5fff12) dispatch=handled
   stage=doing blocked=attempts_cap round=0 attempts=2 handed_over=None comments_read=[] claim=None | #3 state=open draft=True labels=['stage:doing'] factory posts=3
   last factory post: factory: Stage doing stalled 2 times. The last time: Stage doing stalled (attempt 2 of 2): the agent gave no valid decision and entry
tick 27: stopped=None event=comment:F0001-S0002 at af5fff12 (after the tick, remote work-item/F0001-S0002 at c9ca962c) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[15] claim=None
== 9. an illegal stage change is moved back ==
tick 28: stopped=None event=reject:F0001-S0002 at b2f4415b (after the tick, remote work-item/F0001-S0002 at ffedcd29) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[15] claim=None | #3 state=open draft=True labels=['stage:doing'] factory posts=4
   subject: work item F0001-S0002: stage intake -> doing, moved back
   note: The stage was changed from doing to intake, which factory/pipeline.yml does not allow; it is back at doing.
== 10. a merge found right before an agent run is handled first ==
tick 30: stopped=None event=run:F0001-S0002 at ffedcd29 (after the tick, remote work-item/F0001-S0002 at (deleted) dispatch=handled
   agent runs during the tick: 0 | S0002 in done/: True | branch on remote: None
== 11. a stop with no work to do is a counted error, reported once ==
tick 31: stopped=None event=duplicate:F0001-S0004 at 255baf1a (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=error
   count: ('duplicate:F0001-S0004', '255baf1a', 1, False, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 32: stopped=None event=duplicate:F0001-S0004 at 255baf1a (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=error
   count: ('duplicate:F0001-S0004', '255baf1a', 2, False, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
2026-10-14T11:35:00Z error cap reached on duplicate:F0001-S0004: CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md
tick 33: stopped=None event=duplicate:F0001-S0004 at 255baf1a (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=reported
   count: ('duplicate:F0001-S0004', '255baf1a', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 34: stopped=None event=duplicate:F0001-S0004 at 255baf1a (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=capped
   count: ('duplicate:F0001-S0004', '255baf1a', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 35: stopped=None event=duplicate:F0001-S0004 at 255baf1a (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=capped
   count: ('duplicate:F0001-S0004', '255baf1a', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
   factory log: ['2026-10-14T11:35:00Z error cap reached on duplicate:F0001-S0004: CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md']
exit 0
````

Green. What each step shows:

- **0. The wiring.** `build_handlers` registers ten kinds, `run` as `RunGate`, and `NOT_YET_HANDLED` holds the three kinds of F0008 and F0009.
- **1–2. Comments and an agent's question.** The three comments written while the stage worked are copied at the next stop, by id (`comments_read=[1, 2, 3]`):
  - the blank one is read without an entry;
  - the one starting `factory:` is copied (decision 1);
  - the `\r\n` comment becomes one entry.

  They are older than the question's post, so the wait stays (decision 15). The question is posted once, as `coder: …`, and tick 5 posts nothing more. The comment written after the post (id 5; id 4 is the factory's post) ends the wait in the same commit.
- **3. The hand-over.** The first attempt fails at `post_comment`, after the description was replaced and the draft flag cleared. `handed_over` stays unset and the error is counted. The next tick completes it with one cost table post (2 posts: the question and the table). The description has the seven sections of decision 17.
- **4. A close with a reason, within the cap.**
  - The comment and the `close` entry are recorded first, then the `send_back` entry.
  - The pull request is open again as a draft, labelled `stage:doing`, with `round=1`.
  - Nothing is posted.
- **5. A close without a comment, past the cap.** With `round=2 > 1` and `blocked=send_back`, the `ask` handler posts `factory: This story has now been sent back 2 times, more than 1. …`. A comment after the post answers it, and `round` stays at 2 (decision 15).
- **6. A merge.** The story is archived under `done/` with `stage done` and the entry `done (pull request merged); cost: 5 runs, …`. Its cost records move beside it, the branch is deleted, and nothing is posted.
- **7. A close before the approval.**
  - The close is found by the run gate: the story was due to run and is not waiting, so the evaluation does not look it up.
  - It is discarded with 0 agent runs, back in the backlog byte for byte, and the branch is deleted.
  - Started again, it has one cost record (the new intake run) and a new pull request (#3): the bill is empty (GH4.3).
- **8. The attempts cap.** Two stalls bring the attempts to 2. The `ask` handler records the question (`blocked=attempts_cap`) and posts it with the latest stall's text. The answer sets `attempts` to 0.
- **9. An illegal stage change.**
  - The human changes doing → intake by hand.
  - `reject` moves it back with the subject `… stage intake -> doing, moved back` and posts the correction note naming `factory/pipeline.yml`.
  - The label `stage:doing` is set again.
- **10. A merge before a run.** The story is due to run and its pull request is merged. The gate hands the event to the merged handler: 0 agent runs, the story is archived and the branch is gone (decision 20).
- **11. A duplicate.** The error is counted on ticks 31 and 32 and reported on tick 33. Ticks 34 and 35 are capped. With no branch on the remote, the report is the factory log line (decision 16).

## 3 Mutation score

There is no `make mutants` target. That follows the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`), so there is no score from that target. As in the F0006 acceptance, I ran a hand pass instead:

- on a fresh copy of today's `src/` and `tests/` (`/tmp/f7mut`, green unmutated: 212 tests in 20 s);
- with the script `/tmp/f7demo/mutate.py`, 52 mutants over every F0007 module: the eleven handler modules and `domain/answers.py`, `send_back.py`, `hand_over.py`, `archive.py` and the send-back cap of `post_texts.py`;
- each mutant run against `tests/application/handlers`, the domain tests of those modules and `tests/entry/test_wiring_handlers.py`.

```bash
uv run python /tmp/f7demo/mutate.py
```

**50 of 52 killed.** Grouped by module, with the test that killed each:

| # | Module | Mutants | Result |
|---|---|---|---|
| 0, 2–3 | `recording.py` | no clean before the checkout; a refused branch deletion or push passes | killed |
| 1 | `recording.py` | no `reset_to(origin/<branch>)` after the checkout | **survived** (equivalent) |
| 4–7, 9–12 | `comments.py` | factory posts or read ids copied; blank comments copied; CRLF kept; an older or a blank comment answers; the post looked up under the wrong kind; an answer without a posted question | killed |
| 8 | `comments.py` | the entry's date taken without `astimezone(UTC)` | **survived** (equivalent) |
| 13–15 | `answers.py` | attempts or crashes not reset; `round` reset too | killed |
| 16–19 | `questions.py` | the cap `<` → `<=`; key `n` from the journal length; no speaker prefix; posted before recorded | killed |
| 20–22 | `merged.py` | cost records not moved; claim kept; branch deleted before the archive is pushed | killed |
| 23–30 | `closed.py` | discard deletes the branch first; no draft after the reopen; reopen before the close is recorded; close recorded twice; `handed_over` kept; no label; round not raised; claim kept | killed |
| 31–34 | `send_back.py`, `post_texts.py` | target `next[0]`; the cap of any capped stage; any comment is a reason; cap `>` → `>=` | killed |
| 35–39 | `reject.py` | note key off by one; corrections moved back; no label; claim kept; note posted after the record | killed |
| 40–46 | `hand_over.py` (both) | handed over again; not marked ready; cost key without the result number; any stage handed over; recorded before the effects; a report from any speaker; short ids of 8 | killed |
| 47 | `lookups.py` | the event's detail dropped | killed |
| 48–50 | `run_gate.py` | closed runs the stage; merged goes to the closed handler; kind not rewritten | killed |
| 51 | `archive.py` | a path outside the lifecycle folders accepted | killed |

Both survivors are equivalent mutants, not missing criteria:

- **1.** `WorkItemRecorder.check_out` runs `reset_to("HEAD")`, then `checkout(branch, start_point="origin/<branch>")`, then `reset_to("origin/<branch>")`. `GitCli.checkout` with a start point is `git switch --force-create`, which already puts the branch at the remote head, and the first `reset_to` already removed every leftover. The third call cannot change anything the tests or a kill could observe. It is a harmless belt-and-braces line.
- **8.** `PullRequestComment`'s `created_at` validator (`factory.domain.hosting`) already converts every timestamp to UTC. The handler's `astimezone(UTC)` is therefore redundant. The test with a Berlin timestamp just before midnight UTC (`test_append_adds_one_dated_human_comment_entry_per_comment_in_order`) does pin the rule at the DTO.

No group of survivors, so no draft for missing criteria. `make check` reports 99 % branch coverage over `src/factory` (4947 statements, 23 missed, 23 partial branches).

## 4 What the stories noticed

Collected from the coder, reviewer and documenter entries of S0001–S0010, and where each stands:

- **`_state_of` is defined five times, with two behaviours.** S0001's reviewer, and S0002, S0005, S0006, S0007 and S0009's coders, noted it. It lives in `comments.py`, `questions.py`, `closed.py`, `reject.py` and `hand_over.py`. The first three raise `ValueError`; `reject.py` and `hand_over.py` raise `CannotHandle`. The path is reachable only when the branch's head file has lost its state after the event was evaluated. Either exception is a counted error of the dispatcher, so nothing is lost. No draft of its own: a story that next touches the handlers can share it in `recording.py`.
- **`CommentCopier.copy` does not fetch** (S0001 coder and reviewer). The callers run inside a tick, which fetches first, and the project guide says so. Nothing to do.
- **The F0007 handlers were not registered until S0010** (S0006 reviewer and documenter, S0007 documenter). Resolved by S0010. Its documentation repair missed three passages of the operator guide (section 5).
- **The operator guide's opening paragraph does not name these handlers** (S0008 documenter, "a summary and still true"). Still standing; part of draft S0011.
- **`REQUIRED` in `tests/application/handlers/test_handlers_raise.py` lacks `hand_over`** (S0009 tester, coder and reviewer). The test walks the package, so the new module is covered; its `REQUIRED` list is only a floor. No draft. Whoever next touches that test can add `hand_over` and `run_gate`.
- **F0006-S0007's Demo prints the old `NOT_YET_HANDLED`** (S0010 coder and reviewer). That is an archived story's record of its own day. Nothing to do.
- **The claim is cleared in the state, not through `ClaimService.release`** (S0003, S0005, S0006). This is decision 22, allowed by `tests/test_claim_ownership.py`. Section 6.

## 5 The documentation as a whole

I read `README.md`, the operator guide's opening paragraph and every section that F0007 touched, the project guide's "The handlers of the events" and its journal-reading rule, and the two F0007 entries of `docs/decisions.md`. I checked them against the code and the demo. The sections each story wrote for its own handler match:

- the hand-over, merge, discard, send-back and move-back sections of the operator guide;
- "An event that keeps failing" and "Stops that cannot be done";
- the project guide's ask, merged, reject, lookup, recorder and copier subsections.

What does not match:

1. **`ask` and `comment` described as not registered** (operator guide):
   - the cap bullet of "A stall: the stall note" ("no tick registers it yet, so today the event is a counted error");
   - "The factory's own questions" ("today these comments do not appear");
   - "Which comment answers a question" ("today comments are not handled … Once it is registered").

   `build_handlers` registers both (demo step 0), and the same guide's "An event that keeps failing" says so. The guide contradicts itself and the code.
2. **The send-back row of the questions table.** The row says that a close "sends the story back again, or discards it". After a send-back the story is at `doing`, not at an approval, so a close discards it. The question's own option 2 says "discard".
3. **The summaries of what is built** in `README.md` and the operator guide's opening paragraph stop at "the dispatcher with the run handler". A newcomer reads that no handler of the human's acts exists.
4. **The project guide's closed handler.** Step 1 under "A close before the approval discards the story" says that at an approval the handler "returns and does nothing: the send-back is F0007-S0005's to fill in there". The project guide also has no subsection for:
   - the send-back;
   - the comment handler's answer rule (`unblock`);
   - the hand-over handler.

   The operator guide describes all three for the operator; an agent's guide has nothing.
5. **The journal-reading rule in the project guide** lists `factory.application.handlers.hand_over` as allowed to use `entry_text`. The test allows `factory.domain.hand_over`, by the human's answer in S0009.

None of these is a wrong example that a user runs. Draft S0011 repairs all five.

## 6 Decisions taken for the human

Decisions 1–20 and 22–24 of `FEATURE.md` were built as written. The demo shows 1, 2, 3, 5, 9, 10, 11, 15, 16, 17 and 20 directly, and 7 (byte for byte, branch deleted, nothing posted).

**Still open, for the human to decide:**

- **A. Decision 21: a branch left behind by an interrupted discard.** A kill or a refused deletion between the pushed discard and the branch deletion leaves the old branch with its closed pull request on the remote. A new start of the story reads that old state, the `RunGate` discards it again, and GH4.3 (an empty bill on restart) fails on that path. The operator guide tells the operator to delete the branch by hand (decision 8). `FEATURE.md` names two options:
  - (a) F0006's tick deletes the remote branch of any work item whose file is in `backlog/` on `origin/main`;
  - (b) F0005-S0002's opening deletes a branch whose recorded pull request is closed.

  Both belong to another feature, so I wrote no draft here. I recommend (a). It also covers the same leftover after a merge (decision 6), when the file is under `done/`, if its rule is widened to `done/`.
- **B. Carried from the F0006 acceptance (item A): a work item branch created by hand is never judged by the move rule.** S0006 kept the exemption of the opening commit, and the operator guide documents it. No answer is recorded, so today's behaviour, option (a) of that report, stands by default. I list it only for the human to confirm or revisit.

**Answers given during the stories**, all built as answered:

- **S0005**
  - Entry 3: a second close after an earlier send-back and a new `result` records a new `close`.
  - Entry 7: the test's `CLAIM` moved to `stage="approval"`, and the domain validator stays.
- **S0006** entry 3: two criteria added. A failing `set_labels` raises and leaves the correction pushed. An unreadable parent is `CannotHandle`.
- **S0007** entry 3: the `question_posted` rule is F0006-S0002's and is only relied on.
- **S0009** entry 5: `ALLOWED["entry_text"]` in `tests/test_no_journal_reading.py` now names `factory.domain.hand_over`.
- **S0010** entry 5: the gate's test body gained a journal section, and `MergedHandler` stays strict about the journal.

Three of these (S0005 entry 7, S0009, S0010) are the same pattern: a test whose fixture could not hold under an existing rule, found only by the coder and settled through the human under R9. Section 8 gives the cost.

## 7 The slow checks

None. Beyond `make check` the project has no slow check: no `make mutants` target (by the recorded decision; section 3 has a hand pass instead), no image scan and no SBOM.

## 8 Cost

The ten stories cost 71 runs, 150.7 min and $19.83. No story needed a review round.

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0001 | 6 | 10.3 | $2.06 | first pass |
| S0002 | 6 | 8.3 | $1.77 | first pass |
| S0003 | 6 | 8.5 | $2.02 | first pass |
| S0004 | 6 | 9.2 | $1.43 | first pass |
| S0005 | 10 | 17.1 | $3.04 | an intake question (two criteria), then a test fixture refused by the claim validator, sent back through the human and the tester |
| S0006 | 7 | 23.2 | $2.11 | an intake question (two criteria added) |
| S0007 | 7 | 10.7 | $1.99 | an intake question (the `question_posted` rule) |
| S0008 | 6 | 6.7 | $1.16 | first pass |
| S0009 | 8 | 30.9 | $2.07 | a test of F0005 (`test_no_journal_reading.py`) contradicted the Interface: question, tester, coder again |
| S0010 | 9 | 25.8 | $2.18 | a test fixture without a journal: question, tester, coder again |

**S0005 stands out** at 10 runs and $3.04, with two questions.

**S0009 and S0010 are the longest in wall time.** Their logs show the extra coder run after the test change, not why the 8 and 9 runs took 31 and 26 minutes; the per-run minutes are not in the logs.

**The cost pattern.** The "test that contradicts the Interface" round trip (S0005, S0009, S0010) cost three extra runs each, about $1.80 together. In all three the conflict was between a fixture and a rule from an earlier story, which intake cannot see from the Interface alone. That is a property of R9 and of how the tester writes fixtures, not of this feature, so it is the human's to weigh.

## Proposed stories

- `drafts/F0007-S0011-documentation-after-the-human-on-the-pull-request.md`: the five documentation findings of section 5. Documentation only.

No second draft. The hand mutation pass left no survivor that a criterion could kill (section 3). The `_state_of` clean-up and the `REQUIRED` list (section 4) are too small for a story of their own. The open product question (section 6, A) belongs to F0006 or F0005.

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 50 of 52, and both survivors are equivalent)
         1 Scope: none. Every scope item has its story (S0001–S0010) and its code. Nothing out of scope was built. One small difference, not a finding: HAND_OVER_CLOSING lives in domain/hand_over.py, not post_texts.py, as S0009's Interface and the human's answer placed it.
         2 Feature demo: green, exit 0. The script is /tmp/f7demo/demo.py (md5 171e9092…), with the production handler_factory on a real remote; output pasted. It walks through comments copied by id; a question posted once and answered; a hand-over that fails once and is completed from state; a send-back within the cap and a send-back question past it; a merge with its bill; a discard found by RunGate with 0 runs and an empty bill on restart; the attempts cap; a move back; a merge before a run; and a duplicate capped and reported.
         3 Mutation score: no make mutants target. The hand pass covered 52 mutants over every F0007 module and killed 50. Survivor 1 (check_out's last reset, after switch --force-create) and survivor 8 (astimezone(UTC), which the DTO validator already applies) are both equivalent. No group, so no criteria draft. make check is green at 99 %.
         4 Noticed: _state_of is defined five times and raises ValueError or CannotHandle (harmless, no draft). copy does not fetch (by design). The handlers are now registered (S0010). The REQUIRED list in test_handlers_raise lacks hand_over (the module walk covers it). F0006-S0007's old demo text is history. The claim is cleared in the state (decision 22).
         5 Documentation: five findings, all in draft S0011. The operator guide says in three places that ask and comment are not registered. The send-back row of its questions table says a close sends the story back again; it discards. The README and operator-guide summaries omit F0007. The project guide says the closed handler does nothing at an approval, and it has no send-back, answer or hand-over subsection. The project guide's journal-reading rule names handlers.hand_over instead of domain.hand_over.
         6 Decisions: decisions 1–20 and 22–24 were built as written. Open for the human: decision 21, the branch left behind by an interrupted discard, which breaks GH4.3 on that path. Its fix belongs to F0006 or F0005; I recommend the tick deleting the remote branch of a work item that is in backlog/. Also carried from F0006 for confirmation: a branch created by hand is never judged. The story answers of S0005, S0006, S0007, S0009 and S0010 were built as answered.
         7 Slow checks: none (no mutants target, no image scan, no SBOM).
         8 Cost: 71 runs, 150.7 min, $19.83, with no review rounds. S0005 stands out (10 runs, $3.04, two questions). S0005, S0009 and S0010 each paid about 3 runs for a test fixture that clashed with an earlier rule, settled through the human under R9. S0009 and S0010 are the longest in wall time; the logs do not say why.
