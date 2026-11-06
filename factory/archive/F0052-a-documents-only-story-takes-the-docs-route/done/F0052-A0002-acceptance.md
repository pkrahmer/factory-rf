---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 578
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T00:35:53.803115Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T00:44:56.922671Z'
  stage: acceptance
  run: 0f4601b7c39146fe9e4f5a560a7d7012
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-06T00:48:53.074944Z'
  stage: done
stories: [F0052-S0001, F0052-S0002, F0052-S0003, F0052-S0004, F0052-S0005]
outcome: accepted
---

# Acceptance of A documents-only story takes the docs route

## Recommendation

**Accepted with stories.** The whole feature now does what `feature.md` promised. On the shipped `factory/pipeline.yml`, a documents-only story walks `docs-only` → `docs-review` → `docs-approval`, is sent back and closed back along that route, and is merged. The way back through `tests` reaches `approval` and closes to `doing`. The two findings of the first acceptance are fixed: an acceptance merged at `acceptance` says "merged before approval" again, and a rewrite may rename the guides' headings and add a page. The feature smoke test below shows all four, and `make check` is green. Two small leftovers are worth a story each, and neither breaks a promise:

- The reviewer's seven-rule fallback in `docs-review` is still in `reviewer.md` and lags behind the style page (S0006).
- The project guide says "headings are free", but the guide guard and the document check still need seven headings by name, and a script points to two more (S0007, a documents-only story, so it would be the route's first real use).

## 1 Scope

Each scope item has its story: the second route (S0001), the intake's choice and the agents' texts (S0002), and the style page and glossary (S0003). S0004 and S0005 came from the first acceptance (F0052-A0001). The human merged them, and feature decision 7 gives their leaves. S0004 is in scope because it repairs a side effect of the route on the acceptance's merge entry. S0005 serves the goal ("the rewrite of the guides … will take this route"). Nothing in *Out of scope* was touched:

- The template `operator/template/factory/pipeline.yml` is unchanged.
- No style tool was added.
- The code route is unchanged: `test_an_intake_decision_tests_still_takes_todays_route_to_approval`, and part [2] of the smoke test.

What S0004 built: `is_before_approval` (`src/factory/work/domain/acceptance.py:309`) follows `next[0]` with a visited set. `PipelineDefinition.position` is gone (the human's answer, S0004 journal 19). What S0005 built: `index_problems` in `tests/support/guide_files_support.py`, and the two guide guards without their `HEADINGS` tables.

The goal is reached in mechanism. In practice it is still unproven: `docs-review` and `docs-approval` have not yet run on a real story. S0003 left the route, and S0004 and S0005 rightly took the code route, because they change code and tests. The next feature's rewrite stories will be the route's first real use. The proposed S0007 could be that use sooner.

## 2 Feature smoke test

The walk a user of the feature does, on the shipped `factory/pipeline.yml` and not on a test copy, in four parts:

- [1] A documents-only story is sent back once at the review, closed once at `docs-approval`, then merged.
- [2] The documenter takes the way back to the code route, and a close at `approval` sends the story to `doing`.
- [3] `is_before_approval` for every shipped stage, and an acceptance merged while at `acceptance`, through the acceptance walk.
- [4] A rewrite of a copy of `docs/project-guide`: every heading renamed, a page added unnamed and then named, and an area page removed, each checked with `index_problems`.

The module was written to a `mktemp -d` folder and run with the repository's fixtures. The trap removed it.

Command:

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/test_feature_smoke.py" <<'EOF'   # abridged here to its steps
# [1] push factory/pipeline.yml (as shipped) + no-op Makefile; start_story; intake→docs-only; docs-only→docs-review (writes docs/example.md);
#     docs-review→docs-only; docs-only→docs-review; docs-review→docs-approval; tick; human comment + close; tick;
#     docs-only→docs-review (rewrites docs/example.md); docs-review→docs-approval; tick; human merge + merge_by_human; three ticks
# [2] same world setup; intake→docs-only; docs-only→tests; tests→doing→review→docs→smoke-test→approval; tick; close; tick
# [3] walk fixture; push the shipped definition; print is_before_approval per stage; open FIRST, record at acceptance, merge, tick; assert entry
# [4] copytree docs/project-guide to tmp_path; rename every ##/### heading; add examples.md; index_problems(…, AREA_FILES) at each step
EOF
PYTHONPATH=tests uv run pytest -p conftest -s "$d/test_feature_smoke.py"
```

Output, with the stage-environment and disk log lines left out:

```
[1] a documents-only story on the shipped factory/pipeline.yml
         intake decides docs-only     -> stage=docs-only round=0 blocked=None
      docs-only decides docs-review   -> stage=docs-review round=0 blocked=None
    docs-review decides docs-only     -> stage=docs-only round=1 blocked=None
      docs-only decides docs-review   -> stage=docs-review round=1 blocked=None
    docs-review decides docs-approval -> stage=docs-approval round=1 blocked=None
  hand-over: handed_over=docs-approval draft=False labels=['stage:docs-approval']
  close at docs-approval -> stage=docs-only round=2
      docs-only decides docs-review   -> stage=docs-review round=2 blocked=None
    docs-review decides docs-approval -> stage=docs-approval round=2 blocked=None
2026-10-12T12:00:00Z handler error run:F0001-A0001 1 of 3: AgentRuntimeError: agent runtime failed: no scripted run is queued
  docs/example.md on main: '# Example\n\nShorter.\n'
  journal results: ['intake', 'docs-only', 'docs-review', 'docs-only', 'docs-review']
.
[2] the way back: docs-only decides tests on the shipped definition
         intake decides docs-only     -> stage=docs-only round=0 blocked=None
      docs-only decides tests         -> stage=tests round=0 blocked=None
          tests decides doing         -> stage=doing round=0 blocked=None
          doing decides review        -> stage=review round=0 blocked=None
         review decides docs          -> stage=docs round=0 blocked=None
           docs decides smoke-test    -> stage=smoke-test round=0 blocked=None
     smoke-test decides approval      -> stage=approval round=0 blocked=None
  close at approval -> stage=doing round=1
.
[3] acceptances merged on the shipped factory/pipeline.yml
  is_before_approval: {'intake': True, 'tests': True, 'doing': True, 'review': True, 'docs': True, 'smoke-test': True, 'docs-only': True, 'docs-review': True, 'docs-approval': False, 'acceptance': True, 'approval': False, 'done': False}
  merged at acceptance: outcome=accepted entry='done (pull request merged before approval); cost: 2 runs, 3.0 min, 3 turns, 30 tokens in (0 more from cache), 200 out, $1.50'
.
[4] a rewrite of the project guide in a copy: every heading renamed, a page added
  ...
.
============================== 4 passed in 3.24s ===============================
```

The first run of [4] renamed `## The files` as well, so every page counted as unnamed. That run showed a pin that is still there (check 5). I ran [4] again without renaming that one heading:

```
  headings renamed (all but the index's '## The files'): 175 -> []
  new page, unnamed -> ['not in the index: examples.md']
  new page named in the index -> []
  the index's '## The files' renamed -> 11 problems
```

(The removed area page gave `['missing: work.md']` in the first run.)

**Green.**

- The handler error in [1] is expected: it is the feature's own acceptance, which starts after the archive and has no scripted run queued.
- In [3], `acceptance` is `True` again. In the first acceptance it was `False`.
- The feature's tests also pass together: `uv run pytest` over the guide guards, `test_docs_route.py`, `test_acceptance_merged_on_two_routes.py` and `tests/work/domain/` gave `571 passed in 15.86s`.

`make check`, as I found it: `test: green (140.8 s)`, `check: green`, coverage 99.26 %.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Items from S0001 to S0003 that the first acceptance listed and that are still open:

- The reviewer's seven-rule fallback in `docs-review`. Still in `agents/agents/reviewer.md` step 3, and still pinned by `test_claude_agent_texts_docs_route.py::test_the_reviewer_in_docs_review_lists_each_style_rule_once`. `docs/project-guide/agents.md:295` still says "Until the style page exists". Proposed: S0006.
- The test notes on `test_docs_route.py` and the loose substrings in `test_claude_agent_texts_docs_route.py`. Unchanged, notes only.
- The version names in `factory/pipeline.yml` comments: the human's file.

New from S0004 and S0005:

- S0004, the tester (entry 5): `tests/guards/test_areas.py` refused a work-area test module that imported nothing of `work`. The human answered with a real import (entry 8). Resolved.
- S0004, the coder (entry 14) and the reviewer (entry 16, finding 4): `PipelineDefinition.position` became dead. It was removed with its test, under the human's leave (entry 19). Resolved.
- S0004, the coder (entry 18) and the human (entry 19): the coder's rewrite of criterion 7 was dropped by the take, because the coder's write paths do not hold the work item. The reviewer wrote the correction instead (entry 27). See check 6.
- S0004: the earlier test `tests/work/domain/test_acceptance_before_approval.py::test_only_a_stage_before_the_first_approval_is_before_approval` still has a name that describes the positional rule that went. Renaming it needs a leave. It is a note only; no story is proposed.
- S0005, the tester (entry 8): a line in *The files* that names a page that is missing and has no sentence gives neither `missing:` nor `not in the index:`. It is untested.
- S0005, the reviewer (entry 12): no row covers "a word but no full stop" or "a full stop but no word". The code handles both as the Interface says. Notes only.
- S0005, the documenter (entry 14): the lines in *The files* for `agents.md` and `machine.md` name the sections *Replaced in v1.2* and *Replaced from v1*, which the style page forbids. This is left to the next feature's rewrite of those pages.
- S0005, the tester wrote `index_problems` itself (entry 8). The coder then built nothing (entry 10): one run of $0.17 that only ran `make check`. See check 8.

## 5 The documentation as a whole

`make documents`: `documents ok`. Read as a newcomer:

- **"Headings are free" is not quite true.** `docs/project-guide/README.md:15` says the guard requires every page in *The files* and every area page, "headings are free". But some headings still keep their names:
  - The guard reads `## The files` by name (smoke test [4]).
  - The document check requires *Kill points* and *Fault-injection paths* in the project guide's index, *Install* and *Configuration* in `install.md`, and *The stops* in `stops.md` (`OPERATOR_GUIDE_SECTIONS` and `PROJECT_GUIDE_SECTIONS`, `src/factory/shared/domain/documents.py:41-47`).
  - The document check exempts *Replaced from v1* from its search for v1 words (`REPLACED_SECTION`, line 48).
  - `operator/vm/setup.sh` points to *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md`. These are pinned by `tests/vm/test_vm_setup_install_hint.py` and `test_vm_setup_text.py`.

  A documenter on `docs-only` runs `make documents`, so it would see the first group before the check does. It would not see a dangling pointer from the script, and it may not change the script. The next feature's rewrite stories say "headings may change", so this sentence is what they will rely on. Proposed: S0007.
- **Still stale from the first acceptance:**
  - `docs/operator-guide/pipeline.md:41`, *The docs route*: "skips the tests, doing and review stages", although the route has its own review. It also says "against the style page … once it exists".
  - `docs/project-guide/agents.md:295`: "Until the style page exists".
  - `README.md` lines 3 and 38: one route for every story.

  The human's run log (`docs/runs/2026-11-05-f0052/log.md`) leaves these to the next feature's stories of the same files. The `agents.md` sentence goes with S0006 instead, because that story removes what it describes.
- **Correct as written by S0004 and S0005:**
  - `docs/project-guide/pipeline.md`, *More than one route, more than one approval stage*: the forward moves, and "the order … does not matter". No mention of `position(stage)` remains anywhere under `docs/`.
  - `docs/project-guide/README.md`, *Shared test helpers*: names `before_approval_support.py` and `two_routes_support.py`.
  - `docs/decisions.md:1600` and `:1608`: the two new entries.
  - `docs/operator-guide/work-items.md`, *Merged before its approval*: true again, as smoke test [3] shows.

## 6 Decisions taken for the human

Accept or revisit. From the first acceptance, still standing: `feature.md` decisions 1 to 7, and its list items 3 to 6. Item 2 (the fallback) is now S0006. Item 6 is still open: on the code route, `review` sends findings that are only about documents forward with `docs`, which counts no round. It was answered once and is not written into `reviewer.md`. New:

1. S0004: "before the approval" is read from the forward moves (`next[0]`), not from the position in the file (`docs/decisions.md:1608`). Rejected: reordering `factory/pipeline.yml`.
2. S0004, journal 19: `PipelineDefinition.position` and its test were removed, because nothing called them.
3. S0004, journal 8: the new merge test stays in `tests/work/application/` and checks against `AcceptanceState`, so that the area guard is met by a real import.
4. S0005: the guides' headings are no longer pinned (`docs/decisions.md:1600`). Rejected: changing the tables' rows in every rewrite story.
5. S0005, journal 4:
   - An index line may have a colon after the name.
   - `test_the_guide_holds_the_index_and_its_named_files` survives the merge of the two index tests.
   - The check `names == sorted(...)` is dropped. So a file in `docs/project-guide/` that is not Markdown (a `notes.txt`) is no longer flagged.
6. S0005, the tester (entry 8): a line in *The files* without a sentence, for a page that is missing, reports nothing. This is untested.
7. Pipeline, from S0004 journal 18/19: R5 says a stage rewrites the Description when the journal changes it, but the coder's write paths do not hold `{work_item}`. So the take drops the coder's rewrite, and a later reviewer has to make it. Options: give the coder `{work_item}` in `factory/pipeline.yml` (the human's file), or say in the agents' texts that the reviewer corrects the Description. This is for the human; no story is proposed.
8. Pipeline, from S0005: a story that changes only tests takes the code route, where the tester writes everything and the coder only runs `make check`. Accept the cost of one run, or think about a route for it later. This is for the human; no story is proposed.

Earlier tests changed in S0004 and S0005, each with its leave:

- `tests/pipeline/application/test_docs_route.py` (S0004):
  - `TWO_ROUTES` moved to `tests/support/two_routes_support.py`, under the standing leave to move a shared helper.
  - The row `acceptance` changed from `False` to `True`, under feature decision 7.
- `tests/pipeline/adapters/test_pipeline_yaml.py` (S0004): `test_position_is_the_index_in_the_stages` deleted, under the human's leave in S0004 journal 19.
- `tests/work/domain/test_acceptance_before_approval.py` (S0004): `FIXTURE`, `ROLES` and `without_approval` moved to `tests/support/before_approval_support.py`, under the standing leave.
- `tests/guards/test_project_guide_files.py` and `tests/guards/test_operator_guide_files.py` (S0005): `HEADINGS` and their tests removed, and the two index tests merged, under feature decision 7.
- `tests/support/guide_files_support.py` (S0005): `guide_headings` removed, because its only callers were the tests that decision 7 removes. The reviewer counted this as covered by the Interface (journal 12).

No earlier test was changed without a leave. The first acceptance's list for S0001 to S0003 stands.

## 7 The slow checks

The Makefile offers nothing beyond `make check` except reports: `areas`, `duplicates`, `documents`, and `mutants` (excluded, check 3). There is no image scan and no SBOM.

- `make documents`: `documents ok`.
- `make duplicates`: `5 new, 40 known, 3 gone`. These are the same findings the coders recorded. None is in a file of this feature: `claude_runtime`/`opencode_runtime`, `hand_over`/`work.application.acceptance`, `cost_records.py`. The target exits non-zero on new findings, as a record.
- Slowest tests (`.reports/junit.xml`, 10,449 tests, about 1,180 s of worker time): the podman and process time-limit tests, at about 10 s each (`ROOMY_LIMIT`). The feature's 132 tests take 28 s in all. The slowest of them is `test_docs_route.py::test_a_close_at_docs_approval_takes_the_round_cap_of_docs_review[third-past-the-cap]`, at 4.0 s. The suite is 264 tests smaller than at the first acceptance, because S0005 removed the heading rows.

Disk: free space fell from 24.1 GB at the previous record (`disk acceptance`, the first acceptance) to 23.9 GB now, on all three mounts, which share one pool. Used space stayed at 1.4 GB on `/srv/factory/vm` and at 0.0 GB on `state` and `/tmp`. S0004 and S0005 changed a few hundred lines of code, tests and documents, so they do not explain the 0.2 GB. Over the whole feature, free space fell by 1.0 GB (24.9 to 23.9 GB) outside the measured mounts. Snapshots, container layers or caches on the pool are the likely place. The human's log already says to watch it over the next feature, and it is still growing slowly.

## 8 Cost

The stories cost 60 runs, 72.0 min, 438 turns and $15.37:

| Story | Runs | Minutes | Cost | Questions |
| --- | --- | --- | --- | --- |
| S0001 | 10 | 14.2 | $3.53 | 0 |
| S0002 | 19 | 20.6 | $4.40 | 3 |
| S0003 | 10 | 7.9 | $1.96 | 2 |
| S0004 | 14 | 23.1 | $3.93 | 2 |
| S0005 | 7 | 6.2 | $1.56 | 1 |

- **S0004 stands out for a one-function change.** It needed 14 runs, 6 of them `doing`. Twice a test change had to go coder → tester → coder:
  - the area guard on the new test module (journal 7 to 14);
  - the review's three test cleanups and the deletion of the `position` test (journal 16 to 25).

  Each round trip cost a coder run that changed nothing (journal 10 and 21, $0.08 to $0.23 each). The most expensive runs were the first tests run ($0.79) and the second review ($0.76).
- S0005 was cheap. Its one wasted run is the coder that built nothing ($0.17, 2.6 min), because the tester wrote the support function.
- S0001 to S0003: as the first acceptance reported. S0002 had the most runs, and S0003 left the docs route because of the guard that S0005 has now removed.

Human interventions: 8 questions answered, all of the cause `question`, with 0.4 h waited. S0002 needed the human most, with three questions (journal 4, 9, 14: missing criteria, the form of the sections, and a CRC pin). S0004 and S0003 had two each. S0004's were the test guard (journal 8) and the dead `position` (journal 19). S0003's were the guard change and the route of document-only review findings. S0005 had one, with four sub-answers on the index-line format and the test rows (journal 4).

## Proposed stories

- `backlog/F0052-S0006-the-docs-reviewer-judges-by-the-style-page-alone.md`: drops the seven-rule fallback from `reviewer.md`'s `docs-review`, and its pinning test. Then the reviewer judges by the style page's eight rules and its sections, not by an older list. It needs the human's leave in `feature.md` for the earlier test.
- `backlog/F0052-S0007-the-project-guide-names-the-headings-a-check-still-requires.md`: a documents-only story. *The files* names the nine headings that the guard, the document check and `setup.sh` still need, so the next feature's rewrites do not rename them and leave the route. It could be the docs route's first real use; the human may instead fold it into the next feature's rewrite of `docs/project-guide/README.md`.

Both pass `factory-check-story`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed

   1 Scope: S0001 to S0003 cover each scope item. S0004 and S0005 came from the first acceptance, under feature decision 7. Nothing out of scope was touched: the template is unchanged and so is the code route. The goal is met in mechanism, but `docs-review` and `docs-approval` have still not run on a real story. S0003 left the route, and S0004 and S0005 rightly took the code route.
   2 Feature smoke test: green, 4 passed, on the shipped `factory/pipeline.yml`.
      - The docs route works: sent back once at `docs-review` (round 1), closed back to `docs-only` at `docs-approval` (round 2), then merged with the document on main.
      - The way back through `tests` reaches `approval`, and a close there sends the story to `doing`.
      - `is_before_approval(acceptance)` is True again, and an early-merged acceptance gets "done (pull request merged before approval)".
      - A copy of the project guide with 175 headings renamed and a page added and named in the index gives `index_problems == []`.
      - `make check` is green (140.8 s, coverage 99.26 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: still open from S0001 to S0003 is the reviewer's seven-rule fallback, which leads to S0006. New ones:
      - `position` and the area-guard import: resolved.
      - The coder's rewrite of the Description was dropped by the take.
      - A test name still describes the positional rule that went (note only).
      - The `index_problems` edge rows are untested (notes only).
      - The tester wrote the support function, so the coder built nothing.
   5 Documentation: `docs/project-guide/README.md` says "headings are free", but some headings must keep their names:
      - `## The files`, which the guard reads.
      - Kill points, Fault-injection paths, Install, Configuration and The stops, which the document check requires.
      - Replaced from v1, which the document check exempts from its search for v1 words.
      - Two headings of `machine.md`, which `setup.sh` points to.

      That is S0007. The stale texts in `operator-guide/pipeline.md` and the README are left to the next feature, as the human's log says. The texts S0004 and S0005 wrote are correct.
   6 Decisions: the feature's 7 decisions and the open items of the first acceptance, plus 8 new ones:
      - forward moves instead of the position in the file;
      - `position` removed;
      - the area-guard import;
      - headings no longer pinned;
      - the index-line format, with the non-Markdown check dropped;
      - the untested line without a sentence;
      - the coder's write paths hold no `{work_item}`, although R5 asks for Description rewrites;
      - a tests-only story costs a coder run that builds nothing.

      Every earlier test in S0004 and S0005 was changed under a named leave.
   7 Slow checks: nothing beyond reports. `documents ok`. `duplicates` 5 new, 40 known, 3 gone, none in the feature's files. The slowest tests are the 10 s limit tests; the feature's 132 tests take 28 s. Disk: free space fell 0.2 GB since the previous record (1.0 GB over the whole feature) while used space stayed at 1.4 GB. The changes do not explain it.
   8 Cost: 60 runs, 72.0 min, $15.37. S0004 stands out: 14 runs for one function, 6 of them `doing`, because of two coder→tester→coder round trips. S0002 needed the human most (3 of the 8 questions). 0.4 h waited in all.

   Proposed:
   - F0052-S0006: the docs reviewer judges by the style page alone. It needs a leave for an earlier test.
   - F0052-S0007: the project guide names the headings a check still requires. It is a documents-only story, so it could be the route's first real use.

   Both pass `factory-check-story`.

   Not done: removing `/tmp/pytest-of-factory`, which my smoke-test runs left, was denied. It is lost with the stage.
3. factory: done (pull request merged); cost: 1 runs, 8.9 min, 45 turns, 111819 tokens in (3381138 more from cache), 31166 out, $2.19
