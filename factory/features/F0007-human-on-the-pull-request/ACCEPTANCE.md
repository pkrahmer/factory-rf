---
stage: accept
pr: 94
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0007-S0001, F0007-S0002, F0007-S0003, F0007-S0004, F0007-S0005, F0007-S0006, F0007-S0007, F0007-S0008, F0007-S0009, F0007-S0010, F0007-S0011]
---
# Acceptance of The human on the pull request

## Verdict

**accepted.** This is the second acceptance of F0007. The first (pull request #92, merged) found that the ten stories together do what `FEATURE.md` promised, and proposed one draft, S0011, for five documentation findings. S0011 was built and merged. Its changes are documentation only: `src/` and `tests/` are byte for byte the same as at the first acceptance (`git diff --quiet 94f0064 HEAD -- src tests pyproject.toml uv.lock Makefile`).

I re-ran the first acceptance's feature demo against today's code. It is green and prints the same events, counts, posts and states; only commit ids differ. The hand mutation pass again kills 50 of 52, and the two survivors are still the two equivalent mutants. `make check` is green at 99.22 %. I read the five findings against the docs and the code, and all five are repaired. The new project-guide subsections match `closed.py`, `comments.py`, `answers.py`, `send_back.py` and `hand_over.py`.

Nothing of weight is left. Decision 21 is now covered by F0008-S0004's draft. The two remaining product points are listed in section 6 for the human. No drafts.

## 1 Scope

None. The scope table of the first acceptance (`git show 94f0064:factory/features/F0007-human-on-the-pull-request/ACCEPTANCE.md`, section 1) still holds: each scope item has its story (S0001–S0010) and its code, and the code is unchanged since then.

S0011 stays inside the scope. `FEATURE.md` lists it as proposed by the feature acceptance. It changed only `README.md`, `docs/operator-guide.md` and `docs/project-guide.md`, and its tester and coder wrote nothing, on purpose.

Out of scope stays out:

- `crash`, `expired` and `acceptance_due` are still in `NOT_YET_HANDLED` (demo step 0).
- The handlers do nothing specific to an acceptance.
- Labels are written again only after a send-back and after a move back.

## 2 Feature demo

The script is unchanged from the first acceptance: `/tmp/f7demo/demo.py`, md5 `171e909241458a727503d764181f0a8d`. That report describes it in section 2. In short, it uses:

- the production `handler_factory` and `production_environment()`, with a `Tick` per pass;
- a real bare remote with a human clone (`tests/human_clone.py`) and `GitCli`;
- `FakeHostingService`, on which the human comments, closes and merges;
- `FakeAgentRuntime` with scripted results.

The pipeline is intake → doing (`round_cap: 1`) → approval (`next: [done, doing]`), with `attempts_cap: 2`.

```bash
uv run python /tmp/f7demo/demo.py; echo "exit $?"
```

````text
== 0. the wiring ==
NOT_YET_HANDLED: ('crash', 'expired', 'acceptance_due')
registered: {'idle': 'IdleHandler', 'run': 'RunGate', 'comment': 'CommentHandler', 'ask': 'AskHandler', 'merged': 'MergedHandler', 'closed': 'ClosedHandler', 'reject': 'RejectHandler', 'hand_over': 'HandOverHandler', 'duplicate': 'DuplicateHandler', 'pull_request_lookup': 'PullRequestLookupHandler'}
== 1. S0001 starts; the human comments while the stage works; the agent asks ==
tick 1: stopped=None event=run:F0001-S0001 at e9731bf2 (after the tick, remote work-item/F0001-S0001 at dd3aadd0) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=0
tick 2: stopped=None event=run:F0001-S0001 at dd3aadd0 (after the tick, remote work-item/F0001-S0001 at a153acb4) dispatch=handled
   stage=doing blocked=question round=0 attempts=0 handed_over=None comments_read=[] claim=None
== 2. the comments are copied by id; the question is posted once; a later comment answers ==
tick 3: stopped=None event=comment:F0001-S0001 at a153acb4 (after the tick, remote work-item/F0001-S0001 at 8cb98e5c) dispatch=handled
   stage=doing blocked=question round=0 attempts=0 handed_over=None comments_read=[1, 2, 3] claim=None
   journal: (5, 'coder', 'question', 'shall hello() take a name?')
   journal: (6, 'human', 'comment', 'Please keep it short.')
   journal: (7, 'human', 'comment', 'factory: this looks like a factory post but has no marker')
tick 4: stopped=None event=ask:F0001-S0001 at 8cb98e5c (after the tick, remote work-item/F0001-S0001 at 8cb98e5c) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=1
   last factory post: coder: shall hello() take a name?
tick 5: stopped=None event=idle:- dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=1
tick 6: stopped=None event=comment:F0001-S0001 at 8cb98e5c (after the tick, remote work-item/F0001-S0001 at 5c13ade6) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[1, 2, 3, 5] claim=None
   journal: (8, 'human', 'comment', 'No name, keep it plain.')
== 3. the hand-over, failing once, completed from state ==
tick 8: stopped=None event=run:F0001-S0001 at 5c13ade6 (after the tick, remote work-item/F0001-S0001 at f02fa1e4) dispatch=handled
tick 9 (post_comment fails): stopped=None event=hand_over:F0001-S0001 at f02fa1e4 (after the tick, remote work-item/F0001-S0001 at f02fa1e4) dispatch=error
   count: ('hand_over:F0001-S0001', 'f02fa1e4', 1, False, 'HostingServiceError: hosting service post_comment failed: injected failure')
   stage=approval blocked=None round=0 attempts=0 handed_over=None comments_read=[1, 2, 3, 5] claim=None | #1 state=open draft=False labels=['stage:approval'] factory posts=1
tick 10: stopped=None event=hand_over:F0001-S0001 at f02fa1e4 (after the tick, remote work-item/F0001-S0001 at 670c6f0f) dispatch=handled
   stage=approval blocked=None round=0 attempts=0 handed_over=approval comments_read=[1, 2, 3, 5] claim=None | #1 state=open draft=False labels=['stage:approval'] factory posts=2
   description sections: ['## Description', '## Acceptance criteria', '## Tests', '## Review', '## Documentation', '## Smoke test', '## Commits']
tick 11: stopped=None event=idle:- dispatch=handled
   #1 state=open draft=False labels=['stage:approval'] factory posts=2
== 4. a close at the approval with a reason sends back within the cap ==
tick 12: stopped=None event=closed:F0001-S0001 at 670c6f0f (after the tick, remote work-item/F0001-S0001 at f984a02d) dispatch=handled
   stage=doing blocked=None round=1 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7] claim=None | #1 state=open draft=True labels=['stage:doing'] factory posts=2
   journal: (11, 'human', 'comment', 'Rename the module, please.')
   journal: (12, 'human', 'close', 'closed the pull request.')
   journal: (13, 'factory', 'send_back', 'sent back to doing, round 1.')
