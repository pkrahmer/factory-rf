# The thirteen fault-injection paths, and reject walked

## Assignment (as of log entry 1)

Walk each of v1's thirteen fault-injection paths with an injection test, and walk `reject` (path 9) with the kill that v1 never ran live. The thirteen paths are behaviour paths (a question, a rework, a cap, a close, a hand edit), none of them a kill point, and v1.1 keeps every mechanism they exercise, so no path is mapped to a removing item: each is a named test that runs the path against a real local bare remote, the fake hosting client and the fake agent runtime, with one kill or one stall added at the step the path adds, using the cases and helpers of F0011-S0001. The paths are also data (`FAULT_PATHS`), so that the project guide and the document check of F0011-S0004 name the same tests. It covers WE1.2 and WE1.3 and keeps kept thing 21 (every run is a fault-injection run, root causes recorded) and kept thing 13. Four further paths that v1's run 1 walked and that the book does not number (a restart during a stage, a close while the stages work, a discarded story started again, a merge while the move-back question is open) are not rows; the project guide notes where each went. A path that fails is a defect to fix under `src/`, never a test to bend.

## Interface

`src/factory/domain/fault_paths.py`

```python
from pydantic import BaseModel, ConfigDict


class FaultPath(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    number: int
    title: str
    case: str
    test: str


FAULT_PATHS: tuple[FaultPath, ...]
```

The thirteen rows, in number order. `case` is the id of the `KillPointCase` of F0011-S0001 whose kill the path's test arms (paths 4, 6 and 8 use `agent-run-dies`, whose stall is a scripted result, not an armed point); `test` is the name of the test function in `tests/test_fault_paths.py`.

| number | title | case | test |
|---|---|---|---|
| 1 | intake asks: a behaviour without a criterion | `agent-run-tick` | `test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once` |
| 2 | intake asks for an edge case | `commit-push` | `test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once` |
| 3 | the tester finds a criterion against the interface | `post-record` | `test_tester_question_killed_between_post_and_record_posts_once` |
| 4 | a review rework | `agent-run-dies` | `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round` |
| 5 | a documenter finding | `tick-other` | `test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts` |
| 6 | a smoke test finding | `agent-run-dies` | `test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back` |
| 7 | the round cap | `post-record` | `test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` |
| 8 | the attempts cap and its retry | `agent-run-dies` | `test_attempts_cap_run_stalls_twice_asks_human_without_retrying_and_retries_on_comment` |
| 9 | `reject` after a stage change by hand | `commit-push` | `test_reject_of_hand_stage_change_killed_between_commit_and_push_reverts_once_and_leaves_main_clean` |
| 10 | two work items in progress | `tick-other` | `test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits` |
| 11 | a close at the approval | `tick-other` | `test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once` |
| 12 | a feature acceptance refused, or merged | `container` | `test_feature_acceptance_container_lost_during_review_reclones_reruns_once_and_books_close_or_merge` |
| 13 | a test change the human approves | `agent-run-tick` | `test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round` |

