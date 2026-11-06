---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 581
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T01:14:03.082411Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T01:23:25.673963Z'
  stage: acceptance
  run: aae414c806024e3e90fcda0ba31a3719
stories: [F0052-S0001, F0052-S0002, F0052-S0003, F0052-S0004, F0052-S0005, F0052-S0006, F0052-S0007]
outcome: null
---

# Acceptance of A documents-only story takes the docs route

## Recommendation

**Accepted with stories.** The feature now does what `feature.md` promised, in practice as well as in mechanism. S0007 was the first real story on the docs route: it went `intake` → `docs-only` → `docs-review` → `docs-only` → `docs-review` → `docs-approval` and was merged, for 6 runs and $0.94. The feature smoke test is green on the shipped `factory/pipeline.yml`, and so is `make check`.

One finding has weight, but it breaks no promise of the feature. A documents-only change keeps `make check`'s key, because `factory/pipeline.yml` leaves `README.md` and `docs/*.md` out of it, yet tests under `make test` read those files (smoke test [4]). So on the docs route a passed check from an earlier story is reused, even when the change turns `make check` red. S0007's first run did exactly that, and the check ran only because the stage image had changed. The fix is a one-line change by the human in `factory/pipeline.yml` (check 6, item 1). S0008 then brings the operator guide in line with it. S0009 documents the index-line trap that stalled S0007.

## 1 Scope

Each scope item has its story:

- The second route and its approval: S0001.
- The intake's choice and the agents' texts: S0002.
- The style page and the glossary: S0003.

S0004 and S0005 came from the first acceptance (F0052-A0001), and S0006 and S0007 from the second (F0052-A0002). The human started all four, and feature decisions 7 and 8 give the leaves they used. In this round:

- S0006 (`agents/agents/reviewer.md` step 3, and `docs/project-guide/agents.md:295`) removed the reviewer's seven-rule fallback. The reviewer on `docs-review` now judges by the style page alone. It touched an agent file, so it rightly took the code route (intake, entry 3).
- S0007 (`docs/project-guide/README.md`, *The files*) names the nine headings that a check or a script still finds by name.

Nothing out of scope was touched:

- The template `operator/template/factory/pipeline.yml` was last changed in F0051.
- No style tool was added.
- The code route is unchanged (smoke test [2]).

The gap the second acceptance named is closed. The goal had been reached in mechanism only, with `docs-review` and `docs-approval` never run on a real story. S0007 has now run them: a red check stall, one send-back by the reviewer (a list-rendering finding), and the human's merge at `docs-approval` (commit `8c4621486`, "handed over at docs-approval"). Nothing in scope is left without a story.

## 2 Feature smoke test

The walk a user of the feature does, on the shipped `factory/pipeline.yml`, through the factory's tick, the fake hosting service and real git, in four parts:

- [1] A documents-only story is sent back once at the review, closed once at `docs-approval`, then merged and archived.
- [2] The way back to the code route: a close at `approval` sends the story to `doing`.
- [3] The shipped texts of this round: the reviewer's `docs-review` step 3, and the nine headings in *The files* with the files that hold them.
- [4] The check's key before and after a documents-only change that breaks the guide guard, on a clone of this checkout.

The module was written with the file tool into a `mktemp -d` folder and run with the repository's fixtures:

```bash
cd /work/checkout && PYTHONPATH=tests uv run pytest -p conftest -s -q -p no:cacheprovider /tmp/tmp.zJCquVbwRM/test_feature_smoke.py 2>&1 | grep -v "stage environment\|^disk" | tail -70
```

In outline, the module does this:

- [1] It pushes the shipped `factory/pipeline.yml` and a no-op Makefile to `main` and starts a story. Each agent run is a scripted fake run with a decision, and the documenter's runs write `docs/example.md`. A close is a human comment plus `close_by_human`. A merge is `human.merge`, then `merge_by_human`, then three ticks.
- [2] It runs the same setup, then the decisions `docs-only` and `tests`, then every forward decision of the code route up to `approval`, then a close.
- [3] It reads `agents/agents/reviewer.md` and `docs/project-guide/README.md`, and greps the named files for each heading.
- [4] It clones `/work/checkout` into `tmp_path` and computes `GitCli.work_tree_id` with `check`'s `not_read` from the shipped definition. It then renames `## The files` and computes the id again, and runs `index_problems` before and after the rename.

