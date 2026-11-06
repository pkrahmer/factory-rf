---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 584
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T01:53:09.075567Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T01:59:45.516747Z'
  stage: acceptance
  run: 52fa49bb06084aafa394df2991456482
stories: [F0052-S0001, F0052-S0002, F0052-S0003, F0052-S0004, F0052-S0005, F0052-S0006, F0052-S0007, F0052-S0008, F0052-S0009]
outcome: null
---

# Acceptance of A documents-only story takes the docs route

## Recommendation

**Accepted.** The feature does what `feature.md` promised. The third acceptance's one finding of weight is closed. The human changed `check`'s `not_read` (commit `130ba04c1`), and the feature smoke test now shows the check's key changing after a documents-only change that breaks the guide guard (part [4]). S0008 and S0009 then went down the docs route without a stall, and `make check` really ran after each `docs-only` run.

One small contradiction is left. The decision log's entry on the docs route still says that `make check` reuses its result when only documents changed, and the decision log is outside the next feature's rewrite. I propose one documents-only story for it (S0010). It breaks no promise of the feature.

## 1 Scope

Each scope item has its story:

- The second route and its approval: S0001.
- The intake's choice and the agents' texts: S0002.
- The style page and the glossary: S0003.

S0004 to S0009 came from the three earlier acceptances, and the human started each one. This round's two stories came from the third acceptance:

- S0008 (`docs/operator-guide/pipeline.md`, the paragraph "kumpel-factory's own definition" and *The docs route*; `docs/decisions.md:872`) makes the guide quote the shipped `check:` line. It also says why the documents stay in the key. It ran after the human's change under *The human's changes*, "Before S0008's start".
- S0009 (`docs/project-guide/README.md`, *The files*) says which list items the guard reads as a page entry.

Both are documents-only, and both took the docs route: intake → `docs-only` → `docs-review` → … → `docs-approval` → merged.

Nothing out of scope was touched. The template `operator/template/factory/pipeline.yml` is unchanged since F0051. No style tool was added, and the code route is unchanged (smoke test [2]). The goal is reached in mechanism and in practice: three stories (S0007, S0008, S0009) have now been merged on the docs route. Nothing in scope is left without a story.

## 2 Feature smoke test

This is what a user of the feature does, on the shipped `factory/pipeline.yml`, through the factory's tick, the fake hosting service and real git. It has four parts:

- [1] A documents-only story is sent back once at the review, closed once at `docs-approval`, then merged and archived.
- [2] The way back to the code route: a close at `approval` sends the story to `doing`.
- [3] The shipped texts of this round: the operator guide's quote of `check`, and the index rule of *The files* against the guard's `INDEX_LINE`.
- [4] The check's key before and after a documents-only change that breaks the guide guard, on a clone of this checkout. The key is checked again after a change under `docs/runs/`.

I wrote the module into a `mktemp -d` folder and ran it with the repository's fixtures:

```bash
cd /work/checkout && PYTHONPATH=tests uv run pytest -p conftest -s -q -p no:cacheprovider -p no:randomly -o addopts="" /tmp/tmp.dfhelmlkpe/test_feature_smoke.py 2>&1 | grep -v "stage environment\|disk acceptance" | tail -60
```

In outline:

- [1] and [2] push the shipped definition and a no-op Makefile to `main` and start a story. Each agent run is a scripted fake run with a decision, and the documenter's runs write `docs/example.md`. A close is a human comment plus `close_by_human`; a merge is `human.merge`, then `merge_by_human` and three ticks.
- [3] reads `docs/operator-guide/pipeline.md` and `docs/project-guide/README.md` and matches the list items of *The files* with `INDEX_LINE`.
- [4] clones `/work/checkout` into `tmp_path` and computes `GitCli.work_tree_id` with `check`'s `not_read` from the shipped definition. It renames `## The files`, then computes the id again and runs `index_problems` before and after.