`tests/proof_support.py` gains these helpers (the rest is F0011-S0001's):

```python
def drive_to(world: World, work_item: WorkItemId, stage: str) -> None: ...
def timed_out(*, writes: dict[str, str] | None = None) -> ScriptedRun: ...
```

- `drive_to` first makes sure `main` holds a `Makefile` whose targets `check`, `lint` and `test` each exit 0 (pushed with `human.push_file`); then, for a story already started with `start_story`, it runs ticks, each with one queued `completed(next[0])` run (no writes; for `tests` a file `tests/test_example.py`, for `doing` a file `src/example.py`), until the work item's `stage` is `stage` with no claim set; for `approval` it runs ticks until `handed_over == "approval"`.
- `timed_out` is a `ScriptedRun` whose result has `end_reason="time_limit"`, no decision, no entry and a duration of 40 minutes.

How the paths treat the numbers of the pipeline fixture: `round_cap` is 3 at `review`, `docs` and `smoke-test`; `attempts_cap` is 2; `ERROR_CAP` is 3. In every path test the clock is advanced by `KILL_TO_RERUN` between a kill and the restart; "the restarted runtime" is the `agent_runtime` of the world returned by `restart`; "the pull request" is `pull_request_of(world, work_item)`; the work item is the one `start_story` returned.

Tests: `tests/domain/test_fault_paths.py` (criteria 16 and 17); `tests/test_fault_paths.py` (criteria 1 to 15 and 18, one test function per path named as in the table, path 12 parametrized over `refused` and `accepted`); the helpers are in `tests/proof_support.py`.

## Acceptance criteria

1. Path 1: `start_story`; arm `AGENT_RUN`; queue `completed("question", "Which format does the title take?", writes=leak_writes(...))`; the first tick raises `InjectedKill`; advance the clock by 5 seconds; `restart`; queue the same question run without writes; three ticks. Exactly one post of kind `question` exists and its body contains `Which format does the title take?`; the work item is at stage `intake` with `blocked == "question"`, `attempts == 0` and `crashes == 1`; `repeated_posts` is empty.
2. Path 1, second half (a smoke test without `Expect:` is caught by code, not by an agent): `check_story_form(document, form, folder="backlog")` of F0002-S0005 returns no finding for the story `start_story` writes, and at least one finding for the same story with the line that follows its first Smoke test code block replaced by an empty line.
3. Path 2: `start_story`; arm `BEFORE_PUSH` with `after=1`; queue `completed("question", "Which of the two limits is meant?", writes=leak_writes(...))`; the first tick raises; read `HEAD` of the checkout (the unpushed question commit); advance 5 seconds; `restart`; queue the same question run without writes; three ticks. That commit is not reachable from any `origin/*` branch (`Git.is_ancestor` against each remote branch is false); the journal holds exactly one record of kind `question`; exactly one post of kind `question` exists; `crashes == 1` and `attempts == 0`.
4. Path 3: `drive_to(world, work_item, "tests")`; arm `AFTER_POST`; queue `completed("question", "Test and interface disagree on the order. Which wins?")`; the first tick that posts raises `InjectedKill`; advance 5 seconds; `restart`; queue nothing; three ticks. Exactly one post of kind `question` exists; the work item is at stage `tests` with `blocked == "question"`; the restarted runtime has received no request; `repeated_posts` is empty.
5. Path 4: `drive_to(world, work_item, "review")`; queue `died()`, then `completed("doing", "Finding 1: the empty list has no test.")`. After the first tick `attempts == 1`, the stage is `review` and the last journal record is of kind `stall`; after the second tick the stage is `doing`, `round == 1` and `crashes == 0`.
6. Path 5: `drive_to(world, work_item, "docs")`; arm `AFTER_PUSH` with `after=1` (the claim's push is the first, the result's push the second); queue `completed("doing", "Finding: the README example fails.")`; the first tick raises after the move-back is pushed; advance 5 seconds; `restart`; queue `completed("review", "Fixed.")`; one tick. `round == 1` (the move back is counted once), `crashes == 0`, the journal holds exactly one record of speaker `documenter` and kind `result`, and the restarted runtime has received exactly one request (the coder's stage started on the first tick).
7. Path 6: `drive_to(world, work_item, "smoke-test")`; queue `timed_out()`, then `completed("doing", "Expect not met: the title is not stripped.")`. After the first tick `attempts == 1`, the stage is `smoke-test`, and the cost sidecar holds a record with `end_reason == "time_limit"` and `cost_usd is None`; after the second tick the stage is `doing` and `round == 1`.
8. Path 7 (round cap 3): `drive_to(world, work_item, "review")`; arm `AFTER_POST`; repeat one tick with queued `completed("doing", "Finding.")` at `review` and one with queued `completed("review", "Fixed.")` at `doing`. After the third send-back `round == 3` and no post of kind `round_cap` exists; the fourth send-back asks, and the tick that posts that question raises `InjectedKill` (at most 12 ticks in all). After `restart` (clock advanced 5 seconds, nothing queued) and three ticks, exactly one post of kind `round_cap` exists, `blocked == "round_cap"`, and the restarted runtime has received no request.
9. Path 8 (attempts cap 2): `start_story`; queue `died()`, `died()`. After the first tick `attempts == 1` and the post of kind `stall` contains the word `retrying` (any case); after the second tick `attempts == 2`, `blocked == "attempts_cap"`, exactly one post of kind `attempts_cap` exists and none of the posts made in the second tick contains `retrying`; two more ticks add no request and no post. Then `hosting.add_human_comment(number, "Retry.")`, queue `completed("question", "Which format does the title take?")` and run three ticks: `attempts == 0` and the runtime has received a third request.
10. Path 9, the revert: `drive_to(world, work_item, "tests")`; `human.push_file` the work item's file on its branch with `stage: review` (not in the `next` of `tests`); arm `BEFORE_PUSH` with `after=0`; the first tick raises during the correction's push; advance 5 seconds; `restart`; three ticks. The journal holds exactly one record of kind `move_back`, the stage on `origin/<branch>` is `tests`, and exactly one post of kind `correction` exists (`test_reject_of_hand_stage_change_killed_between_commit_and_push_reverts_once_and_leaves_main_clean`, first half).
11. Path 9, the main branch: in the same scenario `origin/main` points at the commit it pointed at before the hand push, and `checkout.status().changes` is empty after the three ticks (the killed `reject` leaves nothing dirty; GH3.5).
12. Path 10: two stories started with `start_story` before the first tick (the second returns the higher id); arm `AFTER_PUSH` with `after=0`; the first tick raises after the claim of the lower id is pushed; advance 5 seconds; `restart`; queue `completed("question", "Which format does the title take?")`; three ticks. The lower id has `blocked == "question"` and `crashes == 1`; the restarted runtime has received exactly one request; the higher id has no branch on the remote (`Git.resolve("origin/work-item/<higher id>")` is `None`).
13. Path 11: `drive_to(world, work_item, "approval")`; `hosting.close_by_human(number)` with no comment; arm `AFTER_PUSH` with `after=0`; the first tick raises after the close is recorded and pushed; advance 5 seconds; `restart`; three ticks. The journal holds exactly one record of kind `close`; the pull request is `open` and a draft; exactly one post of kind `send_back` exists; `blocked == "send_back"`.
14. Path 12, parametrized over `refused` and `accepted`: `drive_to(world, work_item, "approval")`; `human.merge(branch, "merge")` and `hosting.merge_by_human(number, merge_commit)`; ticks until the story is under `done/` and the acceptance of its feature (id `<feature>-A0001`, branch `branch_name` of that id) is running; arm `AGENT_RUN`; queue `completed("approval", "Recommendation: accepted.")`; the tick raises `InjectedKill`; advance 5 seconds; `restart(world, empty_disk=True)`; queue the same run; three ticks. The restarted runtime has received exactly one request; the acceptance's pull request is ready for review; then `hosting.close_by_human(acceptance_number)` (`refused`) or `hosting.merge_by_human(...)` after `human.merge` (`accepted`) and three ticks: the acceptance, read from `origin/main`, is under `done/` and its state has `outcome == "refused"` or `"accepted"`; `repeated_posts` is empty.
15. Path 13: `drive_to(world, work_item, "doing")`; queue `completed("question", "Test T contradicts criterion 3. Change it?")`; one tick; `hosting.add_human_comment(number, "(a) the tester fixes the test.")`; queue `completed("tests", "Change test T: expect 3, not 2.")`; ticks until the stage is `tests`; arm `AGENT_RUN`; queue `completed("doing", "Changed test T.", writes=leak_writes(...))`; the tick raises; advance 5 seconds; `restart`; queue `completed("doing", "Changed test T.")`; three ticks. The stage is `doing`, `round == 0` (the move from `doing` to `tests` counts no round) and `attempts == 0`; the restarted runtime has received exactly one request; `MARKER` is in no commit's `src/leak.py`.
16. `FAULT_PATHS` holds exactly the thirteen rows of the table above, in number order, with those numbers, titles, cases and tests.
17. Every `case` of `FAULT_PATHS` is the id of a row of `KILL_POINT_CASES`.
18. Every `test` of `FAULT_PATHS` is the name of a function in `tests/test_fault_paths.py`.
19. make check stays green.
20. docs: `docs/project-guide.md` gets the section *Fault-injection paths*, a table with one row per path (number, title, case, test as `` `test_...` ``) and a note that no path is mapped to a removing item because v1.1 keeps every mechanism the thirteen exercise, followed by the four further paths of run 1 and where each went (the restart during a stage: removed by the claim and the crash rules, walked by paths 1 and 13; the close while the stages work: recorded first, no test of its own; the discarded story started again: removed by the empty bill at start; the merge while the move-back question is open: no item names it); `docs/decisions.md` records that each path is walked with one kill, by judgment, as `fault-paths.md` proposed. README and operator guide are untouched.

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
Expect: `13 True True`, then the line `test_reject_of_hand_stage_change_killed_between_commit_and_push_reverts_once_and_leaves_main_clean`.

```bash
uv run pytest tests/test_fault_paths.py tests/domain/test_fault_paths.py -q -p no:cacheprovider
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
