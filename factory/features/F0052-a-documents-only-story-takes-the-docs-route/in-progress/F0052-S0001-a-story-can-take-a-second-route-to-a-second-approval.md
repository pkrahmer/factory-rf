---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 572
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T21:46:48.640497Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T21:46:48.647057Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T21:47:12.581520Z'
  stage: intake
  run: 59f0f1b316854d9dbf59911b4476524b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T21:47:18.190209Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T21:50:38.620716Z'
  stage: tests
  run: b8b14106ed4c42e9891876b3876e8fdb
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T21:50:44.049380Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-05T21:55:58.342600Z'
  stage: doing
  run: a66fb417f67a4cb38098e47a20b90b43
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-05T21:56:05.850703Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-05T21:58:04.337013Z'
  stage: review
  run: 5879499a125047de851c981b6352d557
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T21:58:09.608026Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-05T21:58:28.661718Z'
  stage: doing
  run: 7b341a9cffa34e6c9c8b72d47d064693
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T21:58:33.586146Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-05T21:59:48.625000Z'
  stage: tests
  run: b158bac7bfd0435ba78ce325118a9563
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-05T21:59:54.807147Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-05T22:05:13.335393Z'
  stage: doing
  run: db3000ac829a46cb9a795673c2d8522f
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-05T22:05:21.275403Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-05T22:06:09.499874Z'
  stage: review
  run: 1abcaa4340c844799b2cd4be3fb3d7a4
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-05T22:06:14.776990Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-11-05T22:06:43.768243Z'
  stage: docs
  run: 019f040ca4ec4de69eb3e11404686b71
---

# A story can take a second route to a second approval

## Description

F0052 adds a route for documents-only stories: `intake` → `docs-only` → `docs-review` → `docs-approval` → `done` (feature decision 1). The code names no stage, so the factory may already carry a story along it, but nothing proves that it does, and three places are known to depend on the stage order: `is_before_approval` (`factory.work.domain.acceptance`) compares a stage's position with the definition's first approval stage, a close at an approval stage sends the story to that stage's second `next` (`send_back_target`), and that close's round cap is the cap of the first capped stage whose first `next` is that approval stage (`send_back_cap`). This story pins the behaviour with a walk through the fake world, on a pipeline definition written in the test that holds both routes, and fixes whatever the walk finds. It changes no shipped pipeline definition: the human adds the route at S0002's merge.

## Interface

- No new module. Any fix goes where the walk finds the fault, and the coder names it in its entry.
- The test pipeline definition: today's stages of `factory/pipeline.yml`, with `intake.next = [tests, docs-only]` and, after `smoke-test`, the three stages of the feature's *The human's changes* (`docs-only` with `next: [docs-review, tests]`), in that order, then `acceptance`, `approval`, `done`.
- `tests/pipeline/application/test_docs_route.py` (new): the walks of the criteria, in the fake world, with the fake agent runtime giving each role its decision.
- The story's work item lives under `factory/features/<feature>/in-progress/` as any story's does.

## Acceptance criteria

1. A story whose intake decides `docs-only` moves `intake` → `docs-only` → `docs-review` → `docs-approval`, one stage per tick, with one journal entry per stage and the label `stage:<name>` of each stage on its pull request. At `docs-approval` the pull request is handed over (ready for review, the description written), as at `approval`.
2. A merge of that pull request archives the story to `done/` as a merge at `approval` does.
3. A close of that pull request at `docs-approval` sends the story back to `docs-only` (the stage's second `next`), with the send-back's journal entry, and not to `doing`.
4. At `docs-review`, a decision `docs-only` counts one round; a third send-back stops at the round cap of two and asks the human, as at `review`.
5. A story at `docs-only` whose documenter decides `tests` moves to `tests` without a round, then takes today's route `doing` → `review` → `docs` → `smoke-test` → `approval`, and a close there sends it to `doing` (the way back, feature decision 6).
6. A story whose intake decides `tests` still takes today's route to `approval`, unchanged (one walk to `approval`).
7. `is_before_approval` is true for `docs-only` and `docs-review` and false for `docs-approval`, `acceptance` and `approval` in the test definition (one row per stage).
8. A close at `docs-approval` takes its round cap from `docs-review`, the capped stage whose first `next` is `docs-approval` (`send_back_cap`, `factory.work.domain.send_back`): a close that brings the round to two sends the story to `docs-only` and asks nothing, and one that brings it to three still sends it to `docs-only` but blocks it (`send_back`) and asks the human, as a close past the cap at `approval` does (one row per side).
9. `make check` stays green.
10. docs: `docs/project-guide/pipeline.md`, *The pipeline definition*: a definition may hold more than one route and more than one approval stage; a close at an approval stage sends the story to that stage's second `next`. `docs/operator-guide/pipeline.md`: the same, in one sentence for the operator. `docs/decisions.md`: none (the feature's decision 1 goes in at S0002).