Output:

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
2026-10-12T12:00:00Z disk acceptance: /tmp/pytest-of-factory/pytest-0/test_1_docs_route0 1000.0 GB free, 0.0 GB used; ...
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
  hand-over: handed_over=approval draft=False
  close at approval -> stage=doing round=1
.
[3] the shipped texts of S0006 and S0007
  docs-review: new sentence 1 | 'until' 0 | 'Only the current truth.' 0
  'The files'                  named: True  exists in docs/project-guide/README.md: True
  'Kill points'                named: True  exists in docs/project-guide/README.md: True
  'Fault-injection paths'      named: True  exists in docs/project-guide/README.md: True
  'Install'                    named: True  exists in docs/operator-guide/install.md: True
  'Configuration'              named: True  exists in docs/operator-guide/install.md: True
  'The stops'                  named: True  exists in docs/operator-guide/stops.md: True
  'The machine'                named: True  exists in docs/operator-guide/machine.md: True
  'The rebuild after a merge'  named: True  exists in docs/operator-guide/machine.md: True
  'Replaced from v1' named: True
.
[4] the check's key after a documents-only change that breaks the guide guard
  guard before: []
  guard after renaming '## The files': 10 problems
  check's key tree before=2503ea5b3c55 after=2503ea5b3c55 same=True
  the whole tree changed: True
.
4 passed in 4.40s
```

**Parts [1] to [3] are green.** The handler error in [1] is expected: it is the fake feature's own acceptance, which starts after the archive and has no scripted run queued.

**Part [4] shows the finding.** A documents-only change that makes the guard fail ten times leaves `make check`'s key unchanged. The id `2503ea5b3c55` is the same tree that the journals of S0006 (entry 11) and S0007 (entry 12) name for their reused checks. The factory reuses a passed check for a key that is the same command, tree, definition digest and image (`src/factory/pipeline/application/known_results.py:54-62`). So any later documents-only stage on that image takes the earlier pass, whatever the documents now say.

Two runs show how this played out in S0007:

- Entry 6 was red only because the image had changed between S0006 (`35dc5a55…`) and S0007 (`2c138284…`, its cost records), so no pass was known for the new key.
- Entry 12, in round 1, reused the pass of entry 8. The round-1 change was harmless, but `make check` never checked it.

`make check`, as I found it: `test: green (140.8 s)`, coverage 99.26 %, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Still open from the first two acceptances:

- `docs/operator-guide/pipeline.md:41`, *The docs route*: it says "skips the tests, doing and review stages" and "once it exists". `README.md` lines 3 and 38 still describe one route. Both are left to the next feature's rewrite, as S0006's Description and the human's run log say.
- The test notes on `test_docs_route.py`, the loose substrings in `test_claude_agent_texts_docs_route.py`, and the name of `test_only_a_stage_before_the_first_approval_is_before_approval`, which still describes the positional rule. All are notes.
- The untested edge rows of `index_problems` (S0005, entries 8 and 12). These are notes.
- The lines in *The files* for `agents.md` and `machine.md` still name the sections *Replaced in v1.2* and *Replaced from v1*. Left to the rewrite.

New from S0006:

- The coder (entry 7) saw `docs/project-guide/agents.md:295`, "Until the style page exists". The documenter removed it under criterion 4 (entry 11). Resolved.
- The documenter (entry 11) left the operator guide's "once it exists" to the next feature. Open, as above.
- The reviewer (entry 9) noted where `STYLE_PAGE_SENTENCE` sits in the module. Not a finding.

New from S0007:

- The documenter, entry 8: a list item in *The files* that starts with a name in backticks and goes on to a sentence is read by the guard as a page entry. The guide does not say so. That rule caused the stall in entry 6 (`missing: ## The files`), which cost a run. Proposed: S0009.
- The stall itself: on `docs-only` the documenter's instructions (`agents/agents/documenter.md`, `### docs-only`) ask only for `make documents`, which does not run the guide guards. The guard ran only because `make check` was not reused that time (check 2 [4]). In round 1 the documenter ran the guard by hand, on its own. This is the reuse finding, with the human's fix under check 6, item 1.
- The intake, entry 3: the smoke test's first `Expect:` was weak, a count of at least 1 over nine headings. My smoke test [3] checks all nine. A note.
- The reviewer, entry 10: style rule 8, which asks for a file to be linked by a relative link, was not applied to the code paths in the index, because the index has no links anywhere. This is a style question for the next feature's rewrite (check 6, item 3).