== 5. a close without a comment past the cap asks; the answer unblocks ==
tick 13: stopped=None event=run:F0001-S0001 at f984a02d (after the tick, remote work-item/F0001-S0001 at 251436bf) dispatch=handled
tick 14: stopped=None event=hand_over:F0001-S0001 at 251436bf (after the tick, remote work-item/F0001-S0001 at 0c2f6f6c) dispatch=handled
tick 15: stopped=None event=closed:F0001-S0001 at 0c2f6f6c (after the tick, remote work-item/F0001-S0001 at d9600f95) dispatch=handled
   stage=doing blocked=send_back round=2 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7] claim=None | #1 state=open draft=True labels=['stage:doing'] factory posts=3
tick 16: stopped=None event=ask:F0001-S0001 at d9600f95 (after the tick, remote work-item/F0001-S0001 at d9600f95) dispatch=handled
   #1 state=open draft=True labels=['stage:doing'] factory posts=4
   last factory post: factory: This story has now been sent back 2 times, more than 1. What should happen? 1. Comment what should ch
tick 17: stopped=None event=comment:F0001-S0001 at d9600f95 (after the tick, remote work-item/F0001-S0001 at 633e157b) dispatch=handled
   stage=doing blocked=None round=2 attempts=0 handed_over=None comments_read=[1, 2, 3, 5, 7, 10] claim=None
