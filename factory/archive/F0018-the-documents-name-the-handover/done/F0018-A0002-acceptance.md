---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 219
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T13:09:01.562143Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-18T13:11:55.465569Z'
  stage: acceptance
  run: a7fff4266a4b4201a64c443f0547de28
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-18T13:13:13.658368Z'
  stage: done
stories: [F0018-S0001, F0018-S0002]
outcome: accepted
---

# Acceptance of The documents name the handover

## Recommendation

**Accepted.** All four Scope items are now built and true. S0001 changed the README, the operator guide and the decision log's handover entry, and S0002 changed the two passages for the agents (`docs/project-guide.md:1710`, `docs/decisions.md:11`). That closes the Goal gap the first acceptance (F0018-A0001) found. The feature smoke test is green, `make check` is green inside v1.1's own container, and no module under `src/factory` changed, so there are no mutants. The one item still open (the "observed at the shakedown" wording) depends on facts only the human has, so I list it under 6 and do not propose a story for it.

## 1 Scope

| Scope item | Story | Where |
|---|---|---|
| README opening and *How it is built* | S0001 | `README.md:3`, `README.md:26` |
| Operator guide bullet under *Replaced from v1* | S0001 | `docs/operator-guide.md:1162` |
| Decision-log entry for the handover | S0001 | `docs/decisions.md:545` |
| Project guide *The document check*, decision log *Three top-level paths* | S0002 | `docs/project-guide.md:1710`, `docs/decisions.md:11` (merge `5ca496f7`) |