## 5 The documentation as a whole

`make documents`: `documents ok`. Read as a newcomer:

- **The operator guide says that the project's own `not_read` leaves out only what `make check` does not read. That is not true.** At `docs/operator-guide/pipeline.md:56-63` the guide warns that "a path listed by mistake can let a reused `check` pass a fault". It then quotes kumpel-factory's own definition as leaving out "only Markdown and JSON Lines files, because `make lint` reads every Python file". But `make test` reads the Markdown under `README.md` and `docs/`:
  - the four guide and folder guards under `tests/guards/`;
  - `tests/entry/test_check_documents_operator_guide.py`, which copies the real README, decision log and project guide;
  - `tests/operator_scripts/test_operator_site_check.py:510`, which reads `docs/operator-guide/site.md`.

  The quoted block also lags the shipped line, which has `factory/archive/*` as well. An operator who copies this advice gets the same hole. This gap comes from the earlier known-results feature, but the docs route makes it the normal case. Proposed: S0008, after the human's change.
- **The new texts of this round are correct.**
  - *The files* in `docs/project-guide/README.md`: the nine headings, their files and their reasons are all true (smoke test [3]). The two lists are now separated by "The folder holds these pages:".
  - `docs/project-guide/agents.md`, *The docs route*: the reviewer judges by the style page alone, which agrees with `reviewer.md` step 3.
- **Missing: the index-line rule.** *The files* says the guard requires every page to be named there, but not how the guard recognises a page entry. Proposed: S0009.
- **Still stale, left to the next feature:** `docs/operator-guide/pipeline.md:41` and `README.md` lines 3 and 38 (check 4).

No contradiction between two stories' texts. No example that no longer runs, apart from the `not_read` block above, which is a quotation and not a command.

## 6 Decisions taken for the human

Accept or revisit. The earlier lists stand:

- `feature.md` decisions 1 to 8.
- The first acceptance's items 3 to 6. Item 6 is still not written into `reviewer.md`: on the code route, `review` sends findings that concern only documents forward with `docs`.
- The second acceptance's items 1 to 8. Item 7: the coder's write paths do not hold `{work_item}`, although R5 asks for a rewrite of the Description. Item 8: a story that changes only tests costs a coder run that builds nothing.

New:

1. **The check's key leaves out the documents its tests read** (feature decision 3, `factory/pipeline.yml`, the human's file). Options:
   - (a) Drop `"README.md"` and `"docs/*.md"` from `check`'s `not_read` and add `"docs/runs/*"`, which no test reads. Every docs-only and docs run then pays one real `make check`, about 2.5 minutes of machine time and no tokens. Feature decision 3 changes from "reuses" to "runs".
   - (b) Keep the reuse, and move every test that reads the real documents from `make test` into `make documents`. That needs the Makefile (the human's), the moving of earlier tests (a leave), and a story or two.
   - (c) Accept the hole, and rely on the next code story's `make check` to find a broken guard on `main`.

   I would choose (a): it is one line, and it makes the decision log's rule "a forgotten path costs one run, never a silenced check" true again. S0008 is written for (a).
2. S0006 took the code route: `agents/agents/reviewer.md` is not a path the documenter may write (intake, entry 3). That is correct under decision 4. It shows that a change to agent text, however small, pays for a tester and a coder (6 runs, $0.90).
3. S0007, the reviewer (entry 10): the index names files as code paths, not as relative links, although style rule 8 asks for links. The rule was read as "follow the page's own form". The next feature's rewrite should settle whether rule 8 holds for the project guide's index.
4. S0007, the documenter's form (entries 5, 8 and 12): the nine headings are one list with a lead-in, then "The folder holds these pages:", then the page list. The first item begins with the words "The heading", so that the guard does not read it as a page.

Earlier tests changed in this round, each with its leave:

- `tests/agent_files/test_claude_agent_texts_docs_route.py` (S0006): `STYLE_RULES` and `test_the_reviewer_in_docs_review_lists_each_style_rule_once` were removed, and `test_the_reviewer_in_docs_review_judges_the_writing_by_the_style_page_alone` was added with `STYLE_PAGE_SENTENCE`. This is under feature decision 8, as tester entry 5 and reviewer entry 9 name it.
- S0007 changed no test.

No earlier test was changed without a leave. The earlier acceptances' lists for S0001 to S0005 stand.

## 7 The slow checks

The Makefile offers nothing beyond `make check` except reports: `areas`, `duplicates`, `documents`, and `mutants`, which is excluded (check 3). There is no image scan and no SBOM.

- `make documents`: `documents ok`.
- `make duplicates`: `duplicates: 5 new, 40 known, 3 gone`. These are the same findings as at the second acceptance, and none of them is in this round's files. As a record, the target exits non-zero on new findings.
- Slowest tests (`.reports/junit.xml`: 10,451 tests, about 1,189 s of worker time): the time-limit tests, at about 10 s each (`ROOMY_LIMIT`):
  - `test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]`, 10.1 s;
  - `test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_streaming-group]`, 10.0 s.

  The feature's route, acceptance and guide tests (93 cases) take 23.8 s. The slowest of them is `test_docs_route.py::test_a_close_at_docs_approval_takes_the_round_cap_of_docs_review[third-past-the-cap]`, at 3.9 s. The suite has two more tests than at the second acceptance, most likely because S0006 swapped a parametrized test for one with two more rows.

Disk: free space fell from 24.4 GB at the previous record (`disk start`) to 23.7 GB now, on all three mounts, which share one pool. Used space stayed at 1.4 GB on `/srv/factory/vm` and at 0.0 GB on `state` and `/tmp`. S0006 and S0007 changed about 20 lines of text and one test module, so they do not explain 0.7 GB. Two things in the cost records come close:

- `store_free_bytes` falls steadily from run to run, from 23.87 GB at S0006's intake to 23.75 GB at S0007's last review.
- The stage image was rebuilt between the two stories (`35dc5a55…` to `2c138284…`).

A rebuild that leaves layers, or snapshots growing on the pool, is the likely place, as at the earlier acceptances. It is still slow, and still worth watching over the next feature.

## 8 Cost

The stories cost 72 runs, 78.6 min, 506 turns and $17.21:

| Story | Route | Runs | Minutes | Cost | Questions |
| --- | --- | --- | --- | --- | --- |
| S0001 | code | 10 | 14.2 | $3.53 | 0 |
| S0002 | code | 19 | 20.6 | $4.40 | 3 |
| S0003 | code (left docs) | 10 | 7.9 | $1.96 | 2 |
| S0004 | code | 14 | 23.1 | $3.93 | 2 |
| S0005 | code | 7 | 6.2 | $1.56 | 1 |
| S0006 | code | 6 | 4.5 | $0.90 | 0 |
| S0007 | docs | 6 | 2.1 | $0.94 | 0 |

- **S0007 is the route's first measured use.** It took 6 runs, but only 2.1 minutes of run time, against 4.5 minutes for S0006's code route. Two of the six runs were rework:
  - the documenter's second run after the red check (entry 6, $0.09);
  - the reviewer's round-0 finding and its fix ($0.35 for the review and $0.10 for the fix).

  Without them the route would have cost 3 runs and about $0.40. The single dearest run was that round-0 `docs-review`, at 43.5 s and $0.35, because it checked every fact against the code. S0009 would have prevented the first rework.
- **S0006 shows what the code route costs for one sentence of agent text.** Its coder run took 172 s for a one-line change ($0.17); its shell calls, mostly `make check`, took 153 s of that.
- **Of the earlier stories, S0004 still stands out:** two coder → tester → coder round trips (see the second acceptance).

Human interventions: 8 questions answered, all of the cause `question`, with 0.4 h waited. All eight fell in S0001 to S0005. S0006 and S0007 needed no question. S0002 needed the human most, with three questions (journal 4, 9 and 14: missing criteria, the form of the sections, and a CRC pin).

## Proposed stories

- `backlog/F0052-S0008-the-operator-guide-says-the-check-reads-the-documents.md`: a documents-only story, to run after the human's change of `check`'s `not_read` (check 6, item 1, option a). The operator guide then quotes the shipped `not_read` and says why the documents stay in the key, and *The docs route* says that the check runs again. With option (b) or (c) it needs rewriting.
- `backlog/F0052-S0009-the-project-guide-says-which-index-lines-name-a-page.md`: a documents-only story. It writes into *The files* the rule by which the guard reads a page entry, so that the next feature's rewrite of the index does not stall the way S0007 did.

Both pass `factory-check-story`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed

   1 Scope: every scope item has its story. S0006 and S0007 came from the second acceptance. Nothing out of scope was touched. S0007 was the docs route's first real story: `docs-only` → `docs-review` → `docs-only` → `docs-review` → `docs-approval`, then merged. So the goal is now reached in practice, not only in mechanism.
   2 Feature smoke test: 4 passed on the shipped `factory/pipeline.yml`, and the walk is green. A documents-only story was sent back at the review, closed at `docs-approval` and merged. The way back to the code route closes to `doing`. The shipped texts of S0006 and S0007 are true, and all nine named headings exist. Part [4] shows the finding: renaming `## The files` makes the guard report 10 problems but leaves `make check`'s key at tree `2503ea5b3c55`. That is the tree S0006 and S0007 reused, so on the docs route the factory reuses an earlier pass. S0007's first run escaped only because the stage image had changed. `make check` is green (140.8 s, 99.26 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the S0006 items are resolved, except the operator guide's "once it exists", which is left to the next feature. In S0007, a list item starting with a name in backticks is read as a page entry, and that caused the stall (S0009). On `docs-only` the documenter runs only `make documents`, so it never runs the guide guards. A weak `Expect:` and style rule 8 against code paths are notes.
   5 Documentation: `docs/operator-guide/pipeline.md:56-63` says the project's `not_read` leaves out only files `make check` does not read. But `make test` reads `README.md` and `docs/` (S0008), and the quoted block lags the shipped line. The index does not say how the guard recognises a page (S0009). The new texts of S0006 and S0007 are correct. The README and `pipeline.md:41` are still stale, left to the next feature.
   6 Decisions: the earlier lists stand. New:
      - the check's `not_read` against the documents its tests read: options (a) drop them, (b) move those tests to `make documents`, (c) accept; I would choose (a), a one-line change by the human;
      - S0006 took the code route for agent text, which is correct;
      - style rule 8 in the index;
      - S0007's list form.

      The only earlier test changed was `test_claude_agent_texts_docs_route.py`, under feature decision 8.
   7 Slow checks: nothing beyond reports. `documents ok`; duplicates 5 new, 40 known, 3 gone, none in this round's files. The slowest tests are the 10 s limit tests; the feature's 93 cases take 23.8 s. Disk: free space fell 0.7 GB since `disk start` (24.4 to 23.7 GB) while used space stayed at 1.4 GB. The changes do not explain it; the steady fall in `store_free_bytes` and an image rebuild between S0006 and S0007 are the likely place.
   8 Cost: 72 runs, 78.6 min, $17.21. S0007 on the docs route took 6 runs, 2.1 min and $0.94, about 3 runs and $0.40 without its stall and send-back. S0006 cost $0.90 for one sentence of agent text on the code route. 8 questions, 0.4 h waited, all in S0001 to S0005; S0002 needed the human most, with 3.

   Proposed:
   - F0052-S0008: the operator guide quotes the check's `not_read` and says why the documents stay in the key. It runs after the human's change of that line.
   - F0052-S0009: the project guide says which lines of its index name a page.

   Both pass `factory-check-story`.

   Not done: removing my temporary folder `/tmp/tmp.zJCquVbwRM` (the smoke-test module) and `/tmp/pytest-of-factory` was denied. Both are lost with the stage.
