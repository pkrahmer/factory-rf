---
stage: accept
pr: 118
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0009-S0001, F0009-S0002, F0009-S0003, F0009-S0004, F0009-S0005, F0009-S0006, F0009-S0007, F0009-S0008, F0009-S0009, F0009-S0010, F0009-S0011, F0009-S0012, F0009-S0013, F0009-S0014]
---
# Acceptance of Feature acceptance

This is the second acceptance of F0009. The first (pull request 114, merged) covered S0001 to S0011 and proposed S0012 to S0014, which have since been built and archived. This report covers all fourteen stories. It re-runs the first report's checks against today's `main`, and it reads the three new stories in full.

## Verdict

**accepted with drafts.** The feature does what `FEATURE.md` promises, and the three findings of the first acceptance are repaired:

- The board now shows a running acceptance as a work item row.
- The project guide and the README say that the acceptance is wired.
- The three mutation survivors are killed.

The end-to-end feature demo (section 2) is green through the production `handler_factory`. `make check` is green, and a hand mutation pass killed 11 of 12 mutants. The one survivor is a near-equivalent tie-break.

One finding remains, of low weight. The operator guide's **Merge** bullet does not say that a merge that brought proposed stories leaves the feature `incomplete`. Its **Accepted again** paragraph says the feature is then `accepted`, without that condition. The status table says it correctly, so this is an imprecision, not a broken promise. One draft repairs it.

## 1 Scope

None. The first acceptance's table of scope items, stories and code still holds, and the three later stories add to it:

| Story | What it added | Code |
|---|---|---|
| S0012 | A work item row for each running acceptance, in `work_item_order` after its feature's stories (decision 23) | `running_work_items` in `src/factory/application/acceptance_reading.py:249`, now shared by `BoardReader.read` (`src/factory/application/board.py:44`) and `Watcher.evaluate` (`src/factory/application/watcher.py:38`) |
| S0013 | Documentation only: the project guide's three stale "not wired" sentences, and the README's sentence on the feature acceptance | `docs/project-guide.md:457`, `:459`, `:505`; `README.md:3` |
| S0014 | Tests only: `open` refusing every non-due status, story files counted only directly in their folder, and the exact 9999 error | `tests/application/test_acceptance_refusals.py`, `tests/domain/test_acceptance_facts_limit.py`; no `src/` change |

Each condition of the Goal's "Done when" is shown again in section 2:

- **Due with a `.gitkeep`:** step 1.
- **The order for a slug that starts with a digit:** step 0 and feature `F0002-2fa-login`. The missing slug is S0001 criteria 8 and 9.
- **Merge accepted:** step 1.
- **Close refused with the reason:** step 2.
- **Repeat:** step 3.
- **`NOT_YET_HANDLED` empty:** step 0.
- **Merge before the approval:** S0011 criterion 1.

No story went outside the scope. S0012 changed `watcher.py` only to share the join and sort it already had (reviewer, S0012 entry 5), with no change of behaviour. Out of scope stayed out: there is no validation of the report's sections, no stopping rule, no reviewer instructions (F0010), and the backlog is still writable by the reviewer.

## 2 Feature demo

The walk is the first acceptance's script, unchanged except for four more `watch()` calls. They show the board at the approval, while merged and unrecorded, after the booking, and after the close. That way the demo also covers the gap S0012 closed.

The walk runs against:

- the production `handler_factory` (`factory.entry.wiring`), one `Tick` per step, and `run_watch` (the code of `factory-watch`);
- a real bare remote, a `GitCli` checkout and a human clone;
- `FakeHostingService` and `FakeAgentRuntime`. The scripted acceptance reviewer edits the report below its head and writes one proposed story into the backlog.

The script is the `<details>` block of the first report (commit `5e5b989`, `factory/features/F0009-feature-acceptance/ACCEPTANCE.md`). The guard refuses files outside the repository, so it was taken from git and piped to standard input. No file was left behind:

```bash
git show 5e5b989:factory/features/F0009-feature-acceptance/ACCEPTANCE.md \
  | awk '/^```python$/{f=1;next} f&&/^```$/{f=0} f' \
  | sed -e '/^print("   state on branch:"/a watch()' -e '/^print("   -- the human squash-merges --")/a watch()' \
        -e '/^print("   branch gone:"/a watch()' -e '/^print(f"   -- the human comments on #/a watch()' \
  | PYTHONDONTWRITEBYTECODE=1 uv run python -
```