== 6. a merge archives the story with its bill ==
tick 18: stopped=None event=run:F0001-S0001 at 633e157b (after the tick, remote work-item/F0001-S0001 at a976d06f) dispatch=handled
tick 19: stopped=None event=hand_over:F0001-S0001 at a976d06f (after the tick, remote work-item/F0001-S0001 at d3b6c6b3) dispatch=handled
tick 20: stopped=None event=merged:F0001-S0001 at d3b6c6b3 (after the tick, remote work-item/F0001-S0001 at (deleted) dispatch=handled
   on main: ['done', 'F0001-S0001-s1.md'] stage done | last entry: done (pull request merged); cost: 5 runs, 10.0 min, 25 turns, 500 tokens in (0 more from cache), 100 out, $0.50
   cost records beside it: True | files in done/: ['factory/features/F0001-demo/done/F0001-S0001-s1.costs.jsonl', 'factory/features/F0001-demo/done/F0001-S0001-s1.md']
   branch on remote: None | new posts on the merged PR: 0
== 7. a close before the approval discards (found by the run gate); a restart starts with an empty bill ==
tick 21: stopped=None event=run:F0001-S0002 at 3974d762 (after the tick, remote work-item/F0001-S0002 at 8ffa72a1) dispatch=handled
tick 22: stopped=None event=run:F0001-S0002 at 8ffa72a1 (after the tick, remote work-item/F0001-S0002 at (deleted) dispatch=handled
   agent runs in tick 22: 0
   back in backlog byte for byte: True | branch on remote: None | #2 state=closed draft=True labels=['stage:doing'] factory posts=0
tick 23: stopped=None event=run:F0001-S0002 at 0fcccedf (after the tick, remote work-item/F0001-S0002 at f5cdcd1d) dispatch=handled
   cost records after the restart: 1 | pull request: 3
== 8. the attempts cap: recorded, posted, answered ==
tick 24: stopped=None event=run:F0001-S0002 at f5cdcd1d (after the tick, remote work-item/F0001-S0002 at b8ee092f) dispatch=handled
tick 25: stopped=None event=run:F0001-S0002 at b8ee092f (after the tick, remote work-item/F0001-S0002 at aa77fc45) dispatch=handled
   stage=doing blocked=None round=0 attempts=2 handed_over=None comments_read=[] claim=None
tick 26: stopped=None event=ask:F0001-S0002 at aa77fc45 (after the tick, remote work-item/F0001-S0002 at d7a0ab0f) dispatch=handled
   stage=doing blocked=attempts_cap round=0 attempts=2 handed_over=None comments_read=[] claim=None | #3 state=open draft=True labels=['stage:doing'] factory posts=3
   last factory post: factory: Stage doing stalled 2 times. The last time: Stage doing stalled (attempt 2 of 2): the agent gave no valid decision and entry
tick 27: stopped=None event=comment:F0001-S0002 at d7a0ab0f (after the tick, remote work-item/F0001-S0002 at 0ab5529f) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[15] claim=None
== 9. an illegal stage change is moved back ==
tick 28: stopped=None event=reject:F0001-S0002 at 70a2bda0 (after the tick, remote work-item/F0001-S0002 at 9c8c3083) dispatch=handled
   stage=doing blocked=None round=0 attempts=0 handed_over=None comments_read=[15] claim=None | #3 state=open draft=True labels=['stage:doing'] factory posts=4
   subject: work item F0001-S0002: stage intake -> doing, moved back
   note: The stage was changed from doing to intake, which factory/pipeline.yml does not allow; it is back at doing.
== 10. a merge found right before an agent run is handled first ==
tick 30: stopped=None event=run:F0001-S0002 at 9c8c3083 (after the tick, remote work-item/F0001-S0002 at (deleted) dispatch=handled
   agent runs during the tick: 0 | S0002 in done/: True | branch on remote: None
== 11. a stop with no work to do is a counted error, reported once ==
tick 31: stopped=None event=duplicate:F0001-S0004 at f79c2f02 (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=error
   count: ('duplicate:F0001-S0004', 'f79c2f02', 1, False, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 32: stopped=None event=duplicate:F0001-S0004 at f79c2f02 (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=error
   count: ('duplicate:F0001-S0004', 'f79c2f02', 2, False, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
2026-10-14T11:35:00Z error cap reached on duplicate:F0001-S0004: CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md
tick 33: stopped=None event=duplicate:F0001-S0004 at f79c2f02 (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=reported
   count: ('duplicate:F0001-S0004', 'f79c2f02', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 34: stopped=None event=duplicate:F0001-S0004 at f79c2f02 (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=capped
   count: ('duplicate:F0001-S0004', 'f79c2f02', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
tick 35: stopped=None event=duplicate:F0001-S0004 at f79c2f02 (after the tick, remote work-item/F0001-S0004 at (deleted) dispatch=capped
   count: ('duplicate:F0001-S0004', 'f79c2f02', 3, True, 'CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md')
   factory log: ['2026-10-14T11:35:00Z error cap reached on duplicate:F0001-S0004: CannotHandle: cannot handle duplicate: two work items share the id F0001-S0004: F0001-S0004 at factory/features/F0001-demo/in-progress/F0001-S0004-copy.md and factory/features/F0001-demo/in-progress/F0001-S0004-s4.md']
exit 0
````

Green. I diffed this output against the first acceptance's (`/tmp/f7demo/out.txt`), masking 8-character hex ids, temporary paths and times. The only difference is the trailing `exit 0` line, which the first run did not capture. Every event, count, `reported`/`capped` flag, journal entry, label and post is the same. The first acceptance's reading of each step therefore stands. Against the Goal's "Done when":

- **Each handler keeps the human's act through a failure.** A hand-over fails at `post_comment` and is completed from state (ticks 9–10). A close is recorded before the reopen (step 4). The kill points are pinned by the stories' tests and by mutants 22–27 and 39.
- **No post repeats.** Ticks 5 and 11 are idle, and the post count does not change. One cost table is posted after the failed attempt.
- **Every comment event is bounded by the error cap of three.** Step 11 shows the cap: counted, then reported, then capped. S0007's tests show it for `comment` and `ask` through the dispatcher.
- **A close or a merge found right before an agent run is handled before that run.** Steps 7 and 10, each with 0 agent runs.

## 3 Mutation score

There is no `make mutants` target. That follows the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`), so that target gives no score. Instead I repeated the first acceptance's hand pass:

- on a fresh copy of today's `src/` and `tests/` (`/tmp/f7mut2`);
- with the same 52 mutants (`/tmp/f7demo/mutate2.py`, which is `mutate.py` with the new root), over every F0007 module;
- each mutant run against `tests/application/handlers`, the domain tests of those modules and `tests/entry/test_wiring_handlers.py`.

```bash
uv run python /tmp/f7demo/mutate2.py
```

**50 of 52 killed**, the same mutants killed by the same tests as in the first pass. The table in the first acceptance's section 3 applies unchanged. The survivors are the same two, and both are still equivalent:

- **1 `recording.py`, no `reset_to(origin/<branch>)` after the checkout.** `GitCli.checkout` with a start point is `git switch --force-create`, which already puts the branch at the remote head after the first `reset_to("HEAD")`. The third call changes nothing that can be observed.
- **8 `comments.py`, the entry date without `astimezone(UTC)`.** `PullRequestComment`'s `created_at` validator already converts every timestamp to UTC, and a test pins that rule at the DTO.

No group of survivors, so no draft for missing criteria. `make check` is green: lint, types, layers, sast, secrets, licenses, and the tests with 99.22 % branch coverage.

## 4 What the stories noticed

S0011 noticed nothing new:

- The documenter wrote "Stale but unrelated and left alone: none seen".
- The tester, coder and reviewer had nothing to build and noted nothing else.
- The one remark is the demo's: command 3's grep was too broad. It matched line 638 of the project guide, the new hand-over subsection, which rightly names `factory.application.handlers.hand_over` as the module of `HandOverHandler`. The human ruled it not a finding (S0011 entry 8). That grep came from the first acceptance's own draft, so the lesson is the acceptor's: a Demo grep for a stale phrase must anchor on the context of that phrase, not on a name the repaired text may also use.

What the first acceptance collected, and where it stands:

- **Repaired by S0011:** the operator guide's opening paragraph did not name the handlers (S0008's documenter).
- **Still standing, no draft:**
  - `_state_of` is defined five times. Three copies raise `ValueError`; `reject.py` and `hand_over.py` raise `CannotHandle`. Both are counted errors of the dispatcher, so nothing is lost.
  - `REQUIRED` in `tests/application/handlers/test_handlers_raise.py` lacks `hand_over` and `run_gate`. The test walks the whole package, so the list is only a floor.

  Neither breaks a rule. F0008's handlers (crash, expired) will sit beside these modules, and a story there can share `_state_of` in `recording.py` in passing.
- **Unchanged by design:** `CommentCopier.copy` does not fetch, because the tick fetches first. F0006-S0007's archived Demo shows its own day's `NOT_YET_HANDLED`.

## 5 The documentation as a whole

I read `README.md` from the top, then the operator guide's opening paragraph and every F0007 section, including "The factory's own questions", "Which comment answers a question" and "An event that keeps failing". In the project guide I read "The handlers of the events" and the journal-reading rule. I checked them against the code and the demo.

The five findings of the first acceptance are repaired:

1. **`ask` and `comment` are no longer called unregistered.** A grep for "registers it yet", "Once it is registered", "today comments are not handled", "not registered" and "these comments do not appear" finds nothing in `README.md` or `docs/`. The cap bullet now says that the `ask` handler records and posts the attempts-cap question, as demo step 8 shows.
2. **The send-back row of the questions table** now says that a close discards the story, which is what `ClosedHandler` does at a non-approval stage (demo step 7).
3. **The summaries of what is built.** `README.md` and the operator guide's opening now name the handlers of the human's acts, and both still say that no command runs ticks before F0010.
4. **The project guide's closed handler.** Its step 1 now points to the send-back. The three new subsections match the code:
   - **The send-back.** `send_back_target` is `next[1]` or `None`. `send_back_cap` is the first capped stage whose `next[0]` is the approval. `recorded_since_latest_result` counts any record when there is no result. The order is close recorded → `reopen` → `set_draft(True)` → `sent back` → `set_labels` (`closed.py:70-117`).
   - **The comment handler.** The post is keyed by the blocked value and the latest question's number, and the comment's id must be greater than the post's. `unblock` resets only `attempts` or `crashes` and keeps `round` (`comments.py:103-126`, `answers.py`).
   - **The hand-over.** The order is description → `set_draft(False)` → cost table keyed by the latest result's number, or `0` → record, and it returns at once when `handed_over` equals the stage (`hand_over.py:45-80`). The report speakers include `smoke-tester` (`domain/hand_over.py:15-19`).
5. **The journal-reading rule** names `factory.domain.hand_over`, matching `ALLOWED` in `tests/test_no_journal_reading.py`.

The operator guide's "An event that keeps failing" lists `crash`, `expired` and `acceptance_due` as unhandled. That equals `NOT_YET_HANDLED` in demo step 0, and the project guide and `docs/decisions.md` say the same.

Newcomer check of `README.md`'s commands:

- `uv run factory-watch` ends with status 2 and `factory-watch: no instance settings are wired yet`, as written.
- `uv run factory-run` ends with `ModuleNotFoundError: No module named 'factory.entry.run'`, as written.
- `uv run factory-check-story` on a story here prints `cannot read factory/story-form.md: …` and exits 2. That is what the operator guide says it does in this repository, whose `factory/` tree is v1's.

Findings: none.

## 6 Decisions taken for the human

Decisions 1–20 and 22–24 of `FEATURE.md` were built as written. The first acceptance's section 6 maps them to the demo, and the code has not changed since. S0011 took no decision of its own. Its one question (S0011 entry 7) was the demo grep, and the human answered (b): not a finding.

What happened to the two items the first acceptance left open:

- **A. Decision 21: a branch left behind by an interrupted discard.** This is now covered by a plan, not yet by code.
  - F0008 decision 17 takes option (a), the tick's cleanup of a branch whose story is in `backlog/`, as the draft `factory/features/F0008-crash-recovery/drafts/F0008-S0004-a-stale-branch-of-a-discarded-story-is-deleted.md`. Its criterion 11 restores GH4.3 after a kill.
  - Until F0008-S0004 is merged, the operator guide's instruction (delete the branch by hand) is the only way out, and it is documented.
  - Still for the human: F0008 decision 17 leaves the branches of stories in `done/` alone. So the leftover after a merge (F0007 decision 6: a kill between the pushed archive and the branch deletion) is never deleted. It is harmless, because nothing reads a branch of an archived story, but it is clutter on the remote. The first acceptance recommended widening the rule to `done/`. I keep that recommendation; it is a one-line change of S0004 before F0008 starts. The night log of 2026-10-14 20:00 lists it "to be weighed before F0008 starts".
- **B. A work item branch created by hand is never judged by the move rule** (carried from the F0006 acceptance, item A). This is still unanswered. Today's behaviour, the opening commit exempt, stands by default and is documented in the operator guide. I list it only for the human to confirm or revisit.

The answers given during S0005, S0006, S0007, S0009 and S0010 were built as answered; the first acceptance lists them.

## 7 The slow checks

None. Beyond `make check` the project has no slow check: no `make mutants` target (by the recorded decision; section 3 has the hand pass instead), no image scan and no SBOM.

## 8 Cost

The eleven stories cost 78 runs, 157.1 min and $20.69. The first acceptance accounted for S0001–S0010: 71 runs, 150.7 min, $19.83. Its own run cost $4.30 and is not in the sum.

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0011 | 7 | 6.4 | $0.86 | documentation only; one extra demo run for the question about the too-broad grep (entries 7–9) |

S0011 does not stand out. It cost a fifth of the acceptance that found it.

**Two cost patterns, both seen before:**

- **Empty stages on a documentation-only story.** The tester, coder and reviewer each spent a run to say there was nothing to do; the F0006 acceptance saw the same with its S0008.
- **The extra demo run.** It came from a Demo that the acceptor wrote; section 4 has the lesson.

Within the feature, S0005 still stands out: 10 runs and $3.04, with two questions. The first acceptance's section 8 gives the detail, including the three "fixture against an earlier rule" round trips of S0005, S0009 and S0010.

## Proposed stories

None. The five findings of the first acceptance are repaired by S0011. The mutation pass left only equivalent survivors. The two items still standing in section 4 are too small for a story of their own. The open matters of section 6 are product questions: one belongs to F0008's draft S0004, which is the human's, and the other is unanswered since F0006.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 50 of 52, and both survivors are equivalent)
      This is the second acceptance of F0007. The first (#92) proposed S0011 for five documentation findings, and S0011 is now merged. src/ and tests/ are unchanged since the first acceptance (94f0064); only README.md and docs/ changed.
      1 Scope: none. Every scope item has its story (S0001–S0010) and its unchanged code. S0011 is documentation inside the scope. Nothing out of scope was built: crash, expired and acceptance_due are still in NOT_YET_HANDLED.
      2 Feature demo: green, exit 0. I re-ran /tmp/f7demo/demo.py (md5 171e9092…) with the production handler_factory on a real remote, and the output is pasted. With ids, paths and times masked, it is identical to the first run: comments copied by id, a question posted once and answered, a hand-over completed from state after a failure, a send-back within the cap and the send-back question past it, a merge with its bill, a discard by RunGate with 0 runs and an empty bill on restart, the attempts cap, a move back, a merge before a run, and a duplicate capped and reported.
      3 Mutation score: no make mutants target. The same 52 hand mutants on a fresh copy (/tmp/f7mut2) killed 50, the same ones as before. The survivors are the same two equivalent mutants: check_out's last reset, and astimezone(UTC), which the DTO already applies. No group, so no criteria draft. make check is green at 99.22 %.
      4 Noticed: S0011 noticed nothing new. Its demo's command 3 grep was too broad and matched a correct module name; that was the acceptor's own draft, and the human ruled it not a finding. Still standing without a draft: _state_of is defined five times, and the REQUIRED floor in test_handlers_raise lacks hand_over and run_gate.
      5 Documentation: no findings. All five findings of the first acceptance are repaired. I checked the new project-guide subsections (send-back, comment answers, hand-over) against closed.py, comments.py, answers.py, send_back.py and hand_over.py. The README's commands behave as written.
      6 Decisions: decisions 1–20 and 22–24 were built as written. Decision 21 is now planned as F0008-S0004 (option a), which is a draft. Still for the human: F0008 decision 17 leaves branches of stories in done/ alone, so decision 6's leftover after a merge is never deleted; I recommend widening S0004 to done/ before F0008 starts. Item B, a hand-created branch never judged, is still unanswered and stands by default.
      7 Slow checks: none (no mutants target, no image scan, no SBOM).
      8 Cost: 78 runs, 157.1 min, $20.69. S0011 cost 7 runs, 6.4 min and $0.86, with one extra demo run for the grep question; it does not stand out. Documentation-only stories still pay for empty tester, coder and reviewer runs. Within the feature, S0005 still stands out (10 runs, $3.04).
