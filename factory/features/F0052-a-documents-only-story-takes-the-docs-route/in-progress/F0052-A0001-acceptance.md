---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 575
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-05T23:30:48.684774Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-05T23:40:33.580695Z'
  stage: acceptance
  run: 8a14d48600634aa095eb9bdeaeddbe96
stories: [F0052-S0001, F0052-S0002, F0052-S0003]
outcome: null
---

# Acceptance of A documents-only story takes the docs route

## Recommendation

**Accepted with stories.** The route does what `feature.md` promised. On the shipped `factory/pipeline.yml`, a documents-only story goes intake → `docs-only` → `docs-review` → `docs-approval`. A send-back at the review counts a round, a close at `docs-approval` returns it to the documenter, and a merge archives it. The feature smoke test below shows this, and `make check` is green. Two findings are worth stories, and neither breaks a promise of this feature:

- Placing `docs-approval` before `acceptance` silently changed `is_before_approval`. An acceptance merged at its review stage no longer gets the "merged before approval" entry that the operator guide promises (S0004).
- The guide guards pin every heading and the project guide's file list. So the next feature's rewrite stories cannot stay on the docs route, which is the use this feature was built for (S0005).

## 1 Scope

Each of the three scope bullets has its story, and nothing in *Out of scope* was touched:

- S0001: the fake-world walks in `tests/pipeline/application/test_docs_route.py`. No code needed changing.
- S0002: the agent texts `agents/agents/intake.md` step 6, `documenter.md` `### docs-only` and `reviewer.md` `### docs-review`, with `tests/agent_files/test_claude_agent_texts_docs_route.py`. The human's change to `factory/pipeline.yml` came with them (098e9c396).
- S0003: `docs/project-guide/style.md` and `glossary.md`.

The template `operator/template/factory/pipeline.yml` is unchanged. Nothing under `src/` changed.

The goal is reached in mechanism, not yet in practice. S0003 was the route's first real use. The intake chose `docs-only`, but the check after the documenter was red: `tests/guards/test_project_guide_files.py` pins the guide's file list, and the story adds two pages. The documenter took the way back (feature decision 6), and the story went the whole code route. On the way it raised two questions to the human and had one crash. So `docs-review` and `docs-approval` have never run on a real story. The same pins will push every story of the next feature off the route (check 5, S0005).

## 2 Feature smoke test

This walks one documents-only story along the shipped `factory/pipeline.yml`, not a test copy. The story is sent back once at the review, closed once at `docs-approval` with a reason, and then merged. The run also prints `is_before_approval` for every stage of the shipped definition. The test module was written to a `mktemp -d` folder, run with the repository's fixtures, and removed.

Command:

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/test_feature_smoke.py" <<'EOF'   # the walk; abridged here to its steps
# push factory/pipeline.yml (as shipped) and a Makefile of no-op targets to main; start_story(world)
# step(intake→docs-only), step(docs-only→docs-review, writes docs/example.md), step(docs-review→docs-only),
# step(docs-only→docs-review), step(docs-review→docs-approval), tick (hand-over), human comment + close, tick,
# step(docs-only→docs-review, rewrites docs/example.md), step(docs-review→docs-approval), tick,
# human merge + merge_by_human, three ticks; print done/, docs/example.md on main, is_before_approval per stage
EOF
PYTHONPATH=tests uv run pytest -p conftest -s "$d/test_feature_smoke.py"
```

Output (the stage-environment and disk log lines left out):

```
       intake decides docs-only     -> stage=docs-only round=0 blocked=None
    docs-only decides docs-review   -> stage=docs-review round=0 blocked=None
  docs-review decides docs-only     -> stage=docs-only round=1 blocked=None
    docs-only decides docs-review   -> stage=docs-review round=1 blocked=None
  docs-review decides docs-approval -> stage=docs-approval round=1 blocked=None
hand-over: handed_over=docs-approval draft=False labels=['stage:docs-approval']
close at docs-approval -> stage=docs-only round=2 blocked=None draft=True
    docs-only decides docs-review   -> stage=docs-review round=2 blocked=None
  docs-review decides docs-approval -> stage=docs-approval round=2 blocked=None