```text
== 0. wiring and order ==
NOT_YET_HANDLED: ()
order: ['F0001-A0001', 'F0002-S0001', 'F0002-S0002', 'F0002-A0001', 'F0003-S0001']
== 1. feature F0002-2fa-login (slug starts with a digit): two archived stories and a .gitkeep ==
   status={'F0002': 'due'} due=['F0002']
   watch| event: acceptance_due:F0002  acceptance of F0002 is due
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=0  in-progress=0  done=2  acceptance=due
   watch| work items
tick 1 (opens the acceptance): event=acceptance_due:F0002 dispatch=handled agent runs so far=0
   branch: True | pull requests: 0
   report head: --- | stage: acceptance | blocked: null | round: 0 | attempts: 0 | crashes: 0 | pull_request: null | comments_read: [] | handed_over: null | claim: null | journal: [] | stories: [F0002-S0001, F0002-S0002] | outcome: null | --- |  | # Acceptance of Two-factor login |  | ## Journal | 
   status={'F0002': 'in_flight'} due=[]
tick 2 (the acceptance reviewer runs): event=run:F0002-A0001 dispatch=handled agent runs so far=1
   prompt's last three lines: ['Archived stories: F0002-S0001, F0002-S0002', 'Next free story number: F0002-S0003', 'Cost of the stories: 2 runs, 3.0 min, 3 turns, 30 tokens in (0 more from cache), 200 out, $1.50']
   pull request #1 draft=True title='F0002-A0001: Acceptance of Two-factor login'
   state on branch: ['stage: approval', 'blocked: null', 'pull_request: 1', 'handed_over: null', 'stories: [F0002-S0001, F0002-S0002]', 'outcome: null']
   watch| event: hand_over:F0002-A0001
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=0  in-progress=0  done=2  acceptance=in_flight
   watch| work items
   watch| F0002-A0001  Acceptance of Two-factor login  in-progress  stage=approval  blocked=-  claim=-  running_since=-  pull_request=1
tick 3 (hand-over at the approval): event=hand_over:F0002-A0001 dispatch=handled agent runs so far=1
   pull request #1 draft=False; description:
      | ## Recommendation
      | 
      | **accepted with drafts.** The stories together do what the feature promised.
      | 
      | ## Findings in short
      | 
      | accepted with drafts; 1 drafts proposed
      | 
      | ## Proposed stories
      | 
      | - `F0002-S0003-lockout.md`: a gap the parts left.
      | 
      | Merge to accept the report and take the proposed stories into the feature's backlog, where you refine them before starting any. Close, with a comment saying why, to refuse: the report stays on the main branch as refused with your comment, the proposed stories are discarded, and the feature counts as not accepted until another story is archived and a new acceptance runs. Nobody answers comments while the acceptance waits here; they go into the report's journal.
   factory posts: ['Cost of this work item so far']
tick 4 (the human has not decided yet): event=idle:- dispatch=handled agent runs so far=1
tick 5 (still waiting: the hand-over is not repeated): event=idle:- dispatch=handled agent runs so far=1
   factory posts now: 1
   -- the human squash-merges --
   watch| event: merged:F0002-A0001
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=1  in-progress=0  done=2  acceptance=merged_unrecorded
   watch| work items
   watch| F0002-A0001  Acceptance of Two-factor login  in-progress  stage=approval  blocked=-  claim=-  running_since=-  pull_request=1
   status={'F0002': 'merged_unrecorded'} due=[]
tick 6 (the merge is booked): event=merged:F0002-A0001 dispatch=handled agent runs so far=1
   booked state: ['stage: done', 'stories: [F0002-S0001, F0002-S0002]', 'outcome: accepted']
   last journal line: 3. factory: done (pull request merged); cost: 1 runs, 3.0 min, 12 turns, 0 tokens in (0 more from cache), 0 out, $0.42
   on main: ['factory/features/F0002-2fa-login/backlog/.gitkeep', 'factory/features/F0002-2fa-login/backlog/F0002-S0003-lockout.md', 'factory/features/F0002-2fa-login/done/F0002-A0001-acceptance.costs.jsonl', 'factory/features/F0002-2fa-login/done/F0002-A0001-acceptance.md', 'factory/features/F0002-2fa-login/done/F0002-S0001-totp.costs.jsonl', 'factory/features/F0002-2fa-login/done/F0002-S0001-totp.md', 'factory/features/F0002-2fa-login/done/F0002-S0002-recovery-codes.md', 'factory/features/F0002-2fa-login/feature.md']
   branch gone: True
   watch| event: idle:-
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=1  in-progress=0  done=2  acceptance=incomplete
   watch| work items
   status={'F0002': 'incomplete'} due=[]
tick 7 (the proposed story waits for the human): event=idle:- dispatch=handled agent runs so far=1
== 2. feature F0003-search: reviewed, handed over, closed with a reason ==
tick 8 (opens the acceptance): event=acceptance_due:F0003 dispatch=handled agent runs so far=1
tick 9 (the acceptance reviewer runs): event=run:F0003-A0001 dispatch=handled agent runs so far=2
tick 10 (hand-over): event=hand_over:F0003-A0001 dispatch=handled agent runs so far=2
   -- the human comments on #2 and closes it --
   watch| event: closed:F0003-A0001
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=1  in-progress=0  done=2  acceptance=incomplete
   watch| F0003  Search  backlog=0  in-progress=0  done=1  acceptance=in_flight
   watch| work items
   watch| F0003-A0001  Acceptance of Search  in-progress  stage=approval  blocked=-  claim=-  running_since=-  pull_request=2
tick 11 (the close is booked): event=closed:F0003-A0001 dispatch=handled agent runs so far=2
   booked state: ['stage: done', 'outcome: refused']
   recommendation section: Refused by the human on 2026-10-16: The ranking belongs to another feature. / **not accepted.** Ranking is missing.
   on main: ['factory/features/F0003-search/done/F0003-A0001-acceptance.costs.jsonl', 'factory/features/F0003-search/done/F0003-A0001-acceptance.md', 'factory/features/F0003-search/done/F0003-S0001-index.md', 'factory/features/F0003-search/feature.md']
   status={'F0002': 'incomplete', 'F0003': 'refused'} due=[]
tick 12 (refused rests): event=idle:- dispatch=handled agent runs so far=2
== 3. another story archived in F0003: due again, a new acceptance A0002 ==
   status={'F0002': 'incomplete', 'F0003': 'due'} due=['F0003']
tick 13 (opens the repeated acceptance): event=acceptance_due:F0003 dispatch=handled agent runs so far=2
   branch work-item/F0003-A0002: True | A0001 report unchanged: True
   A0002: ['stage: acceptance', 'stories: [F0003-S0001, F0003-S0003]']
   watch| event: run:F0003-A0002
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=1  in-progress=0  done=2  acceptance=incomplete
   watch| F0003  Search  backlog=0  in-progress=0  done=2  acceptance=in_flight
   watch| work items
   watch| F0003-A0002  Acceptance of Search  in-progress  stage=acceptance  blocked=-  claim=-  running_since=-  pull_request=-
exit 0
```