Output (part [3] from its second run; the first run's pattern matched the guide's generic example on line 53 before the project's line 62, and printed `False`):

```
[1] a documents-only story on the shipped factory/pipeline.yml
        intake decides docs-only     -> stage=docs-only round=0 blocked=None
     docs-only decides docs-review   -> stage=docs-review round=0 blocked=None
   docs-review decides docs-only     -> stage=docs-only round=1 blocked=None
     docs-only decides docs-review   -> stage=docs-review round=1 blocked=None
   docs-review decides docs-approval -> stage=docs-approval round=1 blocked=None
  hand-over: handed_over=docs-approval draft=False
  close at docs-approval -> stage=docs-only round=2
     docs-only decides docs-review   -> stage=docs-review round=2 blocked=None
   docs-review decides docs-approval -> stage=docs-approval round=2 blocked=None
2026-10-12T12:00:00Z handler error run:F0001-A0001 1 of 3: AgentRuntimeError: agent runtime failed: no scripted run is queued
  docs/example.md on main: '# Example\n\nRight.\n'
  archived: ['F0001-S0001-first.md']
.
[2] the way back to the code route
        intake decides docs-only     -> stage=docs-only round=0 blocked=None
     docs-only decides tests         -> stage=tests round=0 blocked=None
         tests decides doing         -> stage=doing round=0 blocked=None
         doing decides review        -> stage=review round=0 blocked=None
        review decides docs          -> stage=docs round=0 blocked=None
          docs decides smoke-test    -> stage=smoke-test round=0 blocked=None
    smoke-test decides approval      -> stage=approval round=0 blocked=None
  close at approval -> stage=doing round=1
.
[3] the shipped texts of S0008 and S0009
  guide quotes the shipped check line: True
  '"docs/*.md"' in the guide: 0
  'README.md' in check's not_read: False
  list items 15: page entries 11, others 4
  others start with a word or italics: True
  no other item starts with a backtick: True
  the rule's trap is read as a page: True
.
[4] the check's key after a documents-only change that breaks the guide guard
  guard before: []
  guard after renaming '## The files': 10 problems
  check's key tree before=e89fd68a4e0d after=f34c47b8795b same=False
  a change under docs/runs/ keeps the key: True
.
4 passed in 4.20s
```

**All four parts are green.** The handler error in [1] is expected: it comes from the fake feature's own acceptance, which starts after the archive and has no scripted run queued.

**Part [4] is the third acceptance's finding, now closed.** Before the human's change, the same rename left the key at `2503ea5b3c55`. Now the key changes, so the factory cannot reuse an earlier pass. A change under `docs/runs/` still keeps the key, as the guide says.

The stories' journals show the same thing in practice. S0008's two `docs-only` stages each took about three minutes from start to result (entries 4–5 and 8–9), and the documenter's runs took 40 s and 19 s of that. So `make check` ran for real both times.

`make check`, as I found it: `test: green (140.7 s)`, coverage 99.26 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Still open from the earlier acceptances, all left to F0054's rewrite of the guides and the README:

- `docs/operator-guide/pipeline.md:41`, *The docs route*, still says the route "skips the tests, doing and review stages", although it has `docs-review`. It also still says "once it exists" of the style page, which exists.
- `README.md` line 3 still describes one route.
- The lines in *The files* for `agents.md` and `machine.md` still name the sections *Replaced in v1.2* and *Replaced from v1*.
- The test notes from the first two acceptances (`test_docs_route.py`, the loose substrings in `test_claude_agent_texts_docs_route.py`, the name `test_only_a_stage_before_the_first_approval_is_before_approval`, and the untested edge rows of `index_problems`) are notes, unchanged.

New from S0008:

- The documenter (entries 5 and 9) flagged the "Two warnings" bullet in `pipeline.md` (the docs stage runs `secrets` with nothing left out) as possibly stale. I checked it against `factory/pipeline.yml:15,35,37`, and it is true: `secrets` has no `not_read`, and both `docs` and `docs-only` run it. It is incomplete, since it does not name `docs-only`. Left to F0054.
- The reviewer (entries 7 and 11): the advice "never a whole folder" sits beside the project's own whole-folder patterns (`planning/*`, `session-logs/*`, `docs/runs/*`). The rewritten paragraph now gives the reason ("folders that hold no code and that no test reads"), so the two no longer contradict each other. Left to F0054.
- The documenter (entry 5) went beyond the Interface and changed the generic example away from `"docs/*.md"`. The reviewer accepted that and had the example corrected to file-type patterns. Resolved.

New from S0009:

- Nothing was noticed outside the story. The reviewer's rejected notes (entries 7, 11 and 15) were about sentence length inside the story's own paragraph.
- The rule now in *The files* matches `INDEX_LINE` (smoke test [3]). A list item that starts with a name in backticks is a page entry, and all four other items start with a word or with italics.

The third acceptance's other item is closed: on `docs-only` the documenter's `make documents` does not run the guide guards. Since the human's change, the factory's own `make check` after the stage runs them (smoke test [4]).

## 5 The documentation as a whole

`make documents`: `documents ok`. Read as a newcomer:

- **`docs/decisions.md` contradicts itself on the reuse of the check.**
  - Line 1588, in *A documents-only story takes the docs route*: "`make check` reuses its result when only documents changed."
  - Line 872, under the known results, added by S0008: `not_read` keeps the documents in the key, "A documents-only change that turns `make check` red then runs it again."

  The second is what the factory does (smoke test [4]). F0053 and F0054 both leave `docs/decisions.md` out, so no coming story fixes it. Proposed: S0010. `feature.md` decision 3 says the same old thing, but that file is the human's (check 6, item 1).
- **The new texts of this round are correct.**
  - `docs/operator-guide/pipeline.md:58-63`: the paragraph is true, and the block equals `factory/pipeline.yml:10` character for character (smoke test [3]).
  - *The docs route*'s new sentence agrees with `docs-only`'s `checks`.
  - `docs/project-guide/README.md`, *The files*: the index rule is true of the guard.
- **Still stale, left to F0054:** `docs/operator-guide/pipeline.md:41` and `README.md` line 3 (check 4).

The texts of different stories do not contradict each other, apart from the decision log above. No example has stopped running.

## 6 Decisions taken for the human

The earlier lists still stand, to accept or revisit:

- `feature.md` decisions 1 to 8.
- The first acceptance's items 3 to 6.
- The second acceptance's items 1 to 8.
- The third acceptance's items 2 to 4.

New, or changed by this round:

1. **Feature decision 3 is no longer true as written.** It says that "`make check` reuses its result when only documents changed". Since the human's change of `not_read` (option (a) of the third acceptance's item 1), a documents-only change runs `make check` again. Each `docs-only` run now pays about 2.5 minutes of machine time and no tokens. `feature.md` is the human's to bring in line. S0010 brings the decision log in line.
2. **S0008's documenter changed the generic `not_read` example beyond the Interface** (entry 5), because the smoke test's grep for `"docs/*.md"` would otherwise have failed. The reviewer accepted the change and had it corrected to `["notes/*.md", "notes/*.jsonl"]`.
3. **S0008's decision-log line has no "Why" line of its own** (entry 5): the story gave none beyond criterion 6. The reason sits in the Decision line itself, and the `Rejected:` line names moving the guards into `make documents`.
4. **S0009's form** (entries 9 and 13): other list items in *The files* start "with a word, plain or in italics". The reviewer widened the rule to italics because three of the four exception items start with `*`.
5. **S0009 used the whole round cap of `docs-review`** (round 2). Each round found a new sentence-length problem, and round 1's problem was in the text that round 0's proposed fix had produced. One more send-back would have asked the human. Accept, or ask that the reviewer check the whole changed paragraph against every style rule in one round, which would be a change to `agents/agents/reviewer.md` on the code route.