## Smoke test

```bash
uv run pytest tests/pipeline/application/test_docs_route.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: no new module by design. It names the one new test file, `tests/pipeline/application/test_docs_route.py`, and the test pipeline definition stage by stage (intake `next`, `docs-only`, `docs-review`, `docs-approval`, their order). It names the two functions the walk exercises in the Description, `is_before_approval` (`factory.work.domain.acceptance:309`) and `send_back_target` (`factory.work.domain.send_back:30`); both exist. Any fix is located by the walk, and the coder names it in its entry.
   - Criteria: 1 to 7 each describe one walk or one table, and each is testable by one test function (7 is one row per stage). Failing sides are covered. The close at `docs-approval` going to `docs-only` and not to `doing` is criterion 3. The round cap is criterion 4, and the round-free move to `tests` is criterion 5. The old route is unchanged in criterion 6. `is_before_approval` is false for the approval stages in criterion 7. The Interface states no rule beyond these. Criteria 8 and 9 are the closing ones, in order.
   - Smoke test: `uv run pytest tests/pipeline/application/test_docs_route.py 2>&1 | tail -1 | grep -c passed` is runnable. It passes no `-q`, and `pyproject.toml` `addopts` already sets one, so the last line is the `N passed` summary. `Expect: 1` can be checked against the output.
   - Architecture: the test sits in `tests/pipeline/application/`, which mirrors the package. It uses the fake world and the fake agent runtime, and git is not faked. A fix would land in the `work` or `pipeline` area. The story makes no new package or dependency and does not touch `factory/pipeline.yml`.
   - Scope: the story is S0001 of F0052 and matches the feature's scope bullet 1. It makes no pipeline definition change (that is the human's at S0002's merge), changes no agent, and does not touch the code route. Nothing in "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: wrote the walks of criteria 1 to 7 in the fake world. They run on a pipeline definition written in the test (`TWO_ROUTES`): the stages, caps, checks and reports of today's `factory/pipeline.yml`, `intake.next = [tests, docs-only]`, and after `smoke-test` the three stages from the feature's *The human's changes*. That puts `docs-only`, `docs-review` and `docs-approval` before `acceptance`, `approval` and `done`. The test pushes the definition to `main` with a Makefile that has every target the definition names, then starts the story.

   - criterion 1: tests/pipeline/application/test_docs_route.py::test_an_intake_decision_docs_only_walks_the_docs_route_to_a_hand_over_at_docs_approval
   - criterion 2: tests/pipeline/application/test_docs_route.py::test_a_merge_at_docs_approval_archives_the_story_to_done
   - criterion 3: tests/pipeline/application/test_docs_route.py::test_a_close_at_docs_approval_sends_the_story_back_to_docs_only
   - criterion 4: tests/pipeline/application/test_docs_route.py::test_a_send_back_at_docs_review_counts_a_round_and_the_third_asks_the_human (rows: first send-back, second at the cap, third past the cap)
   - criterion 5: tests/pipeline/application/test_docs_route.py::test_a_documenter_decision_tests_takes_the_code_route_whose_close_sends_back_to_doing
   - criterion 6: tests/pipeline/application/test_docs_route.py::test_an_intake_decision_tests_still_takes_todays_route_to_approval
   - criterion 7: tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval (one row per stage)

   How I read the criteria:
   - Criterion 1's "one journal entry per stage" is checked as one `result` record each for intake, docs-only and docs-review. No agent runs at docs-approval.
   - The hand-over is checked by `handed_over == "docs-approval"`, the pull request no longer a draft, and its description ending with `HAND_OVER_CLOSING`.
   - For criteria 3 and 5, the human comments before the close, so the send-back has a reason and asks no question.

   Files created: tests/pipeline/application/test_docs_route.py. No earlier test file was changed.

   Result of the one run (`uv run pytest -q tests/pipeline/application/test_docs_route.py`): 13 passed. Every module imported, and nothing failed. The walk found no fault in today's code, so there are no red tests on this branch: the story's "fixes whatever the walk finds" comes down to nothing to fix, and the coder has only to confirm `make check`. Two lint-only edits came after that run: a line split, and the parametrized test's case values made keyword-only. `make lint` is green. The type check was skipped, as this stage says.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: Ran `make check` on the tester's commit: `check: green`, with `test: green (141.1 s)` and total coverage at 99.26 %. `tests/pipeline/application/test_docs_route.py` was already green before I did anything, so there were no failing tests to work from. I changed no code and wrote no files. The working tree is clean apart from the factory's own files.

   - What I built: nothing. In the fake world, all the walks pass against today's code on the `TWO_ROUTES` definition: the docs route to a hand-over at `docs-approval`, the merge to `done/`, the close back to `docs-only`, the round cap at `docs-review`, the way back through `tests`, the unchanged code route, and the `is_before_approval` table. Nothing failed, so there was no fault to locate and no fix to name, as the Interface says.
   - Main decision: leave `is_before_approval` (`factory.work.domain.acceptance`) and `send_back_target` (`factory.work.domain.send_back`) as they are. I rejected guarding them against other stage orders: no failing test asks for it, it is beyond the description, and it would be a new story (R13).
   - Refactor: no diff, so nothing to refactor.
   - Description: no journal entry changed the meaning of the task, so I left it as it is.
   - Noticed but did not touch: the docs criterion (criterion 9) is still open for the docs stage.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 40 known, 3 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`. The only file it adds is `tests/pipeline/application/test_docs_route.py`, and nothing under `src/` changes. I read the test against criteria 1 to 7. I also read `is_before_approval` (`src/factory/work/domain/acceptance.py:309`), `send_back_target` and `send_back_cap` (`src/factory/work/domain/send_back.py:30`, `:38`), and `ClosedHandler._send_back` (`src/factory/pipeline/application/handlers/closed.py:72`).

   Group 1, criteria: each of criteria 1 to 7 has a test that checks what the criterion says. Criterion 4 checks both sides of its cap: round 2 at the cap passes, round 3 is blocked with `round_cap`. Criterion 7 has one row per stage. The coder's `make check` was green (entry 7). Gap: a close at an approval stage takes its round cap from `send_back_cap`, which also depends on the stage order, and on this route it resolves to `docs-review`. No criterion names it, and no test closes past the cap at `docs-approval`. Pinning it needs no change under `src/`, so I added it as a criterion myself.

   Groups 2 and 3, architecture and security: nothing found. The test uses the fake world and a real git remote. It adds no secrets, no nosec, nosemgrep or baseline markers, and no shell built from strings.

   Group 4, quality: two points in the new test file, listed below.

   Group 5, work item hygiene: the coder's journal explains why nothing was fixed and what it decided not to guard against. Criterion 10 (the docs criterion) still describes what the reader must know.

   1. criterion 8 added: it needs its test. `## Acceptance criteria` 8, a close at `docs-approval` past the round cap of `docs-review`: one row at round two (sent to `docs-only`, nothing asked) and one at round three (sent to `docs-only`, blocked `send_back`, a question). Write them as rows of one parametrized test in `tests/pipeline/application/test_docs_route.py`. The closing criteria are now 9 and 10.
   2. `tests/pipeline/application/test_docs_route.py:63`: the `# noqa: E501` silences ruff for the whole `TWO_ROUTES` literal, and it is the only such marker on a test's own code. The marker can go: drop `time_limit`/`lease_duration` from the roles, as `PIPELINE_YAML` in `tests/support/git_support.py:21` does, or break the long `acceptance-reviewer` flow mapping over several lines.
   3. `tests/pipeline/application/test_docs_route.py:271`: `test_only_the_docs_routes_working_stages_lie_before_the_approval` takes the `two_routes` fixture, which pushes a pipeline definition and a Makefile to `main` for every row. The test only parses the `TWO_ROUTES` text, so taking `world` (or a `RuamelPipelineDefinitionReader()`) is enough.

   description corrected: "two places are known to depend on the stage order: `is_before_approval` … and … `send_back_target`" -> "three places …: `is_before_approval` …, `send_back_target`, and that close's round cap is the cap of the first capped stage whose first `next` is that approval stage (`send_back_cap`)".

   Earlier tests: none. The diff only adds `tests/pipeline/application/test_docs_route.py` (status `A`) and changes no test file that `main` already holds.
