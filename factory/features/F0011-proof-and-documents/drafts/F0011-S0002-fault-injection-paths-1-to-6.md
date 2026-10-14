# Fault-injection paths 1 to 6

## Assignment (as of log entry 1)

Walk the first six of v1's thirteen fault-injection paths with an injection test each, and make the thirteen paths data (`FAULT_PATHS`, here its first six rows). The thirteen paths are behaviour paths (a question, a rework, a cap, a close, a hand edit), none of them a kill point, and v1.1 keeps every mechanism they exercise, so no path is mapped to a removing item: each is a named test that runs the path against a real local bare remote, the fake hosting client and the fake agent runtime, with one kill or one stall added at the step the path adds, using the cases and helpers of F0011-S0001. This story walks paths 1 to 6 (a question, an edge case, a tester question, a review rework, a documenter finding, a smoke test finding); F0011-S0003 walks paths 7 to 13, `reject` (path 9) included, and completes the table. The paths are data so that the project guide and the document check of F0011-S0005 name the same tests. It covers WE1.2 and WE1.3 and keeps kept thing 21 (every run is a fault-injection run, root causes recorded) and kept thing 13. Four further paths that v1's run 1 walked and that the book does not number (a restart during a stage, a close while the stages work, a discarded story started again, a merge while the move-back question is open) are not rows; the project guide notes where each went. A path that fails is a defect to fix under `src/`, never a test to bend.

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

The rows of this story, in number order (F0011-S0003 appends rows 7 to 13). `case` is the id of the `KillPointCase` of F0011-S0001 whose kill point the path's test arms (paths 4 and 6 use `agent-run-dies`, whose stall is a scripted result, not an armed point); the path's own crash charge may differ from the case's `charges_crash` (path 5 arms `AFTER_PUSH` after the result's push, which charges no crash), so the case names the kill point and not the class of the path. `test` is the name of the test function in `tests/test_fault_paths.py`; each row's `test` is at most 90 characters, a property of the rows that criterion 11 checks, not a validation of `FaultPath`.

| number | title | case | test |
|---|---|---|---|
| 1 | intake asks: a behaviour without a criterion | `agent-run-tick` | `test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once` |
| 2 | intake asks for an edge case | `commit-push` | `test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once` |
| 3 | the tester finds a criterion against the interface | `post-record` | `test_tester_question_killed_between_post_and_record_posts_once` |
| 4 | a review rework | `agent-run-dies` | `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round` |
| 5 | a documenter finding | `tick-other` | `test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts` |
| 6 | a smoke test finding | `agent-run-dies` | `test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back` |

The model is closed: `frozen=True` refuses the assignment of a field and `extra="forbid"` refuses an unknown key, each with a `pydantic.ValidationError`; a value of the wrong type (`number="one"`) is refused with it too.