**What it shows.** Every line of the first walk comes out as it did then:

- the opening, with the head only and no pull request;
- the three facts at the end of the prompt;
- the four-part description, and the cost table posted once;
- the squash merge: first `merged_unrecorded`, then booked `accepted` with its own cost, the proposed story kept and the branch gone;
- the close, booked `refused` with the human's reason first;
- the repeat as `A0002`, with A0001 unchanged byte for byte;
- no `reject`, and `idle` while the acceptance waits.

**New since the first acceptance.** The board now lists the running acceptance under `work items` at every point of its life:

- at the approval: `stage=approval  pull_request=1`;
- merged and not yet booked: the row is still there, beside `acceptance=merged_unrecorded`;
- at the close: `pull_request=2`;
- as `A0002`, just opened: `stage=acceptance  pull_request=-`.

The row is gone once the acceptance is booked. That is the gap the first demo found, and it is closed.

**Observation (the finding of section 5).** After tick 6 the feature row reads `acceptance=incomplete`, because the merge brought `F0002-S0003-lockout.md` into the backlog. The code does what decision 4 says. The operator guide's **Accepted again** paragraph says that the feature is then `accepted`, without the condition. Draft S0015.

## 3 Mutation score

The project has no `make mutants` target, by the decision "No `mutants` target, no mutmut" in `docs/decisions.md`. I ran a hand pass like the first acceptance's:

- **How each mutant was applied:** in memory. A meta-path finder compiled the mutated source in place of the module, with `PYTHONDONTWRITEBYTECODE=1`, so no file in the checkout changed. `git status` afterwards showed only this report and the draft.
- **Tests run:** the feature's 35 test modules: every `tests/*/test_*acceptance*.py`, `test_board*.py`, `test_watch*.py`, `test_evaluation_due.py` and `test_split_by_work_item_kind.py`. Each mutant ran with `pytest -x`.
- **Which mutants:** the three survivors of the first pass, to see whether S0014 killed them, and nine mutants on what S0012 added.

**Score: 11 of 12 killed.** Over both passes, 41 of 42.

| Mutant | Result | Killed by |
|---|---|---|
| `open`: `status != "due"` → `status == "incomplete"` (first pass's survivor 16) | killed | `test_acceptance_refusals.py::test_only_a_due_feature_is_opened[in_flight]` |
| `_names`: `if len(path.parts) == 1` dropped (survivor 26) | killed | `test_a_story_file_counts_only_directly_in_its_folder` (`'due' == 'incomplete'`) |
| `acceptance_facts`: `> _LAST_NUMBER` → `> _LAST_NUMBER + 1` (survivor 8) | killed | `test_the_next_story_number_ends_at_9999` (`ValidationError is ValueError`) |
| `running_work_items` drops the acceptances | killed | the close walk (`'idle' == 'closed'`) |
| `running_work_items` drops the stories | killed | board and watcher tests |
| `running_work_items` unsorted | killed | `test_rows_come_in_work_item_order` |
| sorted by path only | killed | `test_rows_come_in_work_item_order` (`F0002-A0001` before `F0002-S0003`) |
| sorted by the plain id string | killed | the same |
| `reverse=True` | killed | board tests |
| board rows from the stories only | killed | `test_board_reader_acceptance.py` |
| board rows without the last | killed | board tests |
| `running_work_items` without the `snapshot.path` tie-break | **survived** | — |

The survivor is near-equivalent. Two snapshots with one id do not occur:

- `RemoteWorkItems.read` reads one `in-progress/` per feature id;
- `snapshots()` gives one per acceptance;
- `sorted` is stable over git's ordered listing.

The tie-break came from the S0012 reviewer's request to share the watcher's key, not from an Interface. It is not worth a story.

Coverage is 99.53 %. The feature's two missed lines are the same as before:

- `src/factory/application/acceptance_reading.py:238`, a report that is listed but missing at its ref;
- `src/factory/domain/acceptance.py:320`, trailing blank lines of a hand-edited report without a journal.

Both are defensive branches.

## 4 What the stories noticed

I collected these from the coder, reviewer and documenter entries of S0012 to S0014, and checked again the first acceptance's items that were still open:

- **S0012.**
  - The reviewer rejected, as a finding, reading the remote twice in `BoardReader.read`: `fill_board` reads the statuses and `running_work_items` reads the snapshots. They are different reads, and the Interface asked for both. It costs a second set of `git show` calls per `factory-watch`. This is a performance remark, with no draft.
  - The coder noticed that the feature rows still print before the work item rows, as asked.
- **S0013.** The documenter noted two things, both correct as they stand:
  - `docs/decisions.md` cites F0009 story ids, in dated decision entries;
  - the README and the operator guide still say that `factory-run` is unbuilt until F0010.
- **S0014.** Nothing noticed. The coder changed no `src/`, as the assignment expected.
- **Still open from the first acceptance, checked against today's code:**
  - **No-state refusals.** Those of the three acceptance handlers are still untested (`src/factory/application/acceptance.py:205`, `:278`, `:339`). The open draft `factory/features/F0008-crash-recovery/drafts/F0008-S0007-the-no-state-refusals-of-require-states-callers.md` covers the same class. The human can widen that draft to these three calls, so I wrote no new one.
  - **"Today in UTC" written twice.** It is in `src/factory/application/handlers/closed.py:93` and in `AcceptanceClosed._today` (`src/factory/application/acceptance.py:327`). The duplicate is one line, too small for a story.
  - **The story `MergedHandler` has no "already in `done/`" guard.** It is harmless today (the stale-branch deletion covers a kill) and is a case for F0011's kill points.
  - **Corrected from the first report.** It said that `entry/check_story.py` builds the feature file's path by hand. It does so from the constants `FEATURES_DIRECTORY` and `FEATURE_FILE_NAME` (`src/factory/entry/check_story.py:78`) over a local `Path`, not a remote one, so `feature_file_path` does not fit. Not a finding.
  - **A reviewer that drops the report's front matter loses its report silently** (F0005's restore rule). Still for F0010's reviewer instructions.