10. factory: started doing as vm.
11. coder: Round 1. All three of the reviewer's findings in entry 9 are changes to `tests/pipeline/application/test_docs_route.py`, and the coder never edits tests (R9), so I changed no code and wrote no files. The work goes to the tester.

    - **Criterion 8 needs its test.** A close at `docs-approval` takes its round cap from `docs-review` (`send_back_cap`, `factory.work.domain.send_back`). It needs one parametrized test with two rows:
      - round two: the story goes back to `docs-only` and no question is asked;
      - round three: the story goes back to `docs-only`, is blocked with `send_back`, and a question is asked.
      The reviewer's reading says this needs no change under `src/`.
    - **Remove the `# noqa: E501` at `test_docs_route.py:63`.** Make the `TWO_ROUTES` literal fit within the line length instead. Either drop the roles' `time_limit` and `lease_duration`, as `PIPELINE_YAML` in `tests/support/git_support.py` does, or break the long `acceptance-reviewer` flow mapping over several lines.
    - **Change the fixture at `test_docs_route.py:271`.** `test_only_the_docs_routes_working_stages_lie_before_the_approval` should take `world`, or a `RuamelPipelineDefinitionReader()`, instead of the `two_routes` fixture. It only parses the `TWO_ROUTES` text, and `two_routes` pushes a definition and a Makefile to `main` for every row.

    Description: the reviewer already updated it to name three order-dependent places (`send_back_cap` is the third) and added criterion 8. That makes the closing criteria 9 and 10, so there is nothing left for me to rewrite. Once the tester has made these changes, the next doing round runs `make check` on the new test. If the round-three row fails, the fix goes in `send_back_cap` or `ClosedHandler._send_back` (`src/factory/pipeline/application/handlers/closed.py`).