`tests/proof_support.py` gains these helpers (the rest is F0011-S0001's):

```python
def drive_to(world: World, work_item: WorkItemId, stage: str) -> None: ...
def timed_out(*, writes: dict[str, str] | None = None) -> ScriptedRun: ...
```

- `drive_to` first makes sure `main` holds a `Makefile` whose targets `check`, `lint` and `test` each exit 0 (pushed with `human.push_file`); then, for a story already started with `start_story`, it runs ticks, each with one queued `completed(next[0])` run (no writes; for `tests` a file `tests/test_example.py`, for `doing` a file `src/example.py`), until the work item's `stage` is `stage` with no claim set; for `approval` it runs ticks until `handed_over == "approval"`.
- `timed_out` is a `ScriptedRun` whose result has `end_reason="time_limit"`, no decision, no entry and a duration of 40 minutes.

How the paths treat the numbers of the pipeline fixture: `round_cap` is 3 at `review`, `docs` and `smoke-test`; `attempts_cap` is 2; `ERROR_CAP` is 3. In every path test the clock is advanced by `KILL_TO_RERUN` between a kill and the restart; "the restarted runtime" is the `agent_runtime` of the world returned by `restart`; "the pull request" is `pull_request_of(world, work_item)`; the work item is the one `start_story` returned; a run queued for a tick that is said to raise at `AGENT_RUN` carries `kill=True`.

Tests: `tests/domain/test_fault_paths.py` (criteria 8 to 10); `tests/test_fault_path_names.py` (criterion 11); `tests/test_fault_paths.py` (criteria 1 to 7, one test function per path named as in the table); the helpers are in `tests/proof_support.py`.

## Acceptance criteria

1. Path 1: `start_story`; arm `AGENT_RUN`; queue `completed("question", "Which format does the title take?", writes=leak_writes(world, work_item), kill=True)`; the first tick raises `InjectedKill`; advance the clock by 5 seconds; `restart`; queue the same question run without writes; three ticks. Exactly one post of kind `question` exists and its body contains `Which format does the title take?`; the work item is at stage `intake` with `blocked == "question"`, `attempts == 0` and `crashes == 1`; `repeated_posts` is empty.
2. Path 1, second half (a smoke test without `Expect:` is caught by code, not by an agent): `check_story_form(document, form, folder="backlog")` of F0002-S0006 returns no finding for the story `start_story` writes, and at least one finding for the same story with the `Expect:` line that follows its first Smoke test code block replaced by an empty line (`start_story` writes the `Expect:` line directly after the block).
3. Path 2: `start_story`; arm `BEFORE_PUSH` with `after=1`; queue `completed("question", "Which of the two limits is meant?", writes=leak_writes(world, work_item))`; the first tick raises; read `HEAD` of the checkout (the unpushed question commit); advance 5 seconds; `restart`; queue the same question run without writes; three ticks. That commit is not reachable from any `origin/*` branch (`Git.is_ancestor` against each remote branch is false); the journal holds exactly one record of kind `question`; exactly one post of kind `question` exists; `crashes == 1` and `attempts == 0`.
4. Path 3: `drive_to(world, work_item, "tests")`; arm `AFTER_POST`; queue `completed("question", "Test and interface disagree on the order. Which wins?")`; the first tick that posts raises `InjectedKill`; advance 5 seconds; `restart`; queue nothing; three ticks. Exactly one post of kind `question` exists; the work item is at stage `tests` with `blocked == "question"`; the restarted runtime has received no request; `repeated_posts` is empty.
5. Path 4: `drive_to(world, work_item, "review")`; queue `died()`, then `completed("doing", "Finding 1: the empty list has no test.")`. After the first tick `attempts == 1`, the stage is `review` and the last journal record is of kind `stall`; after the second tick the stage is `doing`, `round == 1` and `crashes == 0`.
6. Path 5: `drive_to(world, work_item, "docs")`; arm `AFTER_PUSH` with `after=1` (the claim's push is the first, the result's push the second); queue `completed("doing", "Finding: the README example fails.")`; the first tick raises after the move-back is pushed; advance 5 seconds; `restart`; queue `completed("review", "Fixed.")`; one tick. `round == 1` (the move back is counted once), `crashes == 0`, the journal holds exactly one record of speaker `documenter` and kind `result`, and the restarted runtime has received exactly one request (the coder's stage started on the first tick).
7. Path 6: `drive_to(world, work_item, "smoke-test")`; queue `timed_out()`, then `completed("doing", "Expect not met: the title is not stripped.")`. After the first tick `attempts == 1`, the stage is `smoke-test`, and the cost sidecar holds a record with `end_reason == "time_limit"` and `cost_usd is None`; after the second tick the stage is `doing` and `round == 1`.
8. The first six rows of `FAULT_PATHS` are exactly the six rows of the table above, in number order, with those numbers, titles, cases and tests.
9. Every `case` of `FAULT_PATHS` is the id of a row of `KILL_POINT_CASES`.
10. A `FaultPath` is a closed model: assigning a field of a built one (`setattr` with the field name in a variable), an unknown key and `number="one"` are each rejected with `pydantic.ValidationError`, the last two constructed through a variable typed `type[BaseModel]`.
11. Every `test` of the first six rows of `FAULT_PATHS` is the name of a function in `tests/test_fault_paths.py` and is at most 90 characters long (its `def` line must fit ruff's line length of 100).
12. make check stays green.
13. docs: `docs/project-guide.md` gets the section *Fault-injection paths*, a table with one row per path built so far (number, title, case, test as `` `test_...` ``; F0011-S0003 adds the rows 7 to 13), the sentence that the case names the kill point the path arms and the path's own crash charge may differ from the case's, a note that no path is mapped to a removing item because v1.1 keeps every mechanism the thirteen exercise, and the four further paths of run 1 and where each went (the restart during a stage: removed by the claim and the crash rules, walked by paths 1 and 13; the close while the stages work: recorded first, no test of its own; the discarded story started again: removed by the empty bill at start; the merge while the move-back question is open: no item names it); `docs/decisions.md` records that each path is walked with one kill, by judgment, as `fault-paths.md` proposed. README and operator guide are untouched.

## Demo

```bash
uv run python -c "
from factory.domain.fault_paths import FAULT_PATHS
from factory.domain.kill_point_cases import KILL_POINT_CASES
ids = {c.id for c in KILL_POINT_CASES}
print(len(FAULT_PATHS) >= 6, [p.number for p in FAULT_PATHS[:6]] == list(range(1, 7)), all(p.case in ids for p in FAULT_PATHS))
print(FAULT_PATHS[3].test)
"
```
Expect: `True True True`, then the line `test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_fault_paths.py tests/domain/test_fault_paths.py
```
Expect: the last line reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