## 5 The documentation as a whole

I read `README.md`; the operator guide's "Looking at the remote: `factory-watch`", "When a feature acceptance is due" and "The hand-over of an acceptance" in full; the project guide's "The feature acceptance", "Events", "The watcher's command line" and the wiring of the handlers; and the F0009 entries of `docs/decisions.md`.

The first acceptance's findings are repaired:

- The stale-wording grep of S0013 finds nothing.
- `docs/project-guide.md:505` says every kind is registered, `acceptance_due` included. That agrees with `:579` and with the code.
- `:457` and `:459` say that the handlers are registered.
- `README.md:3` names the feature acceptance and points to the operator guide.
- The operator guide says "directly in" (`docs/operator-guide.md:432`).
- The `factory-watch` section describes the acceptance rows exactly as the demo printed them: the title `Acceptance of <feature title>`, the folder `in-progress`, the state from the branch, and the place after the feature's stories.
- The project guide's board paragraph (`:558`) names `running_work_items` and says the watcher shares it.

**The finding.** "The hand-over of an acceptance" describes the status after a merge in two places:

- **Merge** says that the proposed stories stay in the backlog, but not what that does to the status.
- **Accepted again** says: "Once the new acceptance's merge is recorded, the feature is `accepted` and not due".

With proposed stories, which the reviewer is told to write, the feature is `incomplete` instead. The demo's tick 6 shows this. The status table (`docs/operator-guide.md:442`, "A recorded result does not stand while a story file waits") and the paragraph **Merged before its approval** (`:486`) say it correctly, so the guide contradicts itself and the code is right. An operator who expects `accepted` after the merge will see `incomplete` on the board. The rule is stated correctly a few paragraphs away, so I judge this an imprecision, not a contradiction that misleads into a wrong act. Draft S0015.

Nothing else contradicts. I found no example that no longer runs: the board example and the event line match the demo.

## 6 Decisions taken for the human

`FEATURE.md` now lists 23 decisions. Decisions 1 to 22 are summarized in the first acceptance's section 6 (commit `5e5b989`) and are unchanged. The ones to look at again:

- **12.** A merge books `accepted` whatever the recommendation says.
- **4.** A waiting story comes before a recorded result. Together with the reviewer's proposed stories, every accepted round of drafts leads to one more acceptance: this feature is on its second, and S0015 would make a third. There is no stopping rule (out of scope, v2).
- **17.** Acceptances go through the stage protocol with two additions. The alternative was a separate runner.
- **22.** The test-change leave of the second and third groups (`tests/test_no_journal_reading.py`, `tests/application/test_board_reader.py`) is still marked "for the human to confirm in the morning" in `FEATURE.md`. The first acceptance's merge did not say whether it confirmed them.

New since the first acceptance:

- **23** (S0012). Every acceptance from `AcceptanceReader.snapshots()` gets a work item row through `work_item_row`, sorted with the stories by `work_item_order`. The feature rows and the event line are unchanged.
- **A default no decision names** (S0012 reviewer, round 1). The board and the watcher now share `running_work_items`, which breaks ties by `snapshot.path`, so the board took over the watcher's tie-break. It has no visible effect (section 3).
- **S0013's story text.** For a docs-only story the tester writes no tests, and the coder makes no commit. The stages still ran (section 8).

The defaults the first report listed still stand:

- the facts' cost line silently skips a story without a cost sidecar;
- a report with unreadable front matter is restored whole, with no word in the journal.

The story logs of S0012 to S0014 hold no answers from the human.

## 7 The slow checks

None. The project offers nothing beyond `make check`: no image scan, no SBOM, and no `make mutants` (by decision). `make check` was green as I found it, with lint, types, layers, sast, secrets, licenses, and tests at 99.53 % coverage, in 3 min 03 s.

## 8 Cost