No test changed in this round: S0008 and S0009 are documents-only, and `.reports/junit.xml` holds 10,451 tests, as at the third acceptance. No earlier test was changed without a leave. The earlier acceptances' lists for S0001 to S0006 stand.

## 7 The slow checks

Apart from `make check`, the Makefile has only the reports `areas`, `duplicates` and `documents`, and `mutants`, which is excluded (check 3). There is no image scan and no SBOM.

- `make documents`: `documents ok`.
- `make duplicates`: `duplicates: 5 new, 40 known, 3 gone`, as at the second and third acceptances. None of them is in this round's files, which are documents. As a record, the target exits non-zero on new findings.
- Slowest tests (`.reports/junit.xml`: 10,451 tests, about 1,187 s of worker time): the time-limit tests, at about 10 s each (`ROOMY_LIMIT`):
  - `test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[137-at-the-limit]`, 10.05 s;
  - `test_claude_runtime_resume.py::test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures`, 10.04 s;
  - `test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_streaming-group]`, 10.04 s.

  The feature's route tests, guide guards and document tests (238 cases with the operator-site and check-documents tests) take 41.8 s.

Disk: free space fell from 23.7 GB at the previous record (`disk acceptance`, the third acceptance) to 23.5 GB now, on all three mounts, which share one pool. Used space stayed at 1.4 GB on `/srv/factory/vm` and 0.0 GB on `state` and `/tmp`. S0008 and S0009 changed a few paragraphs of Markdown, which does not explain 0.2 GB.

The cost records show the same steady fall as before. `store_free_bytes` went from 23.70 GB at S0008's intake to 23.57 GB at S0009's last review: about 11 MB per run over 12 runs, with no image rebuild between them (all on `2c138284…`). Three acceptances in a row show this per-run fall, so the cause is the run itself (snapshots, transcripts or container layers on the pool), not a change of the feature. It is worth a look outside this feature.

## 8 Cost

The stories cost 84 runs, 83.8 min, 572 turns and $18.99:

| Story | Route | Runs | Minutes | Cost | Questions |
| --- | --- | --- | --- | --- | --- |
| S0001 | code | 10 | 14.2 | $3.53 | 0 |
| S0002 | code | 19 | 20.6 | $4.40 | 3 |
| S0003 | code (left docs) | 10 | 7.9 | $1.96 | 2 |
| S0004 | code | 14 | 23.1 | $3.93 | 2 |
| S0005 | code | 7 | 6.2 | $1.56 | 1 |
| S0006 | code | 6 | 4.5 | $0.90 | 0 |
| S0007 | docs | 6 | 2.1 | $0.94 | 0 |
| S0008 | docs | 5 | 2.6 | $0.82 | 0 |
| S0009 | docs | 7 | 2.5 | $0.95 | 0 |