12. factory: started tests as vm.
13. tester: Round 1, approved test change. I made the three changes to `tests/pipeline/application/test_docs_route.py` that the coder listed in entry 11, from the reviewer's findings in entry 9. No other test file changed and I created no files.

    - **Criterion 8:** added `test_a_close_at_docs_approval_takes_the_round_cap_of_docs_review`, a parametrized test with two rows:
      - `second-at-the-cap`: two closes leave the story at `docs-only`, round 2, not blocked, with no `send_back` question posted.
      - `third-past-the-cap`: three closes leave it at `docs-only`, round 3, blocked `send_back`, with one `send_back` question posted.
      - Each close has a human comment as its reason. Between closes the story walks `docs-only` → `docs-review` → `docs-approval` and is handed over again. One extra tick after the last close lets the ask handler post the question.
    - **`# noqa: E501` removed:** `TWO_ROUTES` now fits the line length because two lines are written in block style instead of flow style: the `acceptance-reviewer` role and the `docs` stage, which was also too long. Its content is the same.
    - **Fixture change:** `test_only_the_docs_routes_working_stages_lie_before_the_approval` now takes `world` instead of `two_routes`, so its rows no longer push to `main`.

    The criterion → test map is otherwise unchanged from entry 5; criterion 8 maps to `tests/pipeline/application/test_docs_route.py::test_a_close_at_docs_approval_takes_the_round_cap_of_docs_review`.

    The one run (`uv run pytest -q tests/pipeline/application/test_docs_route.py`) passed all 15 tests and every module imported. The cap at `docs-approval` already behaves as criterion 8 says, so the branch still has no red test. A line-length fix came after that run, and I checked it with a second run, which also passed. `make lint`: lint: green (0.1 s). I skipped the type check, as this stage says.

    `lint`: lint: green (0.1 s)
14. factory: started doing as vm.
15. coder: Round 1: I checked the tester's changes from entry 13 and changed no code. `make check` passed on the committed state (`check: green`, `test: green (132.7 s)`, coverage 99.26 %). Before I started, `git status --short` showed no changes in the working tree.

    - **What I built:** nothing. All 15 tests in `tests/pipeline/application/test_docs_route.py` pass against today's code, including the new criterion 8 rows `second-at-the-cap` and `third-past-the-cap`. On the `TWO_ROUTES` definition, `send_back_cap` (`factory.work.domain.send_back`) already takes the cap from `docs-review`, and `ClosedHandler._send_back` (`src/factory/pipeline/application/handlers/closed.py`) already blocks a close past that cap with `send_back`. The walk found no fault, so there is no fix to name.
    - **Main decision:** I left `is_before_approval`, `send_back_target` and `send_back_cap` unchanged. I decided against guarding them against other stage orders: no test asks for it, and it goes beyond the description (R13).
    - **Reviewer's findings from entry 9:** all three were test changes, and the tester made them in entry 13. None of them needed code.
    - **Refactor:** my diff is empty, so there was nothing to refactor.
    - **Description:** the reviewer had already rewritten it, naming `send_back_cap` and adding criterion 8. Nothing else in the journal changes what the task means.
    - **Noticed but did not touch:** the docs criterion (10) is still open for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
