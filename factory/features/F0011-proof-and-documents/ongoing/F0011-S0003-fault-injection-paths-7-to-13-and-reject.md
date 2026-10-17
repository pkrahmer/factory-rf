---
stage: review
pr: 147
blocked: null
comments_seen: 4
round: 1
attempts: 0
---
# Fault-injection paths 7 to 13, and reject walked

## Assignment (as of log entry 1)

Walk the last seven of v1's thirteen fault-injection paths with an injection test each, `reject` (path 9) walked with the kill that v1 never ran live, and complete `FAULT_PATHS` with its rows 7 to 13. The paths are behaviour paths (a cap, a retry, a hand edit, two work items, a close, a feature acceptance, a test change), none of them a kill point, and v1.1 keeps every mechanism they exercise, so no path is mapped to a removing item: each is a named test that runs the path against a real local bare remote, the fake hosting client and the fake agent runtime, with one kill or one stall added at the step the path adds, using the cases and helpers of F0011-S0001 and F0011-S0002. The story appends rows to `FAULT_PATHS` of F0011-S0002 and leaves its first six rows as they are. It covers WE1.2 and WE1.3 and keeps kept thing 21 (every run is a fault-injection run, root causes recorded) and kept thing 13. A path that fails is a defect to fix under `src/`, never a test to bend.

## Interface

`src/factory/domain/fault_paths.py` (F0011-S0002 creates it; this story appends seven rows to `FAULT_PATHS` and changes nothing else)

The rows of this story, after the six of F0011-S0002, in number order. `case` is the id of the `KillPointCase` of F0011-S0001 whose kill point the path's test arms (path 8 uses `agent-run-dies`, whose stall is a scripted result, not an armed point); the path's own crash charge may differ from the case's `charges_crash` (path 9 arms `BEFORE_PUSH` before a handler's push, which charges no crash; path 11 arms `AFTER_PUSH` after a handler's push). `test` is the name of the test function in `tests/test_fault_paths_7_to_13.py`; each row's `test` is at most 90 characters, a property of the rows that criterion 11 checks, not a validation of `FaultPath`. No `test` contains the word `retrying`: `tests/test_retrying_wording.py` refuses it in any string under `src/factory` outside the post texts.

| number | title | case | test |
|---|---|---|---|
| 7 | the round cap | `post-record` | `test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` |
| 8 | the attempts cap and its retry | `agent-run-dies` | `test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment` |
| 9 | `reject` after a stage change by hand | `commit-push` | `test_reject_killed_before_push_reverts_once_and_leaves_main_clean` |
| 10 | two work items in progress | `tick-other` | `test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits` |
| 11 | a close at the approval | `tick-other` | `test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once` |
| 12 | a feature acceptance refused, or merged | `container` | `test_acceptance_container_lost_in_review_reruns_once_and_books_result` |
| 13 | a test change the human approves | `agent-run-tick` | `test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round` |

`tests/proof_support.py` gains one helper (the rest is F0011-S0001's and F0011-S0002's):

```python
def work_item_file(world: World, work_item: WorkItemId) -> str: ...
```

- `work_item_file` is the path of the work item's file on `origin/<branch>`: the one `.md` file of `Git.list_files("origin/<branch>", "factory/features/F0001-example/in-progress")` whose name starts with the work item's id.

How the paths treat the numbers of the pipeline fixture: `round_cap` is 3 at `review`, `docs` and `smoke-test`; `attempts_cap` is 2; `ERROR_CAP` is 3. In every path test the clock is advanced by `KILL_TO_RERUN` between a kill and the restart; "the restarted runtime" is the `agent_runtime` of the world returned by `restart`; "the pull request" is `pull_request_of(world, work_item)`; the work item is the one `start_story` returned; a run queued for a tick that is said to raise at `AGENT_RUN` carries `kill=True`.

Tests: `tests/domain/test_fault_paths_all_rows.py` (criterion 9); `tests/test_fault_paths_table.py` (criteria 10 and 11); `tests/test_fault_paths_7_to_13.py` (criteria 1 to 8, one test function per path named as in the table, path 12 parametrized over `refused` and `accepted`); the helpers are in `tests/proof_support.py`.

## Acceptance criteria