The three acceptances cost another 3 runs and $7.11, outside this sum.

- **The docs route now has three measured stories, each under $1 and under 3 minutes of run time.** On each of them, `docs-review` is the dearest stage: $0.19 to $0.27 per run, against $0.07 to $0.13 for `docs-only`.
  - S0008 needed one send-back (three findings, two of them sentence length).
  - S0009 needed two, at the round cap, for one paragraph (check 6, item 5). That is why it has the most runs of the three: three `docs-review` runs at $0.64, two-thirds of its cost.
- **Machine time is not in these minutes.** Since the human's change, each `docs-only` stage runs `make check` for real, about 2.5 minutes after the agent (S0008, entries 4–5 and 8–9). That costs no tokens.
- **Of the earlier stories, S0002 and S0004 still stand out** (see the second acceptance): S0002 with three questions, and S0004 with two coder → tester → coder round trips.

Human interventions: 8 questions answered, all of the cause `question`, with 0.4 h waited. All eight fell in S0001 to S0005, and S0006 to S0009 needed none. S0002 needed the human most, with three questions (journal 4, 9 and 14: missing criteria, the form of the sections, and a CRC pin).

## Proposed stories

- `backlog/F0052-S0010-the-decision-log-says-a-documents-only-change-runs-the-check.md`: a documents-only story. It corrects the docs route's entry in `docs/decisions.md`, which still says that `make check` is reused after a documents-only change, so that it agrees with the known results' line of F0052-S0008 and with the shipped behaviour. Neither F0053 nor F0054 touches the decision log. It passes `factory-check-story`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed

   1 Scope: every scope item has its story. S0008 and S0009 came from the third acceptance, and both took the docs route through to a merge. Nothing out of scope was touched. Three stories have now been merged on the docs route, so the goal is reached in practice.
   2 Feature smoke test: 4 passed on the shipped `factory/pipeline.yml`.
      - [1] A documents-only story was sent back at review, closed at `docs-approval`, then merged and archived.
      - [2] Through the way back to the code route, a close at `approval` sends the story to `doing`.
      - [3] The guide's quoted `check:` line equals the shipped one, and the index rule matches `INDEX_LINE`.
      - [4] After a documents-only change that breaks the guard, the check's key changes (`e89fd68a4e0d` → `f34c47b8795b`); a change under `docs/runs/` keeps it.
      So the third acceptance's reuse finding is closed. `make check` is green (140.7 s, 99.26 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed:
      - S0008's "Two warnings" bullet about `secrets` is true but does not name `docs-only`.
      - The advice "never a whole folder" is now reconciled by the paragraph's reason.
      - S0009 noticed nothing outside the story.
      - The older stale texts (`pipeline.md:41`, the README's one route, the *Replaced* headings) are left to F0054.
   5 Documentation: `docs/decisions.md:1588` still says that `make check` is reused when only documents changed. That contradicts line 872 (S0008) and the factory's behaviour, and neither F0053 nor F0054 touches the decision log (S0010). This round's new texts are correct.
   6 Decisions:
      - `feature.md` decision 3 is now out of date (the human's file).
      - S0008's documenter changed the generic example beyond the Interface.
      - S0008's decision-log line has no Why line.
      - S0009 allows italics at the start of the other list items.
      - S0009 used the whole `docs-review` round cap: each round found a new sentence-length problem.
      No test changed in this round.
   7 Slow checks: nothing beyond reports.
      - `documents ok`; duplicates 5 new, 40 known, 3 gone, as before.
      - The slowest tests are the 10 s time-limit tests.
      - Disk: free space fell 0.2 GB (23.7 → 23.5 GB) while used space stayed at 1.4 GB. `store_free_bytes` falls about 11 MB per run with no image rebuild, the third acceptance in a row to show it. This round's changes do not explain it, so the cause lies outside the feature.
   8 Cost: 84 runs, 83.8 min, $18.99.
      - S0008 cost $0.82 and S0009 $0.95; `docs-review` is the dearest stage on the route.
      - S0009's three reviews made up two-thirds of its cost.
      - 8 questions, 0.4 h waited, all in S0001 to S0005; S0002 needed the human most, with 3.

   Proposed:
   - F0052-S0010: the decision log's docs route entry says a documents-only change runs the check again. It passes `factory-check-story`.

   Not done: removing my temporary folder `/tmp/tmp.dfhelmlkpe` (the smoke-test module) and `/tmp/pytest-of-*` was denied. Both are lost with the stage.