The fourteen stories cost 113 runs, 309.9 min and $33.45, about 8.1 runs and $2.39 per story. The first eleven cost 93 runs, 259.2 min and $29.71 (see the first report for the outliers there: S0008 at $4.12, S0011 with 14 runs). The three stories since cost 20 runs, 50.7 min and $3.74:

| Story | Runs | Min | $ | Note |
|---|---|---|---|---|
| S0012 | 8 | 24.5 | 2.11 | One review round: the coder had copied the watcher's join and sort, and the reviewer had it shared (`running_work_items`). This is the only one of the three that changed `src/`. |
| S0013 | 6 | 9.4 | 0.54 | Documentation only. Intake, tester, coder and reviewer each ran and recorded "nothing to do" before the documenter wrote four sentences. |
| S0014 | 6 | 16.8 | 1.09 | Tests only, green from the start; no `src/` change. |

None of them stands out against the feature's average.

A pattern for the human, about the pipeline's own files, which are theirs: a docs-only story still pays for four stages that have nothing to do. S0013 paid about half its runs for them. A stage path for docs-only stories, or the human's edit by hand (which S0013 itself offered), would save that.

## Proposed stories

- `drafts/F0009-S0015-what-the-board-shows-after-an-accepted-merge.md`: the operator guide's **Merge** bullet and **Accepted again** paragraph should say that a merge that brought proposed stories leaves the feature `incomplete`, as the status table, the code and the demo do. It is documentation only and small enough for a hand edit.

## Log (append only)

1. acceptor: accepted with drafts; 1 drafts proposed; make mutants 11/12. This was a hand pass: by decision the project has no `make mutants` target, so 12 mutants were applied in memory against the feature's 35 test modules. Over both acceptances the total is 41/42.
      1 Scope: none. Every scope item has its story and its code. S0012 to S0014 closed the first acceptance's three findings: the board row, the stale docs, and the three survivors. No story went outside the scope, and the out-of-scope items stayed out.
      2 Feature demo: green. It is the first acceptance's script with four more `watch()` calls, run through the production `handler_factory` with 13 real ticks and a real remote. Due with a `.gitkeep`, opened, reviewed, handed over, squash-merged and booked accepted. Closed and booked refused with the reason first. Repeated as A0002. No `reject` anywhere. The board now shows the acceptance's row at the approval, while merged and unrecorded, at the close, and when A0002 opens.
      3 Mutation: 11/12 killed. The first pass's three survivors are all killed now, by S0014's tests. The new mutants on S0012's code (`running_work_items`, the board rows) are killed except the `snapshot.path` tie-break. That one is near-equivalent, because two snapshots with one id do not occur, so it gets no draft. Coverage is 99.53 %, and the two missed lines are defensive branches.
      4 Noticed: S0012 reads the remote twice per board (a performance remark only). The acceptance handlers' three no-state refusals are still untested; the human can widen the open draft F0008-S0007 to cover them. "Today in UTC" is still written twice. The story `MergedHandler`'s missing done/ guard is a case for F0011. The front-matter loss is a matter for F0010's instructions. I corrected one earlier remark: check_story's path built by hand is not a finding.
      5 Docs: the first acceptance's findings are repaired. Still open: in the operator guide's "The hand-over of an acceptance", the **Merge** bullet and the **Accepted again** paragraph say the feature is `accepted` after a recorded merge. When the merge brought proposed stories it is `incomplete` instead, as the status table (`:442`), the before-approval paragraph (`:486`), the code and the demo all show. This is an imprecision, not a broken promise. Draft S0015.
      6 Decisions: there are 23. Flagged for the human: merge accepts whatever the recommendation says (12); every accepted round of drafts leads to another acceptance, with no stopping rule (4; this feature is on its second); the separate-runner alternative (17); and decision 22's test-change leave, still marked "for the human to confirm". New: decision 23 (the board rows) and the path tie-break default that the board took over from the watcher.
      7 Slow checks: none beyond `make check`, which was green as I found it (3 min 03 s, 99.53 %).
      8 Cost: 113 runs, 309.9 min, $33.45 in all (about $2.39 per story). The three new stories cost 20 runs, 50.7 min, $3.74. S0012 is the most expensive of the three ($2.11, one review round on a duplicated join). S0013 was docs-only and still paid for four stages that had nothing to do, which is a matter for the pipeline's own files.
      Open: none for this stage. Draft S0015 is the human's to refine, promote or do by hand.