16. factory: started review as vm.
17. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`. The diff adds one file, `tests/pipeline/application/test_docs_route.py`, and changes nothing under `src/`. I read the test against criteria 1 to 8 and the Interface. I also read the code the walks exercise: `is_before_approval` (`src/factory/work/domain/acceptance.py:309`), `send_back_target` and `send_back_cap` (`src/factory/work/domain/send_back.py:30`, `:38`), and the use of `send_back_cap` in `ClosedHandler._send_back` (`src/factory/pipeline/application/handlers/closed.py:78`).

    Group 1, criteria. Each of criteria 1 to 8 has a test, and each test checks what its criterion says:
    - Criterion 1 checks the `stage:<name>` labels, one `result` record each for intake, docs-only and docs-review, and the hand-over (`handed_over`, not a draft, the closing line of the description).
    - Criterion 3 checks the target `docs-only` and the text of the send-back entry.
    - Criterion 4 has rows on both sides of the cap of two (rounds 1, 2 and 3; the third is blocked `round_cap` and asks).
    - Criterion 5 checks `round == 0` after the move to `tests`, and that the close at `approval` sends the story to `doing`.
    - Criterion 7 has one row per stage.
    - Criterion 8 has two rows of one parametrized test: round 2 is not blocked and asks nothing, round 3 is blocked `send_back` and asks. `send_back_cap` only looks at stages whose `next[0]` is the approval, so in this definition the cap can only come from `docs-review`.
    - The test definition `TWO_ROUTES` matches the Interface: `intake.next = [tests, docs-only]`, `docs-only` with `next: [docs-review, tests]`, and the three new stages after `smoke-test` and before `acceptance`, `approval`, `done`.
    - The coder's `make check` was green (entry 15: `check: green`, coverage 99.26 %).

    Groups 2 and 3, architecture and security: nothing found. The test uses the fake world and a real git remote, and lives where the package layout says. Entry 9's `# noqa: E501` is gone, and the diff adds no other suppression marker, secret or shell string.

    Group 4, quality: nothing under `src/`. The test file is new, so the points on it below are notes.

    Group 5, work item hygiene:
    - The coder's entries 7 and 15 explain the main decision (the walks found no fault, so no code changed) and what was rejected (guarding the three functions against other stage orders, which goes beyond the description).
    - The Description, as corrected in entry 9, matches what was built.
    - Docs criterion 10 still says what the reader must know. `docs/project-guide/pipeline.md` already describes `send_back_cap`, so criterion 8 needs no extra docs.

    no findings

    Notes:
    1. `tests/pipeline/application/test_docs_route.py:249`: `state = head_state(two_routes, story)` is a dead assignment. Every row has `send_backs >= 1`, so the loop always overwrites it; it could go.
    2. `tests/pipeline/application/test_docs_route.py:151`: the criterion 1 test repeats the three steps of `_walk_docs_route` inline so that it can record each stage and label. A `_walk_docs_route` that returns the states it reached would serve both.

    Earlier tests: none. The diff only adds `tests/pipeline/application/test_docs_route.py` (status `A`) and changes no test file that `main` already holds.
18. factory: started docs as vm.
19. documenter: Docs round for the criterion 10 text. I changed two files, both documents, so I did not run `make check` (the factory's checks decide).

    Files changed:
    - `docs/project-guide/pipeline.md`: added the paragraph "More than one route, more than one approval stage" after the stage/role description in *The pipeline definition*. It says a definition may hold several routes and several approval stages. A close at an approval stage goes to that stage's second `next` (`send_back_target`). The round cap comes from the first capped stage whose `next[0]` is that approval (`send_back_cap`). `is_before_approval` compares against the first approval stage in `stages`. It points to `tests/pipeline/application/test_docs_route.py`.
    - `docs/operator-guide/pipeline.md`: one sentence on the same rule for the operator, before the paragraph on the template's smoke test.

    I read the diff (only the new test file; nothing under `src/` changed). I read `is_before_approval`, `send_back_target` and `send_back_cap` and checked each sentence against them. The walks found no fault, so I have no findings for the coder.

    Cross-read and found current: `docs/project-guide/pipeline.md` (the close/send-back sections, "A close at the approval sends the story back", which already describes `send_back_cap` as the first capped stage with `next[0]` equal to the approval) and `docs/operator-guide/pipeline.md`.

    `docs/decisions.md`: no change, as the criterion says (feature decision 1 goes in at S0002). I wrote no "Why" or "Rejected" line.

    Stale text I noticed and did not touch: none that is unrelated to this story.

    `check`: check: green (not run again: passed on tree 5cb5ca321340 at 2026-11-05T22:02:38Z)
    `secrets`: secrets: green (0.7 s)
    `documents`: documents ok