2026-10-12T12:00:00Z handler error run:F0001-A0001 1 of 3: AgentRuntimeError: agent runtime failed: no scripted run is queued
archived: ['F0001-S0001-first.costs.jsonl', 'F0001-S0001-first.md']
docs/example.md on main: '# Example\n\nA better page.\n'
is_before_approval on the shipped definition: {'intake': True, 'tests': True, 'doing': True, 'review': True, 'docs': True, 'smoke-test': True, 'docs-only': True, 'docs-review': True, 'docs-approval': False, 'acceptance': False, 'approval': False}
.
1 passed in 1.66s
```

**Green.** The handler error is the feature's own acceptance, which starts after the archive and has no scripted run queued; it is expected. One value is wrong: `'acceptance': False`. On the definition before this feature it was `True`, as `tests/work/domain/test_acceptance_before_approval.py` still pins on its own copy. `is_before_approval` compares a stage with the first approval stage in the file, and that is now `docs-approval`. `AcceptanceMerged._book` (`src/factory/work/application/acceptance.py:320`) passes this value to `book_merge`. So an acceptance the human merges while it is still at `acceptance` now gets the ordinary `done (pull request merged); cost: ...` entry. `docs/operator-guide/work-items.md` (*Merged before its approval*) and the decision log promise `done (pull request merged before approval); ...`. The booking itself (`accepted`) is unaffected. S0001's criterion 7 pinned `acceptance` → `False` on its test definition, and `docs/project-guide/pipeline.md` even names the rule, but nobody tied it back to the acceptance. Proposed: S0004.

`make check` as I found it: `check: green` (`test: green (132.5 s)`, coverage 99.26 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001, reviewer notes (entry 17):
  - `tests/pipeline/application/test_docs_route.py:249` has a dead assignment `state = head_state(...)`.
  - The criterion 1 test repeats `_walk_docs_route` inline.
  - Both are small test cleanups, and nobody owns them. No story: S0004 changes that module and may take them along if the human wants.
- S0002, reviewer notes (entry 38): in `test_claude_agent_texts_docs_route.py`, the rows `its checklist` and `its decisions, and steps 1 to 3` are loose substrings. The documenter's two hand-offs are separate functions, not rows of one rule. Both are notes only.
- S0002, documenter (entry 40) and smoke tester (entry 42): they doubted that the `docs/decisions.md` entry covers feature decisions 1 to 6. **Resolved:** I read the entry *A documents-only story takes the docs route*, and all six are there, with the three rejected options.
- S0003, documenter (entries 5, 8, 24) and coder (entry 15): the header comments of `factory/pipeline.yml` and older `docs/decisions.md` entries use version names. The first is the human's file, and the second is history, outside the next feature's scope. Left to the human.
- S0003, documenter (entry 5): the drafts' rules 8 to 10 (facts from the code, a *Reference* section, examples that show where they were run) were left out of `style.md`. The reviewer agreed. This is listed under 6.
- S0003, reviewer (entry 17): on the code route, the `review` stage has no way to send findings that are only about documents to the documenter. `doing` reaches a coder who may not write `docs/`. The human answered `docs` (entry 18), a forward move that counts no round. This is listed under 6.
- S0003, the stall (entry 6): the documenter on `docs-only` runs only `make documents`. A guard test broken by a new page shows up only in the factory's check after the stage, which costs a stall before the way back. This is the cause behind S0005.

## 5 The documentation as a whole

`make documents`: `documents ok`. Read as a newcomer:

- **Contradiction with the style page:** `tests/guards/test_operator_guide_files.py` requires the operator guide to keep the headings `## Replaced in v1.2` and `## Replaced from v1`. Rules 1 and 7 of `docs/project-guide/style.md` forbid version names and "no longer" history. The same file pins 128 earlier headings, and `test_project_guide_files.py` pins 158 more plus the file list. The rewrite stories of the next feature say "its headings may change". Each of them would be red after `docs-only` and would leave the route, as S0003 did. Proposed: S0005, to start before the rewrite.
- **Stale since S0003:** `docs/project-guide/agents.md`, *The docs route*, says "Until the style page exists, the reviewer's subsection lists the seven style rules itself". `docs/operator-guide/pipeline.md`, *The docs route*, says "against the style page ... once it exists". The page exists now. The fallback list in `agents/agents/reviewer.md` has seven rules, while the page has eight (rule 8, relative links).
- **Inaccurate:** `docs/operator-guide/pipeline.md`, *The docs route*, first sentence: "skips the tests, doing and review stages". The route has a review of its own (`docs-review`). It skips the code review, not the review.
- **The README:** `README.md` lines 3 and 38 still say that every story goes through tests, code, review, documentation and a smoke test. The README's rewrite is out of scope here and is a story of the next feature.
- No story is proposed for the last three points. The next feature rewrites exactly these files (`operator-guide/pipeline.md`, `project-guide/agents.md`, `README.md`), one story each, and corrects wrong claims. The human may add these three points to those stories when refining.
- `docs/project-guide/pipeline.md`, *More than one route*: correct as of today. It changes with S0004.
- The glossary: I found no contradiction with the operator guide's stops or the decision log.