S0002 lay outside the Scope when it was proposed. The human widened `feature.md` for it (`e8c017dd`, after S0002's intake question on #218), so no story falls outside the Scope now. Out of scope holds: `git diff 26d9c43b HEAD --stat -- tests src image template claude factory/v1` is empty. The feature's changes outside `factory/` are `README.md`, three files in `docs/`, the `Makefile` (the human's umask fix `27bdaa73`, merged from `main`) and the human's night log. The Goal's second purpose was that factory-rf's own `make check` runs through v1.1's stages inside its container. It holds: both stories ran all their stages there, and my `make check` below ran there too. Finding: none.

## 2 Feature smoke test

The walk-through checks the feature's purpose from beginning to end. The newcomer, the operator and the agents each read their document, and each claim is checked against the tree, the pipeline definition and the real commands (`factory-check-story`, `check_documents`). I wrote it as one script in a `mktemp -d` folder that removes itself, ran it from the checkout with `bash "$d/smoke.sh" 2>&1`, and it printed:

```
## 1 newcomer: the README names the handover and v1.1's tree
1
1
0
## 2 operator: the guide's bullet under Replaced from v1
1
## 3 agents: the project guide and the decision log name the pipeline definition
1710:This repository's pipeline definition (`factory/pipeline.yml`) runs it as a check of the docs stage throu
11:`image/` (Dockerfile, compose file, entrypoint), `templat
545:## factory-rf is built by v1.1 since the handover
## 4 what the documents say holds in the pipeline definition
31:  docs: {role: documenter, next: [smoke-test, doing], checks: [check, documen
20:  coder: {write_paths: ["src/*", "image/*", "template/*", "claude/*"], time_limit: 40, 
## 5 the tree they describe
feature-form.md features pipeline.yml story-form.md v1 
FEATURE.md TICKET.md features stages.yml 
17
factory/stages.yml absent
## 6 no document outside history still says v1's configuration runs this repository
matches exit 1
## 7 v1.1 builds from it: the story form accepts both archived stories, refuses v1's location
factory/features/F0018-the-documents-name-the-handover/done/F0018-S0001-the-documents-name-the-handover.md: ok
factory/features/F0018-the-documents-name-the-handover/done/F0018-S0002-the-agents-guide-names-the-pipeline-definition.md: ok
exit 0
factory/v1/features/F0001-boundaries/done/F0001-S0001-kill-points.md: not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md
exit 1
0
## 8 the document check
documents ok
exit 0
```

What each step checks:
- Step 1: the README has the handover sentence and the *How it is built* sentence, and no "shakedown".
- Step 2: the operator guide's bullet.
- Step 3: the two sentences S0002 rewrote and the decision-log entry.
- Step 4: the pipeline definition backs both new sentences. The docs stage runs `documents`, and the coder's write paths are the four the decision log names.
- Step 5: the tree matches the documents: v1's files are under `factory/v1/` (17 features), and no `factory/stages.yml` is left at the top.
- Step 6: no stale phrase is left in `README.md` or `docs/`; grep finds nothing and exits 1.
- Step 7: `factory-check-story` accepts both archived stories, refuses v1's location, and `src/` never names `factory/v1`.
- Step 8: `documents ok`.

All eight steps are green, where F0018-A0001's step 7 showed the two stale passages.

`make check`, as I found it: `test: green (47.8 s)`, total coverage 99.44 %, `check: green`.

## 3 Mutation score

```
$ make mutants
mutants: no module under src/factory changed by F0018
```

No mutants (0/0) and no survivors: the feature changed only documents.

## 4 What the stories noticed

- S0002: the coder (entry 10), the reviewer (entry 12), the documenter (entry 14, "Stale text I noticed and did not touch: none") and the smoke-tester (entry 16) noticed nothing. The intake (entry 3) noticed that S0002 lay outside the Scope, and the human settled it (entry 4).
- S0001 (already collected by F0018-A0001): the documenter's stale "observed at the shakedown" wording at `docs/decisions.md:462`, `docs/decisions.md:504` and `docs/operator-guide.md:259`. It is still there unchanged. The night log's entry of 15:02 holds it **For the morning**, because it needs the human's facts (6, item 7). The coder's umask fault is closed by `27bdaa73`.

I propose no story: the one open observation is the human's to settle first.

## 5 The documentation as a whole

I read `README.md` (opening, *Getting started*, *How it is built*, *Replaced from v1*), the operator guide's intro and *Replaced from v1*, the project guide's *The document check* and glossary table, and the decision log's opening entries and its last entry, as a newcomer would. The README, the operator guide, the project guide and the decision log now agree with each other and with `factory/pipeline.yml` on who builds this repository and from what. The project guide's glossary row (`docs/project-guide.md:1753`, "`stages.yml`, stage table | the pipeline definition (`factory/pipeline.yml`)") matches the new sentence at line 1710. The handover is explained at length once (decisions) and briefly in the README and the operator guide, without contradiction.

Not findings, but written down so they are not taken for gaps:
- The README's first sentence, "The factory, reimplemented by v1 of itself", is still true: it says how v1.1 came to exist, and line 3 then names the handover.
- `docs/decisions.md:13` (*No `mutants` target, no mutmut*) is superseded explicitly by the dated entry at line 353, as the log's convention is.
- `docs/decisions.md:337` says "`make check` does not run it … wiring it in is left to the human". That is dated history, and the project guide's *The document check* carries the current wiring.

The `factory-check-story` examples hold for this repository (step 7). No section is missing. Finding: none.

## 6 Decisions taken for the human

1. The first work item v1.1 builds on itself is this documentation story, before 5a (the write guard): the human's choice, handover plan option C. (`feature.md`, decision 1)
2. v1's history stays in `factory/v1/`, and v1.1's features continue from F0018 because `make mutants` finds modules by the feature id in commit subjects. (`feature.md`, decision 2)
3. S0002 rewords the *Three top-level paths* sentence in place, keeping the pointer to v1's file, rather than adding a dated line. (`feature.md`, decision 3; S0002 entry 4, answer 2)
4. The Scope was widened to the two passages for the agents, and S0002 was added to the Stories list, by the human's edit of `feature.md` (`e8c017dd`; S0002 entry 4, answer 1).
5. S0002's criterion 1 ("the tester and the coder each end with an entry saying so") is accepted as a process note that the reviewer checks on the diff, not a test. (S0002 entry 4, answer 3)
6. Carried from F0018-A0001, already in the human's sight there:
   - the umask answer (`27bdaa73`: `make test` and `make mutants` run under `umask 022`, and the seal stays strict);
   - the documenter's inferred *Rejected* bullet in the handover entry (`docs/decisions.md`, last line);
   - "its stages" in the README, chosen to pass `check_documents`.
7. Open: did the shakedown of 2026-10-18 observe the second user, the reaping and the Podman init? If yes, a docs story like S0002 can date `docs/decisions.md:462`, `docs/decisions.md:504` and `docs/operator-guide.md:259`. If no, they stay as they are.

Earlier tests changed: none. S0002's reviewer (entry 12, point 6) says no test file on `main` was changed, renamed or deleted, and `git diff 8518d4f4 HEAD --stat -- tests src` is empty. No finding.

## 7 The slow checks

The project offers nothing beyond `make check`, `make mutants`, `make duplicates` and `make documents`: no image scan and no SBOM target. `make duplicates` (S0002 coder entry 10): `0 new, 39 known, 0 gone`. `make documents`: `documents ok`.

Disk is unchanged against the previous record, F0018-A0001's own disk line: `/work` 0.4 GB used, `/state` and `/tmp` 0.0 GB, 985.6 GB free at both. S0002 changed two lines of documents, which explains no growth, and there is none. `/tmp/pytest-of-agent` is 114 MB, the same as F0018-A0001 reported. It is pytest's three-session rotation, from the agents' `make check` runs, not from the feature, and the night log already has it as a finding for the instance.

Slowest tests, from `.reports/junit.xml` of my `make check`: 4726 tests, 499.4 s summed over the workers, 47.8 s wall clock.
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- `tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]`: 3.8 s
- `tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over`: 3.6 s
- `tests/test_fault_paths_7_to_13.py::test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once`: 3.1 s
- `tests/adapters/test_process.py::test_grandchild_is_killed_with_the_child_at_the_time_limit`: 3.0 s

They wait for time limits or ticks by design, and none is new in this feature.

## 8 Cost

14 runs, 7.4 min, $1.71 for the two stories. S0001 took 7 runs ($1.10, explained in F0018-A0001: the coder's question that found the umask fault). S0002 took 7 runs for $0.60:

| Run | Cost | Time |
|---|---|---|
| intake (asked, entry 3) | $0.05 | |
| intake (accepted, entry 6) | $0.02 | |
| tester | $0.11 | 47 s |
| coder | $0.10 | 54 s |
| reviewer | $0.13 | |
| documenter | $0.06 | |
| smoke-tester | $0.14 | |

S0002 does not stand out. Its second intake run was the price of a question that needed the human's widening of `feature.md`. For the human, not a finding: the tester, coder and reviewer each spent a full run ($0.34 together, more than half of S0002) to confirm that a documentation-only story changes nothing in their lanes. The tester and the coder each ran `make test` or `make check` for it. That is the pipeline's fixed shape for every story, not this feature's fault.

## Proposed stories

None. The feature's promises hold, `make mutants` has nothing to mutate, and the stories noticed nothing new. The one open observation (6, item 7) waits for the human's facts before it can become a story.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed; make mutants 0/0
   1 Scope: all four Scope items are built. S0001 did the README, the operator guide and the handover entry. S0002 did `docs/project-guide.md:1710` and `docs/decisions.md:11`, which the human added to the Scope in `e8c017dd`. That closes the Goal gap F0018-A0001 found. Out of scope holds: nothing changed under `src/`, `tests/`, `image/`, `template/`, `claude/` or `factory/v1/`.
   2 Feature smoke test: green, all 8 steps. The README, operator guide, project guide and decision-log claims hold against the tree and `factory/pipeline.yml` (the docs stage's checks and the coder's write paths). No stale phrase is left. `factory-check-story` accepts both archived stories and refuses v1's location, and the document check prints `documents ok`. `make check` was green as I found it (coverage 99.44 %, 47.8 s).
   3 Mutation score: `mutants: no module under src/factory changed by F0018`, so there are no mutants and no survivors.
   4 Noticed: S0002's stages noticed nothing. S0001's "observed at the shakedown" wording (`decisions.md:462`, `:504`, `operator-guide.md:259`) is still open and needs the human's facts, so it is listed under 6, not proposed.
   5 Documentation: the four documents agree with each other and with the pipeline definition on who builds the repository and from what. Superseded decision entries are dated history. No contradiction, no missing section.
   6 Decisions for the human: feature decisions 1 to 3, the Scope widening for S0002, criterion 1 as a process note, the three items carried from F0018-A0001 (umask, the inferred *Rejected* bullet, "its stages"), and the open shakedown question. No earlier test was changed.
   7 Slow checks: nothing beyond the make targets; `duplicates` 0 new. Disk is unchanged against F0018-A0001's record (/work 0.4 GB). `/tmp/pytest-of-agent` is still 114 MB from pytest's rotation, not from the feature. Slowest test: the resume time-limit test, 5.0 s.
   8 Cost: 14 runs, $1.71 (S0001 $1.10, S0002 $0.60). Nothing stands out. In S0002, the tester, coder and reviewer runs ($0.34) confirmed that a docs-only story changes nothing in their lanes; that is the pipeline's fixed shape, noted for the human.
3. factory: done (pull request merged); cost: 1 runs, 2.8 min, 17 turns, 44890 tokens in (518439 more from cache), 10699 out, $0.68