1. Path 7 (round cap 3): `drive_to(world, work_item, "review")`; arm `AFTER_POST`; repeat one tick with queued `completed("doing", "Finding.")` at `review` and one with queued `completed("review", "Fixed.")` at `doing`. After the third send-back `round == 3` and no post of kind `round_cap` exists; the fourth send-back asks, and the tick that posts that question raises `InjectedKill` (at most 12 ticks in all). After `restart` (clock advanced 5 seconds, nothing queued) and three ticks, exactly one post of kind `round_cap` exists, `blocked == "round_cap"`, and the restarted runtime has received no request.
2. Path 8 (attempts cap 2): `start_story`; queue `died()`, `died()`. After the first tick `attempts == 1` and the post of kind `stall` contains the word `retrying` (any case); after the second tick `attempts == 2`, the post of kind `stall` made in that tick does not contain `retrying` and no post of kind `attempts_cap` exists (the `ask` handler records and posts the question on the next tick); after the third tick `blocked == "attempts_cap"` and exactly one post of kind `attempts_cap` exists; two more ticks add no request and no post. Then `hosting.add_human_comment(number, "Retry.")`, queue `completed("question", "Which format does the title take?")` and run three ticks: `attempts == 0` and the runtime has received a third request.
3. Path 9, the revert: `drive_to(world, work_item, "tests")`; `human.push_file` the work item's file (`work_item_file`) on its branch with its text on `origin/<branch>` changed to `stage: review` (not in the `next` of `tests`); arm `BEFORE_PUSH` with `after=0`; the first tick raises during the correction's push; advance 5 seconds; `restart`; queue `completed("question", "Which test?")`; three ticks. The journal holds exactly one record of kind `move_back`, the stage on `origin/<branch>` is `tests`, and exactly one post of kind `correction` exists (`test_reject_killed_before_push_reverts_once_and_leaves_main_clean`, first half).
4. Path 9, the main branch: in the same scenario `origin/main` points at the commit it pointed at before the hand push, and `checkout.status().changes` is empty right after the kill, before `restart` (the killed `reject` leaves nothing dirty; GH3.5).
5. Path 10: two stories started with `start_story` before the first tick (the second returns the higher id); arm `AFTER_PUSH` with `after=0`; the first tick raises after the claim of the lower id is pushed; advance 5 seconds; `restart`; queue `completed("question", "Which format does the title take?")`; three ticks. The lower id has `blocked == "question"` and `crashes == 1`; the restarted runtime has received exactly one request; the higher id has no branch on the remote (`Git.resolve("origin/work-item/<higher id>")` is `None`).
6. Path 11: `drive_to(world, work_item, "approval")`; `hosting.close_by_human(number)` with no comment; arm `AFTER_PUSH` with `after=0`; the first tick raises after the close is recorded and pushed; advance 5 seconds; `restart`; three ticks. The journal holds exactly one record of kind `close`; the pull request is `open` and a draft; exactly one post of kind `send_back` exists; `blocked == "send_back"`.
7. Path 12, parametrized over `refused` and `accepted`: `drive_to(world, work_item, "approval")`; `human.merge(branch, "merge")` and `hosting.merge_by_human(number, merge_commit)`; ticks (at most 6) until `origin/work-item/F0001-A0001` (the branch of the feature's acceptance) exists and its state has no claim; arm `AGENT_RUN` and queue `completed("approval", "Recommendation: accepted.", kill=True)`; the next tick raises `InjectedKill`; advance 5 seconds; `restart(world, empty_disk=True)`; queue the same run without `kill`; three ticks. The restarted runtime has received exactly one request; the acceptance's pull request is ready for review; then `hosting.close_by_human(acceptance_number)` (`refused`) or `hosting.merge_by_human(...)` after `human.merge` (`accepted`) and three ticks: the acceptance, read from `origin/main`, is under `done/` and its state has `outcome == "refused"` or `"accepted"`; `repeated_posts` is empty.
8. Path 13: `drive_to(world, work_item, "doing")`; queue `completed("question", "Test T contradicts criterion 3. Change it?")`; two ticks (the question is recorded on the first and posted on the second) and exactly one post of kind `question` exists; only then `hosting.add_human_comment(number, "(a) the tester fixes the test.")`; queue `completed("tests", "Change test T: expect 3, not 2.")`; ticks (at most 4) until the stage is `tests`; arm `AGENT_RUN`; queue `completed("doing", "Changed test T.", writes=leak_writes(world, work_item), kill=True)`; the tick raises; advance 5 seconds; `restart`; queue `completed("doing", "Changed test T.")`; one tick (the rerun of the tester's stage; a further tick would start the coder's stage with nothing queued). The stage is `doing`, `round == 0` (the move from `doing` to `tests` counts no round) and `attempts == 0`; the restarted runtime has received exactly one request; `MARKER` is in no commit's `src/leak.py`.
9. `FAULT_PATHS` holds exactly thirteen rows in number order: the six rows of F0011-S0002 unchanged, then the seven rows of the table above, with those numbers, titles, cases and tests.
10. Every `test` of `FAULT_PATHS` is the name of a function in `tests/test_fault_paths.py` or in `tests/test_fault_paths_7_to_13.py`, and no name is the name of a function in both.
11. Every `test` of `FAULT_PATHS` is at most 90 characters long (its `def` line must fit ruff's line length of 100).
12. make check stays green.
13. docs: `docs/project-guide.md` adds to its section *Fault-injection paths* the table rows of paths 7 to 13 (number, title, case, test as `` `test_...` ``), so that the table holds one row per path; `docs/decisions.md` records that the paths 7 to 13 are walked with one kill or one stall each, by judgment, and that path 9 walks `reject` with the kill between commit and push. README and operator guide are untouched.

## Demo

```bash
uv run python -c "
from factory.domain.fault_paths import FAULT_PATHS
from factory.domain.kill_point_cases import KILL_POINT_CASES
ids = {c.id for c in KILL_POINT_CASES}
print(len(FAULT_PATHS), [p.number for p in FAULT_PATHS] == list(range(1, 14)), all(p.case in ids for p in FAULT_PATHS))
print(FAULT_PATHS[8].test)
"
```
Expect: `13 True True`, then the line `test_reject_killed_before_push_reverts_once_and_leaves_main_clean`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_fault_paths_7_to_13.py tests/test_fault_paths_table.py tests/domain/test_fault_paths_all_rows.py
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names `src/factory/domain/fault_paths.py` (exists, from F0011-S0002) and one helper, `work_item_file(world, work_item) -> str`, with its behaviour stated. The seven rows are given with number, title, case and test. The helpers the criteria use (`drive_to`, `completed`, `died`, `restart`, `leak_writes`, `pull_request_of`, `repeated_posts`, `start_story`, `MARKER`, `KILL_TO_RERUN`) exist in `tests/proof_support.py`.
   - Criteria: each of 1 to 8 is one scenario test named in the table. Each gives the exact ticks, kills, advances and assertions, so no further decision is left. Each rule has its failing side:
     - The round cap is tested on both sides: no `round_cap` post after the third send-back, one after the fourth.
     - The attempts cap is tested on both sides: `retrying` appears in the stall post of the first tick and not in that of the second.
     - The reject revert is tested twice: the journal and stage in criterion 3, and `main` clean in criterion 4.
     - Criterion 11 gives the 90-character limit on the test names, and criterion 10 the unique-name rule.
   - Demo: both commands are runnable. Each `Expect:` line is checkable: `13 True True` and the named test line for the first, and `passed` with no `failed` or `error` for the second.
   - Architecture: tests plus appended domain data rows in `factory.domain`, with no I/O. The `test_retrying_wording` constraint is respected.
   - Scope: matches the feature's scope (the thirteen paths, one kill or stall each, `reject` walked). The first six rows stay as they are, and the docs criterion touches only the project guide and the decision log.
3. tester: wrote the tests for criteria 1–11. Criterion 12 is the gate and criterion 13 belongs to docs.

   Mapping:
   - criterion 1: tests/test_fault_paths_7_to_13.py::test_round_cap_question_killed_between_post_and_record_posts_once_and_waits
   - criterion 2: tests/test_fault_paths_7_to_13.py::test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment
   - criteria 3 and 4: tests/test_fault_paths_7_to_13.py::test_reject_killed_before_push_reverts_once_and_leaves_main_clean. It reads `status().changes` right after the kill and checks `origin/main` against the commit before the hand push once the rerun is over. The hand move uses the reader and writer to set `stage: review`.
   - criterion 5: tests/test_fault_paths_7_to_13.py::test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits
   - criterion 6: tests/test_fault_paths_7_to_13.py::test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once
   - criterion 7: tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused|accepted]. The booked acceptance is found as the one file of `<feature>/done` on `origin/main` whose name starts with `F0001-A0001`.
   - criterion 8: tests/test_fault_paths_7_to_13.py::test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round
   - criterion 9: tests/domain/test_fault_paths_all_rows.py::test_the_paths_are_the_six_first_rows_then_the_seven_last_in_number_order. It checks number, title and case of the first six rows; their test names are already pinned by tests/domain/test_fault_paths.py.
   - criterion 10: tests/test_fault_paths_table.py::test_every_path_test_is_a_function_of_exactly_one_path_module
   - criterion 11: tests/test_fault_paths_table.py::test_every_path_test_name_is_at_most_ninety_characters

   Files: created tests/test_fault_paths_7_to_13.py, tests/test_fault_paths_table.py and tests/domain/test_fault_paths_all_rows.py. In tests/proof_support.py I added `work_item_file(world, work_item)` as the Interface describes it.

   Imports: every module imported. Nothing is missing, because `FAULT_PATHS` and the helpers already exist.

   The one `make test` run (`tail -5`) was taken before I made path 9 a plain test function. It showed these red:
   - the all-rows test, as intended: rows 7–13 are missing.
   - both cases of path 12.
   - path 9, as an ERROR. At that time its setup was a fixture, so a missing `InjectedKill` or a failing step showed up as a setup error. I then folded the fixture into the test, so it now reports as a failure.

   Paths 7, 8, 10, 11 and 13 and the table tests did not show in that tail. They may already pass, since the mechanisms exist. The tail does not show why path 9 or path 12 fails. The coder should read those failures first and treat them as defects under src/, per the Assignment. If one turns out to be a wrong test, end with a question.

   `make lint` is green; I ran ruff format on the new files. I did not run the type check (skipped in this stage).

   Rejected:
   - testing the two sides of the 90-character limit on made-up names. The criterion is a property of the rows, not a validation of `FaultPath`.
   - checking that the two path modules share no function at all. Both define the `world` fixture, so the check covers only the path test names, as the criterion says.

   Open: tests/test_fault_path_names.py (from F0011-S0002) still checks only the first six rows. I left it alone because it is not my test.

   `make lint`: lint: green
   `make test`: FAILED tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result[accepted]
4. coder: two tests pick the wrong file, and I can't fix them myself (R9). Rows 7 to 13 are added. The tests for criteria 3, 4 and 7 still fail, so `make check` is red, and the cause is in the tests, not in `src/`.

   Done: appended the seven rows of the Interface table to `FAULT_PATHS` in `src/factory/domain/fault_paths.py`. The first six rows are unchanged. Commit e6207f4. ruff and mypy pass on that file.

   The defect: the work item's cost-record sidecar sits beside it. That file is `<work item>.costs.jsonl` (`COST_RECORDS_SUFFIX`, `cost_records_path`; project guide, *Identity, order and places of work items*). It moves with the work item into `done/` (operator guide). By the time a work item reaches `tests` or `approval`, its folder holds both `F0001-S0001-first.md` and `F0001-S0001-first.costs.jsonl`. Two selections that expect exactly one match therefore fail with `ValueError: too many values to unpack (expected 1)`:
   - `tests/proof_support.py::work_item_file` (path 9, criteria 3 and 4). It takes "the one file whose name starts with the work item's id", but there are two.
   - `tests/test_fault_paths_7_to_13.py::_booked`, line 236 (path 12, both cases). It takes the one file in `done/` on `origin/main` whose name starts with `F0001-A0001`, and that matches the acceptance and its `.costs.jsonl`.

   Evidence: I narrowed both selections to paths ending in `.md`, but only in the working tree, and then restored the tests byte for byte. With that change all 11 tests of the three new modules pass, including paths 9 and 12. So `src/` needs no further fix.

   Options:
   (a) The tester narrows both selections to the work item's Markdown file, either by requiring `.md` or by excluding `COST_RECORDS_SUFFIX`. The Interface's sentence for `work_item_file` then reads "the one `.md` file … whose name starts with the work item's id". Recommended.
   (b) Change `src/` so that no sidecar sits beside the work item. That contradicts the recorded cost-record design, and I reject it.

   I would choose (a). On that answer I end with `tests` and name the two changes.

   Refactor: nothing to refactor; the diff is seven data rows.
   Not touched: `tests/test_fault_path_names.py` still checks only the first six rows (the tester noted this too).
5. human (pull request comment, 2026-10-17): (a). The tester narrows both selections to the work item's Markdown file: `tests/proof_support.py::work_item_file` and `tests/test_fault_paths_7_to_13.py::_booked` take the one `.md` file whose name starts with the id, so the `.costs.jsonl` sidecar is not counted; `src/` stays. The Interface's sentence for `work_item_file` reads "the one `.md` file … whose name starts with the work item's id".
6. coder: the human answered (a), so this goes back to the tester for two test changes. `src/` stays as it is.

   Test changes for the tester: in `tests/proof_support.py::work_item_file` and `tests/test_fault_paths_7_to_13.py::_booked`, select only the one file whose name starts with the id and ends in `.md`. That way the `.costs.jsonl` sidecar no longer makes the match ambiguous.

   Ticket: I changed the Interface sentence for `work_item_file` to read "the one `.md` file of `Git.list_files(...)` whose name starts with the work item's id", as the human stated. The Assignment's meaning is unchanged, so I did not rewrite it.

   State: rows 7 to 13 are already in `src/factory/domain/fault_paths.py` (commit e6207f4). Last round I tried the `.md` narrowing in the working tree only and restored the tests afterwards. With it, all 11 tests of the three new modules passed. After the tester's change I expect `make check` to be green with no further change under `src/`.

   Still open: `tests/test_fault_path_names.py` checks only the first six rows. I have not touched it.
7. tester: tester (approved test change): I made the change the human approved in entry 5 and the coder named in entry 6. Each selection now takes only the work item's Markdown file, so the `.costs.jsonl` sidecar no longer makes the match ambiguous. Nothing under `src/` changed.

   Changed:
   - `tests/proof_support.py::work_item_file`: it now selects the one path whose name starts with the work item's id and ends in `.md`. I updated the docstring to say "`.md` file" and shortened "the example feature's" to "the feature's" so the line stays within the line-length limit.
   - `tests/test_fault_paths_7_to_13.py::_booked`: it now selects the one path in `done/` on `origin/main` whose name starts with the acceptance id and ends in `.md`.

   I ran ruff format on both files.

   `make test`: green, with total coverage at 99.55 %. Paths 9 and 12 now pass.
   `make lint`: green.

   Still open: `tests/test_fault_path_names.py` still checks only the first six rows. That change was not approved, so I left the file alone.

   `make lint`: lint: green
   `make test`: test: green
8. coder: `make check` is green, with total coverage at 99.55 %. The tester's change from entry 7 fixed both failing selections. Each now takes only the `.md` file, so the cost sidecar no longer makes them ambiguous. This round needed no new code under `src/`.

   Built: in `src/factory/domain/fault_paths.py`, seven rows (paths 7 to 13) added to `FAULT_PATHS` after the first six, with number, title, case and test as the Interface table gives them (commit e6207f4). The first six rows are unchanged.

   Design: the paths are behaviour paths whose mechanisms v1.1 already has. So all eleven tests of the three new modules pass on the existing code, with no defect to fix under `src/`. I rejected changing `src/` so that no cost sidecar sits beside the work item. That would contradict the recorded cost-record design, and the human chose (a) in entry 5.

   Refactor: nothing to change. The diff under `src/` is seven data rows.

   Noticed, not touched: `tests/test_fault_path_names.py` (from F0011-S0002) still checks only the first six rows. It is not my test. Criterion 13 (the project guide's rows 7 to 13 and the decision-log entry) is for the docs stage.

   `make check`: check: green
9. reviewer: groups 1 to 3 pass. Group 4 (quality) fails: the new test module copies a shared fixture and helpers that already exist.

   Groups 1 to 3:
   - Criteria 1 to 11 each have a test that checks what the criterion says: the ticks, the kills, the advances by `KILL_TO_RERUN` and the assertions.
   - The coder's entry 8 reports `make check` green.
   - The diff under `src/` is the seven data rows in `src/factory/domain/fault_paths.py`. They match the Interface table, and the first six rows are unchanged.
   - The `CLAUDE.md` and `docs/runs/` changes on the branch are the human's own commits, not the pipeline's.

   Findings:
   1. `tests/test_fault_paths_7_to_13.py:43-45`: the `world` fixture is a copy of the shared `world` fixture in `tests/conftest.py:123-126` and shadows it (`CLAUDE.md` Tests: shared fixtures live in `tests/conftest.py`). Fix: delete the module's fixture and use the one in conftest.
   2. `tests/test_fault_paths_7_to_13.py:53-55`: `_rerun` (advance by `KILL_TO_RERUN`, then `restart`) is a second copy of `_rerun` in `tests/test_fault_paths.py:48-50`. `CLAUDE.md` counts a second copy of an existing helper as a finding. Fix: make it one public helper in `tests/proof_support.py`, for example `rerun(world, *, empty_disk=False) -> World` with a docstring, and call it from the new module.
   3. `tests/test_fault_paths_7_to_13.py:48-50`: the `work_item` fixture is a second copy of the one in `tests/test_fault_paths.py:43-45` (`CLAUDE.md` Tests: setup that several tests share is a fixture). Fix: put it once in `tests/conftest.py` beside `world` and use it from the new module.

   Routing: all three fixes are in the tester's own files, plus a new shared helper or fixture. The coder cannot edit tests (R9), so the coder must send them to the tester through the route R9 allows. Removing the old copies in `tests/test_fault_paths.py` (F0011-S0002's tests) is not part of these findings, because that needs the human's yes.

   Not judged: group 5, ticket hygiene, because the review stops at the first failing group.
10. coder: the reviewer's three findings (entry 9) are all about test code. I can't make those changes myself (R9), so I need your answer before the tester can make them. `src/` needs no change.

    I checked the findings against the code and all three are real duplicates:
    1. `tests/test_fault_paths_7_to_13.py:42-45`: the module's `world` fixture repeats `tests/conftest.py:123-126` and hides it.
    2. `tests/test_fault_paths_7_to_13.py:53-55`: `_rerun` repeats `tests/test_fault_paths.py:48-50`. The only difference is an extra `empty_disk` parameter.
    3. `tests/test_fault_paths_7_to_13.py:47-50`: the `work_item` fixture repeats `tests/test_fault_paths.py:43-45`.

    Question: may the tester make these test changes?
    (a) In `tests/test_fault_paths_7_to_13.py`, delete the module's `world` fixture so the one in conftest is used. Move the `work_item` fixture (`start_story(world)`) into `tests/conftest.py` beside `world`, with a docstring, and delete the module's copy. Replace `_rerun` with a public helper in `tests/proof_support.py`, `rerun(world: World, *, empty_disk: bool = False) -> World`, which advances the clock by `KILL_TO_RERUN` and then calls `restart`. Give it a docstring and call it from the new module. Leave the copies in `tests/test_fault_paths.py` (F0011-S0002) alone.
    (b) Same as (a), but also switch `tests/test_fault_paths.py` to the shared `world`, `work_item` and `rerun` and delete its copies. That removes every duplicate, but it changes a test file from another story.
    (c) Keep the tests as they are and accept the duplicates.

    I would choose (a). It fixes exactly what the reviewer found and stays inside this story's own test files. Option (b) could follow later as a story of its own.

    On your answer, I end with `tests` and name the changes for the tester.
11. human (pull request comment, 2026-10-17): (b). The tester removes every copy: the module's `world` fixture goes (the one in `tests/conftest.py` is used); `work_item` moves into `tests/conftest.py` beside `world`, with a docstring; `_rerun` becomes the public `rerun(world: World, *, empty_disk: bool = False) -> World` in `tests/proof_support.py`, with a docstring. Both `tests/test_fault_paths_7_to_13.py` and F0011-S0002's `tests/test_fault_paths.py` use the shared three and drop their copies; this is the human's leave for that change to S0002's tests (recorded as F0011 decision 20). No test changes what it asserts. `src/` stays.
12. coder: the human answered (b) in entry 11, so the reviewer's three findings go to the tester as one test change. `src/` stays as it is.

    Test change for the tester: remove all three duplicates, and keep every assertion as it is.
    - Delete the module-level `world` fixture in `tests/test_fault_paths_7_to_13.py`, so the one in `tests/conftest.py` is used.
    - Move the `work_item` fixture (`start_story(world)`) into `tests/conftest.py` beside `world`, with a docstring.
    - Replace both `_rerun` copies with one public helper in `tests/proof_support.py`: `rerun(world: World, *, empty_disk: bool = False) -> World`, with a docstring. It advances the clock by `KILL_TO_RERUN` and then calls `restart`.
    - In both `tests/test_fault_paths_7_to_13.py` and `tests/test_fault_paths.py`, use these shared three and drop the local `world`, `work_item` and `_rerun`. Entry 11 is the human's leave to change F0011-S0002's `tests/test_fault_paths.py` (F0011 decision 20).

    State: rows 7 to 13 are in `src/factory/domain/fault_paths.py` (commit e6207f4). `make check` was green as of entry 8. After the tester's change I expect it to stay green with no change under `src/`.

    Still open: `tests/test_fault_path_names.py` still checks only the first six rows. I have not touched it.
13. tester: I made the test change from entries 11 and 12 (the human's option (b)). I removed every copy of the duplicated fixture and helper. No assertion changed, and nothing under `src/` changed.

    - `tests/proof_support.py`: added the public helper `rerun(world: World, *, empty_disk: bool = False) -> World`, with a docstring. It advances the clock by `KILL_TO_RERUN`, then calls `restart(world, empty_disk=empty_disk)`.
    - `tests/conftest.py`: added the `work_item` fixture beside `world`, with a docstring. It returns `start_story(world)`. Its imports now include `WorkItemId` and `start_story`.
    - `tests/test_fault_paths_7_to_13.py`: deleted the module's own `world` and `work_item` fixtures and `_rerun`. Its calls now use `rerun`, and I dropped the imports that became unused (`KILL_TO_RERUN`, `build_world`).
    - `tests/test_fault_paths.py` (F0011-S0002's tests, changed with the human's leave in entry 11): same change. Deleted the local `world` and `work_item` fixtures and `_rerun`, switched the calls to `rerun`, and dropped the unused imports (`Path`, `KILL_TO_RERUN`, `build_world`, `start_story`).

    `make lint`: green. `make test`: green, total coverage 99.55 %.

    Still open, as before: `tests/test_fault_path_names.py` still checks only the first six rows. I did not touch it because no change to it was approved.

    `make lint`: lint: green
    `make test`: test: green
14. coder: round 1. The reviewer's three findings from entry 9 are fixed by the tester's change in entry 13, which the human approved in entry 11 as option (b). Nothing under `src/` changed this round. `make check` is green on the committed state, with total coverage at 99.55 %.

    I checked that every copy is gone:
    - `world` and `work_item` are now defined only in `tests/conftest.py` (lines 125 and 131).
    - `rerun` is the one public helper in `tests/proof_support.py:337`.
    - Neither `tests/test_fault_paths.py` nor `tests/test_fault_paths_7_to_13.py` defines its own fixture or `_rerun` any more.

    Built (unchanged since entry 8): the seven rows for paths 7 to 13 in `FAULT_PATHS`, `src/factory/domain/fault_paths.py`, commit e6207f4. The first six rows are unchanged.

    Design (as before): the paths only exercise mechanisms v1.1 already has, so they need no change under `src/`. I rejected removing the cost sidecar from beside the work item (entry 5, option (a)).

    Refactor: nothing to change. The diff under `src/` is seven data rows.

    Noticed, not touched:
    - `tests/proof_support.py:388` has a private `_rerun(world, work_item, kill, ...)` used by the kill-point cases. It also advances by `KILL_TO_RERUN` and restarts, then queues an answer and runs ticks. It could call the new public `rerun` for its first two lines. It is test code, so it is not mine to change.
    - `tests/test_fault_path_names.py` still checks only the first six rows.
    - Criterion 13 (project guide and decision log) is for the docs stage.

    `make check`: check: green

    `make check`: check: green
