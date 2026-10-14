---
stage: accept
pr: 81
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0006-S0001, F0006-S0002, F0006-S0003, F0006-S0004, F0006-S0005, F0006-S0006, F0006-S0007, F0006-S0008, F0006-S0009]
---
# Acceptance of Reading the remote

## Verdict

**accepted.** This is the second acceptance of F0006. The first (pull request #78, merged) found that the feature did what `FEATURE.md` promised and proposed two stories. Both were built and merged:

- S0008 repaired the seven documentation findings.
- S0009 added the criteria behind the one surviving mutant.

Re-running the first acceptance's feature demo against today's code gives the same result: green, the same events, counts and outcomes; only the commit ids differ. The hand-mutation pass, extended by three mutants on the report's failure handling, now kills 28 of 28. `make check` is green at 99.35 %.

Nothing of weight is left. The one open matter is a product question (section 6, item A), and it belongs to F0007. No drafts.

## 1 Scope

None. The scope table of the first acceptance (`ACCEPTANCE.md` at commit `3d278f7`, section 1) still holds: each of the seven scope items has its story (S0001–S0007) and the code those stories name. Every "Done when" clause of the Goal shows in the demo (section 2).

The two new stories stay inside the scope:

- **S0008** is documentation only. It changed `README.md` and `docs/operator-guide.md` and touched no code.
- **S0009** is tests only: 97 lines in `tests/application/test_dispatcher.py`, and `src/` unchanged. It pins the dispatcher rule "a failed report does not count and is made again" (scope item "The dispatcher and the tick status").

Out of scope stays out. There are still no handlers for the human's acts (F0007), for a crash or an expired lease (F0008), or for the acceptance (F0009). There is no preflight or scheduler (F0010) and no `build_boundaries`. The consequence that the operator guide lacked in the first acceptance is now documented: until F0007 and F0008 register their handlers, an unhandled kind is reported once and then holds back all new work.

## 2 Feature demo

The script is unchanged from the first acceptance. It is pasted in full in that report (`git show 3d278f7:factory/features/F0006-reading-the-remote/ACCEPTANCE.md`, section 2) and kept at `/tmp/f6demo/demo.py` (md5 `8115237581a3a60a6136cd7246a307d3`).

What it uses:

- the production `handler_factory` and `production_environment()`;
- a real bare remote with a human clone (`tests/human_clone.py`);
- `GitCli`, `FakeHostingService`, and `FakeAgentRuntime` wrapped so that the human can push during a run;
- the installed `factory-watch`, called as a process.

The steps: 0 the command line; 1 a tick runs a stage; 2 a fresh clone continues; 3 a hand push past a stale local branch; 4 `run_watch`; 5 a failed fetch and its recovery; 6 the three merge methods; 7 a rejected result push and its single report; 8 a branch created by hand; 9 a stage changed by hand.

```bash
uv run python /tmp/f6demo/demo.py; echo "exit $?"
```

````text
== 0. the command line ==
$ factory-watch --follow -> exit 2; stdout []; stderr ['factory-watch: error: unrecognized arguments: --follow']; 'follow' in help: False
$ factory-watch --help -> exit 0; stdout ['usage: factory-watch [-h]']; stderr []; 'follow' in help: False
$ factory-watch  -> exit 2; stdout []; stderr ['factory-watch: no instance settings are wired yet']; 'follow' in help: False
NOT_YET_HANDLED: ('comment', 'ask', 'merged', 'closed', 'reject', 'hand_over', 'crash', 'expired', 'duplicate', 'pull_request_lookup', 'acceptance_due')
agent PATH: /work/factory-rf/.venv/bin:/usr/local/bin:/usr/bin:/bin | factory-guard found: True
== 1. tick 1 in the operator's checkout, production handlers ==
tick 1: stopped=None event=run:F0001-S0001 at 6262a320 (after the tick, remote work-item/F0001-S0001 at 6a54ff93) dispatch=handled
   agent request environment == production environment: True
== 2. a fresh clone sees the same and continues ==
   original: run:F0001-S0001 6a54ff93 doing
   fresh:    run:F0001-S0001 6a54ff93 doing
tick 2 (fresh clone): stopped=None event=run:F0001-S0001 at 6a54ff93 (after the tick, remote work-item/F0001-S0001 at 97f4979b) dispatch=handled
== 3. a hand push past a stale local branch ==
   operator's checkout is on work-item/F0001-S0001 ; local work-item/F0001-S0001 at 6a54ff93 says stage doing
tick 3: stopped=None event=hand_over:F0001-S0001 at c4ddc416 (after the tick, remote work-item/F0001-S0001 at c4ddc416) dispatch=error
   count: ('hand_over:F0001-S0001', 'c4ddc416', 1, False, 'UnhandledEvent: no handler for event kind hand_over')
   local branch after the tick: None | checkout on: main
== 4. factory-watch's view (run_watch on the same boundaries) ==
   exit 0
   | event: hand_over:F0001-S0001
   | 
   | features
   | F0001  Demo feature  backlog=1  in-progress=3  done=0  acceptance=-
   | work items
   | F0001-S0001  Story 1  in-progress  stage=approval  blocked=-  claim=-  running_since=-  pull_request=1
   | F0001-S0002  Story 2  in-progress  stage=intake  blocked=-  claim=-  running_since=-  pull_request=-
   | F0001-S0003  Story 3  in-progress  stage=intake  blocked=-  claim=-  running_since=-  pull_request=-
== 5. a failed fetch is a repository stop ==
2026-10-14T09:20:00Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp1e9qfqhe/remote.git' does not appear to be a git repository
2026-10-14T09:20:00Z fatal: Could not read from remote repository.
2026-10-14T09:20:00Z 
2026-10-14T09:20:00Z Please make sure you have the correct access rights
2026-10-14T09:20:00Z and the repository exists.
tick 4: stopped=fetch_failed event=None dispatch=None
   health stops: [('repository', 'fetch_failed')]
2026-10-14T09:25:00Z stop cleared fetch_failed
tick 5: stopped=None event=hand_over:F0001-S0001 at c4ddc416 (after the tick, remote work-item/F0001-S0001 at c4ddc416) dispatch=error
   count: ('hand_over:F0001-S0001', 'c4ddc416', 2, False, 'UnhandledEvent: no handler for event kind hand_over')
   health stops: []
== 6. no merge method is misread as an illegal stage change ==
   merged by merge: event merged:F0001-S0001
   merged by squash: event merged:F0001-S0001
   merged by rebase: event merged:F0001-S0001
tick 6: stopped=None event=merged:F0001-S0001 at c4ddc416 (after the tick, remote work-item/F0001-S0001 at c4ddc416) dispatch=error
   count: ('merged:F0001-S0001', 'c4ddc416', 1, False, 'UnhandledEvent: no handler for event kind merged')
== 7. a rejected push is judged from the remote's state ==
tick 7: stopped=None event=run:F0001-S0002 at 3d22bee6 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=error
   count: ('run:F0001-S0002', '3d22bee6', 1, False, 'PushFailed: push of work-item/F0001-S0002 failed: rejected')
tick 8: stopped=None event=crash:F0001-S0002 at e7ffdc15 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=error
   count: ('crash:F0001-S0002', 'e7ffdc15', 1, False, 'UnhandledEvent: no handler for event kind crash')
tick 9: stopped=None event=crash:F0001-S0002 at e7ffdc15 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=error
   count: ('crash:F0001-S0002', 'e7ffdc15', 2, False, 'UnhandledEvent: no handler for event kind crash')
tick 10: stopped=None event=crash:F0001-S0002 at e7ffdc15 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=reported
   count: ('crash:F0001-S0002', 'e7ffdc15', 3, True, 'UnhandledEvent: no handler for event kind crash')
tick 11: stopped=None event=crash:F0001-S0002 at e7ffdc15 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=capped
   count: ('crash:F0001-S0002', 'e7ffdc15', 3, True, 'UnhandledEvent: no handler for event kind crash')
tick 12: stopped=None event=crash:F0001-S0002 at e7ffdc15 (after the tick, remote work-item/F0001-S0002 at e7ffdc15) dispatch=capped
   count: ('crash:F0001-S0002', 'e7ffdc15', 3, True, 'UnhandledEvent: no handler for event kind crash')
   S0002 on the remote: stage intake | claim factory-1 | pr None
   factory posts on its pull request: 0
tick 13 (after the human's push): stopped=None event=crash:F0001-S0002 at 0fc472ab (after the tick, remote work-item/F0001-S0002 at 0fc472ab) dispatch=error
   count: ('crash:F0001-S0002', '0fc472ab', 1, False, 'UnhandledEvent: no handler for event kind crash')
== 8. a stage changed by hand is an illegal change ==
   event: ask:F0001-S0003 | no pull request
   S0003 on its branch: stage approval | last_stage_change: None
   pull requests: [(1, 'work-item/F0001-S0001', True, 0), (2, 'work-item/F0001-S0002', True, 1)]
   > #2: The factory failed 3 times on `crash:F0001-S0002` and has stopped retrying it. Last error: UnhandledEvent: no handler for event kind crash. A new commit on the work item's branch (now at e7ffdc157b97) makes the factory try again.
== 9. a hand stage change on a branch the factory wrote ==
   event: reject:F0001-S0002 | stage changed from intake to approval, which the pipeline definition does not allow
tick 15: stopped=None event=reject:F0001-S0002 at 08837c58 (after the tick, remote work-item/F0001-S0002 at 08837c58) dispatch=error
   count: ('reject:F0001-S0002', '08837c58', 1, False, 'UnhandledEvent: no handler for event kind reject')
exit 0
````

I diffed this output against the first acceptance's, with the temporary directory masked. The only differences are commit ids, which depend on commit timestamps. Every event, count, `reported`/`capped` flag, stop and post is the same. The first acceptance's reading of each step stands. In short:

- **Goal clauses.** The hand push is seen past a stale local branch, and that branch is then deleted (step 3). A failed fetch is a stop that the next tick clears (step 5). No merge method gives `reject` (step 6). The rejected push is judged from the remote, posts exactly one report and is then capped, and a human push restarts the count (step 7). A fresh clone continues the work item (step 2). The unhandled kinds are counted errors (steps 3, 6, 7, 9). `--follow` is refused (step 0). `NOT_YET_HANDLED` lists the eleven kinds (step 0).
- **Step 7's "factory posts on its pull request: 0".** This reads S0002's recorded `pr`, which is `None`. The report went to draft #2, which the dispatcher opened (see step 8's lines). This is decision 9, now documented under "Stops of one work item".
- **Step 8.** The branch created by hand at `approval` is not judged. This is now documented under "A stage changed by hand"; item A of section 6 is still open.

The new rule of S0009 (a report that fails with a git error) cannot be reached inside a tick. The tick fetches first, so a checkout where git fails would stop the tick at the fetch. The rule is shown instead by its story's demo, re-run here:

```bash
uv run pytest --no-header -p no:cacheprovider --cov=factory.application.dispatcher --cov-branch --cov-report=term-missing tests/application/test_dispatcher.py
```

```text
src/factory/application/dispatcher.py      76      0     14      0   100%
-----------------------------------------------------------------------------------
TOTAL                                      76      0     14      0   100%
Required test coverage of 90.0% reached. Total coverage: 100.00%
21 passed in 0.76s
```

Green.

## 3 Mutation score

There is no `make mutants` target. That is the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`), so there is no score from that target.

Instead I repeated the first acceptance's hand pass on a fresh copy of today's `src/` and `tests/`:

- the copy is `/tmp/f6mut3`;
- the script is `/tmp/f6demo/mutate3.py`;
- each mutant runs the test modules of its story.

The pass has three more mutants than the first one, all on the report's failure handling in `src/factory/application/dispatcher.py`, the module S0009 covered. **28 of 28 killed.**

| # | Module | Mutant | Result |
|---|---|---|---|
| 0–6 | `evaluation.py` | the seven mutants of the first pass (merge test, the merge skip, the tier order, the attempts cap, `handed_over`, `remote_state`, the held claim) | killed |
| 7–8 | `tick_status.py` | the cap `>=` → `>`; another remote state keeps the old entries | killed |
| 9–11 | `dispatcher.py` | every hosting failure becomes a log line; a success does not clear; a reported entry is reported again | killed |
| 12 | `dispatcher.py` | a report failing with a non-hosting error is marked reported (**the first pass's survivor**) | **killed** |
| 13–14 | `work_items.py` | a merge commit is judged; the opening commit is judged | killed |
| 15 | `move_rule.py` | approval → done is not legal | killed |
| 16–21 | `tick.py` | the six mutants of the first pass (stops never cleared, branches, clean, status, discard line) | killed |
| 22 | `watcher.py` | comments are listed for every pull request state | killed |
| 23 | `board.py` | `running_since` is not converted to UTC | killed |
| 24 | `wiring.py` | the `PATH` tail is reordered | killed |
| 25 | `dispatcher.py` | a non-hosting report failure becomes a log line (new) | killed |
| 26 | `dispatcher.py` | the log-line exception widened from `HostingServiceError` to every `Exception` (new) | killed |
| 27 | `dispatcher.py` | a hosting failure on a work item with a remote branch is marked reported (new) | killed |

No survivors, so there are no groups. Coverage is 99.35 %, and `dispatcher.py` is now at 100 %. The lines of F0006 that are still not covered are the ones the first acceptance judged harmless:

- `work_items.py:119` and `:149`, which narrow types for mypy;
- `board.py` 72→70;
- `watch.py:65` and `:69`, which are reached once F0010-S0001 wires the boundaries.

## 4 What the stories noticed

The two new stories noticed nothing new:

- S0008's documenter wrote "Stale text unrelated to this story: none seen".
- S0009's coder and documenter wrote "nothing else noticed" and "nothing seen".
- S0008's reviewer remarked that the branch carried the human's `planning/` and `docs/runs/` commits through a merge of `main`. That is the human's business, so nothing to do.

What the first acceptance collected from S0001–S0007, and where it stands now:

- **Repaired by S0008:**
  - the operator guide's attempts-cap lines ("arrives with F0006");
  - its opening paragraph;
  - the missing warning about the declared but unbuilt `factory-run` and `factory-health`.
- **Repaired by S0009:** the uncovered `dispatcher.py:105`.
- **Still standing, still no draft:**
  - `_MAIN_REF` is defined five times (`watcher.py`, `tick.py`, `work_items.py`, `board.py`, and `PIPELINE_REF` in `pipeline_loading.py`).
  - `TickStatus` keeps the entries of other event keys until a success clears them (memory only).
  - The default `err` of `factory-watch`'s `main` has no test.

  None of these is a broken rule. A story that touches these modules (F0010-S0001 wires `watch.py` and the tick) can fold them in.

## 5 The documentation as a whole

I read `README.md` and the opening paragraph of `docs/operator-guide.md`, together with its sections on the stops of a work item, the stall cap, the stops of the tick, "A stage changed by hand" and "An event that keeps failing". I checked them against the code and against the demo:

- **What is built.** `README.md` and the operator guide both name reading the remote, the evaluation, the tick, the dispatcher with the run handler, and `factory-watch`. Both say that no command runs ticks before F0010. Both warn that `factory-run` and `factory-health` end with `ModuleNotFoundError`.
- **The list of unhandled kinds.** The list in "An event that keeps failing" equals `NOT_YET_HANDLED` (I compared both outputs, section 2 step 0). The five common kinds and their causes match what the demo shows: `hand_over` at step 3, `merged` at step 6, `crash` at step 7, `ask` at step 8.
- **The unreadable work item file.** The ways out are now to repair the file or to move the story out of `in-progress/`. Closing the pull request is no longer given as a way out.
- **`reject`.** It is described as a counted error, reported once and then capped, which matches step 9 and decision 14.
- **A branch created by hand.** The guide says its starting stage is never judged, which matches step 8.
- **A report that cannot be posted.** The guide now names a git failure in the checkout next to a hosting-service outage. This matches S0009's tests and mutants 25 and 26.
- **Old phrases.** No line in `README.md` or `docs/` still says "arrives with F0006", "nothing built calls yet", "the event is only recorded" or "closes the pull request" (the grep finds none).
- **`docs/decisions.md` and `docs/project-guide.md`.** Their F0006 entries have no future-tense claim about F0006.

Findings: none. No contradictions between stories, and no example that no longer runs.

## 6 Decisions taken for the human

Decisions 1–16 of `FEATURE.md` were built as written. The first acceptance's section 6 lists the answers given during S0002, S0004, S0005 and S0007. The answers to S0008 and S0009 needed nothing new: both stories ran first-pass, without a question. The alternatives still named in `FEATURE.md` are unchanged and are the human's to take or leave:

- decision 2: a repository stop `work_item_unreadable` instead of an error on every tick;
- decision 8: a report key per event;
- decision 14: skip a capped work item in tier 4.

What happened to the three items the first acceptance raised:

- **A. A work item branch created by hand is never judged by the move rule.** This is still open. The night log of 2026-10-14 lists it "for the human" without an answer.
  - The operator guide now documents today's behaviour, option (a).
  - F0007's draft S0006 (`factory/features/F0007-human-on-the-pull-request/drafts/F0007-S0006-illegal-stage-change-moved-back.md`) still exempts the opening commit. Its tests push a legal commit first so that the illegal one is not the opening commit.
  - My recommendation is unchanged: option (b), judge the opening commit as a change from the first stage, as a story of F0007, next to the `reject` handler.
  - Because F0007's drafts are the human's, I wrote no draft here. If the human chooses (b), the change belongs in F0007-S0006, or in a story next to it, before F0007 starts.
- **B. Order of F0007, F0008 and F0010.** This looks settled. The night log says "F0007 and F0008 before F0010's scheduler, as planned", and that F0010 starts after F0009 is accepted. I list it only for the human to confirm.
- **C. Still open from the F0005 acceptance:** the two pull-request rules, the attempts counted over a work item's whole life, and the `_state_of` copies. F0006 did not touch them.

## 7 The slow checks

None. Beyond `make check` the project has no slow check: no `make mutants` (section 3 has the hand pass instead), no image scan and no SBOM.

## 8 Cost

The nine stories cost 69 runs, 101.0 min and $20.30. The first acceptance accounted for S0001–S0007 (57 runs, 88.9 min, $18.76). Its own run cost $4.63 and is not in the sum. The two stories it proposed:

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0008 | 6 | 5.3 | $0.77 | first pass; documentation only, with the tester and coder stages empty on purpose |
| S0009 | 6 | 6.8 | $0.77 | first pass; three tests, no code change, as the story expected |

Neither stands out. Each passed every stage at the first try, and together they cost $1.54. That is a third of what the acceptance that found them cost.

Within the feature, S0002 still stands out (15 runs, $4.57): two review rounds, each over a one-line test assertion that costs four runs under R9. S0004 is next (10 runs), with two impossible tests sent back through the human. The first acceptance's section 8 gives the detail.

S0008 shows one cost pattern of its own: for a documentation-only story, the tester, coder and reviewer each spend a run to say there is nothing to do. That is about $0.40 of its $0.77. It is a property of the pipeline, not of this feature, so it is the human's to weigh.

## Proposed stories

None. The two findings of the first acceptance are repaired (S0008, S0009). The items still standing in section 4 are too small for a story of their own. Item A of section 6 is a product question whose change would belong to F0007's drafts, which are the human's.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 28 of 28)
      This is the second acceptance of F0006. The first (#78) proposed S0008 (documentation) and S0009 (a report that fails with a git error). Both are now merged and repair what that acceptance found.
      1 Scope: none. Every scope item has its story (S0001–S0007). S0008 changed only docs and S0009 only tests, both inside the scope. Nothing out of scope was built.
      2 Feature demo: green, exit 0. I re-ran the first acceptance's script (/tmp/f6demo/demo.py, pasted in `3d278f7`) with the production handler_factory on a real remote. Its output matches the first run except for commit ids. S0009's rule cannot be reached inside a tick, so I re-ran its own demo: dispatcher.py 100 %, 21 passed.
      3 Mutation score: no make mutants target. The hand pass on a fresh copy of src and tests killed 28 of 28, including the first pass's survivor and three new mutants on the report's failure handling. Coverage is 99.35 %.
      4 Noticed: S0008 and S0009 noticed nothing new. Earlier items are repaired (stale docs, dispatcher.py:105). Three small ones remain without a draft: _MAIN_REF defined five times, TickStatus keeping other keys, and the untested default err of factory-watch's main.
      5 Documentation: no findings. README and the operator guide match the code and the demo, including the NOT_YET_HANDLED list, reject as a counted error, the ways out of an unreadable file, the branch created by hand and the git failure of a report. None of the old phrases remain.
      6 Decisions: 1–16 were built as written; the alternatives in decisions 2, 8 and 14 are still the human's. Item A is still open: a branch created by hand is never judged. F0007-S0006's draft still exempts the opening commit, and I still recommend judging that commit in F0007. Item B looks settled per the night log; the human only confirms. Item C (the F0005 leftovers) is untouched.
      7 Slow checks: none (no mutants target, no image scan, no SBOM).
      8 Cost: 69 runs, 101.0 min, $20.30. S0008 and S0009 each ran first-pass (6 runs, $0.77 each). S0002 still stands out at 15 runs. Documentation-only stories spend about half their cost in stages with nothing to do.