## 6 Decisions taken for the human

Accept or revisit:

1. `feature.md` decisions 1 to 6: three stages of their own; the review after the writing; no smoke test on the docs route; the intake decides by the Interface's paths; routes as branches of the graph; the way back through `tests`. Recorded in `docs/decisions.md`.
2. S0002, journal 9: the docs-route sections are `###` subsections inside `## Stage`. The reviewer's subsection lists the seven rules word for word, checked unconditionally, as the fallback "until the style page exists". The page now exists with eight rules, so the list is dead text that lacks rule 8. Keep it, or drop it together with its test?
3. S0002, journal 14: the documenter's subsection is a bulleted list, because a numbered one breaks `test_claude_agent_texts_docs_slip.py`. The reviewer's "replaces" sentences sit inside the subsection, because the rest of `reviewer.md` is CRC-pinned.
4. S0003, journal 11: no tests for the style page or the glossary; their formats stay the documenter's choice.
5. S0003, documenter and reviewer: the drafts' rules 8 to 10 stay out of `style.md`.
6. S0003, journal 18: on the code route, review findings that are only about documents go forward with `docs`. This counts no round. It was answered once and is not written into `reviewer.md`. Make it a rule, as F0045 did for the smoke test, or keep asking?
7. S0004, if accepted: "before the approval" is read from the forward moves, not from the position in the file. The alternative is to reorder `factory/pipeline.yml` (the human's file) so that every approval stage comes last.
8. S0005, if accepted: drop the heading pins of both guides and read the project guide's file list from its index. The alternative is to keep the pins and change their rows in every rewrite story.

Earlier tests changed, each with its leave:

- `tests/agent_files/test_claude_agent_texts_review_groups.py` (S0002): the human's leave, journal 14.
- `tests/agent_files/test_claude_agent_texts_docs_slip.py` (S0002): the standing leave to move a shared helper (`stage_section` to `tests/support/shipped_agents.py`).
- `tests/guards/test_project_guide_files.py` (S0003): the human's leave, journal 11.

S0001 changed no earlier test. No earlier test was changed without a leave.

## 7 The slow checks

The Makefile offers nothing beyond `make check` but `areas` (a report), `duplicates`, `documents` and `mutants` (excluded, check 3). There is no image scan and no SBOM.

- `make documents`: `documents ok`.
- `make duplicates`: `5 new, 40 known, 3 gone`. These are the same numbers every coder entry of the feature recorded. The feature changed nothing under `src/`, so none of them is its own.
- Slowest tests (`.reports/junit.xml`, 10,713 tests, about 1,180 s of worker time): the podman time-limit tests and the claude-runtime resume tests at about 10 s each (`ROOMY_LIMIT`). The feature's walks in `test_docs_route.py` take 1 to 3.7 s each, about 22 s in all.

Disk: free space fell from 24.9 GB at the previous record (`disk start`) to 24.1 GB now on all three mounts, which share one pool. Used space on `/srv/factory/vm` stayed at 1.4 GB, and on `state` and `/tmp` at 0.0 GB. The feature's changes are about 650 lines of documents and tests, so they do not explain the 0.8 GB. It went somewhere on the pool outside the measured mounts, for example stage snapshots, container layers or a cache. It is worth a look if it keeps growing over the next feature.

## 8 Cost

The feature cost 39 runs, 42.7 min, 276 turns and $9.89:

| Story | Runs | Minutes | Cost |
| --- | --- | --- | --- |
| S0001 | 10 | 14.2 | $3.53 |
| S0002 | 19 | 20.6 | $4.40 |
| S0003 | 10 | 7.9 | $1.96 |

- **S0001 stands out by price for what it built.** It changed no code: the walk found no fault. A review round on the test (a missing criterion and two cleanups) cost a tester, two coder runs of `make check` and a second review.
- **S0002 stands out by runs.** It needed 19 runs, three human questions and two review rounds, and each review round added criteria for text that already existed (criteria 4 and 5). It ran into the CRC pin of an earlier test.
- **S0003 was the cheapest**, but it took 10 runs where the docs route plans 3 or 4: a `check_red` stall, the way back to `tests`, a tester question, a coder run that built nothing, a reviewer question and a crash at `docs`. S0005 addresses the cause.

Human interventions: 5 questions answered, all of the cause `question`, with 0.3 h waited:

- **S0002 needed the human most, with three questions.** The intake found five Interface behaviours without a criterion (journal 4). The tester needed the form of the sections and the rules' text (journal 9). The coder hit the CRC pin (journal 14).
- S0003 had two: the guard change (journal 11) and the route of the review findings (journal 18).

## Proposed stories

- `backlog/F0052-S0004-an-acceptance-merged-at-its-review-stage-says-so-on-every-route.md`: `is_before_approval` follows the forward moves. With that, the shipped order with `docs-approval` before `acceptance` books an early merge with the entry the operator guide promises.
- `backlog/F0052-S0005-a-guide-rewrite-may-rename-its-headings-and-add-a-page.md`: drops the heading pins of both guides and reads the project guide's pages from its index. Then a rewrite in the style page, the next feature, stays on the docs route. Start it before the rewrite.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed

   1 Scope: each of the three scope items has its story, and nothing out of scope was touched (no `src/` change, template unchanged). S0003 was the route's first real use but left it: a guard (`tests/guards/test_project_guide_files.py`) made the check red after `docs-only`, so the story took the whole code route. `docs-review` and `docs-approval` have not yet run on a real story.
   2 Feature smoke test: green. On the shipped `factory/pipeline.yml`, one story went intake → `docs-only` → `docs-review`, was sent back once (round 1), was handed over at `docs-approval`, was closed back to `docs-only` (round 2) and was merged and archived. Side finding from the same run: `is_before_approval(shipped, "acceptance")` is now `False` (it was `True` before the feature). So an acceptance merged early loses the "merged before approval" entry that `docs/operator-guide/work-items.md` promises (S0004).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: test cleanups in `test_docs_route.py` and loose substrings in `test_claude_agent_texts_docs_route.py` are notes only. The doubt about the `docs/decisions.md` entry is resolved: all six feature decisions are there. Version names in `factory/pipeline.yml` comments and old decision-log entries are left to the human. A `docs-only` documenter cannot see a broken guard before the factory's check (the cause behind S0005).
   5 Documentation: the guide guards pin 128 + 158 headings, including `## Replaced in v1.2` and `## Replaced from v1`, which the new style page forbids. So every rewrite story of the next feature would leave the docs route (S0005). Stale "until/once the style page exists" in `docs/project-guide/agents.md` and `docs/operator-guide/pipeline.md`. "Skips the ... review stages" is inaccurate. README lines 3 and 38 still describe one route. These three are left to the next feature's rewrite stories of the same files.
   6 Decisions: the feature's six decisions, plus seven more from the journals and the two proposals for the human to accept or revisit. Among them: the reviewer's seven-rule fallback is dead now, and the code-route review sends document findings forward with `docs`, answered once and not written into `reviewer.md`. Three earlier tests were changed, each under a named leave: S0002 journal 14, the standing leave, and S0003 journal 11.
   7 Slow checks: nothing beyond `make check` except reports. `make documents`: ok. `make duplicates`: 5 new, 40 known, 3 gone, the same before the feature. The slowest tests are the 10 s time-limit tests; the feature's walks add about 22 s. Disk: free space fell from 24.9 to 24.1 GB while measured used space stayed at 1.4 GB, which the feature's roughly 650 lines do not explain.
   8 Cost: 39 runs, 42.7 min, $9.89. S0001 cost $3.53 for no code change. S0002 had 19 runs, 3 of the 5 questions and two review rounds that added criteria, so it needed the human most. S0003 took 10 runs where the route plans 3 or 4 (a stall, the way back, two questions, a crash). 0.3 h waited in all.

   Proposed: F0052-S0004 (`is_before_approval` follows the forward moves) and F0052-S0005 (the guide guards drop their heading pins and read the project guide's pages from its index; start it before the rewrite). Both pass `factory-check-story`. Each changes one earlier test module, for which the human must give a leave when refining.
   Not done: removing `/tmp/pytest-of-factory` and `/tmp/semgrep-mcp`, left by my smoke-test run and `make sast`, was denied. They are lost with the stage.
