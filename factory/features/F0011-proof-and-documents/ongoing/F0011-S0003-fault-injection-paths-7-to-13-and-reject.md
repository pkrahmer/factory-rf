---
stage: tests
pr: 147
blocked: null
comments_seen: 0
round: 0
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

- `work_item_file` is the path of the work item's file on `origin/<branch>`: the one file of `Git.list_files("origin/<branch>", "factory/features/F0001-example/in-progress")` whose name starts with the work item's id.

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
